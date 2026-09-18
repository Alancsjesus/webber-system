"""
Deriva automaticamente "onde está" cada DFD na cadeia DFD→ETP→TR→Procedimento,
para alimentar o Painel Gerencial de Tramitação sem exigir digitação manual do
que o sistema já sabe. Ver core/mesa_atual.py (mesa física atual, manual) e
core/views_rastreabilidade.py (STATUS_CONCLUIDO, mesma semântica de "etapa
concluída" reaproveitada aqui para consistência).
"""
from django.db.models import Q

from core.mesa_atual import mesa_atual_label
from core.views_rastreabilidade import STATUS_CONCLUIDO, _rel

# Status do Procedimento a partir dos quais a execução contratual assume —
# o processo sai do Painel de Tramitação e passa a ser coberto pelo Painel
# de Contratos. Revogado/Anulado/Deserto/Fracassado continuam visíveis aqui
# (processo "parado", ainda é informação de gestão relevante).
PROCEDIMENTO_SAI_DO_PAINEL = ('Contratado',)


def _passos_dfd(dfd):
    """Lista (etapa, registro, concluida) andando a cadeia a partir do DFD."""
    passos = [('DFD', dfd, dfd.status in STATUS_CONCLUIDO['DFD'])]

    etp = _rel(dfd, 'etp')
    if not etp:
        return passos
    passos.append(('ETP', etp, etp.status in STATUS_CONCLUIDO['ETP']))

    tr = _rel(etp, 'tr')
    if not tr:
        return passos
    passos.append(('TR', tr, tr.status in STATUS_CONCLUIDO['TR']))

    procs = list(dfd.procedimentos.all().order_by('-created_at'))
    if not procs:
        return passos
    proc = procs[0]
    concluida = proc.status in STATUS_CONCLUIDO['Procedimento'] or proc.status in PROCEDIMENTO_SAI_DO_PAINEL
    passos.append(('Procedimento', proc, concluida))

    return passos


def estagio_atual_dfd(dfd):
    """
    Retorna (etapa, registro) da etapa em aberto, ou None quando o DFD já
    passou de tudo (Procedimento contratado — execução, fora de escopo).
    """
    passos = _passos_dfd(dfd)
    for etapa, registro, concluida in passos:
        if not concluida:
            return etapa, registro
    if passos[-1][0] == 'Procedimento':
        return None
    return passos[-1][0], passos[-1][1]


def _fontes_dfd(dfd, org_id):
    from modulo_orcamento.models import IndicacaoDotacao
    nomes = (
        IndicacaoDotacao.objects
        .filter(indicacao__org_id=org_id, indicacao__dfd_id=dfd.id)
        .exclude(indicacao__status='Cancelada')
        .values_list('dotacao__fonte_recurso__nome', flat=True)
        .distinct()
    )
    return sorted({n for n in nomes if n})


def _unidade_criacao(registro):
    """
    Unidade organizacional de quem criou o registro (DFD/ETP/TR/Procedimento)
    — usada como local de elaboração/análise quando nenhuma FK estrutural de
    responsabilidade está preenchida. Nunca é o nome da etapa: DFD/ETP/TR são
    peças da fase de instrução processual do planejamento (Lei 14.133/2021),
    não lugares — o "setor" tem que ser sempre uma unidade real.
    """
    autor = registro.created_by
    if not autor:
        return None
    perfil = _rel(autor, 'profile')
    if not perfil or not perfil.unidade_id:
        return None
    return str(perfil.unidade)


def resolver_item_painel(dfd, org_id):
    """
    Resolve o item de painel de um DFD "aberto": setor (label pra agrupar),
    fase (texto), data. Ordem de prioridade documentada no plano: (1)
    TramitacaoExterna aberta do Procedimento, (2) mesa_atual manual, (3) FK
    fixa de responsabilidade da etapa (unidade_demandante/licitante/gestora),
    (4) unidade de quem criou a peça (`_unidade_criacao`), (5) fallback
    último caso — nome da etapa, só quando nem o autor tem unidade cadastrada.

    Retorna None quando o DFD já saiu do escopo do painel (execução contratual).
    """
    estagio = estagio_atual_dfd(dfd)
    if estagio is None:
        return None
    etapa, registro = estagio

    setor = None
    fase = None
    data = registro.updated_at.date() if registro.updated_at else None

    if etapa == 'Procedimento':
        tram = registro.tramitacoes.filter(data_retorno__isnull=True).order_by('-data_envio').first()
        if tram:
            setor = tram.orgao_label
            fase = f'{tram.get_tipo_display()} — {tram.status}'
            data = tram.data_envio

    if setor is None and getattr(registro, 'mesa_atual_object_id', None):
        setor = mesa_atual_label(registro)
        fase = registro.status
        if registro.data_mesa_atual:
            data = registro.data_mesa_atual

    if setor is None:
        if etapa == 'DFD' and dfd.unidade_demandante_id:
            setor = str(dfd.unidade_demandante)
        elif etapa in ('ETP', 'TR') and dfd.unidade_licitante_id:
            setor = str(dfd.unidade_licitante)
        elif etapa == 'Procedimento' and registro.unidade_gestora_id:
            setor = str(registro.unidade_gestora)
        if setor is not None:
            fase = registro.status

    if setor is None:
        setor = _unidade_criacao(registro)
        if setor is not None:
            fase = registro.status

    if setor is None:
        setor = etapa
        fase = registro.status

    return {
        'setor': setor,
        'numero_sei': dfd.numero_sei,
        'objeto': dfd.descricao,
        'fontes_recurso_nomes': _fontes_dfd(dfd, org_id),
        'fase_atual': fase,
        'data_entrada_fase': data,
        'etapa_atual': etapa,
        'etapa_registro_id': registro.id,
    }


def listar_itens_painel(request):
    """
    Monta a lista completa de itens do Painel de Tramitação — automáticos
    (todo DFD "aberto" da org, via resolver_item_painel) + manuais
    (ProcessoTramitacao sem DFD vinculado). Compartilhado por
    PainelTramitacaoView e pelos indicadores (D1), para não duplicar a
    montagem entre o painel bruto e as agregações sobre ele.
    """
    from modulo_demanda.models import DFD
    from .models import ProcessoTramitacao

    busca = request.query_params.get('busca')

    dfds = (
        DFD.objects.filter(org_id=request.org_id)
        .exclude(status='Rejeitada')
        .select_related('etp__tr', 'unidade_demandante', 'unidade_licitante',
                         'mesa_atual_content_type')
        .prefetch_related('procedimentos__tramitacoes',
                           'procedimentos__unidade_gestora',
                           'procedimentos__mesa_atual_content_type')
    )
    if busca:
        dfds = dfds.filter(Q(numero_sei__icontains=busca) | Q(descricao__icontains=busca))

    itens = []
    for dfd in dfds:
        item = resolver_item_painel(dfd, request.org_id)
        if item:
            itens.append(item)

    manuais = ProcessoTramitacao.objects.filter(
        org_id=request.org_id, ativo=True, dfd__isnull=True,
    ).prefetch_related('fontes_recurso')
    if busca:
        manuais = manuais.filter(Q(numero_sei__icontains=busca) | Q(objeto__icontains=busca))
    for p in manuais:
        itens.append({
            'setor': p.get_setor_atual_display(),
            'numero_sei': p.numero_sei,
            'objeto': p.objeto,
            'fontes_recurso_nomes': [f.nome for f in p.fontes_recurso.all()],
            'fase_atual': p.fase_atual,
            'data_entrada_fase': p.data_entrada_fase,
            'etapa_atual': None,
            'etapa_registro_id': None,
            'processo_tramitacao_id': p.id,
            'setor_atual_codigo': p.setor_atual,
        })

    return itens
