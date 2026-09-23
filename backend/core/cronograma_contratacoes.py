"""
Cronograma de Início Sugerido — evolução do Plano de Compras pedida pelo
usuário: comparar o prazo da necessidade com o tempo que cada modalidade
realmente leva neste órgão, para sinalizar quando cada contratação pendente
do PCA precisa começar, e com qual modalidade.

Princípios definidos explicitamente pelo usuário (não são default meu):
1. É uma "sugestão de direcionamento", nunca uma decisão de procedimento —
   por isso a API sempre retorna TODAS as modalidades aplicáveis lado a lado,
   nunca escolhe uma sozinha.
2. A duração de cada modalidade vem de média histórica REAL medida nos
   próprios processos concluídos deste órgão — nunca um número estimado
   "no papel". Quando não há amostra suficiente, o campo vem None com uma
   observação explicando por quê (nunca inventa um número).
3. Avaliar vantajosidade real, não só aplicabilidade: para Adesão/Carona a
   ARP, compara o preço registrado na Ata com a referência mais recente da
   pesquisa de preços (Mapa de Preços) do mesmo item — sinaliza quando o
   preço registrado está acima do que o mercado tem mostrado.
"""
from datetime import date
from decimal import Decimal

AMOSTRA_MINIMA = 3
MODALIDADES_COM_PROCEDIMENTO = [
    'pregao_eletronico', 'concorrencia', 'dispensa_eletronica', 'dispensa_tradicional', 'inexigibilidade',
]

# Lei 14.133/2021, Art. 75 — incisos atualizados por decreto federal:
#   I  — obras, serviços de engenharia ou manutenção de veículos automotores (teto maior, R$ 114.554,16)
#   II — compras em geral e demais serviços (teto menor, R$ 57.277,08)
# Mesmos valores já usados em modulo_licitacao.models.FUNDAMENTO_DISPENSA_CHOICES.
# Só o teto do inciso II é aplicado aqui: os itens consolidados do PCA vêm do
# catálogo SIMPAS (core.ItemCatalogo), ou seja, são sempre compras — usar o
# teto do inciso I (obras/veículos) sem essa distinção arriscaria sugerir
# dispensa acima do limite real do item.
TETO_DISPENSA_COMPRAS = Decimal('57277.08')


def _duracoes_medidas(modalidade, org_id):
    """Dias corridos entre a abertura do Procedimento (created_at) e a
    assinatura do Contrato gerado a partir dele, um valor por processo já
    concluído deste órgão nessa modalidade. Descarta durações negativas
    (contrato assinado antes da abertura do procedimento é dado ruim, não
    duração real) sem propagar o erro para quem consome a média."""
    from modulo_licitacao.models import ResultadoLote

    resultados = (
        ResultadoLote.objects
        .filter(
            procedimento__org_id=org_id,
            procedimento__modalidade=modalidade,
            contrato_gerado__isnull=False,
            contrato_gerado__data_assinatura__isnull=False,
        )
        .select_related('procedimento', 'contrato_gerado')
    )
    duracoes = [
        (r.contrato_gerado.data_assinatura - r.procedimento.created_at.date()).days
        for r in resultados
    ]
    return [d for d in duracoes if d >= 0]


def duracao_media_modalidade(modalidade, org_id, minimo=AMOSTRA_MINIMA):
    """Média em dias corridos, ou None quando a amostra é menor que `minimo`
    — nunca extrapola de poucos casos. Ver `_duracoes_medidas`."""
    duracoes = _duracoes_medidas(modalidade, org_id)
    if len(duracoes) < minimo:
        return None
    return round(sum(duracoes) / len(duracoes))


def estatisticas_duracao_por_modalidade(org_id, minimo=AMOSTRA_MINIMA):
    """Painel de avaliação: para cada modalidade que passa por Procedimento,
    quantos processos concluídos existem, e média/mínimo/máximo de dias do
    início à assinatura do contrato — usado no Painel Gerencial de
    Tramitação para medir, não só apontar prazo em curso (ver
    modulo_tramitacao.indicadores, que mede tempo na etapa ATUAL de
    processos em andamento; isto mede o ciclo completo de processos já
    concluídos)."""
    from modulo_licitacao.models import MODALIDADE_CHOICES

    labels = dict(MODALIDADE_CHOICES)
    estatisticas = []
    for modalidade in MODALIDADES_COM_PROCEDIMENTO:
        duracoes = _duracoes_medidas(modalidade, org_id)
        amostra_suficiente = len(duracoes) >= minimo
        estatisticas.append({
            'modalidade': modalidade,
            'modalidade_label': labels.get(modalidade, modalidade),
            'quantidade_amostra': len(duracoes),
            'amostra_suficiente': amostra_suficiente,
            'duracao_media': round(sum(duracoes) / len(duracoes)) if amostra_suficiente else None,
            'duracao_min': min(duracoes) if duracoes else None,
            'duracao_max': max(duracoes) if duracoes else None,
        })
    return estatisticas


def _resultados_concluidos(org_id):
    """Base comum das duas medições segmentadas abaixo — evita duas queries
    quase idênticas divergirem com o tempo."""
    from modulo_licitacao.models import ResultadoLote

    return (
        ResultadoLote.objects
        .filter(procedimento__org_id=org_id, contrato_gerado__isnull=False,
                contrato_gerado__data_assinatura__isnull=False)
        .select_related('procedimento', 'procedimento__tr', 'contrato_gerado')
        .prefetch_related('procedimento__tramitacoes')
    )


def estatisticas_duracao_por_tipo_objeto(org_id, minimo=AMOSTRA_MINIMA):
    """A mesma medição de `estatisticas_duracao_por_modalidade`, mas agrupada
    pelo tipo_objeto do TR (bens / serviços / serviços de engenharia /
    híbrido / obras) em vez de pela modalidade — um pregão de bens comuns e
    um pregão de obras não têm o mesmo ciclo, e uma média só por modalidade
    escondia essa diferença. Só entra quem tem TR vinculado: dispensa por
    valor, por exemplo, costuma dispensar TR/ETP e não tem como ser
    classificada por natureza do objeto aqui."""
    from modulo_tr.models import TR

    labels = dict(TR.TIPO_OBJETO_CHOICES)
    grupos = {}
    for r in _resultados_concluidos(org_id):
        tr = r.procedimento.tr
        if not tr or not tr.tipo_objeto:
            continue
        dias = (r.contrato_gerado.data_assinatura - r.procedimento.created_at.date()).days
        if dias < 0:
            continue
        grupos.setdefault(tr.tipo_objeto, []).append(dias)

    estatisticas = []
    for tipo_objeto, duracoes in grupos.items():
        amostra_suficiente = len(duracoes) >= minimo
        estatisticas.append({
            'tipo_objeto': tipo_objeto,
            'tipo_objeto_label': labels.get(tipo_objeto, tipo_objeto),
            'quantidade_amostra': len(duracoes),
            'amostra_suficiente': amostra_suficiente,
            'duracao_media': round(sum(duracoes) / len(duracoes)) if amostra_suficiente else None,
            'duracao_min': min(duracoes),
            'duracao_max': max(duracoes),
        })
    estatisticas.sort(key=lambda e: -(e['duracao_media'] or 0))
    return estatisticas


def estatisticas_impacto_tramitacao_externa(org_id, minimo=AMOSTRA_MINIMA):
    """Compara, DENTRO DE CADA MODALIDADE, a duração de processos que
    passaram por ao menos um órgão externo (Casa Civil, PGE, SEFAZ...) contra
    os que não passaram. A diferença é MEDIDA a partir de TramitacaoExterna
    real, não presumida por categoria do objeto (ex.: "veículo" não é, por si
    só, o motivo do atraso — o trâmite pela Casa Civil que esse tipo de
    compra costuma exigir, é).

    Segmentado por modalidade — nunca comparar "com" de um Pregão contra
    "sem" de uma Dispensa: são processos com ritmo naturalmente diferente, e
    misturar os dois reproduziria exatamente o problema de esconder sinal que
    motivou existir esta função (ver estatisticas_duracao_por_modalidade)."""
    from modulo_licitacao.models import MODALIDADE_CHOICES

    labels = dict(MODALIDADE_CHOICES)
    por_modalidade = {}
    for r in _resultados_concluidos(org_id):
        dias = (r.contrato_gerado.data_assinatura - r.procedimento.created_at.date()).days
        if dias < 0:
            continue
        grupo = por_modalidade.setdefault(r.procedimento.modalidade, {'com': [], 'sem': []})
        chave = 'com' if r.procedimento.tramitacoes.all() else 'sem'
        grupo[chave].append(dias)

    def _grupo(duracoes):
        amostra_suficiente = len(duracoes) >= minimo
        return {
            'quantidade_amostra': len(duracoes),
            'amostra_suficiente': amostra_suficiente,
            'duracao_media': round(sum(duracoes) / len(duracoes)) if amostra_suficiente else None,
        }

    resultado = []
    for modalidade, grupo in por_modalidade.items():
        com, sem = _grupo(grupo['com']), _grupo(grupo['sem'])
        impacto_dias = (com['duracao_media'] - sem['duracao_media']
                        if com['duracao_media'] is not None and sem['duracao_media'] is not None else None)
        resultado.append({
            'modalidade': modalidade,
            'modalidade_label': labels.get(modalidade, modalidade),
            'com_tramitacao_externa': com,
            'sem_tramitacao_externa': sem,
            'impacto_dias': impacto_dias,
        })
    resultado.sort(key=lambda r: -(r['impacto_dias'] if r['impacto_dias'] is not None else -10**9))
    return resultado


def _referencia_mercado(codigo_simpas, org_id):
    """Preço unitário mais recente calculado pela pesquisa de preços (Mapa)
    para o mesmo código SIMPAS, quando existir."""
    from modulo_mapa_precos.models import ItemMapa

    if not codigo_simpas:
        return None
    return (
        ItemMapa.objects
        .filter(mapa__org_id=org_id, codigo_simpas=codigo_simpas, valor_unitario_calculado__isnull=False)
        .order_by('-mapa__created_at')
        .first()
    )


def opcoes_modalidade(item_catalogo, valor_estimado_total, org_id, atas_por_catalogo):
    """Monta, para um item consolidado do PCA, todas as modalidades
    aplicáveis com sua duração medida (ou a razão de não haver uma) e, para
    adesão, o sinal de compatibilidade de preço com o mercado.

    `valor_estimado_total` é o valor TOTAL estimado da contratação deste item
    (quantidade consolidada × preço), não o valor unitário — o teto do Art.
    75, I/II incide sobre o valor da contratação, e usar o preço unitário
    sugeriria dispensa para compras claramente acima do limite legal só
    porque cada unidade é barata (exatamente o fracionamento vedado pelo
    Art. 75, §1º)."""
    opcoes = []

    atas = atas_por_catalogo.get(item_catalogo.id)
    if atas:
        melhor = min(atas, key=lambda ia: ia.valor_unitario_registrado)
        referencia = _referencia_mercado(item_catalogo.codigo_simpas, org_id)
        preco_compativel = (
            melhor.valor_unitario_registrado <= referencia.valor_unitario_calculado
            if referencia else None
        )
        opcoes.append({
            'modalidade': 'adesao_arp',
            'modalidade_label': 'Adesão/Carona a ARP',
            'duracao_dias': None,
            'duracao_obs': ('Sem marco de início registrado no sistema para medir — '
                             'em geral é a via mais rápida por dispensar novo procedimento licitatório.'),
            'ata_numero': melhor.ata.numero_ata,
            'fornecedor_nome': melhor.fornecedor.nome_razao_social if melhor.fornecedor_id else None,
            'valor_unitario_ata': float(melhor.valor_unitario_registrado),
            'valor_referencia_mercado': float(referencia.valor_unitario_calculado) if referencia else None,
            'preco_compativel': preco_compativel,
        })

    if valor_estimado_total is not None and valor_estimado_total <= TETO_DISPENSA_COMPRAS:
        opcoes.append({
            'modalidade': 'dispensa_eletronica',
            'modalidade_label': 'Dispensa Eletrônica (Art. 75, II)',
            'duracao_dias': duracao_media_modalidade('dispensa_eletronica', org_id),
        })

    opcoes.append({
        'modalidade': 'pregao_eletronico',
        'modalidade_label': 'Pregão Eletrônico',
        'duracao_dias': duracao_media_modalidade('pregao_eletronico', org_id),
    })

    for o in opcoes:
        if 'duracao_obs' not in o:
            o['duracao_obs'] = (
                None if o['duracao_dias'] is not None else
                f'Ainda não há {AMOSTRA_MINIMA}+ processos concluídos deste órgão nesta modalidade '
                'para medir a duração real.'
            )

    # Destaque = sugestão de direcionamento, não decisão: a opção de menor
    # duração medida entre as que não têm sinal de preço desfavorável.
    medíveis = [o for o in opcoes if o['duracao_dias'] is not None and o.get('preco_compativel') is not False]
    if medíveis:
        sugerida = min(medíveis, key=lambda o: o['duracao_dias'])
        sugerida['sugerida'] = True

    return opcoes


def montar_cronograma(org_id, exercicio=None):
    """Cronograma de início sugerido para os itens pendentes do PCA deste
    órgão, agrupado por trimestre da data de início mais cedo (prazo da
    necessidade menos a duração medida da opção sugerida)."""
    from modulo_demanda.models import ItemDFD
    from modulo_contrato.models import Contrato
    from modulo_arp.services import atas_vigentes_com_saldo_por_catalogo
    from django.db.models import Exists, OuterRef

    hoje = date.today()
    atas_por_catalogo = atas_vigentes_com_saldo_por_catalogo(org_id)

    qs = (
        ItemDFD.objects
        .filter(dfd__org_id=org_id, item_catalogo__isnull=False)
        .exclude(dfd__status__in=['Rejeitada', 'Cancelada'])
        .annotate(executado=Exists(Contrato.objects.filter(dfd_id=OuterRef('dfd_id'))))
        .filter(executado=False)
        .select_related('item_catalogo', 'dfd')
    )
    if exercicio:
        qs = qs.filter(dfd__prazo_necessidade__year=exercicio)

    consolidado = {}
    for item in qs:
        cat = item.item_catalogo
        chave = cat.id
        if chave not in consolidado:
            consolidado[chave] = {
                'item_catalogo': cat,
                'catalogo_nome': cat.nome,
                'catalogo_simpas': cat.codigo_simpas,
                'quantidade_total': Decimal('0'),
                'valor_total': Decimal('0'),
                'item_ids': [],
                'dfds': [],
                'prazo_necessidade': None,
            }
        g = consolidado[chave]
        g['quantidade_total'] += item.quantidade
        g['valor_total'] += item.quantidade * item.valor_unitario_estimado
        g['item_ids'].append(item.id)
        if item.dfd.numero_sei not in g['dfds']:
            g['dfds'].append(item.dfd.numero_sei)
        prazo = item.dfd.prazo_necessidade
        if prazo and (g['prazo_necessidade'] is None or prazo < g['prazo_necessidade']):
            g['prazo_necessidade'] = prazo

    itens = []
    for g in consolidado.values():
        opcoes = opcoes_modalidade(g['item_catalogo'], g['valor_total'], org_id, atas_por_catalogo)

        sugerida = next((o for o in opcoes if o.get('sugerida')), None)
        data_inicio_sugerida = None
        atrasado = False
        if sugerida and g['prazo_necessidade'] and sugerida['duracao_dias'] is not None:
            from datetime import timedelta
            data_inicio_sugerida = g['prazo_necessidade'] - timedelta(days=sugerida['duracao_dias'])
            atrasado = data_inicio_sugerida < hoje

        # O período carrega o ANO real do início sugerido, não o exercício
        # filtrado — um prazo de janeiro/2027 com duração de ~90 dias empurra
        # o início pra outubro/2026 (ano anterior). Rotular isso como "4º
        # Trimestre" sem ano, junto de itens que de fato começam em 2027,
        # dava a entender que os dois começam no mesmo trimestre real.
        periodo = None
        periodo_label = None
        if data_inicio_sugerida and not atrasado:
            trimestre_num = (data_inicio_sugerida.month - 1) // 3 + 1
            periodo = f'{data_inicio_sugerida.year}-Q{trimestre_num}'
            periodo_label = f'{trimestre_num}º Trimestre de {data_inicio_sugerida.year}'

        itens.append({
            'item_catalogo_id':   g['item_catalogo'].id,
            'catalogo_nome':      g['catalogo_nome'],
            'catalogo_simpas':    g['catalogo_simpas'],
            'quantidade_total':   float(g['quantidade_total']),
            'valor_total':        float(g['valor_total']),
            'item_ids':           g['item_ids'],
            'dfds':               g['dfds'],
            'prazo_necessidade':  g['prazo_necessidade'].isoformat() if g['prazo_necessidade'] else None,
            'opcoes_modalidade':  opcoes,
            'data_inicio_sugerida': data_inicio_sugerida.isoformat() if data_inicio_sugerida else None,
            'atrasado':           atrasado,
            'periodo':            periodo,
            'periodo_label':      periodo_label,
        })

    itens.sort(key=lambda i: (i['data_inicio_sugerida'] is None, i['data_inicio_sugerida'] or ''))

    grupos_periodo = {}
    atrasados, sem_prazo = [], []
    for it in itens:
        if it['atrasado']:
            atrasados.append(it)
        elif it['periodo']:
            grupos_periodo.setdefault(it['periodo'], {'periodo': it['periodo'], 'label': it['periodo_label'], 'itens': []})
            grupos_periodo[it['periodo']]['itens'].append(it)
        else:
            sem_prazo.append(it)

    periodos = [{'periodo': 'atrasado', 'label': 'Atrasado', 'itens': atrasados}]
    periodos += [grupos_periodo[chave] for chave in sorted(grupos_periodo)]
    periodos.append({'periodo': 'sem_prazo', 'label': 'Sem data de início mensurável', 'itens': sem_prazo})

    return {
        'itens': itens,
        'periodos': periodos,
        'aviso': 'Sugestão de direcionamento — a decisão final de modalidade e data é do gestor responsável.',
    }
