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
        'tipo': 'DFD', 'id': str(dfd.pk), 'sei': dfd.numero_sei,
        'valor': str(dfd.valor_estimado),
        **_dados_hash_usuario(dfd),
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
        'tipo': 'ETP', 'id': str(etp.pk), 'sei': etp.numero_sei,
        'valor': str(etp.estimativa_valor),
        **_dados_hash_usuario(etp),
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
        'tipo': 'TR', 'id': str(tr.pk), 'sei': tr.numero_sei,
        'valor': str(tr.estimativa_valor),
        **_dados_hash_usuario(tr),
    })

    e += _cabecalho('MINUTA DO TERMO DE REFERÊNCIA', tr.numero_sei, org_nome, estilos)

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
    e += _cabecalho('DECLARAÇÃO DO ORDENADOR DE DESPESA', indicacao.numero, org_nome, estilos)

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
