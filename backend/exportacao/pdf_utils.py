"""
Utilitários de exportação PDF e HTML para DFD, ETP e TR.
Usa ReportLab para PDF e templates Django para HTML.
"""
import hashlib
import io
from datetime import datetime

from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
import os as _os
from reportlab.platypus import (
    HRFlowable, Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
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
    }
    return mapa.get(codigo) or None


def _renderizar_secao_dfd(codigo, dfd, estilos):
    """
    Retorna lista de flowables para uma seção do DFD.
    Seções com lógica especial (itens, responsáveis) têm renderer próprio.
    Retorna [] quando não há conteúdo.
    """
    e = []

    if codigo == 'identificacao':
        e += _campo('Status', dfd.status, estilos)
        e += _campo('Modalidade', dfd.get_modalidade_aquisicao_display() if hasattr(dfd, 'get_modalidade_aquisicao_display') else dfd.modalidade_aquisicao, estilos)
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

    elif codigo == 'observacoes':
        if dfd.observacoes:
            e += _campo('Observações', dfd.observacoes, estilos)
        if dfd.local_entrega:
            e += _campo('Local de Entrega', dfd.local_entrega, estilos)

    elif codigo == 'itens':
        itens = dfd.itens.all()
        if itens.exists():
            dados = [['#', 'Objeto', 'Unid.', 'Qtd.', 'Valor Unit.', 'Total']]
            for i, item in enumerate(itens, 1):
                dados.append([str(i), item.objeto, item.unidade_medida,
                               str(item.quantidade),
                               _fmt_valor(item.valor_unitario_estimado),
                               _fmt_valor(item.valor_total_estimado)])
            t = Table(dados, colWidths=[0.8*cm, 6.5*cm, 1.5*cm, 1.5*cm, 2.5*cm, 2.5*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), AZUL_GOV),
                ('TEXTCOLOR',  (0, 0), (-1, 0), BRANCO),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
                ('GRID', (0, 0), (-1, -1), 0.5, CINZA_BD),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            e.append(t)

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
            dados = [['Item', 'Unid.', 'Qtd.', 'Vl. Unit.', 'Total', 'Origem']]
            for item in itens:
                obj = item.item_dfd.objeto if item.item_dfd else '—'
                un  = item.item_dfd.unidade_medida if item.item_dfd else '—'
                vlu = _fmt_valor(item.valor_unitario_efetivo)
                tot = _fmt_valor(item.valor_total)
                orig = 'Mapa' if item.preco_origem == 'mapa' else 'DFD'
                dados.append([obj[:45], un, str(item.quantidade), vlu, tot, orig])
            t = Table(dados, colWidths=[5.5*cm, 1.2*cm, 1.5*cm, 2.5*cm, 2.5*cm, 1.3*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), AZUL_CLARO),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
                ('GRID', (0, 0), (-1, -1), 0.5, CINZA_BD),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
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
        for secao in secoes:
            if secao.codigo in FLOWABLE_CODES:
                flowables = _renderizar_lotes_tr(tr, estilos)
                if flowables:
                    e.append(_secao(secao.titulo, estilos))
                    e += flowables
            else:
                valor = _valor_secao_tr(secao.codigo, tr)
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
        for secao in secoes:
            valor = _valor_secao_etp(secao.codigo, etp)
            if valor and str(valor).strip():
                e.append(_secao(secao.titulo, estilos))
                e += _campo('', valor, estilos)
    else:
        fallback = [
            ('necessidade',         'Necessidade da Contratação'),
            ('requisitos',          'Requisitos da Contratação'),
            ('levantamento_mercado','Levantamento de Mercado'),
            ('solucao',             'Descrição da Solução'),
            ('justificativa',       'Justificativa da Solução'),
            ('estimativa_valor',    'Estimativa de Valor'),
            ('riscos',              'Mapa de Riscos'),
            ('sustentabilidade',    'Sustentabilidade'),
            ('parcelamento',        'Parcelamento da Solução e Adjudicação'),
            ('cota_me_epp',         'Reserva de Cota ME/EPP (LC 123/2006)'),
            ('observacoes',         'Observações'),
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
            flowables = _renderizar_secao_dfd(secao.codigo, dfd, estilos)
            if flowables:
                e.append(_secao(secao.titulo, estilos))
                e += flowables
    else:
        # Fallback: ordem atual do código existente
        fallback_codigos = [
            'identificacao', 'descricao', 'justificativa',
            'area_aplicacao', 'prazo', 'unidades',
            'responsaveis', 'vinculo_orcamentario', 'itens', 'observacoes',
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
            'itens': 'Itens da Demanda',
            'observacoes': 'Observações',
        }
        for codigo in fallback_codigos:
            flowables = _renderizar_secao_dfd(codigo, dfd, estilos)
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

    # Bloco de identificação fixo
    e.append(_secao('Identificação', estilos))
    e += _campo('Status', tr.status, estilos)
    e += _campo('ETP de Origem', tr.etp.numero_sei if tr.etp_id else '—', estilos)
    if tr.estimativa_valor:
        e += _campo('Estimativa de Valor', _fmt_valor(tr.estimativa_valor), estilos)

    e += _renderizar_secoes_tr(tr, estilos)
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
