"""
Rastreabilidade de processos de contratação.

Endpoint de leitura para gestores acompanharem a cadeia completa de cada
necessidade: Necessidade → DFD → ETP → TR → Procedimento → Contrato.

Diferente do AuditLog (trilha técnica de sistema), este módulo responde
perguntas de negócio: onde está cada processo, quais documentos existem,
quem é o responsável em cada etapa.
"""
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

_PAPEIS_PERMITIDOS = (
    'admin', 'auditor', 'gestor_planejamento',
    'analista', 'ordenador', 'gestor_contrato',
)

ETAPAS_LABEL = {
    'Necessidade':   'Identificação da Necessidade',
    'DFD':           'Documento de Formalização de Demanda',
    'ETP':           'Estudo Técnico Preliminar',
    'TR':            'Termo de Referência',
    'Procedimento':  'Procedimento Licitatório / Contratação Direta',
    'Contrato':      'Contrato',
}

STATUS_CONCLUIDO = {
    'Necessidade':  ('Aprovada', 'DFD Criado'),
    'DFD':          ('Aprovada', 'Aprovado'),
    'ETP':          ('Aprovado',),
    'TR':           ('Aprovado',),
    'Procedimento': ('Homologado', 'Adjudicado', 'Concluído', 'Dispensado', 'Encerrado'),
    'Contrato':     ('Encerrado',),
}


def _nome(user):
    if not user:
        return None
    return user.get_full_name() or user.username


def _dt(dt):
    return dt.isoformat() if dt else None


def _dias(dt):
    return (now() - dt).days if dt else None


def _rel(obj, attr):
    """Acessa reverse OneToOneField sem levantar RelatedObjectDoesNotExist."""
    try:
        return getattr(obj, attr)
    except Exception:
        return None


def _step(etapa, status, obj_id, objeto, data, responsavel, url, extras=None):
    concluida = status in STATUS_CONCLUIDO.get(etapa, ())
    d = {
        'etapa':       etapa,
        'label':       ETAPAS_LABEL[etapa],
        'status':      status,
        'concluida':   concluida,
        'id':          obj_id,
        'objeto':      objeto,
        'data':        _dt(data),
        'responsavel': responsavel,
        'url':         url,
    }
    if extras:
        d.update(extras)
    return d


def _cadeia(nec):
    """Constrói a cadeia completa de etapas para uma NecessidadePlanejamento."""
    cadeia = []

    cadeia.append(_step(
        etapa='Necessidade', status=nec.status,
        obj_id=nec.id, objeto=nec.titulo,
        data=nec.created_at, responsavel=_nome(nec.created_by),
        url=f'/planejamento/necessidades/{nec.id}',
        extras={'valor': str(nec.valor_estimado), 'prioridade': nec.prioridade},
    ))

    dfd = nec.dfd
    if not dfd:
        return cadeia

    cadeia.append(_step(
        etapa='DFD', status=dfd.status,
        obj_id=dfd.id, objeto=str(dfd),
        data=dfd.created_at, responsavel=_nome(dfd.created_by),
        url=f'/demanda/dfd/{dfd.id}',
        extras={
            'numero_sei': dfd.numero_sei or None,
            'valor': str(dfd.valor_estimado) if dfd.valor_estimado else None,
        },
    ))

    etp = _rel(dfd, 'etp')
    if not etp:
        return cadeia

    cadeia.append(_step(
        etapa='ETP', status=etp.status,
        obj_id=etp.id, objeto=str(etp),
        data=etp.created_at, responsavel=_nome(etp.created_by),
        url=f'/etp/etps/{etp.id}',
        extras={'numero_sei': etp.numero_sei or None},
    ))

    tr = _rel(etp, 'tr')
    if not tr:
        return cadeia

    cadeia.append(_step(
        etapa='TR', status=tr.status,
        obj_id=tr.id, objeto=str(tr),
        data=tr.created_at, responsavel=_nome(tr.created_by),
        url=f'/analise-tecnica/trs/{tr.id}',
        extras={'numero_sei': tr.numero_sei or None},
    ))

    for proc in dfd.procedimentos.all():
        cadeia.append(_step(
            etapa='Procedimento', status=proc.status,
            obj_id=proc.id, objeto=proc.numero or str(proc),
            data=proc.created_at, responsavel=_nome(proc.created_by),
            url=f'/licitacao/{proc.id}',
            extras={
                'modalidade': proc.modalidade,
                'valor': str(proc.valor_estimado) if proc.valor_estimado else None,
            },
        ))

    for contrato in dfd.contratos.all():
        cadeia.append(_step(
            etapa='Contrato', status=contrato.status,
            obj_id=contrato.id, objeto=contrato.objeto[:80] if contrato.objeto else None,
            data=contrato.created_at, responsavel=_nome(contrato.created_by),
            url=f'/contratos/{contrato.id}',
            extras={
                'numero': contrato.numero or None,
                'valor': str(contrato.valor_contrato) if contrato.valor_contrato else None,
                'vigencia_fim': _dt(contrato.data_vigencia_fim),
            },
        ))

    return cadeia


def _etapa_atual(cadeia):
    for i, step in enumerate(cadeia):
        if not step['concluida']:
            return step['etapa'], i
    if cadeia:
        return cadeia[-1]['etapa'], len(cadeia) - 1
    return 'Necessidade', 0


def _qs_base():
    from modulo_planejamento.models import NecessidadePlanejamento
    return (
        NecessidadePlanejamento.objects
        .select_related(
            'created_by',
            'dfd', 'dfd__created_by',
            'dfd__etp', 'dfd__etp__created_by',
            'dfd__etp__tr', 'dfd__etp__tr__created_by',
        )
        .prefetch_related(
            'dfd__procedimentos',
            'dfd__procedimentos__created_by',
            'dfd__contratos',
            'dfd__contratos__created_by',
        )
    )


def _filtrar_qs(qs, p):
    """Aplica filtros ao queryset no banco antes de carregar objetos relacionados."""
    from django.db.models import Q

    if p.get('exercicio'):
        qs = qs.filter(exercicio_fiscal=p['exercicio'])

    if p.get('prioridade'):
        qs = qs.filter(prioridade=p['prioridade'])

    # Busca por título da necessidade
    if p.get('busca'):
        qs = qs.filter(titulo__icontains=p['busca'].strip())

    # Busca por número SEI em qualquer documento da cadeia
    if p.get('sei'):
        sei = p['sei'].strip()
        qs = qs.filter(
            Q(dfd__numero_sei__icontains=sei) |
            Q(dfd__etp__numero_sei__icontains=sei) |
            Q(dfd__etp__tr__numero_sei__icontains=sei) |
            Q(dfd__contratos__numero_processo_sei__icontains=sei)
        ).distinct()

    return qs


class RastreabilidadeListView(APIView):
    """
    Lista todas as necessidades com resumo de progresso na cadeia.

    Filtros via query string:
      busca=<texto>      Busca por título da necessidade
      sei=<numero>       Busca pelo nº SEI em qualquer documento da cadeia
      exercicio=<ano>    Filtra por exercício fiscal
      prioridade=<v>     Alta | Média | Baixa
      etapa=<etapa>      Necessidade | DFD | ETP | TR | Procedimento | Contrato
      page=<n>           Página (padrão 1)
      page_size=<n>      Itens por página (padrão 50, máx 200)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from rest_framework.exceptions import PermissionDenied
        if getattr(request, 'papel', None) not in _PAPEIS_PERMITIDOS:
            raise PermissionDenied('Acesso restrito a gestores e analistas.')

        p = request.query_params
        qs = _filtrar_qs(
            _qs_base().filter(org_id=request.org_id).order_by('-created_at'),
            p,
        )

        filtro_etapa = p.get('etapa', '').strip()

        # Monta resumo linha a linha (etapa atual é computada em Python)
        resultado = []
        for nec in qs:
            cadeia = _cadeia(nec)
            etapa_nome, etapa_idx = _etapa_atual(cadeia)

            if filtro_etapa and etapa_nome != filtro_etapa:
                continue

            dfd = nec.dfd
            etp = _rel(dfd, 'etp') if dfd else None
            tr  = _rel(etp, 'tr')  if etp else None

            resultado.append({
                'id':               nec.id,
                'titulo':           nec.titulo,
                'valor_estimado':   str(nec.valor_estimado),
                'prioridade':       nec.prioridade,
                'exercicio_fiscal': nec.exercicio_fiscal,
                'status':           nec.status,
                'etapa_atual':      etapa_nome,
                'etapa_idx':        etapa_idx,
                'total_etapas':     len(cadeia),
                'tem_dfd':          dfd is not None,
                'tem_etp':          etp is not None,
                'tem_tr':           tr is not None,
                'tem_procedimento': bool(dfd and dfd.procedimentos.exists()),
                'tem_contrato':     bool(dfd and dfd.contratos.exists()),
                'data_criacao':     _dt(nec.created_at),
                'dias_em_aberto':   _dias(nec.created_at),
                'responsavel':      _nome(nec.created_by),
            })

        # Paginação em memória (após filtro de etapa em Python)
        try:
            page      = max(1, int(p.get('page', 1)))
            page_size = min(max(1, int(p.get('page_size', 50))), 200)
        except (ValueError, TypeError):
            page, page_size = 1, 50

        total       = len(resultado)
        total_pages = max(1, (total + page_size - 1) // page_size)
        start       = (page - 1) * page_size

        return Response({
            'count':       total,
            'page':        page,
            'page_size':   page_size,
            'total_pages': total_pages,
            'results':     resultado[start:start + page_size],
        })


class RastreabilidadeDetailView(APIView):
    """Cadeia completa de etapas para uma necessidade específica."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from rest_framework.exceptions import PermissionDenied
        if getattr(request, 'papel', None) not in _PAPEIS_PERMITIDOS:
            raise PermissionDenied('Acesso restrito a gestores e analistas.')

        nec = get_object_or_404(
            _qs_base().filter(org_id=request.org_id),
            pk=pk,
        )

        cadeia = _cadeia(nec)
        etapa_nome, _ = _etapa_atual(cadeia)

        return Response({
            'id':               nec.id,
            'titulo':           nec.titulo,
            'descricao':        nec.descricao,
            'valor_estimado':   str(nec.valor_estimado),
            'prioridade':       nec.prioridade,
            'exercicio_fiscal': nec.exercicio_fiscal,
            'status':           nec.status,
            'etapa_atual':      etapa_nome,
            'data_criacao':     _dt(nec.created_at),
            'dias_em_aberto':   _dias(nec.created_at),
            'responsavel':      _nome(nec.created_by),
            'cadeia':           cadeia,
        })
