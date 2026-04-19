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
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)


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
    conteudo = str(sorted(dados.items())).encode('utf-8')
    return hashlib.sha256(conteudo).hexdigest()[:16].upper()


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


def _bloco_assinaturas(obj, estilos, hash_doc):
    """Gera bloco de assinaturas com criador e aprovador."""
    elementos = []
    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(_secao('Assinaturas', estilos))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(
        '⚠  Este documento requer assinatura digital pelo GOV.BR ou SEI para ter validade jurídica.',
        estilos['aviso'],
    ))

    def _celula_assinatura(usuario, papel, data, titulo):
        linhas = [
            Paragraph(titulo, ParagraphStyle('tt', fontSize=8, textColor=CINZA_TXT,
                                              alignment=TA_CENTER, fontName='Helvetica-Bold')),
            Spacer(1, 0.3 * cm),
            HRFlowable(width='80%', thickness=1, color=CINZA_BD, hAlign='CENTER'),
            Spacer(1, 0.15 * cm),
            Paragraph(usuario, ParagraphStyle('nm', fontSize=10, alignment=TA_CENTER,
                                               fontName='Helvetica-Bold')),
            Paragraph(papel, ParagraphStyle('cg', fontSize=8, textColor=CINZA_TXT,
                                             alignment=TA_CENTER)),
            Paragraph(data, ParagraphStyle('dt', fontSize=8, textColor=CINZA_TXT,
                                            alignment=TA_CENTER)),
        ]
        return linhas

    criador = getattr(obj, 'created_by', None)
    nome_criador = criador.get_full_name() or criador.username if criador else '—'
    data_criacao = obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else '—'

    aprovador = None
    data_aprovacao = '—'
    for h in obj.historico.all():
        if h.status_novo in ('Aprovada', 'Aprovado'):
            aprovador = h.usuario
            data_aprovacao = h.criado_em.strftime('%d/%m/%Y %H:%M')
            break

    nome_aprovador = aprovador.get_full_name() or aprovador.username if aprovador else 'Pendente'

    celula_criador  = _celula_assinatura(nome_criador,   'Criador do Documento',   data_criacao,   'ELABORADO POR')
    celula_aprovador = _celula_assinatura(nome_aprovador, 'Aprovador do Documento', data_aprovacao, 'APROVADO POR')

    tabela = Table(
        [[celula_criador, celula_aprovador]],
        colWidths=[8 * cm, 8 * cm],
        hAlign='CENTER',
    )
    tabela.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elementos.append(tabela)

    elementos.append(Spacer(1, 0.4 * cm))
    elementos.append(Paragraph(
        f'Código de verificação do documento: <b>{hash_doc}</b>',
        ParagraphStyle('hash', fontSize=7, textColor=CINZA_TXT, alignment=TA_CENTER),
    ))
    return elementos


def _cabecalho(tipo_doc, numero_sei, org_nome, estilos):
    return [
        Paragraph(org_nome.upper() or 'WEBBER', estilos['subtitulo']),
        Paragraph(tipo_doc, estilos['titulo_doc']),
        Paragraph(f'Número SEI: {numero_sei}', estilos['subtitulo']),
        HRFlowable(width='100%', thickness=2, color=AZUL_GOV),
        Spacer(1, 0.4 * cm),
    ]


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
        'tipo': 'DFD', 'sei': dfd.numero_sei, 'descricao': dfd.descricao,
        'valor': str(dfd.valor_estimado),
    })

    e += _cabecalho('DOCUMENTO DE FORMALIZAÇÃO DE DEMANDA', dfd.numero_sei, org_nome, estilos)

    e.append(_secao('Identificação', estilos))
    e += _campo('Status', dfd.get_status_display() if hasattr(dfd, 'get_status_display') else dfd.status, estilos)
    e += _campo('Modalidade de Aquisição', dfd.get_modalidade_aquisicao_display() if hasattr(dfd, 'get_modalidade_aquisicao_display') else dfd.modalidade_aquisicao, estilos)
    e += _campo('Áreas de Aplicação', ', '.join(dfd.area_aplicacao) if dfd.area_aplicacao else '—', estilos)
    e += _campo('Prazo de Necessidade', dfd.prazo_necessidade.strftime('%d/%m/%Y') if dfd.prazo_necessidade else '—', estilos)
    e += _campo('Valor Estimado', f'R$ {dfd.valor_estimado:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if dfd.valor_estimado else '—', estilos)

    e.append(_secao('Descrição da Demanda', estilos))
    e += _campo('Descrição', dfd.descricao, estilos)
    if dfd.justificativa_sem_planejamento:
        e += _campo('Justificativa', dfd.justificativa_sem_planejamento, estilos)
    if dfd.observacoes:
        e += _campo('Observações', dfd.observacoes, estilos)
    if dfd.local_entrega:
        e += _campo('Local de Entrega', dfd.local_entrega, estilos)

    # Unidades
    e.append(_secao('Unidades Responsáveis', estilos))
    e += _campo('Unidade Demandante',  str(dfd.unidade_demandante)  if dfd.unidade_demandante_id  else '—', estilos)
    e += _campo('Unidade Licitante',   str(dfd.unidade_licitante)   if dfd.unidade_licitante_id   else '—', estilos)
    e += _campo('Unidade Contratante', str(dfd.unidade_contratante) if dfd.unidade_contratante_id else '—', estilos)

    # Itens
    itens = dfd.itens.all()
    if itens.exists():
        e.append(_secao('Itens da Demanda', estilos))
        dados_tabela = [['#', 'Objeto', 'Unid.', 'Qtd.', 'Valor Unit.', 'Total']]
        for i, item in enumerate(itens, 1):
            def fmt(v):
                return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            dados_tabela.append([
                str(i), item.objeto, item.unidade_medida,
                str(item.quantidade), fmt(item.valor_unitario_estimado),
                fmt(item.valor_total_estimado),
            ])
        t = Table(dados_tabela, colWidths=[0.8*cm, 6.5*cm, 1.5*cm, 1.5*cm, 2.5*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL_GOV),
            ('TEXTCOLOR',  (0, 0), (-1, 0), BRANCO),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRANCO, AZUL_CLARO]),
            ('GRID', (0, 0), (-1, -1), 0.5, CINZA_BD),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        e.append(t)

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
        'tipo': 'ETP', 'sei': etp.numero_sei,
        'necessidade': etp.necessidade_contratacao,
        'valor': str(etp.estimativa_valor),
    })

    e += _cabecalho('ESTUDO TÉCNICO PRELIMINAR', etp.numero_sei, org_nome, estilos)

    e.append(_secao('Identificação', estilos))
    e += _campo('Status', etp.status, estilos)
    e += _campo('DFD de Origem', etp.dfd.numero_sei if etp.dfd_id else '—', estilos)
    if etp.estimativa_valor:
        def fmt(v):
            return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        e += _campo('Estimativa de Valor', fmt(etp.estimativa_valor), estilos)
    if etp.dispensa_motivo:
        e += _campo('Motivo da Dispensa de ETP', etp.dispensa_motivo, estilos)

    campos_etp = [
        ('Necessidade da Contratação', etp.necessidade_contratacao),
        ('Requisitos da Contratação',  etp.requisitos_contratacao),
        ('Levantamento de Mercado',    etp.levantamento_mercado),
        ('Descrição da Solução',       etp.descricao_solucao),
        ('Justificativa da Solução',   etp.justificativa_solucao),
        ('Mapa de Riscos',             etp.riscos),
        ('Critérios de Sustentabilidade', etp.sustentabilidade),
        ('Observações',                etp.observacoes),
    ]
    for label, valor in campos_etp:
        if valor and valor.strip():
            e.append(_secao(label, estilos))
            e += _campo('', valor, estilos)

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
        'tipo': 'TR', 'sei': tr.numero_sei,
        'objeto': tr.objeto_contratacao,
        'valor': str(tr.estimativa_valor),
    })

    e += _cabecalho('TERMO DE REFERÊNCIA', tr.numero_sei, org_nome, estilos)

    e.append(_secao('Identificação', estilos))
    e += _campo('Status', tr.status, estilos)
    e += _campo('ETP de Origem', tr.etp.numero_sei if tr.etp_id else '—', estilos)
    if tr.estimativa_valor:
        def fmt(v):
            return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        e += _campo('Estimativa de Valor', fmt(tr.estimativa_valor), estilos)
    if tr.prazo_execucao:
        e += _campo('Prazo de Execução', tr.prazo_execucao, estilos)
    if tr.local_entrega:
        e += _campo('Local de Entrega', tr.local_entrega, estilos)

    campos_tr = [
        ('Objeto da Contratação',          tr.objeto_contratacao),
        ('Justificativa da Contratação',   tr.justificativa),
        ('Requisitos da Contratação',      tr.requisitos_contratacao),
        ('Obrigações da Contratada',       tr.obrigacoes_contratada),
        ('Obrigações da Contratante',      tr.obrigacoes_contratante),
        ('Critérios de Seleção',           tr.criterios_selecao),
        ('Critérios de Medição e Pagamento', tr.criterios_medicao),
        ('Garantia Contratual',            tr.garantia_contrato),
        ('Observações',                    tr.observacoes),
    ]
    for label, valor in campos_tr:
        if valor and str(valor).strip():
            e.append(_secao(label, estilos))
            e += _campo('', valor, estilos)

    e += _bloco_assinaturas(tr, estilos, hash_doc)
    doc.build(e, onFirstPage=_rodape, onLaterPages=_rodape)
    return buf.getvalue()


# ── HTML ──────────────────────────────────────────────────────────────────────

def gerar_html(tipo: str, contexto: dict) -> str:
    return render_to_string(f'exportacao/{tipo}.html', contexto)


def resposta_pdf(pdf_bytes: bytes, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def resposta_html(html: str, filename: str) -> HttpResponse:
    response = HttpResponse(html, content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
