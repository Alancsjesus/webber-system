"""
Utilitários de exportação PDF e HTML para DFD, ETP e TR.
Usa ReportLab para PDF e templates Django para HTML.
"""
import hashlib
import io
from datetime import datetime
from types import SimpleNamespace

from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
import os as _os
from reportlab.platypus import (
    HRFlowable, Image as RLImage, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

_LOGO_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'static', 'logos')
_LOGOS_ORG = {
    'SSP': _os.path.join(_LOGO_DIR, 'sspba_brasao.png'),
}


# ── Paleta de cores ────────────────────────────────────────────────────────────
AZUL_GOV   = colors.HexColor('#1351B4')
AZUL_CLARO = colors.HexColor('#E8F0FE')
CINZA_BD   = colors.HexColor('#CCCCCC')
CINZA_TXT  = colors.HexColor('#555555')
PRETO      = colors.black
BRANCO     = colors.white


def _estilos():
    base = getSampleStyleSheet()
    estilos = {
        'titulo_doc': ParagraphStyle(
            'titulo_doc', parent=base['Title'],
            fontSize=16, textColor=AZUL_GOV, spaceAfter=4,
            fontName='Helvetica-Bold', alignment=TA_CENTER,
        ),
        'subtitulo': ParagraphStyle(
            'subtitulo', parent=base['Normal'],
            fontSize=10, textColor=CINZA_TXT, spaceAfter=12,
            alignment=TA_CENTER,
        ),
        'secao': ParagraphStyle(
            'secao', parent=base['Normal'],
            fontSize=11, textColor=BRANCO, spaceBefore=14, spaceAfter=4,
            fontName='Helvetica-Bold', backColor=AZUL_GOV,
            leftIndent=-6, rightIndent=-6, borderPadding=(4, 6, 4, 6),
        ),
        'label': ParagraphStyle(
            'label', parent=base['Normal'],
            fontSize=8, textColor=CINZA_TXT, fontName='Helvetica-Bold',
            spaceAfter=1,
        ),
        'valor': ParagraphStyle(
            'valor', parent=base['Normal'],
            fontSize=10, textColor=PRETO, spaceAfter=8, leading=14,
            alignment=TA_JUSTIFY,
        ),
        'rodape': ParagraphStyle(
            'rodape', parent=base['Normal'],
            fontSize=7, textColor=CINZA_TXT, alignment=TA_CENTER,
        ),
        'assinatura_nome': ParagraphStyle(
            'assinatura_nome', parent=base['Normal'],
            fontSize=10, fontName='Helvetica-Bold', alignment=TA_CENTER,
        ),
        'assinatura_cargo': ParagraphStyle(
            'assinatura_cargo', parent=base['Normal'],
            fontSize=8, textColor=CINZA_TXT, alignment=TA_CENTER,
        ),
        'aviso': ParagraphStyle(
            'aviso', parent=base['Normal'],
            fontSize=8, textColor=colors.HexColor('#856404'),
            backColor=colors.HexColor('#FFF3CD'), borderPadding=(6, 6, 6, 6),
            leftIndent=0, alignment=TA_CENTER, spaceAfter=10,
        ),
    }
    return estilos


def _campo(label, valor, estilos):
    """Retorna dois parágrafos: label em cinza + valor em preto."""
    return [
        Paragraph(label.upper(), estilos['label']),
        Paragraph(str(valor) if valor else '—', estilos['valor']),
    ]


def _secao(titulo, estilos):
    return Paragraph(f'  {titulo}', estilos['secao'])


def _hash_documento(dados: dict) -> str:
    """Gera código de verificação robusto incluindo dados do usuário criador e aprovador.
    O código pode ser validado no endpoint GET /api/verificar/<hash>/
    """
    conteudo = str(sorted(dados.items())).encode('utf-8')
    return hashlib.sha256(conteudo).hexdigest()[:20].upper()


def _dados_hash_usuario(obj, aprovador=None):
    """Coleta dados do criador e aprovador para compor o hash de verificação."""
    criador = getattr(obj, 'created_by', None)
    dados = {
        'criador_username': criador.username if criador else '',
        'criador_org':      getattr(criador, 'userprofile', None) and criador.userprofile.org_id.sigla if criador else '',
        'created_at':       obj.created_at.isoformat() if getattr(obj, 'created_at', None) else '',
    }
    if aprovador:
        dados['aprovador_username'] = aprovador.username
        dados['aprovador_org'] = getattr(aprovador, 'userprofile', None) and aprovador.userprofile.org_id.sigla
    return dados


def _rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(CINZA_TXT)
    canvas.drawString(2 * cm, 1.2 * cm, 'Sistema WEBBER — Documento gerado eletronicamente')
    canvas.drawRightString(
        A4[0] - 2 * cm, 1.2 * cm,
        f'Página {doc.page}  •  {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    )
    canvas.restoreState()


def _get_papel_org(usuario):
    """Retorna (papel_display, org_nome) do UserProfile do usuário."""
    if not usuario:
        return ('—', '—')
    try:
        profile = usuario.userprofile
        papel = profile.get_papel_display() if hasattr(profile, 'get_papel_display') else (profile.papel or '—')
        org   = profile.org_id.nome if profile.org_id else '—'
        return (papel, org)
    except Exception:
        return ('—', '—')


def _bloco_assinaturas(obj, estilos, hash_doc, aprovador_override=None, data_aprovacao_override=None):
    """Gera bloco de assinaturas com criador e aprovador."""
    elementos = []
    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(_secao('Assinaturas', estilos))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(
        'Este documento requer assinatura física ou digital (GOV.BR / SEI) para ter validade jurídica.',
        estilos['aviso'],
    ))

    def _celula(titulo, nome, papel_str, org_str, data_str):
        linhas = [
            Paragraph(titulo, ParagraphStyle(
                'tt', fontSize=8, textColor=CINZA_TXT,
                alignment=TA_CENTER, fontName='Helvetica-Bold'
            )),
            Spacer(1, 0.4 * cm),
            HRFlowable(width='90%', thickness=1, color=PRETO, hAlign='CENTER'),
            Spacer(1, 0.15 * cm),
            Paragraph(nome, ParagraphStyle('nm', fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold')),
            Paragraph(papel_str, ParagraphStyle('cg', fontSize=8, textColor=CINZA_TXT, alignment=TA_CENTER)),
            Paragraph(org_str,   ParagraphStyle('og', fontSize=8, textColor=CINZA_TXT, alignment=TA_CENTER)),
            Paragraph(data_str,  ParagraphStyle('dt', fontSize=8, textColor=CINZA_TXT, alignment=TA_CENTER)),
        ]
        return linhas

    criador      = getattr(obj, 'created_by', None)
    nome_criador = criador.get_full_name() or criador.username if criador else '—'
    papel_c, org_c = _get_papel_org(criador)
    data_criacao = obj.created_at.strftime('%d/%m/%Y %H:%M') if getattr(obj, 'created_at', None) else '—'

    # Aprovador: pode vir de override (DOD) ou do histórico
    if aprovador_override:
        aprovador    = aprovador_override
        data_aprov   = data_aprovacao_override or '—'
    else:
        aprovador    = None
        data_aprov   = '—'
        for h in obj.historico.all():
            if h.status_novo in ('Aprovada', 'Aprovado'):
                aprovador  = h.usuario
                data_aprov = h.criado_em.strftime('%d/%m/%Y %H:%M')
                break

    nome_aprov   = aprovador.get_full_name() or aprovador.username if aprovador else 'Pendente de aprovação'
    papel_a, org_a = _get_papel_org(aprovador) if aprovador else ('—', '—')

    tabela = Table(
        [[_celula('ELABORADO POR', nome_criador, papel_c, org_c, data_criacao),
          _celula('APROVADO POR',  nome_aprov,   papel_a, org_a, data_aprov)]],
        colWidths=[8 * cm, 8 * cm],
        hAlign='CENTER',
    )
    tabela.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('BOX',           (0, 0), (0, 0),   0.5, CINZA_BD),
        ('BOX',           (1, 0), (1, 0),   0.5, CINZA_BD),
    ]))
    elementos.append(tabela)

    elementos.append(Spacer(1, 0.4 * cm))
    elementos.append(Paragraph(
        f'Código de verificação: <b>{hash_doc}</b>',
        ParagraphStyle('hash', fontSize=7, textColor=CINZA_TXT, alignment=TA_CENTER),
    ))
    return elementos


def _logo_cabecalho(org_sigla):
    """Retorna Image do ReportLab para o logo da organização, ou None."""
    path = _LOGOS_ORG.get((org_sigla or '').upper())
    if path and _os.path.exists(path):
        return RLImage(path, width=2*cm, height=2*cm, kind='proportional')
    return None


def _cabecalho(tipo_doc, numero_sei, org_nome, estilos, org_sigla=None):
    logo = _logo_cabecalho(org_sigla)
    texto = [
        Paragraph(org_nome.upper() or 'WEBBER', estilos['subtitulo']),
        Paragraph(tipo_doc, estilos['titulo_doc']),
        Paragraph(f'Número SEI: {numero_sei}', estilos['subtitulo']),
    ]
    elementos = []
    if logo:
        tabela = Table([[logo, texto]], colWidths=[2.5*cm, None])
        tabela.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',        (1, 0), (1, 0),   'CENTER'),
            ('LEFTPADDING',  (0, 0), (0, 0),   0),
            ('RIGHTPADDING', (0, 0), (0, 0),   8),
        ]))
        elementos.append(tabela)
    else:
        elementos.extend(texto)
    elementos += [HRFlowable(width='100%', thickness=2, color=AZUL_GOV), Spacer(1, 0.4*cm)]
    return elementos


def _fmt_valor(v):
    """Formata decimal como moeda BRL."""
    try:
        return f'R$ {float(v):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (TypeError, ValueError):
        return '—'


# ── Seções dinâmicas ──────────────────────────────────────────────────────────

def _get_secoes(tipo, modalidade=None):
    """
    Retorna lista de SecaoArtefato ativas para o tipo, filtradas por modalidade.
    Retorna lista vazia se tabela não existir (fallback hardcoded será usado).
    """
    try:
        from core.models import SecaoArtefato
        qs = list(SecaoArtefato.objects.filter(tipo=tipo, ativo=True).order_by('ordem'))
        if modalidade and qs:
            qs = [s for s in qs if not s.aplica_modalidades or modalidade in s.aplica_modalidades]
        return qs
    except Exception:
        return []


def _valor_secao_tr(codigo, tr):
    """Mapeia código de SecaoArtefato → valor de campo do TR."""

    def _permite_consorcio_texto():
        val = getattr(tr, 'permite_consorcio', None)
        if not val:
            return None
        partes = [{'sim': 'Permite consórcio', 'nao': 'Veda consórcio'}.get(val, val)]
        just = getattr(tr, 'permite_consorcio_justificativa', None)
        if just:
            partes.append(f'Justificativa: {just}')
        return '\n'.join(partes)

    def _qualificacao_juridica_texto():
        if getattr(tr, 'qualificacao_juridica_suprimida', False):
            just = getattr(tr, 'qualificacao_juridica_justificativa', '') or ''
            return f'Suprimida — {just}' if just else 'Suprimida'
        return getattr(tr, 'qualificacao_juridica', None)

    def _qualificacao_economica_texto():
        if getattr(tr, 'qualificacao_economica_dispensada', False):
            return 'Dispensada'
        return getattr(tr, 'qualificacao_economica', None)

    def _prazos_texto():
        partes = []
        for campo, label in [
            ('prazo_recebimento_provisorio_dias', 'Recebimento Provisório'),
            ('prazo_recebimento_definitivo_dias', 'Recebimento Definitivo'),
            ('prazo_liquidacao_dias',             'Liquidação'),
            ('prazo_pagamento_dias',              'Pagamento'),
            ('prazo_providencia_irregularidade_dias', 'Providência por Irregularidade'),
        ]:
            v = getattr(tr, campo, None)
            if v is not None:
                partes.append(f'{label}: {v} dia(s)')
        return '\n'.join(partes) if partes else None

    mapa = {
        'objeto':              tr.objeto_contratacao,
        'justificativa':       tr.justificativa,
        'requisitos':          tr.requisitos_contratacao,
        'obrigacoes_contratada':  tr.obrigacoes_contratada,
        'obrigacoes_contratante': tr.obrigacoes_contratante,
        'criterios_selecao':   tr.criterios_selecao,
        'criterios_medicao':   tr.criterios_medicao,
        'prazo_vigencia':      tr.prazo_observacao,
        'local_entrega':       tr.local_entrega,
        'garantia':            tr.garantia_contrato,
        'estimativa_valor':    _fmt_valor(tr.estimativa_valor) if tr.estimativa_valor else None,
        'observacoes':         tr.observacoes,
        'parcelamento_etp':    _valor_parcelamento_etp(tr),
        # Checklist SSP-BA (C0)
        'adequacao_orcamentaria':  getattr(tr, 'adequacao_orcamentaria', None),
        'permite_consorcio':       _permite_consorcio_texto(),
        'qualificacao_juridica':   _qualificacao_juridica_texto(),
        'qualificacao_economica':  _qualificacao_economica_texto(),
        'prazos_execucao':         _prazos_texto(),
        'degrau_lances':           getattr(tr, 'degrau_lances', None),
    }
    return mapa.get(codigo) or None


def _valor_secao_etp(codigo, etp):
    """Mapeia código de SecaoArtefato → valor de campo do ETP."""

    def _parcelamento_texto():
        partes = []
        tipo_label = dict(etp.PARCELAMENTO_CHOICES).get(etp.tipo_parcelamento, '')
        if tipo_label:
            partes.append(f'Tipo: {tipo_label}')
        if etp.parcelamento_justificativa:
            partes.append(f'Justificativa: {etp.parcelamento_justificativa}')
        return '\n'.join(partes) if partes else None

    def _cota_meepp_texto():
        partes = []
        if etp.reserva_cota_me_epp:
            partes.append('Reserva de cota de 25% para ME/EPP: SIM (LC 123/2006, Art. 48, III)')
        else:
            partes.append('Reserva de cota de 25% para ME/EPP: NÃO')
            if etp.reserva_cota_justificativa:
                partes.append(f'Justificativa: {etp.reserva_cota_justificativa}')
        if etp.licitacao_exclusiva_me_epp:
            partes.append('Licitação exclusiva ME/EPP: SIM (até R$80.000)')
        return '\n'.join(partes) if partes else None

    def _classificacao_sensivel_texto():
        val = getattr(etp, 'classificacao_sensivel', None)
        if not val:
            return None
        label = {'sim': 'Sensível', 'nao': 'Não sensível'}.get(val, val)
        just = getattr(etp, 'classificacao_sensivel_justificativa', None)
        return f'{label} — {just}' if just else label

    mapa = {
        'necessidade':         etp.necessidade_contratacao,
        'requisitos':          etp.requisitos_contratacao,
        'levantamento_mercado':etp.levantamento_mercado,
        'solucao':             etp.descricao_solucao,
        'justificativa':       etp.justificativa_solucao,
        'estimativa_valor':    _fmt_valor(etp.estimativa_valor) if etp.estimativa_valor else None,
        'riscos':              etp.riscos,
        'sustentabilidade':    etp.sustentabilidade,
        'parcelamento':        _parcelamento_texto(),
        'cota_me_epp':         _cota_meepp_texto(),
        'observacoes':         etp.observacoes,
        # Checklist SSP-BA (C0)
        'posicionamento_conclusivo': getattr(etp, 'posicionamento_conclusivo', None),
        'classificacao_sensivel':    _classificacao_sensivel_texto(),
        'alinhamento_planesp':       getattr(etp, 'alinhamento_planesp', None),
        'contratacoes_correlatas':   getattr(etp, 'contratacoes_correlatas', None),
        'impacto_ambiental':         getattr(etp, 'impacto_ambiental', None),
        'providencias_pre_contrato': getattr(etp, 'providencias_pre_contrato', None),
        'compra_vs_locacao':         getattr(etp, 'compra_vs_locacao', None),
    }
    return mapa.get(codigo) or None


def _renderizar_secao_dfd(secao, dfd, estilos):
    """
    Retorna lista de flowables para uma seção do DFD.
    Seções com lógica especial (itens, responsáveis) têm renderer próprio; qualquer
    outro código cai no fallback genérico do Document Engine (template_texto ou
    campo homônimo do contexto — ver core/document_engine.py).
    Retorna [] quando não há conteúdo.
    """
    codigo = secao.codigo
    e = []

    if codigo == 'identificacao':
        e += _campo('Status', dfd.status, estilos)
        e += _campo('Classificação preliminar (triagem)', dfd.get_modalidade_aquisicao_display() if hasattr(dfd, 'get_modalidade_aquisicao_display') else dfd.modalidade_aquisicao, estilos)
        if dfd.valor_estimado:
            e += _campo('Valor Estimado', _fmt_valor(dfd.valor_estimado), estilos)

    elif codigo == 'descricao' and dfd.descricao:
        e += _campo('Descrição', dfd.descricao, estilos)

    elif codigo == 'justificativa' and dfd.justificativa_sem_planejamento:
        e += _campo('Justificativa', dfd.justificativa_sem_planejamento, estilos)

    elif codigo == 'area_aplicacao' and dfd.area_aplicacao:
        e += _campo('Áreas de Aplicação', ', '.join(dfd.area_aplicacao), estilos)

    elif codigo == 'prazo' and dfd.prazo_necessidade:
        e += _campo('Prazo de Necessidade', dfd.prazo_necessidade.strftime('%d/%m/%Y'), estilos)

    elif codigo == 'unidades':
        e += _campo('Unidade Demandante',  str(dfd.unidade_demandante)  if dfd.unidade_demandante_id  else '—', estilos)
        e += _campo('Unidade Licitante',   str(dfd.unidade_licitante)   if dfd.unidade_licitante_id   else '—', estilos)
        e += _campo('Unidade Contratante', str(dfd.unidade_contratante) if dfd.unidade_contratante_id else '—', estilos)

    elif codigo == 'responsaveis':
        def _nome(u): return (u.get_full_name() or u.username) if u else '—'
        e += _campo('Fiscal Titular',   _nome(dfd.fiscal_contrato), estilos)
        e += _campo('Fiscal Suplente',  _nome(dfd.fiscal_suplente), estilos)
        e += _campo('Gestor Titular',   _nome(dfd.gestor_contrato), estilos)
        e += _campo('Gestor Suplente',  _nome(dfd.gestor_suplente), estilos)

    elif codigo == 'vinculo_orcamentario':
        nec = getattr(dfd, 'necessidade_origem', None)
        if nec:
            e += _campo('Necessidade de Planejamento', nec.titulo, estilos)
            e += _campo('Exercício', str(nec.exercicio_fiscal), estilos)
        elif dfd.justificativa_sem_planejamento:
            e += _campo('Situação', 'Fora do planejamento — justificativa registrada', estilos)

    elif codigo == 'pca':
        pca = getattr(dfd, 'pca_previsto', None)
        if pca is not None:
            labels = {'sim': 'Sim — previsto no PCA', 'nao': 'Não previsto no PCA'}
            e += _campo('Previsto no PCA', labels.get(pca, 'Não respondido'), estilos)
        just = getattr(dfd, 'pca_justificativa_ausencia', None)
        if just:
            e += _campo('Justificativa de ausência no PCA', just, estilos)

    elif codigo == 'observacoes':
        if dfd.observacoes:
            e += _campo('Observações', dfd.observacoes, estilos)
        # Local de Entrega tem seção própria (codigo='local_entrega') via fallback
        # genérico do Document Engine — não duplicar aqui.

    elif codigo == 'itens':
        itens = dfd.itens.all()
        if itens.exists():
            _ci = ParagraphStyle('_ci', fontSize=8, leading=10, wordWrap='LTR')
            _ci_c = ParagraphStyle('_ci_c', fontSize=8, leading=10,
                                    wordWrap='LTR', alignment=TA_CENTER)
            _ci_r = ParagraphStyle('_ci_r', fontSize=8, leading=10,
                                    wordWrap='LTR', alignment=TA_RIGHT)
            _ci_h = ParagraphStyle('_ci_h', fontSize=8, leading=10,
                                    fontName='Helvetica-Bold',
                                    textColor=BRANCO, alignment=TA_CENTER)
            dados = [[Paragraph(h, _ci_h) for h in ['#', 'Objeto', 'Unid.', 'Qtd.', 'Valor Unit.', 'Total']]]
            for i, item in enumerate(itens, 1):
                dados.append([
                    Paragraph(str(i), _ci_c),
                    Paragraph(item.objeto, _ci),
                    Paragraph(item.unidade_medida, _ci_c),
                    Paragraph(str(item.quantidade), _ci_c),
                    Paragraph(_fmt_valor(item.valor_unitario_estimado), _ci_r),
                    Paragraph(_fmt_valor(item.valor_total_estimado),    _ci_r),
                ])
            t = Table(dados, colWidths=[0.8*cm, 6.5*cm, 1.5*cm, 1.5*cm, 2.5*cm, 2.5*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), AZUL_GOV),
                ('FONTSIZE',   (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
                ('GRID', (0, 0), (-1, -1), 0.5, CINZA_BD),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING',    (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            e.append(t)

    else:
        # Seção sem renderer especial (ex: uma nova seção criada no admin) — usa o
        # Document Engine: respeita template_texto se configurado, senão cai no
        # campo homônimo do contexto do DFD (ex: codigo='local_entrega').
        from core.document_engine import renderizar_secao
        texto = renderizar_secao('DFD', secao, dfd)
        if texto:
            e += _campo('', texto, estilos)

    return e


def _renderizar_lotes_tr(tr, estilos):
    """Gera flowables com a tabela de lotes do TR e seus itens."""
    e = []
    lotes = list(getattr(tr, 'lotes', None).prefetch_related('itens__item_dfd').all()) if hasattr(tr, 'lotes') else []
    if not lotes:
        return e
    for lote in lotes:
        MODAL = {'ampla': 'Ampla Concorrência', 'cota_me_epp': 'Reserva de Cota ME/EPP', 'exclusiva_me_epp': 'Exclusivo ME/EPP'}
        titulo_lote = f'{lote.numero} — {MODAL.get(lote.modalidade, lote.modalidade)}'
        if lote.lote_origem:
            titulo_lote += f' (25% de {lote.lote_origem.numero})'
        e.append(Paragraph(titulo_lote, ParagraphStyle(
            'lote_titulo', fontSize=10, fontName='Helvetica-Bold',
            textColor=AZUL_GOV, spaceBefore=8, spaceAfter=3,
        )))
        itens = list(lote.itens.select_related('item_dfd').all())
        if itens:
            _cel = ParagraphStyle('_cel_lote', fontSize=8, leading=10, wordWrap='LTR')
            _cel_r = ParagraphStyle('_cel_lote_r', fontSize=8, leading=10,
                                    wordWrap='LTR', alignment=TA_RIGHT)
            _cel_c = ParagraphStyle('_cel_lote_c', fontSize=8, leading=10,
                                    wordWrap='LTR', alignment=TA_CENTER)
            _hdr = ParagraphStyle('_hdr_lote', fontSize=8, leading=10,
                                   fontName='Helvetica-Bold', alignment=TA_CENTER)
            dados = [[Paragraph(h, _hdr) for h in ['Item', 'Unid.', 'Qtd.', 'Vl. Unit.', 'Total', 'Origem']]]
            for item in itens:
                obj  = item.item_dfd.objeto if item.item_dfd else '—'
                un   = item.item_dfd.unidade_medida if item.item_dfd else '—'
                vlu  = _fmt_valor(item.valor_unitario_efetivo)
                tot  = _fmt_valor(item.valor_total)
                orig = 'Mapa' if item.preco_origem == 'mapa' else 'DFD'
                dados.append([
                    Paragraph(obj, _cel),
                    Paragraph(un,   _cel_c),
                    Paragraph(str(item.quantidade), _cel_c),
                    Paragraph(vlu,  _cel_r),
                    Paragraph(tot,  _cel_r),
                    Paragraph(orig, _cel_c),
                ])
            t = Table(dados, colWidths=[5.5*cm, 1.2*cm, 1.5*cm, 2.5*cm, 2.5*cm, 1.3*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), AZUL_CLARO),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
                ('GRID', (0, 0), (-1, -1), 0.5, CINZA_BD),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            e.append(t)
        e += _campo('Valor total do lote', _fmt_valor(lote.valor_total), estilos)
    return e


def _valor_parcelamento_etp(tr):
    """Retorna texto com as decisões de parcelamento do ETP vinculado."""
    etp = getattr(tr, 'etp', None)
    if not etp:
        return None
    TIPOS = {'lote_unico': 'Lote único', 'lotes': 'Dividido em lotes', 'por_item': 'Por item'}
    partes = []
    if etp.tipo_parcelamento:
        partes.append(f'Tipo: {TIPOS.get(etp.tipo_parcelamento, etp.tipo_parcelamento)}')
    if etp.parcelamento_justificativa:
        partes.append(f'Justificativa: {etp.parcelamento_justificativa}')
    if etp.reserva_cota_me_epp:
        partes.append('Reserva de cota de 25% para ME/EPP: SIM (LC 123/2006, Art. 48, III)')
        if etp.licitacao_exclusiva_me_epp:
            partes.append('Licitação exclusiva ME/EPP: SIM (até R$80.000)')
    elif hasattr(etp, 'reserva_cota_justificativa') and etp.reserva_cota_justificativa:
        partes.append(f'Reserva de cota ME/EPP: NÃO — {etp.reserva_cota_justificativa}')
    return '\n'.join(partes) if partes else None


def _renderizar_secoes_tr(tr, estilos):
    """Itera seções configuradas de TR e gera flowables."""
    modalidade = getattr(tr, 'modalidade_aquisicao', None)
    secoes = _get_secoes('TR', modalidade)
    e = []

    # Códigos que retornam flowables diretos (não texto)
    FLOWABLE_CODES = {'lotes'}

    if secoes:
        from core.document_engine import renderizar_secao
        for secao in secoes:
            if secao.codigo in FLOWABLE_CODES:
                flowables = _renderizar_lotes_tr(tr, estilos)
                if flowables:
                    e.append(_secao(secao.titulo, estilos))
                    e += flowables
            else:
                valor = renderizar_secao('TR', secao, tr)
                if valor and str(valor).strip():
                    e.append(_secao(secao.titulo, estilos))
                    if secao.descricao:
                        e.append(Paragraph(secao.descricao, ParagraphStyle(
                            'orientacao', fontSize=8, textColor=CINZA_TXT,
                            fontName='Helvetica-Oblique', spaceAfter=4,
                        )))
                    e += _campo('', valor, estilos)
    else:
        # Fallback hardcoded (deploy sem setup_dev)
        fallback = [
            ('objeto',               'Objeto da Contratação'),
            ('justificativa',        'Justificativa da Contratação'),
            ('requisitos',           'Requisitos da Contratação'),
            ('obrigacoes_contratada','Obrigações da Contratada'),
            ('obrigacoes_contratante','Obrigações da Contratante'),
            ('criterios_selecao',    'Critérios de Seleção'),
            ('criterios_medicao',    'Critérios de Medição e Pagamento'),
            ('prazo_vigencia',       'Forma de Execução do Contrato'),
            ('parcelamento_etp',     'Parcelamento e Adjudicação (ETP)'),
            ('local_entrega',        'Local de Entrega'),
            ('garantia',             'Garantia Contratual'),
            ('estimativa_valor',     'Estimativa de Valor'),
            ('adequacao_orcamentaria',  'Adequação Orçamentária e Financeira'),
            ('permite_consorcio',       'Admissibilidade de Consórcio'),
            ('qualificacao_juridica',   'Qualificação Jurídica'),
            ('qualificacao_economica',  'Qualificação Econômico-Financeira'),
            ('prazos_execucao',         'Prazos de Execução e Pagamento'),
            ('degrau_lances',           'Degrau de Lances / Percentual Mínimo de Desconto'),
        ]
        for codigo, titulo in fallback:
            if codigo in FLOWABLE_CODES:
                flowables = _renderizar_lotes_tr(tr, estilos)
                if flowables:
                    e.append(_secao(titulo, estilos))
                    e += flowables
            else:
                valor = _valor_secao_tr(codigo, tr)
                if valor and str(valor).strip():
                    e.append(_secao(titulo, estilos))
                    e += _campo('', valor, estilos)

        # Lotes sempre ao final do fallback
        lotes_fl = _renderizar_lotes_tr(tr, estilos)
        if lotes_fl:
            e.append(_secao('Formação de Lotes da Licitação', estilos))
            e += lotes_fl

        # Observações por último
        obs = _valor_secao_tr('observacoes', tr)
        if obs and obs.strip():
            e.append(_secao('Observações', estilos))
            e += _campo('', obs, estilos)

    return e


def _renderizar_secoes_etp(etp, estilos):
    """Itera seções configuradas de ETP e gera flowables."""
    secoes = _get_secoes('ETP')
    e = []

    if secoes:
        from core.document_engine import renderizar_secao
        for secao in secoes:
            valor = renderizar_secao('ETP', secao, etp)
            if valor and str(valor).strip():
                e.append(_secao(secao.titulo, estilos))
                e += _campo('', valor, estilos)
    else:
        fallback = [
            ('necessidade',              'Necessidade da Contratação'),
            ('requisitos',               'Requisitos da Contratação'),
            ('levantamento_mercado',     'Levantamento de Mercado'),
            ('solucao',                  'Descrição da Solução'),
            ('justificativa',            'Justificativa da Solução'),
            ('estimativa_valor',         'Estimativa de Valor'),
            ('riscos',                   'Mapa de Riscos'),
            ('sustentabilidade',         'Sustentabilidade'),
            ('parcelamento',             'Parcelamento da Solução e Adjudicação'),
            ('cota_me_epp',              'Reserva de Cota ME/EPP (LC 123/2006)'),
            ('posicionamento_conclusivo','Posicionamento Conclusivo'),
            ('classificacao_sensivel',   'Classificação quanto à Sensibilidade'),
            ('alinhamento_planesp',      'Alinhamento ao PLANESP'),
            ('contratacoes_correlatas',  'Contratações Correlatas ou Interdependentes'),
            ('impacto_ambiental',        'Impacto Ambiental'),
            ('providencias_pre_contrato','Providências para Adequação do Ambiente'),
            ('compra_vs_locacao',        'Análise de Compra vs. Locação/Comodato'),
            ('observacoes',              'Observações'),
        ]
        for codigo, titulo in fallback:
            valor = _valor_secao_etp(codigo, etp)
            if valor and str(valor).strip():
                e.append(_secao(titulo, estilos))
                e += _campo('', valor, estilos)

    return e


def _renderizar_secoes_dfd(dfd, estilos):
    """Itera seções configuradas de DFD e gera flowables."""
    secoes = _get_secoes('DFD')
    e = []

    if secoes:
        for secao in secoes:
            flowables = _renderizar_secao_dfd(secao, dfd, estilos)
            if flowables:
                e.append(_secao(secao.titulo, estilos))
                e += flowables
    else:
        # Fallback: ordem atual do código existente
        fallback_codigos = [
            'identificacao', 'descricao', 'justificativa',
            'area_aplicacao', 'prazo', 'unidades',
            'responsaveis', 'vinculo_orcamentario', 'pca', 'itens',
            'local_entrega', 'observacoes',
        ]
        titulos_fallback = {
            'identificacao': 'Identificação',
            'descricao': 'Descrição da Demanda',
            'justificativa': 'Justificativa',
            'area_aplicacao': 'Áreas de Aplicação',
            'prazo': 'Prazo de Necessidade',
            'unidades': 'Unidades Responsáveis',
            'responsaveis': 'Responsáveis pelo Contrato',
            'vinculo_orcamentario': 'Vínculo Orçamentário',
            'pca': 'Previsão no Plano de Contratações Anual (PCA)',
            'itens': 'Itens da Demanda',
            'local_entrega': 'Local de Entrega',
            'observacoes': 'Observações',
        }
        for codigo in fallback_codigos:
            secao_ficticia = SimpleNamespace(codigo=codigo, template_texto='')
            flowables = _renderizar_secao_dfd(secao_ficticia, dfd, estilos)
            if flowables:
                e.append(_secao(titulos_fallback.get(codigo, codigo), estilos))
                e += flowables

    return e


# ── DFD ───────────────────────────────────────────────────────────────────────

def gerar_pdf_dfd(dfd) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    estilos = _estilos()
    e = []

    org_nome = dfd.org_id.nome if dfd.org_id else ''
    hash_doc = _hash_documento({
        'tipo': 'DFD', 'id': str(dfd.pk), 'sei': dfd.numero_sei,
        'valor': str(dfd.valor_estimado),
        **_dados_hash_usuario(dfd),
    })

    e += _cabecalho('DOCUMENTO DE FORMALIZAÇÃO DE DEMANDA', dfd.numero_sei, org_nome, estilos,
                    org_sigla=dfd.org_id.sigla if dfd.org_id else None)
    e += _renderizar_secoes_dfd(dfd, estilos)
    e += _bloco_assinaturas(dfd, estilos, hash_doc)
    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


# ── ETP ───────────────────────────────────────────────────────────────────────

def gerar_pdf_etp(etp) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    estilos = _estilos()
    e = []

    org_nome = etp.org_id.nome if etp.org_id else ''
    hash_doc = _hash_documento({
        'tipo': 'ETP', 'id': str(etp.pk), 'sei': etp.numero_sei,
        'valor': str(etp.estimativa_valor),
        **_dados_hash_usuario(etp),
    })

    e += _cabecalho('ESTUDO TÉCNICO PRELIMINAR', etp.numero_sei, org_nome, estilos,
                    org_sigla=etp.org_id.sigla if etp.org_id else None)

    # Bloco de identificação fixo (não configurável via SecaoArtefato)
    e.append(_secao('Identificação', estilos))
    e += _campo('Status', etp.status, estilos)
    e += _campo('DFD de Origem', etp.dfd.numero_sei if etp.dfd_id else '—', estilos)
    if etp.estimativa_valor:
        e += _campo('Estimativa de Valor', _fmt_valor(etp.estimativa_valor), estilos)
    if etp.dispensa_motivo:
        e += _campo('Motivo da Dispensa de ETP', etp.dispensa_motivo, estilos)

    e += _renderizar_secoes_etp(etp, estilos)
    e += _bloco_assinaturas(etp, estilos, hash_doc)
    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


# ── TR ────────────────────────────────────────────────────────────────────────

def gerar_pdf_tr(tr) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    estilos = _estilos()
    e = []

    org_nome = tr.org_id.nome if tr.org_id else ''
    hash_doc = _hash_documento({
        'tipo': 'TR', 'id': str(tr.pk), 'sei': tr.numero_sei,
        'valor': str(tr.estimativa_valor),
        **_dados_hash_usuario(tr),
    })

    e += _cabecalho('MINUTA DO TERMO DE REFERÊNCIA', tr.numero_sei, org_nome, estilos,
                    org_sigla=tr.org_id.sigla if tr.org_id else None)

    tipo_obj    = getattr(tr, 'tipo_objeto', '') or ''
    eh_bens     = tipo_obj in ('bens', 'hibrido')
    eh_servico  = tipo_obj in ('servicos', 'servicos_engenharia', 'hibrido')

    TIPO_OBJ_LABEL = {
        'bens':                'Bens — Aquisição de materiais/equipamentos',
        'servicos':            'Serviços Comuns',
        'servicos_engenharia': 'Serviços de Engenharia',
        'hibrido':             'Híbrido — Bens e Serviços',
        'obras':               'Obras',
    }

    # Bloco de identificação fixo
    e.append(_secao('Identificação', estilos))
    e += _campo('Status', tr.status, estilos)
    e += _campo('ETP de Origem', tr.etp.numero_sei if tr.etp_id else '—', estilos)
    if tipo_obj:
        e += _campo('Tipo de Objeto', TIPO_OBJ_LABEL.get(tipo_obj, tipo_obj), estilos)
    if getattr(tr, 'contratacao_delegada', False):
        e += _campo('Regime', 'Contratação Delegada', estilos)
    if getattr(tr, 'sistema_registro_precos', False):
        e += _campo('Instrumento', 'Sistema de Registro de Preços — ARP', estilos)
    if tr.estimativa_valor:
        e += _campo('Estimativa de Valor', _fmt_valor(tr.estimativa_valor), estilos)

    e += _renderizar_secoes_tr(tr, estilos)

    # ── Seção de Requisitos parametrizáveis ─────────────────────────────────
    _req = []
    if getattr(tr, 'req_sustentabilidade', False):
        crit = getattr(tr, 'req_sustentabilidade_criterios', '') or 'Conforme processo.'
        _req += _campo('4.1 Sustentabilidade (art. 11, IV)', crit, estilos)
    if getattr(tr, 'req_indicacao_marca', False):
        just = getattr(tr, 'req_indicacao_marca_justific', '') or 'Conforme justificativa no processo.'
        _req += _campo('4.2 Indicação de Marca — Justificativa', just, estilos)
    _exame_map = {'amostra':'Amostra','conformidade':'Exame de conformidade',
                  'prova_conceito':'Prova de conceito','certificacao':'Certificação CONMETRO','teste':'Teste específico'}
    exame = getattr(tr, 'req_exame_adequacao', 'nenhum')
    if exame and exame != 'nenhum':
        desc = f"{_exame_map.get(exame, exame)}{' — ' + tr.req_exame_descricao if tr.req_exame_descricao else ''}"
        _req += _campo('4.3 Exame de Adequação do Objeto (art. 17, §3º)', desc, estilos)
    vistoria = getattr(tr, 'req_vistoria', 'nao')
    if vistoria and vistoria != 'nao':
        _vmap = {'obrigatoria':'Vistoria obrigatória com agendamento','facultativa':'Vistoria facultativa (declaração em substituição)'}
        vdet = f"{_vmap.get(vistoria, vistoria)}{' — ' + tr.req_vistoria_detalhes if tr.req_vistoria_detalhes else ''}"
        _req += _campo('4.4 Vistoria Prévia (art. 63, §2º)', vdet, estilos)
    subcontr = getattr(tr, 'req_subcontratacao', 'nao')
    if subcontr == 'parcial':
        sdesc = getattr(tr, 'req_subcontratacao_descricao', '') or ''
        smep  = ' — Obrigatório subcontratar ME/EPP (art. 48, II, LC 123/2006).' if getattr(tr, 'req_subcontratacao_mep', False) else ''
        _req += _campo('4.5 Subcontratação', f'Parcial permitida. {sdesc}{smep}', estilos)
    else:
        _req += _campo('4.5 Subcontratação', 'Não será admitida a subcontratação do objeto contratual.', estilos)
    if getattr(tr, 'req_garantia_contratacao', False):
        perc = getattr(tr, 'req_garantia_percentual', '') or ''
        mod  = getattr(tr, 'req_garantia_modalidade', '') or 'qualquer modalidade (art. 96, §1º)'
        _req += _campo('4.6.2 Garantia da Contratação (art. 96)', f'{perc}% — {mod}', estilos)
    else:
        _req += _campo('4.6.2 Garantia da Contratação', 'Não será exigida garantia da contratação.', estilos)
    if _req:
        e.append(_secao('4. Requisitos da Contratação', estilos))
        e += _req

    # ── Seção específica BENS ────────────────────────────────────────────────
    if eh_bens:
        e.append(_secao('Seção Específica — Bens', estilos))
        if getattr(tr, 'bens_nao_luxo', True):
            e += _campo('Bem de Luxo', 'O objeto desta contratação não se enquadra como bem de luxo, nos termos do art. 20 da Lei Federal nº 14.133/2021.', estilos)
        if getattr(tr, 'bens_reserva_cota', False):
            perc = getattr(tr, 'bens_reserva_cota_percentual', 25)
            e += _campo('Reserva de Cota ME/EPP (art. 48, III, LC 123/2006)', f'Será reservada a cota de {perc}% do quantitativo licitado para microempresas e empresas de pequeno porte.', estilos)
        if getattr(tr, 'bens_carta_solidariedade', False):
            e += _campo('Carta de Solidariedade', 'Será exigida carta de solidariedade do fabricante para licitantes que não sejam o fabricante do produto.', estilos)
        if getattr(tr, 'bens_validade_pereciveis', ''):
            e += _campo('Validade Mínima dos Produtos', tr.bens_validade_pereciveis, estilos)
        if getattr(tr, 'bens_garantia_tecnica_prazo', None):
            prazo = tr.bens_garantia_tecnica_prazo
            det   = getattr(tr, 'bens_garantia_tecnica_det', '') or ''
            e += _campo('Garantia Técnica', f'Prazo: {prazo} meses. {det}', estilos)

    # ── Seção específica SERVIÇOS ────────────────────────────────────────────
    if eh_servico:
        e.append(_secao('Seção Específica — Serviços', estilos))
        transicao = getattr(tr, 'serv_transicao_contratual', False)
        if transicao:
            tdesc = getattr(tr, 'serv_transicao_descricao', '') or 'A contratada deverá realizar a transição contratual com transferência de conhecimento, tecnologia e técnicas empregadas, sem perda de informações.'
            e += _campo('Transição Contratual com Transferência de Conhecimento', tdesc, estilos)
        else:
            e += _campo('Transição Contratual', 'Não será exigida transição contratual com transferência de conhecimento.', estilos)
        if getattr(tr, 'serv_regime_execucao', ''):
            e += _campo('Regime de Execução', tr.serv_regime_execucao, estilos)
        if getattr(tr, 'serv_materiais', ''):
            e += _campo('Materiais e Equipamentos a Disponibilizar', tr.serv_materiais, estilos)
        if getattr(tr, 'serv_qualificacao_tecnica', ''):
            e += _campo('Qualificação Técnica Exigida', tr.serv_qualificacao_tecnica, estilos)
        if getattr(tr, 'serv_parcelas_relevancia', ''):
            e += _campo('Parcelas de Maior Relevância ou Valor Significativo', tr.serv_parcelas_relevancia, estilos)

    e += _bloco_assinaturas(tr, estilos, hash_doc)
    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


# ── HTML ──────────────────────────────────────────────────────────────────────

def gerar_pdf_plano_compras(dados: dict, org_nome: str, org_sigla: str = None) -> bytes:
    """
    Gera PDF do Relatório de Plano de Compras por família SIMPAS.
    dados = resultado de PlanoComprasView.get()
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    estilos = _estilos()
    e = []

    exercicio = dados.get('exercicio', '')
    titulo    = f'PLANO DE COMPRAS{" — " + str(exercicio) if exercicio else ""}'
    e += _cabecalho(titulo, 'Relatório por Família SIMPAS', org_nome, estilos, org_sigla=org_sigla)

    # Totais gerais
    e.append(_secao('Resumo Geral', estilos))
    e += _campo('Total de Famílias',  str(dados.get('total_familias', 0)), estilos)
    e += _campo('Valor Total Estimado', _fmt_valor(dados.get('valor_total', 0)), estilos)
    e += _campo('Limite de Dispensa',   _fmt_valor(dados.get('limite_dispensa', 62000)), estilos)

    MODAL_COR = {
        'pregao_eletronico': colors.HexColor('#1351B4'),
        'dispensa_agrupada': colors.HexColor('#856404'),
        'dispensa_valor':    colors.HexColor('#155724'),
    }

    for fam in dados.get('familias', []):
        cor_modal = MODAL_COR.get(fam.get('sugestao'), CINZA_TXT)
        titulo_fam = f"Família {fam['familia']} — {fam['sugestao_label']}"
        e.append(Paragraph(f'  {titulo_fam}', ParagraphStyle(
            'fam_titulo', fontSize=11, fontName='Helvetica-Bold',
            textColor=BRANCO, backColor=cor_modal,
            spaceBefore=12, spaceAfter=4, leftIndent=-6, rightIndent=-6,
            borderPadding=(4, 6, 4, 6),
        )))

        # Info da família
        info = (f"{fam['total_dfds']} DFD(s) · "
                f"Qtd. total: {fam['qtd_total']} · "
                f"Valor estimado: {_fmt_valor(fam['valor_total'])}")
        e.append(Paragraph(info, ParagraphStyle(
            'fam_info', fontSize=8, textColor=CINZA_TXT, spaceAfter=4,
        )))

        # Tabela de itens consolidados
        itens = fam.get('itens_consolidados', [])
        if itens:
            cabecalho = [['Código', 'Descrição', 'SIMPAS', 'Unid.', 'Qtd. Total', 'Vl. Unit.', 'Vl. Total', 'DFDs']]
            linhas = list(cabecalho)
            for it in itens:
                linhas.append([
                    it.get('catalogo_codigo', '—'),
                    (it.get('catalogo_nome', '—'))[:45],
                    (it.get('catalogo_simpas', '—'))[:20],
                    it.get('unidade_medida', '—'),
                    str(round(it.get('quantidade_total', 0), 2)),
                    _fmt_valor(it.get('valor_unitario', 0)),
                    _fmt_valor(it.get('valor_total_consolidado', 0)),
                    ', '.join(it.get('dfds', []))[:25],
                ])
            # Linha de total da família
            linhas.append([
                '', 'TOTAL DA FAMÍLIA', '', '', '', '',
                _fmt_valor(fam['valor_total']), '',
            ])

            t = Table(linhas, colWidths=[1.8*cm, 4.5*cm, 2.5*cm, 1.2*cm, 1.5*cm, 2*cm, 2*cm, 2*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0),  (-1, 0),   AZUL_GOV),
                ('TEXTCOLOR',     (0, 0),  (-1, 0),   BRANCO),
                ('FONTNAME',      (0, 0),  (-1, 0),   'Helvetica-Bold'),
                ('BACKGROUND',    (0, -1), (-1, -1),  AZUL_CLARO),
                ('FONTNAME',      (1, -1), (1, -1),   'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0),  (-1, -1),  7),
                ('ROWBACKGROUNDS',(0, 1),  (-1, -2),  [BRANCO, AZUL_CLARO]),
                ('GRID',          (0, 0),  (-1, -1),  0.5, CINZA_BD),
                ('ALIGN',         (3, 0),  (3, -1),   'CENTER'),  # Qtd. centrado
                ('ALIGN',         (5, 0),  (6, -1),   'RIGHT'),   # Vl. Unit. e Vl. Total à direita
                ('VALIGN',        (0, 0),  (-1, -1),  'MIDDLE'),
                ('TOPPADDING',    (0, 0),  (-1, -1),  3),
                ('BOTTOMPADDING', (0, 0),  (-1, -1),  3),
            ]))
            e.append(t)

    # Legenda de modalidades
    e.append(Spacer(1, 0.5*cm))
    legenda_dados = [
        ['Legenda de Modalidades Sugeridas', ''],
        ['Pregão Eletrônico', f'Valor total da família > R$ {_fmt_valor(dados.get("limite_dispensa", 62000))}'],
        ['Dispensa Agrupada', 'Mesma família presente em múltiplos DFDs — agrupamento recomendado'],
        ['Dispensa por Valor', 'Valor dentro do limite de dispensa e DFD único'],
    ]
    tl = Table(legenda_dados, colWidths=[5*cm, 12.5*cm])
    tl.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0),  AZUL_GOV),
        ('TEXTCOLOR',   (0, 0), (-1, 0),  BRANCO),
        ('SPAN',        (0, 0), (-1, 0)),
        ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 7),
        ('GRID',        (0, 0), (-1, -1), 0.5, CINZA_BD),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',  (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    e.append(tl)

    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


def gerar_html(tipo: str, contexto: dict) -> str:
    return render_to_string(f'exportacao/{tipo}.html', contexto)


def resposta_pdf(pdf_bytes: bytes, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def gerar_pdf_mapa(mapa) -> bytes:
    """Gera PDF do Mapa Comparativo de Preços conforme Decreto 22.886/2024."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    estilos = _estilos()
    e = []

    def fmt(v):
        return f'R$ {float(v):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    org_nome = mapa.org_id.nome if mapa.org_id else ''
    hash_doc = _hash_documento({
        'tipo': 'MAPA', 'id': str(mapa.pk),
        'objeto': mapa.objeto[:50],
        'valor': str(mapa.valor_estimado_total),
        **_dados_hash_usuario(mapa),
    })

    e += _cabecalho('MAPA COMPARATIVO DE PREÇOS', f'Mapa nº {mapa.pk}', org_nome, estilos,
                    org_sigla=mapa.org_id.sigla if mapa.org_id else None)

    # Identificação
    e.append(_secao('Identificação', estilos))
    e += _campo('Objeto da Pesquisa', mapa.objeto, estilos)
    e += _campo('Exercício Fiscal', str(mapa.exercicio_fiscal), estilos)
    e += _campo('Fundamento Legal', 'Decreto Estadual 22.886/2024 — Art. 3º e 8º', estilos)
    e += _campo('Método de Cálculo', mapa.get_metodo_calculo_display(), estilos)
    e += _campo('Status', mapa.get_status_display(), estilos)
    if mapa.dfd_id:
        e += _campo('DFD Vinculado', mapa.dfd.numero_sei, estilos)
    if mapa.responsavel:
        nome_resp = mapa.responsavel.get_full_name() or mapa.responsavel.username
        e += _campo('Responsável pela Pesquisa', nome_resp, estilos)
    if mapa.justificativa_metodologia:
        e += _campo('Justificativa da Metodologia', mapa.justificativa_metodologia, estilos)

    # Fontes consultadas
    fontes = mapa.fontes.all()
    if fontes.exists():
        e.append(_secao('Fontes Consultadas (Art. 3º, III — Decreto 22.886/2024)', estilos))
        dados_f = [['Parâmetro', 'Descrição', 'Referência', 'Data', 'Resultado']]
        for f in fontes:
            resultado = 'Infrutífera' if f.infrutífera else 'Coletada'
            dados_f.append([
                f.tipo,
                f.descricao[:35],
                f.referencia[:30] or '—',
                f.data_consulta.strftime('%d/%m/%Y') if f.data_consulta else '—',
                resultado,
            ])
        tf = Table(dados_f, colWidths=[2*cm, 5.5*cm, 4.5*cm, 2.5*cm, 2.5*cm])
        tf.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_GOV),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  BRANCO),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 7),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        e.append(tf)

    # Itens e preços coletados
    for item in mapa.itens.select_related().prefetch_related('precos__fonte').all():
        e.append(_secao(f'Item {item.ordem}: {item.descricao[:60]}', estilos))
        if item.codigo_simpas:
            e += _campo('Código SIMPAS', item.codigo_simpas, estilos)
        e += _campo('Quantidade', f'{item.quantidade} {item.unidade_medida}', estilos)

        # Tabela de preços coletados
        precos = item.precos.all()
        if precos.exists():
            dados_p = [['Origem', 'Parâmetro', 'Órgão / Empresa', 'Data', 'Valor Unit.', 'Status']]
            for p in precos:
                status_txt = '✓ Válido' if p.valido else f'✗ {p.get_motivo_exclusao_display() or "Excluído"}'
                sugestao = f' ⚠ {p.sugestao_exclusao}' if p.sugestao_exclusao and p.valido else ''
                dados_p.append([
                    p.fonte.descricao[:25],
                    p.fonte.tipo,
                    p.origem_orgao_empresa[:25] or '—',
                    p.data_referencia.strftime('%d/%m/%Y') if p.data_referencia else '—',
                    fmt(p.valor_unitario),
                    status_txt + sugestao,
                ])
            tp = Table(dados_p, colWidths=[3.5*cm, 1.5*cm, 3.5*cm, 2*cm, 2.5*cm, 4*cm])
            tp.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_GOV),
                ('TEXTCOLOR',     (0, 0), (-1, 0),  BRANCO),
                ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0), (-1, -1), 7),
                ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
                ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
                ('ALIGN',         (3, 0), (3, -1),  'CENTER'),  # Data centrada
                ('ALIGN',         (4, 0), (4, -1),  'RIGHT'),   # Valor Unit. à direita
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            e.append(tp)

        # Resultado do item
        if item.valor_unitario_calculado:
            e.append(Spacer(1, 0.2*cm))
            resultado_dados = [
                ['Método utilizado', item.get_metodo_aplicado_display() or item.metodo_aplicado,
                 'Nº preços válidos', str(item.qtd_precos_validos),
                 'Valor unit. calculado', fmt(item.valor_unitario_calculado)],
                ['', '', 'Quantidade', str(item.quantidade),
                 'VALOR TOTAL DO ITEM', fmt(item.valor_total_calculado or 0)],
            ]
            tr_item = Table(resultado_dados, colWidths=[3*cm, 3.5*cm, 2.5*cm, 1.5*cm, 3.5*cm, 3*cm])
            tr_item.setStyle(TableStyle([
                ('BACKGROUND', (4, 1), (5, 1), AZUL_CLARO),
                ('FONTNAME',   (4, 1), (5, 1), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 8),
                ('GRID',       (0, 0), (-1, -1), 0.5, CINZA_BD),
                ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            e.append(tr_item)
        if item.alerta:
            e.append(Paragraph(f'⚠ {item.alerta}', estilos['aviso']))
        if item.justificativa_item:
            e += _campo('Justificativa', item.justificativa_item, estilos)

    # Resumo geral
    e.append(_secao('Resumo Geral', estilos))
    resumo = [['Item', 'Descrição', 'Qtd', 'Unid.', 'Valor Unit.', 'Valor Total', 'Preços', 'Método']]
    for item in mapa.itens.all():
        resumo.append([
            str(item.ordem),
            item.descricao[:40],
            str(item.quantidade),
            item.unidade_medida,
            fmt(item.valor_unitario_calculado) if item.valor_unitario_calculado else '—',
            fmt(item.valor_total_calculado) if item.valor_total_calculado else '—',
            str(item.qtd_precos_validos),
            item.metodo_aplicado or '—',
        ])
    resumo.append(['', '', '', '', '', fmt(mapa.valor_estimado_total), '', ''])
    tr_resumo = Table(resumo, colWidths=[0.8*cm, 5*cm, 1*cm, 1.2*cm, 2.5*cm, 2.5*cm, 1.2*cm, 2.8*cm])
    tr_resumo.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),   AZUL_GOV),
        ('TEXTCOLOR',     (0, 0), (-1, 0),   BRANCO),
        ('FONTNAME',      (0, 0), (-1, 0),   'Helvetica-Bold'),
        ('BACKGROUND',    (0, -1),(-1, -1),  AZUL_CLARO),
        ('FONTNAME',      (4, -1),(5, -1),   'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1),  7),
        ('ROWBACKGROUNDS',(0, 1), (-1, -2),  [BRANCO, AZUL_CLARO]),
        ('GRID',          (0, 0), (-1, -1),  0.5, CINZA_BD),
        ('ALIGN',         (2, 0), (3, -1),   'CENTER'),  # Qtd. e Unid. centrados
        ('ALIGN',         (4, 0), (5, -1),   'RIGHT'),   # Valor Unit. e Total à direita
        ('VALIGN',        (0, 0), (-1, -1),  'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1),  3),
        ('BOTTOMPADDING', (0, 0), (-1, -1),  3),
    ]))
    e.append(tr_resumo)

    if mapa.observacoes:
        e += _campo('Observações Gerais', mapa.observacoes, estilos)

    e += _bloco_assinaturas(mapa, estilos, hash_doc)
    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


def _cor_status(s: str):
    """Retorna cor de fundo e texto para um status."""
    mapa = {
        'Rascunho':          (colors.HexColor('#F3F4F6'), colors.HexColor('#374151')),
        'Submetido':         (colors.HexColor('#DBEAFE'), colors.HexColor('#1E40AF')),
        'Submetida':         (colors.HexColor('#DBEAFE'), colors.HexColor('#1E40AF')),
        'Em Análise':        (colors.HexColor('#FEF3C7'), colors.HexColor('#92400E')),
        'Devolvido':         (colors.HexColor('#FFEDD5'), colors.HexColor('#9A3412')),
        'Devolvida':         (colors.HexColor('#FFEDD5'), colors.HexColor('#9A3412')),
        'Aprovado':          (colors.HexColor('#D1FAE5'), colors.HexColor('#065F46')),
        'Aprovada':          (colors.HexColor('#D1FAE5'), colors.HexColor('#065F46')),
        'Cancelado':         (colors.HexColor('#FEE2E2'), colors.HexColor('#991B1B')),
        'Cancelada':         (colors.HexColor('#FEE2E2'), colors.HexColor('#991B1B')),
        'Dispensado':        (colors.HexColor('#EDE9FE'), colors.HexColor('#5B21B6')),
        'Publicado':         (colors.HexColor('#DBEAFE'), colors.HexColor('#1E40AF')),
        'Publicada':         (colors.HexColor('#DBEAFE'), colors.HexColor('#1E40AF')),
        'Homologado':        (colors.HexColor('#D1FAE5'), colors.HexColor('#065F46')),
        'Contratado':        (colors.HexColor('#A7F3D0'), colors.HexColor('#064E3B')),
        'Deserto':           (colors.HexColor('#FEE2E2'), colors.HexColor('#991B1B')),
        'Fracassado':        (colors.HexColor('#FEE2E2'), colors.HexColor('#991B1B')),
        'Revogado':          (colors.HexColor('#F3F4F6'), colors.HexColor('#6B7280')),
        'Anulado':           (colors.HexColor('#F3F4F6'), colors.HexColor('#6B7280')),
        'Em Instrução':      (colors.HexColor('#F3F4F6'), colors.HexColor('#374151')),
        'Identificada':      (colors.HexColor('#F3F4F6'), colors.HexColor('#374151')),
        'Em Análise (Nec)':  (colors.HexColor('#FEF3C7'), colors.HexColor('#92400E')),
        'DFD Criado':        (colors.HexColor('#DBEAFE'), colors.HexColor('#1E40AF')),
    }
    return mapa.get(s, (colors.HexColor('#F9FAFB'), colors.HexColor('#374151')))


def _badge_status(s: str, font_size: int = 7):
    """Retorna um Paragraph com visual de badge colorido para o status."""
    bg, fg = _cor_status(s)
    # hexval() → '0x374151'; [2:] descarta o '0x', deixa '374151'
    fg_hex = fg.hexval()[2:].upper().zfill(6)
    return Paragraph(
        f'<font color="#{fg_hex}">{s or "—"}</font>',
        ParagraphStyle(
            f'badge_{s}', fontSize=font_size, backColor=bg,
            textColor=fg, fontName='Helvetica-Bold',
            alignment=TA_CENTER, borderPadding=(2, 4, 2, 4),
            leading=font_size + 3,
        )
    )


def gerar_pdf_historico(
    titulo: str,
    numero_ref: str,
    historico_entries,
    org_nome: str,
    org_sigla: str = None,
    criado_por=None,
    created_at=None,
) -> bytes:
    """
    Gera PDF do histórico de tramitação de qualquer artefato.
    historico_entries: queryset ou lista com campos:
        status_anterior, status_novo, usuario (FK), motivo, criado_em
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    estilos = _estilos()
    e = []

    hash_doc = _hash_documento({
        'tipo': 'HIST', 'ref': numero_ref, 'org': org_nome,
        'ts': datetime.now().isoformat(),
    })

    e += _cabecalho(f'HISTÓRICO DE TRAMITAÇÃO — {titulo}', numero_ref, org_nome, estilos, org_sigla=org_sigla)

    # Ficha de identificação
    e.append(_secao('Identificação do Documento', estilos))
    id_dados = [
        ['Tipo de artefato', titulo],
        ['Referência / Nº SEI', numero_ref],
        ['Órgão', org_nome or '—'],
        ['Criado por', (criado_por.get_full_name() or criado_por.username) if criado_por else '—'],
        ['Criado em', created_at.strftime('%d/%m/%Y às %H:%M') if created_at else '—'],
        ['Emitido em', datetime.now().strftime('%d/%m/%Y às %H:%M')],
    ]
    t_id = Table(id_dados, colWidths=[4.5*cm, 13*cm])
    t_id.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('TEXTCOLOR',     (0, 0), (0, -1), CINZA_TXT),
        ('ROWBACKGROUNDS',(0, 0), (-1, -1), [BRANCO, AZUL_CLARO]),
        ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    e.append(t_id)
    e.append(Spacer(1, 0.4*cm))

    # Linha do tempo
    e.append(_secao('Linha do Tempo das Tramitações', estilos))
    e.append(Spacer(1, 0.2*cm))

    entradas = list(historico_entries)

    if not entradas:
        e.append(Paragraph('Nenhuma tramitação registrada para este artefato.', estilos['valor']))
    else:
        entradas_ord = list(reversed(entradas))  # cronológico (mais antigo primeiro)

        # Cabeçalho da tabela
        cab = [
            Paragraph('<b>#</b>', ParagraphStyle('ch', fontSize=7, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph('<b>Data / Hora</b>', ParagraphStyle('ch', fontSize=7, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph('<b>Usuário</b>', ParagraphStyle('ch', fontSize=7, textColor=BRANCO)),
            Paragraph('<b>Status anterior</b>', ParagraphStyle('ch', fontSize=7, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph('<b>→</b>', ParagraphStyle('ch', fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph('<b>Novo status</b>', ParagraphStyle('ch', fontSize=7, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph('<b>Motivo / Observação</b>', ParagraphStyle('ch', fontSize=7, textColor=BRANCO)),
        ]
        dados = [cab]

        for i, h in enumerate(entradas_ord, 1):
            usuario = getattr(h, 'usuario', None)
            nome_u  = (usuario.get_full_name() or usuario.username) if usuario else '—'
            data_h  = h.criado_em.strftime('%d/%m/%Y\n%H:%M') if h.criado_em else '—'
            motivo  = (h.motivo or '').strip()
            cat     = getattr(h, 'categoria_motivo', '') or ''

            # Compor célula de motivo
            motivo_partes = []
            if cat:
                motivo_partes.append(Paragraph(
                    f'<b>[{cat}]</b>',
                    ParagraphStyle('cat', fontSize=6, textColor=colors.HexColor('#6B7280'), leading=8),
                ))
            if motivo:
                motivo_partes.append(Paragraph(
                    motivo[:200],
                    ParagraphStyle('mot', fontSize=7, leading=9),
                ))
            if not motivo_partes:
                motivo_partes.append(Paragraph('—', ParagraphStyle('mot', fontSize=7)))

            # Linha com zebra alternada
            linha_bg = BRANCO if i % 2 == 1 else AZUL_CLARO
            dados.append([
                Paragraph(str(i), ParagraphStyle('n', fontSize=7, alignment=TA_CENTER)),
                Paragraph(data_h, ParagraphStyle('dt', fontSize=7, alignment=TA_CENTER, leading=9)),
                Paragraph(nome_u, ParagraphStyle('u', fontSize=7, leading=9)),
                _badge_status(h.status_anterior or '—'),
                Paragraph('→', ParagraphStyle('arr', fontSize=9, alignment=TA_CENTER, textColor=AZUL_GOV)),
                _badge_status(h.status_novo or '—'),
                motivo_partes if len(motivo_partes) > 1 else motivo_partes[0],
            ])

        t = Table(dados, colWidths=[0.7*cm, 2.3*cm, 3.2*cm, 2.8*cm, 0.5*cm, 2.8*cm, 5.2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_GOV),
            ('FONTSIZE',      (0, 0), (-1, -1), 7),
            ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING',   (0, 0), (-1, -1), 4),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ]))
        e.append(t)

        # Resumo
        e.append(Spacer(1, 0.5*cm))
        ultimo = entradas_ord[-1]
        resumo_dados = [
            ['Total de tramitações', str(len(entradas_ord)),
             'Status atual', _badge_status(ultimo.status_novo or '—', font_size=8)],
        ]
        t_res = Table(resumo_dados, colWidths=[4*cm, 2*cm, 4*cm, 7.5*cm])
        t_res.setStyle(TableStyle([
            ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME',      (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('TEXTCOLOR',     (0, 0), (0, -1),  CINZA_TXT),
            ('TEXTCOLOR',     (2, 0), (2, -1),  CINZA_TXT),
            ('BOX',           (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('INNERGRID',     (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ]))
        e.append(t_res)

    # Verificação
    e.append(Spacer(1, 0.6*cm))
    e.append(HRFlowable(width='100%', thickness=0.5, color=CINZA_BD))
    e.append(Spacer(1, 0.2*cm))
    e.append(Paragraph(
        f'Código de verificação: <b>{hash_doc}</b> &nbsp;|&nbsp; '
        'Documento gerado eletronicamente pelo Sistema WEBBER &nbsp;|&nbsp; '
        f'Emitido em {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
        ParagraphStyle('hash', fontSize=7, textColor=CINZA_TXT, alignment=TA_CENTER),
    ))

    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


def resposta_html(html: str, filename: str) -> HttpResponse:
    response = HttpResponse(html, content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ── DOD / Indicação Orçamentária ──────────────────────────────────────────────

def gerar_pdf_indicacao(indicacao) -> bytes:
    """Gera PDF da Declaração do Ordenador de Despesa (DOD)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    estilos = _estilos()
    e = []

    def fmt(v):
        return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    org_nome = indicacao.org_id.nome if indicacao.org_id else ''
    hash_doc = _hash_documento({
        'tipo': 'DOD', 'id': str(indicacao.pk), 'numero': indicacao.numero,
        'exercicio': str(indicacao.exercicio_fiscal),
        'valor': str(indicacao.valor_total),
        **_dados_hash_usuario(indicacao, aprovador=indicacao.ordenador),
    })

    # Cabeçalho
    e += _cabecalho('DECLARAÇÃO DO ORDENADOR DE DESPESA', indicacao.numero, org_nome, estilos,
                    org_sigla=indicacao.org_id.sigla if indicacao.org_id else None)

    # Identificação
    e.append(_secao('Identificação', estilos))
    e += _campo('Número', indicacao.numero, estilos)
    e += _campo('Exercício Fiscal', str(indicacao.exercicio_fiscal), estilos)
    e += _campo('Status', indicacao.get_status_display(), estilos)
    if indicacao.data_aprovacao:
        e += _campo('Data de Aprovação', indicacao.data_aprovacao.strftime('%d/%m/%Y'), estilos)
    if indicacao.ordenador:
        nome_ord = indicacao.ordenador.get_full_name() or indicacao.ordenador.username
        e += _campo('Ordenador de Despesa', nome_ord, estilos)

    # Demanda vinculada
    e.append(_secao('Demanda Vinculada', estilos))
    if indicacao.dfd_id:
        e += _campo('DFD', indicacao.dfd.numero_sei, estilos)
        if indicacao.dfd.descricao:
            e += _campo('Descrição', indicacao.dfd.descricao, estilos)
    elif indicacao.necessidade_id:
        e += _campo('Necessidade', indicacao.necessidade.titulo, estilos)
        e += _campo('Exercício da Necessidade', str(indicacao.necessidade.exercicio_fiscal), estilos)
    else:
        e += _campo('Demanda', 'Não vinculada a DFD ou Necessidade', estilos)

    if indicacao.observacoes:
        e += _campo('Observações', indicacao.observacoes, estilos)

    # Dotações indicadas
    itens = indicacao.itens.select_related(
        'dotacao__acao', 'dotacao__elemento_despesa',
        'dotacao__natureza_despesa', 'dotacao__fonte_recurso'
    ).all()

    if itens.exists():
        e.append(_secao('Dotações Indicadas', estilos))
        cabecalho_tab = [['Ação', 'Elemento', 'Natureza', 'Fonte', 'Valor Indicado']]
        dados_tab = list(cabecalho_tab)
        for item in itens:
            d = item.dotacao
            nd = d.natureza_despesa
            dados_tab.append([
                f'{d.acao.codigo} — {d.acao.nome}'[:40],
                f'{d.elemento_despesa.codigo:02d} — {d.elemento_despesa.descricao}'[:30],
                f'{nd.formato}' if nd else '—',
                f'{d.fonte_recurso.codigo} — {d.fonte_recurso.nome}'[:25],
                fmt(item.valor_indicado),
            ])
        # Linha de total
        dados_tab.append(['', '', '', 'TOTAL', fmt(indicacao.valor_total)])

        t = Table(dados_tab, colWidths=[4.5*cm, 3.5*cm, 2*cm, 3*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_GOV),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  BRANCO),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS',(0, 1), (-1, -2), [BRANCO, AZUL_CLARO]),
            ('BACKGROUND',    (0, -1),(-1, -1), colors.HexColor('#E8F0FE')),
            ('FONTNAME',      (3, -1),(-1, -1), 'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('ALIGN',         (4, 0), (4, -1),  'RIGHT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        e.append(t)

    # Bloco de assinaturas com ordenador como aprovador
    aprov_override = indicacao.ordenador
    data_aprov_str = (
        indicacao.data_aprovacao.strftime('%d/%m/%Y') if indicacao.data_aprovacao else None
    )
    e += _bloco_assinaturas(
        indicacao, estilos, hash_doc,
        aprovador_override=aprov_override,
        data_aprovacao_override=data_aprov_str,
    )

    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


# ── Plano de Aplicação FESP ──────────────────────────────────────────────────

def _sim_nao(valor):
    if valor is True:
        return 'Sim'
    if valor is False:
        return 'Não'
    return 'Não respondido'


def gerar_pdf_plano_aplicacao(plano) -> bytes:
    """Gera o PDF do Plano de Aplicação (FESP / Emendas / Financiamentos)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    estilos = _estilos()
    e = []

    def fmt(v):
        return f'R$ {(v or 0):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    org_nome = plano.org_id.nome if plano.org_id else ''
    hash_doc = _hash_documento({
        'tipo': 'PLANO_APLICACAO_FESP', 'id': str(plano.pk), 'numero': plano.numero,
        'exercicio': str(plano.exercicio_fiscal),
        **_dados_hash_usuario(plano),
    })

    titulo_doc = (
        'PLANO DE APLICAÇÃO — FESP / EMENDAS / FINANCIAMENTOS' if plano.usa_rito_conselho
        else f'PLANO DE APLICAÇÃO — {plano.get_natureza_display().upper()}'
    )
    e += _cabecalho(titulo_doc, plano.numero, org_nome, estilos,
                    org_sigla=plano.org_id.sigla if plano.org_id else None)

    e.append(_secao('Identificação', estilos))
    e += _campo('Número', plano.numero, estilos)
    e += _campo('Ementa', plano.ementa, estilos)
    e += _campo('Exercício Fiscal', str(plano.exercicio_fiscal), estilos)
    e += _campo('Status', plano.get_status_display(), estilos)
    if plano.numero_ato:
        e += _campo('Ato de Homologação', plano.numero_ato, estilos)
    if plano.data_ato:
        e += _campo('Data do Ato', plano.data_ato.strftime('%d/%m/%Y'), estilos)

    if plano.responsavel_gestao_nome:
        e.append(_secao('Responsável pela Gestão do Fundo', estilos))
        e += _campo('Nome', plano.responsavel_gestao_nome, estilos)
        e += _campo('Cargo', plano.responsavel_gestao_cargo, estilos)
        e += _campo('E-mail', plano.responsavel_gestao_email, estilos)

    if plano.responsavel_elaboracao_nome:
        e.append(_secao('Responsável pela Elaboração', estilos))
        e += _campo('Nome', plano.responsavel_elaboracao_nome, estilos)
        e += _campo('Cargo', plano.responsavel_elaboracao_cargo, estilos)

    if plano.usa_rito_conselho:
        e.append(_secao('Vedações Legais (Lei 14.169/2019, art. 4º, §1º)', estilos))
        e += _campo('Não destinação a folha de pessoal/encargos', _sim_nao(plano.declaracao_nao_pessoal), estilos)
        e += _campo('Não destinação a unidade puramente administrativa', _sim_nao(plano.declaracao_nao_unidade_administrativa), estilos)
        e += _campo('Ciência de que os recursos não são contingenciáveis', _sim_nao(plano.declaracao_sem_contingenciamento), estilos)

    if plano.diagnostico:
        e.append(_secao('Diagnóstico', estilos))
        e.append(Paragraph(plano.diagnostico, estilos['valor']))
    if plano.meta_geral:
        e.append(_secao('Meta Geral', estilos))
        e.append(Paragraph(plano.meta_geral, estilos['valor']))
    if plano.justificativa:
        e.append(_secao('Justificativa', estilos))
        e.append(Paragraph(plano.justificativa, estilos['valor']))

    # Decomposição financeira
    e.append(_secao('Decomposição Financeira (R$)', estilos))
    cabecalho_tab = [['Origem', 'Investimento', 'Custeio', 'Total']]
    dados_tab = list(cabecalho_tab)
    for nome, inv, cus in [
        ('Originário',  plano.valor_originario_investimento,  plano.valor_originario_custeio),
        ('Suplementar', plano.valor_suplementar_investimento, plano.valor_suplementar_custeio),
        ('Rendimento',  plano.valor_rendimento_investimento,  plano.valor_rendimento_custeio),
        ('Planejado (alocado a itens)', plano.valor_planejado_investimento, plano.valor_planejado_custeio),
    ]:
        dados_tab.append([nome, fmt(inv), fmt(cus), fmt((inv or 0) + (cus or 0))])
    t = Table(dados_tab, colWidths=[6*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_GOV),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  BRANCO),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
        ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
        ('ALIGN',         (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    e.append(t)

    # Metas Específicas
    metas = list(plano.metas_especificas.all())
    if metas:
        e.append(_secao('Metas Específicas', estilos))
        cabecalho_tab = [['ME', 'Título', 'Status', 'Valor Total']]
        dados_tab = list(cabecalho_tab)
        for meta in metas:
            dados_tab.append([
                str(meta.numero), meta.titulo[:60], meta.get_status_display(), fmt(meta.valor_total),
            ])
        t = Table(dados_tab, colWidths=[1.5*cm, 8.5*cm, 3*cm, 3.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_GOV),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  BRANCO),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('ALIGN',         (3, 0), (3, -1),  'RIGHT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        e.append(t)

    # Instrumentos financeiros vinculados
    from modulo_fesp.models import InstrumentoFinanceiro
    instrumentos = InstrumentoFinanceiro.objects.filter(itens_plano__meta_especifica__plano=plano).distinct()
    if instrumentos.exists():
        e.append(_secao('Instrumentos Financeiros', estilos))
        cabecalho_tab = [['Tipo', 'Número', 'Valor Pactuado']]
        dados_tab = list(cabecalho_tab)
        for inst in instrumentos:
            dados_tab.append([inst.get_tipo_instrumento_display(), inst.numero_instrumento, fmt(inst.valor_total_pactuado)])
        t = Table(dados_tab, colWidths=[6*cm, 6*cm, 4.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_GOV),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  BRANCO),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('ALIGN',         (2, 0), (2, -1),  'RIGHT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        e.append(t)

    # Aprovador: usa o histórico do status que marca a aprovação nesse rito
    # ('homologado' no rito FESP, 'aprovado' no rito simples), já que os
    # status do Plano não seguem o padrão 'Aprovada'/'Aprovado' assumido
    # pelo lookup automático de _bloco_assinaturas.
    aprovador = None
    data_aprov_str = None
    status_aprovacao = 'homologado' if plano.usa_rito_conselho else 'aprovado'
    hist_aprov = plano.historico.filter(status_novo=status_aprovacao).order_by('-criado_em').first()
    if hist_aprov:
        aprovador = hist_aprov.usuario
        data_aprov_str = hist_aprov.criado_em.strftime('%d/%m/%Y %H:%M')

    e += _bloco_assinaturas(
        plano, estilos, hash_doc,
        aprovador_override=aprovador, data_aprovacao_override=data_aprov_str,
    )

    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


# ── PCA ────────────────────────────────────────────────────────────────────────

def gerar_pdf_pca(plano) -> bytes:
    """
    Gera o PDF do Plano de Contratações Anuais (IN SEGES 65/2021).
    Orientação A4 paisagem para acomodar as 12 colunas exigidas.
    """
    from reportlab.lib.pagesizes import landscape
    from decimal import Decimal

    buf    = io.BytesIO()
    estilos = _estilos()
    org    = plano.orgao

    def _rodape_pca(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(CINZA_TXT)
        w = landscape(A4)[0]
        canvas.drawString(1.5 * cm, 1.0 * cm, 'Sistema WEBBER — Documento gerado eletronicamente')
        canvas.drawRightString(w - 1.5 * cm, 1.0 * cm,
            f'Página {doc.page}  •  {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=2 * cm,    bottomMargin=2 * cm,
    )

    e = []

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    logo = _logo_cabecalho(org.sigla)
    if logo:
        e.append(logo)
        e.append(Spacer(1, 0.2 * cm))

    e.append(Paragraph(org.nome.upper(), estilos['titulo_doc']))
    e.append(Paragraph(
        f'PLANO DE CONTRATAÇÕES ANUAIS — EXERCÍCIO {plano.exercicio_fiscal}',
        ParagraphStyle('tit2', fontSize=13, textColor=AZUL_GOV,
                       fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2),
    ))
    e.append(Paragraph(
        'Instrução Normativa SEGES/ME nº 65, de 7 de julho de 2021',
        estilos['subtitulo'],
    ))
    e.append(Spacer(1, 0.3 * cm))

    # ── Metadados ────────────────────────────────────────────────────────────
    status_label = 'PUBLICADO' if plano.status_pca == 'publicado' else 'RASCUNHO'
    cor_status   = '#155724' if plano.status_pca == 'publicado' else '#856404'
    meta_data = [
        [Paragraph('<b>Órgão:</b> ' + org.nome, ParagraphStyle('m', fontSize=9)),
         Paragraph('<b>UASG/Sigla:</b> ' + org.sigla, ParagraphStyle('m', fontSize=9)),
         Paragraph('<b>Exercício:</b> ' + str(plano.exercicio_fiscal), ParagraphStyle('m', fontSize=9)),
         Paragraph(f'<b>Status:</b> <font color="{cor_status}">{status_label}</font>',
                   ParagraphStyle('m', fontSize=9))],
    ]
    meta_t = Table(meta_data, colWidths=[9*cm, 4*cm, 3*cm, 3*cm])
    meta_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_CLARO),
        ('BOX',        (0, 0), (-1, -1), 0.5, CINZA_BD),
        ('GRID',       (0, 0), (-1, -1), 0.5, CINZA_BD),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
    ]))
    e.append(meta_t)
    e.append(Spacer(1, 0.4 * cm))

    # ── Tabela principal ─────────────────────────────────────────────────────
    itens = list(plano.itens.select_related(
        'necessidade', 'necessidade__unidade_demandante',
    ).order_by('numero_sequencial_pca', 'id'))

    CABECALHO = [
        'Seq', 'Área', 'Descrição da Necessidade', 'Vl. Total (R$)',
        'Categoria', 'Prog./Ação', 'Unid. Demandante',
        'Data Est. Início', 'OE — Obj. Estratégico',
    ]
    COL_W = [0.8*cm, 1.8*cm, 7.5*cm, 2.5*cm, 2.2*cm, 2.5*cm, 3.0*cm, 2.5*cm, 3.2*cm]

    estilo_cel = ParagraphStyle('cel', fontSize=7.5, leading=10)
    estilo_hdr = ParagraphStyle('hdr', fontSize=7.5, fontName='Helvetica-Bold',
                                alignment=TA_CENTER, textColor=BRANCO)

    def fmt_v(v):
        if not v:
            return '—'
        return f'{float(v):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    def fmt_d(d):
        return d.strftime('%d/%m/%Y') if d else '—'

    dados = [[Paragraph(h, estilo_hdr) for h in CABECALHO]]
    total_geral = Decimal('0')

    for idx, item in enumerate(itens, start=1):
        nec   = item.necessidade
        areas = ', '.join(nec.area_aplicacao) if nec.area_aplicacao else '—'
        unid_dem = (nec.unidade_demandante.sigla if nec.unidade_demandante else
                    nec.departamento_solicitante or '—')
        cat   = dict(item.CATEGORIA_ORCA_CHOICES).get(item.categoria_orcamentaria, '—')
        total_geral += nec.valor_estimado or Decimal('0')

        dados.append([
            Paragraph(str(item.numero_sequencial_pca or idx), estilo_cel),
            Paragraph(areas, estilo_cel),
            Paragraph(nec.titulo, estilo_cel),
            Paragraph(fmt_v(nec.valor_estimado), estilo_cel),
            Paragraph(cat, estilo_cel),
            Paragraph(item.programa_acao or '—', estilo_cel),
            Paragraph(unid_dem, estilo_cel),
            Paragraph(fmt_d(item.data_estimada_inicio), estilo_cel),
            Paragraph(item.vinculacao_pgi or '—', estilo_cel),
        ])

    # Linha de total
    dados.append([
        Paragraph('', estilo_cel),
        Paragraph('', estilo_cel),
        Paragraph('<b>TOTAL GERAL</b>', ParagraphStyle('tot', fontSize=8,
                  fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph(f'<b>{fmt_v(total_geral)}</b>',
                  ParagraphStyle('totv', fontSize=8, fontName='Helvetica-Bold')),
        Paragraph('', estilo_cel),
        Paragraph('', estilo_cel),
        Paragraph('', estilo_cel),
        Paragraph('', estilo_cel),
        Paragraph('', estilo_cel),
    ])

    tabela = Table(dados, colWidths=COL_W, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  AZUL_GOV),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  BRANCO),
        ('ROWBACKGROUNDS',(0, 1), (-1, -2), [BRANCO, AZUL_CLARO]),
        ('BACKGROUND',    (0, -1),(-1, -1), colors.HexColor('#D1E7DD')),
        ('FONTNAME',      (0, -1),(-1, -1), 'Helvetica-Bold'),
        ('GRID',          (0, 0), (-1, -1), 0.4, CINZA_BD),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 3),
        ('ALIGN',         (3, 1), (3, -1),  'RIGHT'),
        ('SPAN',          (0, -1),(2, -1)),
    ]))
    e.append(tabela)
    e.append(Spacer(1, 0.3 * cm))

    # ── Resumo ───────────────────────────────────────────────────────────────
    resumo_data = [[
        Paragraph(f'<b>Total de itens:</b> {len(itens)}', ParagraphStyle('r', fontSize=8)),
        Paragraph(f'<b>Valor total estimado:</b> R$ {fmt_v(total_geral)}', ParagraphStyle('r', fontSize=8)),
        Paragraph(f'<b>Dotação disponível:</b> R$ {fmt_v(plano.dotacao_total)}' if plano.dotacao_total
                  else '<b>Dotação disponível:</b> —', ParagraphStyle('r', fontSize=8)),
    ]]
    resumo_t = Table(resumo_data, colWidths=[7*cm, 7*cm, 7*cm])
    resumo_t.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, -1), AZUL_CLARO),
        ('FONTSIZE',    (0, 0), (-1, -1), 8),
        ('GRID',        (0, 0), (-1, -1), 0.4, CINZA_BD),
        ('TOPPADDING',  (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',(0,0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    e.append(resumo_t)

    # ── Assinaturas ───────────────────────────────────────────────────────────
    e.append(Spacer(1, 0.5 * cm))
    e.append(_secao('Assinaturas', estilos))
    e.append(Spacer(1, 0.2 * cm))
    e.append(Paragraph(
        'Este documento requer assinatura do Ordenador de Despesas e do Gestor de Planejamento '
        'para ter validade jurídica (IN SEGES/ME nº 65/2021, art. 9º).',
        estilos['aviso'],
    ))

    ass_data = [[
        [Paragraph('GESTOR DE PLANEJAMENTO', ParagraphStyle(
            'tt', fontSize=8, textColor=CINZA_TXT, alignment=TA_CENTER, fontName='Helvetica-Bold')),
         Spacer(1, 0.6 * cm),
         HRFlowable(width='90%', thickness=1, color=PRETO, hAlign='CENTER'),
         Paragraph('Nome / Cargo', ParagraphStyle('nm', fontSize=9, alignment=TA_CENTER,
                                                   fontName='Helvetica-Bold')),
         Paragraph(org.sigla, ParagraphStyle('og', fontSize=8, textColor=CINZA_TXT,
                                              alignment=TA_CENTER))],
        [Paragraph('ORDENADOR DE DESPESAS', ParagraphStyle(
            'tt', fontSize=8, textColor=CINZA_TXT, alignment=TA_CENTER, fontName='Helvetica-Bold')),
         Spacer(1, 0.6 * cm),
         HRFlowable(width='90%', thickness=1, color=PRETO, hAlign='CENTER'),
         Paragraph('Nome / Cargo', ParagraphStyle('nm', fontSize=9, alignment=TA_CENTER,
                                                   fontName='Helvetica-Bold')),
         Paragraph(org.sigla, ParagraphStyle('og', fontSize=8, textColor=CINZA_TXT,
                                              alignment=TA_CENTER))],
    ]]
    ass_t = Table(ass_data, colWidths=[9*cm, 9*cm], hAlign='CENTER')
    ass_t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    e.append(ass_t)

    doc.build(e, onFirstPage=_rodape_pca, onLaterPages=_rodape_pca)
    return buf.getvalue()


def gerar_pdf_contrato(contrato) -> bytes:
    """Gera PDF completo do contrato com aditivos e apostilas."""
    buf    = io.BytesIO()
    org    = contrato.org_id
    estilos = _estilos()

    def _rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(CINZA_TXT)
        canvas.drawString(2 * cm, 1.0 * cm, 'Sistema WEBBER — Documento gerado eletronicamente')
        canvas.drawRightString(A4[0] - 2 * cm, 1.0 * cm,
            f'Página {doc.page}  •  {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)

    e = _cabecalho('CONTRATO', contrato.numero, org.nome if org else '', estilos,
                   org_sigla=org.sigla if org else None)

    # ── Identificação ────────────────────────────────────────────────────────
    e.append(_secao('Identificação do Contrato', estilos))

    def _fmt_data(d):
        return d.strftime('%d/%m/%Y') if d else '—'

    def _fmt_val(v):
        return f'R$ {float(v):,.2f}' if v else '—'

    dados_id = [
        ['Nº do Contrato',          contrato.numero or '—'],
        ['Exercício Fiscal',        str(contrato.exercicio)],
        ['Objeto',                  contrato.objeto or '—'],
        ['Tipo de Origem',          contrato.get_tipo_origem_display() if hasattr(contrato, 'get_tipo_origem_display') else contrato.tipo_origem],
        ['Nº Processo SEI',         contrato.numero_processo_sei or '—'],
        ['Valor do Contrato',       _fmt_val(contrato.valor_contrato)],
        ['Data de Assinatura',      _fmt_data(contrato.data_assinatura)],
        ['Vigência Início',         _fmt_data(contrato.data_vigencia_inicio)],
        ['Vigência Fim',            _fmt_data(contrato.data_vigencia_fim)],
        ['Status',                  contrato.status],
        ['Fiscal do Contrato',      getattr(contrato.fiscal_contrato, 'get_full_name', lambda: '')() or (contrato.fiscal_contrato.username if contrato.fiscal_contrato else '—')],
        ['Gestor do Contrato',      getattr(contrato.gestor_contrato, 'get_full_name', lambda: '')() or (contrato.gestor_contrato.username if contrato.gestor_contrato else '—')],
    ]
    t_id = Table(dados_id, colWidths=[4.5*cm, 13*cm])
    t_id.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('TEXTCOLOR',     (0, 0), (0, -1), CINZA_TXT),
        ('ROWBACKGROUNDS',(0, 0), (-1, -1), [BRANCO, AZUL_CLARO]),
        ('GRID',          (0, 0), (-1, -1), 0.5, CINZA_BD),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    e.append(t_id)
    e.append(Spacer(1, 0.4*cm))

    # ── Garantia ─────────────────────────────────────────────────────────────
    if contrato.garantia_exigida:
        e.append(_secao('Garantia Contratual (Lei 14.133/2021, art. 96-98)', estilos))
        dados_g = [
            ['Tipo de Garantia',     contrato.get_garantia_tipo_display() if hasattr(contrato, 'get_garantia_tipo_display') else contrato.garantia_tipo],
            ['Percentual',           f'{contrato.garantia_percentual}%' if contrato.garantia_percentual else '—'],
            ['Nº Apólice / Título',  contrato.garantia_apolice or '—'],
            ['Vigência da Garantia', f"{_fmt_data(contrato.garantia_vigencia_inicio)} a {_fmt_data(contrato.garantia_vigencia_fim)}"],
        ]
        if contrato.garantia_justificativa_acima_5:
            dados_g.append(['Justificativa > 5%', contrato.garantia_justificativa_acima_5])
        t_g = Table(dados_g, colWidths=[4.5*cm, 13*cm])
        t_g.setStyle(TableStyle([
            ('FONTNAME',  (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE',  (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (0, -1), CINZA_TXT),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID',      (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('VALIGN',    (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',(0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',(0,0),(-1,-1), 5),
            ('LEFTPADDING',(0,0),(-1,-1), 8),
        ]))
        e.append(t_g)
        e.append(Spacer(1, 0.4*cm))

    # ── Apostilas ────────────────────────────────────────────────────────────
    apostilas = list(contrato.apostilas.all().order_by('created_at'))
    if apostilas:
        e.append(_secao(f'Apostilas ({len(apostilas)})', estilos))
        cab = [['Nº', 'Data', 'Objeto']]
        rows = [[a.numero, _fmt_data(a.data), a.objeto] for a in apostilas]
        t_ap = Table(cab + rows, colWidths=[3*cm, 3*cm, 11.5*cm])
        t_ap.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0), AZUL_GOV),
            ('TEXTCOLOR',   (0, 0), (-1, 0), BRANCO),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID',        (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',  (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING',(0,0), (-1,-1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        e.append(t_ap)
        e.append(Spacer(1, 0.4*cm))

    # ── Aditivos ─────────────────────────────────────────────────────────────
    aditivos = list(contrato.aditivos.all().order_by('created_at'))
    if aditivos:
        e.append(_secao(f'Termos Aditivos ({len(aditivos)})', estilos))
        cab = [['Nº', 'Tipo', 'Data', 'Valor Acréscimo', 'Nova Vigência', 'Objeto']]
        rows = [[
            a.numero,
            a.get_tipo_display() if hasattr(a, 'get_tipo_display') else a.tipo,
            _fmt_data(a.data),
            _fmt_val(a.valor_acrescimo),
            _fmt_data(a.nova_vigencia),
            a.objeto,
        ] for a in aditivos]
        t_ad = Table(cab + rows, colWidths=[2.5*cm, 3*cm, 2.2*cm, 2.8*cm, 2.5*cm, 4.5*cm])
        t_ad.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0), AZUL_GOV),
            ('TEXTCOLOR',   (0, 0), (-1, 0), BRANCO),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID',        (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',  (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING',(0,0), (-1,-1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        e.append(t_ad)
        e.append(Spacer(1, 0.4*cm))

    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


def gerar_relatorio_procedimento(proc) -> bytes:
    """
    Relatório completo de tramitação e resultado do Procedimento.
    Seções: identificação, cronologia, peças instrutórias, fundamento legal,
    tramitações externas, histórico de status, resultados por lote.
    """
    from decimal import Decimal

    buf     = io.BytesIO()
    org     = proc.org_id
    estilos = _estilos()

    def _rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(CINZA_TXT)
        canvas.drawString(2 * cm, 1.0 * cm, 'Sistema WEBBER — Documento gerado eletronicamente')
        canvas.drawRightString(A4[0] - 2 * cm, 1.0 * cm,
            f'Página {doc.page}  •  {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)

    modalidade_label = proc.get_modalidade_display() if hasattr(proc, 'get_modalidade_display') else proc.modalidade
    e = _cabecalho(
        f'RELATÓRIO DE PROCEDIMENTO — {modalidade_label.upper()}',
        proc.numero,
        org.nome if org else '',
        estilos,
        org_sigla=org.sigla if org else None,
    )

    def _fmt_d(d):
        return d.strftime('%d/%m/%Y') if d else '—'

    def _fmt_v(v):
        return f'R$ {float(v):,.2f}' if v else '—'

    def _tab(dados, c1=4.5*cm, c2=13*cm):
        t = Table(dados, colWidths=[c1, c2])
        t.setStyle(TableStyle([
            ('FONTNAME',       (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, -1), 8),
            ('TEXTCOLOR',      (0, 0), (0, -1), CINZA_TXT),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID',           (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',     (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
            ('LEFTPADDING',    (0, 0), (-1, -1), 8),
        ]))
        return t

    sp = lambda: e.append(Spacer(1, 0.3*cm))

    # ── 1. Identificação ──────────────────────────────────────────────────────
    e.append(_secao('1. Identificação do Procedimento', estilos))
    e.append(_tab([
        ['Número',           proc.numero],
        ['Modalidade',       modalidade_label],
        ['Status atual',     proc.status],
        ['Exercício fiscal', str(proc.exercicio)],
        ['Objeto',           Paragraph(proc.objeto or '—', ParagraphStyle('obj', fontSize=8, leading=11))],
        ['Valor estimado',   _fmt_v(proc.valor_estimado)],
        ['Processo SEI',     proc.numero_sei or '—'],
        ['Unidade gestora',  proc.unidade_gestora.sigla if proc.unidade_gestora else '—'],
        ['Responsável',      (proc.created_by.get_full_name() or proc.created_by.username) if proc.created_by else '—'],
        ['Criado em',        proc.created_at.strftime('%d/%m/%Y às %H:%M') if proc.created_at else '—'],
    ]))
    sp()

    # ── 2. Cronologia ─────────────────────────────────────────────────────────
    e.append(_secao('2. Cronologia', estilos))
    dados_datas = [
        ['Publicação do edital', _fmt_d(proc.data_publicacao)],
        ['Abertura das propostas', _fmt_d(proc.data_abertura)],
        ['Homologação', _fmt_d(proc.data_homologacao)],
        ['Prazo legal mínimo', f'{proc.prazo_minimo_dias_uteis} dias úteis' if proc.prazo_minimo_dias_uteis else 'N/A'],
    ]
    if proc.alerta_prazo:
        dados_datas.append(['⚠ Alerta de prazo', proc.alerta_prazo])
    if proc.alerta_teto_dispensa:
        dados_datas.append(['⚠ Teto de dispensa', proc.alerta_teto_dispensa])
    e.append(_tab(dados_datas))
    sp()

    # ── 3. Peças instrutórias ─────────────────────────────────────────────────
    e.append(_secao('3. Peças Instrutórias', estilos))
    pecas = []
    if proc.dfd:
        dfd = proc.dfd
        pecas.append(['DFD', f"SEI: {dfd.numero_sei or '—'} | Status: {dfd.status} | {_fmt_d(dfd.created_at.date() if dfd.created_at else None)}"])
        try:
            etp = dfd.etp  # OneToOne — pode não existir
            pecas.append(['ETP', f"SEI: {etp.numero_sei or '—'} | Status: {etp.status}"])
        except Exception:
            pass
    if proc.tr:
        tr = proc.tr
        pecas.append(['Termo de Referência', f"SEI: {tr.numero_sei or '—'} | Status: {tr.status} | {_fmt_d(tr.created_at.date() if tr.created_at else None)}"])
        try:
            for lt in tr.lotes.all():
                vl = f" | Val. est.: {_fmt_v(getattr(lt, 'valor_total_estimado', None))}" if hasattr(lt, 'valor_total_estimado') else ''
                pecas.append([f'  Lote: {lt.titulo or lt.id}', f"Nº itens: {lt.itens.count() if hasattr(lt, 'itens') else '?'}{vl}"])
        except Exception:
            pass
    if not pecas:
        pecas = [['Peças', 'Nenhuma peça instrutória vinculada.']]
    e.append(_tab(pecas))
    sp()

    # ── 4. Fundamento legal ───────────────────────────────────────────────────
    tem_fund = proc.fundamento_dispensa or proc.fundamento_inexigibilidade or proc.justificativa
    if tem_fund:
        e.append(_secao('4. Fundamento Legal', estilos))
        fund_dados = []
        if proc.fundamento_dispensa:
            fund_dados.append(['Fundamento (dispensa)',
                proc.get_fundamento_dispensa_display() if hasattr(proc, 'get_fundamento_dispensa_display') else proc.fundamento_dispensa])
        if proc.fundamento_inexigibilidade:
            fund_dados.append(['Fundamento (inexigibilidade)',
                proc.get_fundamento_inexigibilidade_display() if hasattr(proc, 'get_fundamento_inexigibilidade_display') else proc.fundamento_inexigibilidade])
        if proc.valor_acumulado_dispensa:
            fund_dados.append(['Valor acumulado dispensa', _fmt_v(proc.valor_acumulado_dispensa)])
        if proc.justificativa:
            fund_dados.append(['Justificativa',
                Paragraph(proc.justificativa, ParagraphStyle('jt', fontSize=8, leading=12))])
        e.append(_tab(fund_dados))
        sp()

    # ── helpers de célula ─────────────────────────────────────────────────────
    def _p(txt, bold=False, size=7, mono=False, leading=10, color=None):
        """Cria Paragraph para célula de tabela — garante quebra de linha correta."""
        fn   = 'Helvetica-Bold' if bold else ('Courier' if mono else 'Helvetica')
        kw   = dict(fontName=fn, fontSize=size, leading=leading)
        if color:
            kw['textColor'] = color
        return Paragraph(str(txt) if txt is not None else '—', ParagraphStyle(f'tc{id(txt)}', **kw))

    def _ph(txt):
        """Cabeçalho de coluna: branco, negrito."""
        return _p(txt, bold=True, size=7, color=BRANCO)

    _TS = TableStyle([                    # estilo-base para todas as tabelas
        ('BACKGROUND',     (0, 0), (-1, 0), AZUL_GOV),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
        ('GRID',           (0, 0), (-1, -1), 0.5, CINZA_BD),
        ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',     (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
        ('LEFTPADDING',    (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 4),
    ])

    # ── 5. Tramitações externas ───────────────────────────────────────────────
    # Larguras (total = 17cm): Órgão 4.8 | Tipo 2.8 | SEI 3.5 | Envio 1.7 | Prazo 1.7 | Retorno 1.7 | Sit. 0.8
    tramitacoes = list(proc.tramitacoes.select_related('registrado_por').order_by('data_envio'))
    if tramitacoes:
        CW_TR = [4.8*cm, 2.8*cm, 3.5*cm, 1.7*cm, 1.7*cm, 1.7*cm, 0.8*cm]
        cab = [[_ph('Órgão'), _ph('Tipo'), _ph('Nº SEI'),
                _ph('Envio'), _ph('Prazo'), _ph('Retorno'), _ph('Sit.')]]
        rows = [[
            _p(t.orgao_label),
            _p(t.get_tipo_display() if hasattr(t, 'get_tipo_display') else t.tipo),
            _p(t.numero_sei or '—', mono=True, size=6.5),
            _p(_fmt_d(t.data_envio),    size=7),
            _p(_fmt_d(t.prazo_esperado), size=7),
            _p(_fmt_d(t.data_retorno),   size=7),
            _p(t.status,                 size=6.5),
        ] for t in tramitacoes]
        t_tr = Table(cab + rows, colWidths=CW_TR, repeatRows=1)
        t_tr.setStyle(_TS)
        bloco = [_secao(f'5. Tramitações Externas ({len(tramitacoes)})', estilos), t_tr]
        for t in tramitacoes:
            if t.observacoes:
                bloco.append(Paragraph(
                    f'<b>Obs. — {t.orgao_label}:</b> {t.observacoes}',
                    ParagraphStyle('tobs', fontSize=7, textColor=CINZA_TXT,
                                   leading=10, spaceBefore=3, leftIndent=8),
                ))
        e.append(KeepTogether(bloco))
        sp()

    # ── 6. Histórico de tramitação de status ──────────────────────────────────
    # Larguras (17cm): Data 2.2 | Usuário 3.2 | Status ant. 3.3 | Status novo 3.3 | Motivo 5.0
    historico = list(proc.historico.select_related('usuario').order_by('criado_em'))
    CW_HIST = [2.2*cm, 3.2*cm, 3.3*cm, 3.3*cm, 5.0*cm]
    cab_h = [[_ph('Data / Hora'), _ph('Usuário'), _ph('Status anterior'),
               _ph('Status novo'), _ph('Motivo / Observação')]]
    if historico:
        rows_h = [[
            _p(h.criado_em.strftime('%d/%m/%Y\n%H:%M') if h.criado_em else '—', size=6.5),
            _p((h.usuario.get_full_name() or h.usuario.username) if h.usuario else '—'),
            _p(h.status_anterior or '—'),
            _p(h.status_novo),
            _p(h.motivo or '—'),
        ] for h in historico]
        t_hist = Table(cab_h + rows_h, colWidths=CW_HIST, repeatRows=1)
        t_hist.setStyle(_TS)
        e.append(_secao(f'6. Histórico de Tramitação de Status ({len(historico)} registros)', estilos))
        e.append(t_hist)
    else:
        e.append(KeepTogether([
            _secao('6. Histórico de Tramitação de Status', estilos),
            Paragraph('Nenhuma tramitação registrada.',
                      ParagraphStyle('vz', fontSize=8, textColor=CINZA_TXT)),
        ]))
    sp()

    # ── 7. Resultados por lote ────────────────────────────────────────────────
    # 6 colunas (17cm): Lote 3.0 | Resultado 2.5 | Empresa 4.5 | Val.Est. 2.2 | Val.Adj. 2.2 | Contrato 2.6
    # CNPJ e Desconto ficam abaixo da empresa/valor no mesmo Paragraph
    resultados = list(proc.resultados.select_related('lote', 'contrato_gerado').order_by('descricao_lote'))
    if resultados:
        CW_RES = [3.0*cm, 2.5*cm, 4.5*cm, 2.2*cm, 2.2*cm, 2.6*cm]
        cab_r = [[_ph('Lote'), _ph('Resultado'), _ph('Empresa vencedora / CNPJ'),
                   _ph('Val. estimado'), _ph('Val. adjudicado'), _ph('Contrato')]]
        rows_r = []
        for r in resultados:
            ve   = float(r.valor_estimado or 0)
            vf   = float(r.valor_final   or 0)
            desc = f'Desconto: {((ve - vf) / ve * 100):.1f}%' if ve and vf else ''
            empresa_txt = r.empresa_vencedora or '—'
            if r.cnpj_vencedor:
                empresa_txt += f'\nCNPJ: {r.cnpj_vencedor}'
            val_adj_txt = _fmt_v(r.valor_final)
            if desc:
                val_adj_txt += f'\n({desc})'
            rows_r.append([
                _p(r.descricao_lote or (str(r.lote) if r.lote else f'Lote {r.id}')),
                _p(r.get_resultado_display() if hasattr(r, 'get_resultado_display') else r.resultado),
                _p(empresa_txt),
                _p(_fmt_v(r.valor_estimado)),
                _p(val_adj_txt),
                _p(r.contrato_gerado.numero if r.contrato_gerado else '—'),
            ])
        t_res = Table(cab_r + rows_r, colWidths=CW_RES, repeatRows=1)
        t_res.setStyle(_TS)
        bloco_r = [_secao(f'7. Resultados da Sessão / Adjudicação ({len(resultados)} lote{"s" if len(resultados) != 1 else ""})', estilos), t_res]
        for r in resultados:
            if r.observacoes:
                lote_ref = r.descricao_lote or (str(r.lote) if r.lote else f'Lote {r.id}')
                bloco_r.append(Paragraph(
                    f'<b>Obs. — {lote_ref}:</b> {r.observacoes}',
                    ParagraphStyle('robs', fontSize=7, textColor=CINZA_TXT,
                                   leading=10, spaceBefore=3, leftIndent=8),
                ))
        e.append(KeepTogether(bloco_r))
        sp()

    # ── 8. Observações e revogação ────────────────────────────────────────────
    if proc.motivo_revogacao or proc.observacoes:
        e.append(_secao('8. Observações e Motivo de Revogação', estilos))
        if proc.motivo_revogacao:
            e.append(Paragraph(
                f'<b>Motivo de revogação/anulação:</b> {proc.motivo_revogacao}',
                ParagraphStyle('rev', fontSize=8, leading=12, spaceBefore=4)))
        if proc.observacoes:
            e.append(Paragraph(
                f'<b>Observações gerais:</b> {proc.observacoes}',
                ParagraphStyle('obs2', fontSize=8, leading=12, spaceBefore=4)))
        sp()

    # ── Rodapé de emissão ─────────────────────────────────────────────────────
    e.append(Spacer(1, 0.5*cm))
    e.append(Paragraph(
        f'Relatório emitido em {datetime.now().strftime("%d/%m/%Y às %H:%M")} pelo Sistema WEBBER.',
        ParagraphStyle('emit', fontSize=7, textColor=CINZA_TXT, alignment=TA_CENTER),
    ))

    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


def gerar_pdf_auditoria(logs, org, params=None) -> bytes:
    """Gera PDF da trilha de auditoria para o período/filtros solicitados."""
    buf     = io.BytesIO()
    estilos = _estilos()

    def _rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(CINZA_TXT)
        canvas.drawString(2 * cm, 1.0 * cm,
            'Sistema WEBBER — Documento gerado eletronicamente')
        canvas.drawRightString(A4[0] - 2 * cm, 1.0 * cm,
            f'Página {doc.page}  •  {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)

    org_nome  = org.nome  if org else 'Órgão'
    org_sigla = org.sigla if org else None
    e = _cabecalho('RELATÓRIO DE AUDITORIA E CONTROLE', '', org_nome, estilos, org_sigla=org_sigla)

    e.append(_secao('Filtros aplicados', estilos))
    p = params or {}
    filtros = []
    if p.get('data_ini'): filtros.append(f"Período início: {p['data_ini']}")
    if p.get('data_fim'): filtros.append(f"Período fim: {p['data_fim']}")
    if p.get('modelo'):   filtros.append(f"Módulo: {p['modelo']}")
    if p.get('acao'):     filtros.append(f"Tipo de evento: {p['acao']}")
    if p.get('usuario'):  filtros.append(f"Usuário: {p['usuario']}")
    if p.get('busca'):    filtros.append(f"Busca: {p['busca']}")
    if not filtros:       filtros = ['Todos os registros (sem filtros)']
    ft_style = ParagraphStyle('ft', fontSize=8, textColor=CINZA_TXT, leading=12, leftIndent=8)
    for ft in filtros:
        e.append(Paragraph(f'• {ft}', ft_style))
    e.append(Paragraph(
        f'Total de registros: {len(logs)}  •  Emitido em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
        ParagraphStyle('tot', fontSize=8, textColor=CINZA_TXT, leading=12, spaceBefore=4, leftIndent=8),
    ))
    e.append(Spacer(1, 0.4*cm))

    if not logs:
        e.append(Paragraph('Nenhum registro encontrado para os filtros selecionados.',
            ParagraphStyle('vz', fontSize=9, textColor=CINZA_TXT)))
    else:
        ACAO_ICON = {
            'created':       '+ Criado',
            'deleted':       '✕ Excluído',
            'value_changed': '$ Valor',
            'sei_changed':   '# SEI',
            'login':         '> Login',
            'updated':       '~ Alterado',
        }
        ACAO_COR = {
            'created':       colors.HexColor('#16a34a'),
            'deleted':       colors.HexColor('#dc2626'),
            'value_changed': colors.HexColor('#d97706'),
            'sei_changed':   colors.HexColor('#2563eb'),
            'login':         colors.HexColor('#7c3aed'),
            'updated':       colors.HexColor('#475569'),
        }

        def _ph2(txt):
            return Paragraph(f'<b>{txt}</b>',
                ParagraphStyle('ch2', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold', leading=10))

        cab = [[_ph2('Data / Hora'), _ph2('Módulo'), _ph2('Evento'), _ph2('Descrição'), _ph2('Usuário')]]
        rows = []
        for lg in logs:
            dt       = lg.criado_em.strftime('%d/%m/%Y\n%H:%M') if lg.criado_em else '—'
            mod      = lg.modelo.split('.')[-1] if '.' in lg.modelo else lg.modelo
            acao_txt = ACAO_ICON.get(lg.acao, lg.acao)
            acao_cor = ACAO_COR.get(lg.acao, CINZA_TXT)
            usr      = (lg.usuario.get_full_name() or lg.usuario.username) if lg.usuario else '—'
            rows.append([
                Paragraph(dt,  ParagraphStyle('td0', fontSize=6.5, leading=9,  fontName='Courier')),
                Paragraph(mod, ParagraphStyle('td1', fontSize=7,   leading=10)),
                Paragraph(f'<b>{acao_txt}</b>',
                    ParagraphStyle('ta', fontSize=7, leading=10, textColor=acao_cor, fontName='Helvetica-Bold')),
                Paragraph(lg.descricao or lg.objeto_repr or '—',
                    ParagraphStyle('td3', fontSize=7, leading=10)),
                Paragraph(usr, ParagraphStyle('td4', fontSize=7, leading=10)),
            ])

        t = Table(cab + rows, colWidths=[2.5*cm, 2.5*cm, 2.2*cm, 7.3*cm, 2.5*cm], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1, 0), AZUL_GOV),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID',           (0, 0), (-1, -1), 0.4, CINZA_BD),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',     (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
            ('LEFTPADDING',    (0, 0), (-1, -1), 5),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 4),
        ]))
        e.append(t)

    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


# ── Helpers compartilhados pelos relatórios de processo ───────────────────────

def _cabecalho_relatorio(titulo, subtitulo, org, estilos):
    """
    Cabeçalho visual com logo do órgão, título, subtítulo e data de extração.
    Mantém identidade visual dos demais PDFs do sistema.
    """
    logo      = _logo_cabecalho(org.sigla if org else None)
    org_nome  = org.nome.upper() if org else 'WEBBER'
    data_ext  = datetime.now().strftime('%d/%m/%Y às %H:%M')

    bloco_texto = [
        Paragraph(org_nome, ParagraphStyle('on', fontSize=8, textColor=CINZA_TXT,
                                            fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph(titulo, ParagraphStyle('tit', fontSize=15, textColor=AZUL_GOV,
                                          fontName='Helvetica-Bold', alignment=TA_CENTER,
                                          spaceAfter=2)),
        Paragraph(subtitulo, ParagraphStyle('sub', fontSize=9, textColor=CINZA_TXT,
                                             alignment=TA_CENTER, spaceAfter=2)),
        Paragraph(f'Data de extração: {data_ext}',
                  ParagraphStyle('dt', fontSize=7.5, textColor=CINZA_TXT,
                                  alignment=TA_CENTER, fontName='Helvetica-Oblique')),
    ]

    elementos = []
    if logo:
        tabela = Table([[logo, bloco_texto]], colWidths=[2.8*cm, None])
        tabela.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',        (1, 0), (1, 0),   'CENTER'),
            ('LEFTPADDING',  (0, 0), (0, 0),   0),
            ('RIGHTPADDING', (0, 0), (0, 0),   10),
        ]))
        elementos.append(tabela)
    else:
        elementos.extend(bloco_texto)

    elementos += [
        HRFlowable(width='100%', thickness=2, color=AZUL_GOV),
        Spacer(1, 0.4*cm),
    ]
    return elementos


def _bloco_artefato(titulo_secao, campos, estilos):
    """Caixa de informações de um artefato com título azul e tabela de campos."""
    elementos = [_secao(titulo_secao, estilos)]
    dados = [[
        Paragraph(f'<b>{k}</b>', ParagraphStyle('lbl', fontSize=8, textColor=CINZA_TXT,
                                                  fontName='Helvetica-Bold')),
        Paragraph(str(v) if v else '—', ParagraphStyle('val', fontSize=8, leading=11)),
    ] for k, v in campos]
    t = Table(dados, colWidths=[4.5*cm, 13*cm])
    t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [BRANCO, AZUL_CLARO]),
        ('GRID',           (0, 0), (-1, -1), 0.4, CINZA_BD),
        ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',     (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
        ('LEFTPADDING',    (0, 0), (-1, -1), 7),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 0.3*cm))
    return elementos


def _mini_historico(historico_qs, estilos):
    """Tabela compacta do histórico de tramitação de um artefato."""
    hist = list(historico_qs.select_related('usuario').order_by('criado_em'))
    if not hist:
        return []
    cab = [[
        Paragraph('<b>Data</b>',    ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
        Paragraph('<b>Usuário</b>', ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
        Paragraph('<b>De</b>',      ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
        Paragraph('<b>Para</b>',    ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
        Paragraph('<b>Motivo</b>',  ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
    ]]
    rows = [[
        Paragraph(h.criado_em.strftime('%d/%m/%Y %H:%M') if h.criado_em else '—',
                  ParagraphStyle('hv', fontSize=6.5, leading=9, fontName='Courier')),
        Paragraph((h.usuario.get_full_name() or h.usuario.username) if h.usuario else '—',
                  ParagraphStyle('hv', fontSize=7, leading=10)),
        Paragraph(h.status_anterior or '—', ParagraphStyle('hv', fontSize=7, leading=10)),
        Paragraph(h.status_novo,            ParagraphStyle('hv', fontSize=7, leading=10)),
        Paragraph(h.motivo or '—',          ParagraphStyle('hv', fontSize=7, leading=10)),
    ] for h in hist]
    t = Table(cab + rows, colWidths=[3*cm, 3.2*cm, 3*cm, 3*cm, 5.3*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0), AZUL_GOV),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
        ('GRID',           (0, 0), (-1, -1), 0.4, CINZA_BD),
        ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',     (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
        ('LEFTPADDING',    (0, 0), (-1, -1), 5),
    ]))
    return [t, Spacer(1, 0.25*cm)]


def _rodape_fn(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(CINZA_TXT)
    canvas.drawString(2 * cm, 1.0 * cm, 'Sistema WEBBER — Documento gerado eletronicamente')
    canvas.drawRightString(A4[0] - 2 * cm, 1.0 * cm,
        f'Página {doc.page}  •  {datetime.now().strftime("%d/%m/%Y %H:%M")}')
    canvas.restoreState()


# ── Relatório por Processo SEI ────────────────────────────────────────────────

def gerar_pdf_relatorio_sei(numero_sei: str, org_id, org) -> bytes:
    """
    Consolida todos os artefatos que possuem o número SEI informado
    e a trilha de auditoria associada a cada um deles.
    """
    from core.models import AuditLog

    buf     = io.BytesIO()
    estilos = _estilos()

    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    e = []
    e += _cabecalho_relatorio(
        'RELATÓRIO POR PROCESSO SEI',
        f'Processo: {numero_sei}',
        org, estilos,
    )

    encontrou = False

    # ── DFD ──────────────────────────────────────────────────────────────────
    try:
        from modulo_demanda.models import DFD, HistoricoTramitacao
        dfds = list(DFD.objects.filter(org_id=org_id, numero_sei=numero_sei)
                               .select_related('created_by', 'unidade_demandante'))
        for dfd in dfds:
            encontrou = True
            campos = [
                ('Nº SEI',          dfd.numero_sei),
                ('Status',          dfd.status),
                ('Unidade',         str(dfd.unidade_demandante) if dfd.unidade_demandante else '—'),
                ('Criado por',      (dfd.created_by.get_full_name() or dfd.created_by.username) if dfd.created_by else '—'),
                ('Criado em',       dfd.created_at.strftime('%d/%m/%Y') if dfd.created_at else '—'),
            ]
            e.append(KeepTogether(_bloco_artefato('DFD — Documento de Formalização de Demanda', campos, estilos)))
            e += _mini_historico(dfd.historico, estilos)
    except Exception:
        pass

    # ── ETP ──────────────────────────────────────────────────────────────────
    try:
        from modulo_etp.models import ETP, HistoricoETP
        etps = list(ETP.objects.filter(dfd__org_id=org_id, numero_sei=numero_sei)
                               .select_related('created_by', 'dfd'))
        for etp in etps:
            encontrou = True
            campos = [
                ('Nº SEI',    etp.numero_sei),
                ('Status',    etp.status),
                ('DFD vinc.', etp.dfd.numero_sei if etp.dfd else '—'),
                ('Criado por',(etp.created_by.get_full_name() or etp.created_by.username) if etp.created_by else '—'),
                ('Criado em', etp.created_at.strftime('%d/%m/%Y') if etp.created_at else '—'),
            ]
            e.append(KeepTogether(_bloco_artefato('ETP — Estudo Técnico Preliminar', campos, estilos)))
            e += _mini_historico(etp.historico, estilos)
    except Exception:
        pass

    # ── TR ───────────────────────────────────────────────────────────────────
    try:
        from modulo_tr.models import TR, HistoricoTR
        trs = list(TR.objects.filter(org_id=org_id, numero_sei=numero_sei)
                             .select_related('created_by'))
        for tr in trs:
            encontrou = True
            campos = [
                ('Nº SEI',    tr.numero_sei),
                ('Status',    tr.status),
                ('Criado por',(tr.created_by.get_full_name() or tr.created_by.username) if tr.created_by else '—'),
                ('Criado em', tr.created_at.strftime('%d/%m/%Y') if tr.created_at else '—'),
            ]
            e.append(KeepTogether(_bloco_artefato('TR — Termo de Referência', campos, estilos)))
            e += _mini_historico(tr.historico, estilos)
    except Exception:
        pass

    # ── Procedimento ─────────────────────────────────────────────────────────
    try:
        from modulo_licitacao.models import Procedimento, HistoricoProcedimento
        procs = list(Procedimento.objects.filter(org_id=org_id, numero_sei=numero_sei)
                                         .select_related('created_by', 'unidade_gestora'))
        for proc in procs:
            encontrou = True
            campos = [
                ('Número',      proc.numero),
                ('Modalidade',  proc.get_modalidade_display() if hasattr(proc, 'get_modalidade_display') else proc.modalidade),
                ('Status',      proc.status),
                ('Nº SEI',      proc.numero_sei),
                ('Valor est.',  f'R$ {float(proc.valor_estimado):,.2f}' if proc.valor_estimado else '—'),
                ('Criado em',   proc.created_at.strftime('%d/%m/%Y') if proc.created_at else '—'),
            ]
            e.append(KeepTogether(_bloco_artefato('Procedimento (Licitação/Contratação Direta)', campos, estilos)))
            e += _mini_historico(proc.historico, estilos)
    except Exception:
        pass

    # ── Contrato ──────────────────────────────────────────────────────────────
    try:
        from modulo_contrato.models import Contrato
        contratos = list(Contrato.objects.filter(org_id=org_id, numero_processo_sei=numero_sei)
                                         .select_related('created_by', 'fiscal_contrato', 'gestor_contrato'))
        for c in contratos:
            encontrou = True
            campos = [
                ('Número',       c.numero),
                ('Status',       c.status),
                ('Objeto',       c.objeto[:200] if c.objeto else '—'),
                ('Valor',        f'R$ {float(c.valor_contrato):,.2f}' if c.valor_contrato else '—'),
                ('Vigência',     f'{c.data_vigencia_inicio} a {c.data_vigencia_fim}' if c.data_vigencia_inicio else '—'),
                ('Fiscal',       (c.fiscal_contrato.get_full_name() or c.fiscal_contrato.username) if c.fiscal_contrato else '—'),
                ('Gestor',       (c.gestor_contrato.get_full_name() or c.gestor_contrato.username) if c.gestor_contrato else '—'),
            ]
            e.append(KeepTogether(_bloco_artefato('Contrato', campos, estilos)))
    except Exception:
        pass

    # ── Trilha AuditLog ───────────────────────────────────────────────────────
    logs = list(
        AuditLog.objects.filter(
            org_id=org_id,
            descricao__icontains=numero_sei,
        ).select_related('usuario').order_by('criado_em')[:100]
    )
    if logs:
        e += [_secao('Trilha de Auditoria associada ao processo', estilos)]
        e += _mini_historico_audit(logs, estilos)

    if not encontrou and not logs:
        e.append(Paragraph(
            f'Nenhum artefato encontrado com o número SEI "{numero_sei}" neste órgão.',
            ParagraphStyle('vz', fontSize=9, textColor=CINZA_TXT, spaceBefore=8),
        ))

    doc.build(e, onFirstPage=_rodape_fn, onLaterPages=_rodape_fn)
    return buf.getvalue()


def _mini_historico_audit(logs, estilos):
    """Tabela de logs AuditLog num relatório de processo."""
    ICON = {'created':'+ Criado','deleted':'✕ Excluído','value_changed':'$ Valor',
            'sei_changed':'# SEI','login':'→ Login','updated':'~ Alterado'}
    CORES = {'created':colors.HexColor('#16a34a'),'deleted':colors.HexColor('#dc2626'),
             'value_changed':colors.HexColor('#d97706'),'sei_changed':colors.HexColor('#2563eb'),
             'login':colors.HexColor('#7c3aed'),'updated':colors.HexColor('#475569')}
    cab = [[
        Paragraph('<b>Data / Hora</b>', ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
        Paragraph('<b>Evento</b>',      ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
        Paragraph('<b>Descrição</b>',   ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
        Paragraph('<b>Usuário</b>',     ParagraphStyle('hc', fontSize=7, textColor=BRANCO, fontName='Helvetica-Bold')),
    ]]
    rows = []
    for lg in logs:
        cor = CORES.get(lg.acao, colors.HexColor('#475569'))
        rows.append([
            Paragraph(lg.criado_em.strftime('%d/%m/%Y\n%H:%M') if lg.criado_em else '—',
                      ParagraphStyle('ldt', fontSize=6.5, leading=9, fontName='Courier')),
            Paragraph(f'<b>{ICON.get(lg.acao, lg.acao)}</b>',
                      ParagraphStyle('lac', fontSize=7, leading=10, textColor=cor, fontName='Helvetica-Bold')),
            Paragraph(lg.descricao or lg.objeto_repr or '—',
                      ParagraphStyle('lds', fontSize=7, leading=10)),
            Paragraph((lg.usuario.get_full_name() or lg.usuario.username) if lg.usuario else '—',
                      ParagraphStyle('lus', fontSize=7, leading=10)),
        ])
    t = Table(cab + rows, colWidths=[2.8*cm, 2.2*cm, 9*cm, 3*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0), AZUL_GOV),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
        ('GRID',           (0, 0), (-1, -1), 0.4, CINZA_BD),
        ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',     (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
        ('LEFTPADDING',    (0, 0), (-1, -1), 5),
    ]))
    return [t, Spacer(1, 0.3*cm)]


# ── Relatório por Cadeia de Demanda (Necessidade) ─────────────────────────────

def gerar_pdf_relatorio_necessidade(nec, org) -> bytes:
    """
    Percorre a cadeia completa: Necessidade → DFD → ETP → TR → Procedimento → Contrato.
    Cada artefato aparece com seus dados e histórico de tramitação.
    """
    buf     = io.BytesIO()
    estilos = _estilos()

    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2.5*cm)
    e = []
    e += _cabecalho_relatorio(
        'RELATÓRIO DE DEMANDA',
        f'{nec.titulo}  —  Exercício {nec.exercicio_fiscal}',
        org, estilos,
    )

    def _fmt_d(d):
        return d.strftime('%d/%m/%Y') if d else '—'

    def _fmt_v(v):
        return f'R$ {float(v):,.2f}' if v else '—'

    # ── 1. Necessidade ────────────────────────────────────────────────────────
    e.append(KeepTogether(_bloco_artefato('1. Necessidade de Planejamento', [
        ('Título',         nec.titulo),
        ('Status',         nec.status),
        ('Prioridade',     nec.prioridade),
        ('Exercício',      str(nec.exercicio_fiscal)),
        ('Valor estimado', _fmt_v(nec.valor_estimado)),
        ('Unid. demand.',  str(nec.unidade_demandante) if nec.unidade_demandante else '—'),
        ('Tipo execução',  nec.tipo_execucao),
        ('Descrição',      nec.descricao[:400] if nec.descricao else '—'),
        ('Criado por',     (nec.created_by.get_full_name() or nec.created_by.username) if nec.created_by else '—'),
        ('Criado em',      _fmt_d(nec.created_at.date() if nec.created_at else None)),
    ], estilos)))
    e += _mini_historico(nec.historico.all(), estilos)

    # ── 2. DFD ───────────────────────────────────────────────────────────────
    dfd = getattr(nec, 'dfd', None)
    if dfd:
        e.append(KeepTogether(_bloco_artefato('2. DFD — Documento de Formalização de Demanda', [
            ('Nº SEI',    dfd.numero_sei or '—'),
            ('Status',    dfd.status),
            ('Criado em', _fmt_d(dfd.created_at.date() if dfd.created_at else None)),
            ('Criado por',(dfd.created_by.get_full_name() or dfd.created_by.username) if dfd.created_by else '—'),
        ], estilos)))
        e += _mini_historico(dfd.historico.all(), estilos)

        # ── 3. ETP ────────────────────────────────────────────────────────────
        try:
            etp = dfd.etp
            e.append(KeepTogether(_bloco_artefato('3. ETP — Estudo Técnico Preliminar', [
                ('Nº SEI',    etp.numero_sei or '—'),
                ('Status',    etp.status),
                ('Criado em', _fmt_d(etp.created_at.date() if etp.created_at else None)),
            ], estilos)))
            e += _mini_historico(etp.historico.all(), estilos)
        except Exception:
            e.append(Paragraph('3. ETP: não vinculado.',
                ParagraphStyle('na', fontSize=8, textColor=CINZA_TXT, spaceBefore=4)))

        # ── 4. TR ─────────────────────────────────────────────────────────────
        try:
            from modulo_tr.models import TR
            trs = list(TR.objects.filter(dfd=dfd).select_related('created_by').prefetch_related('lotes'))
            for idx, tr in enumerate(trs, 4):
                lotes = list(tr.lotes.all())
                e.append(KeepTogether(_bloco_artefato(f'{idx}. TR — Termo de Referência', [
                    ('Nº SEI',    tr.numero_sei or '—'),
                    ('Status',    tr.status),
                    ('Qtd lotes', str(len(lotes))),
                    ('Criado em', _fmt_d(tr.created_at.date() if tr.created_at else None)),
                ], estilos)))
                e += _mini_historico(tr.historico.all(), estilos)

                # ── 5. Procedimento ────────────────────────────────────────────
                from modulo_licitacao.models import Procedimento
                procs = list(Procedimento.objects.filter(tr=tr)
                             .select_related('unidade_gestora')
                             .prefetch_related('historico__usuario', 'tramitacoes', 'resultados__contrato_gerado'))
                for proc in procs:
                    e.append(KeepTogether(_bloco_artefato('Procedimento', [
                        ('Número',     proc.numero),
                        ('Modalidade', proc.get_modalidade_display() if hasattr(proc, 'get_modalidade_display') else proc.modalidade),
                        ('Status',     proc.status),
                        ('Nº SEI',     proc.numero_sei or '—'),
                        ('Valor est.', _fmt_v(proc.valor_estimado)),
                        ('Publicação', _fmt_d(proc.data_publicacao)),
                        ('Abertura',   _fmt_d(proc.data_abertura)),
                        ('Homolog.',   _fmt_d(proc.data_homologacao)),
                    ], estilos)))
                    e += _mini_historico(proc.historico.all(), estilos)

                    # Tramitações externas
                    trams = list(proc.tramitacoes.all().order_by('data_envio'))
                    if trams:
                        e.append(Paragraph('Tramitações externas:',
                            ParagraphStyle('ts', fontSize=7.5, textColor=AZUL_GOV,
                                           fontName='Helvetica-Bold', spaceBefore=4)))
                        for t in trams:
                            e.append(Paragraph(
                                f'• {t.orgao_label} — Envio: {_fmt_d(t.data_envio)} | '
                                f'Retorno: {_fmt_d(t.data_retorno)} | Sit.: {t.status}',
                                ParagraphStyle('tl', fontSize=7.5, textColor=CINZA_TXT,
                                               leading=11, leftIndent=8)))

                    # Resultados
                    resultados = list(proc.resultados.select_related('contrato_gerado').all())
                    for r in resultados:
                        e.append(KeepTogether(_bloco_artefato('Resultado / Adjudicação', [
                            ('Lote',     r.descricao_lote or str(r.lote) if r.lote else '—'),
                            ('Resultado',r.get_resultado_display() if hasattr(r, 'get_resultado_display') else r.resultado),
                            ('Empresa',  r.empresa_vencedora or '—'),
                            ('CNPJ',     r.cnpj_vencedor or '—'),
                            ('Val. est.', _fmt_v(r.valor_estimado)),
                            ('Val. adj.', _fmt_v(r.valor_final)),
                            ('Contrato', r.contrato_gerado.numero if r.contrato_gerado else '—'),
                        ], estilos)))

        except Exception:
            pass

    else:
        e.append(Paragraph('2. DFD: não vinculado a esta necessidade.',
            ParagraphStyle('na', fontSize=8, textColor=CINZA_TXT, spaceBefore=4)))

    doc.build(e, onFirstPage=_rodape_fn, onLaterPages=_rodape_fn)
    return buf.getvalue()
