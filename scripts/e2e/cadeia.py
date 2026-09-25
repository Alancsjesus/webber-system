"""
Teste ponta a ponta da cadeia de contratação via API real (backend em :9000).

Plano de Aplicação (FESP ou Financiamento) → Necessidade → DFD → Indicação
Orçamentária (DOD) → ETP → TR → Procedimento → Resultado → Contrato →
Fiscalização (medição atestada) → Pagamento (contrato + execução orçamentária).

Uso:  python scripts/e2e/cadeia.py fesp|financiamento|saque [--api URL] [--conferir]
      --api (ou WEBBER_API): backend alvo, ex. https://webber-backend.onrender.com/api
      (padrão: http://localhost:9000/api)
      --conferir: só leitura — confere no backend alvo a cadeia já registrada no
      estado local (ex.: produção carregada com `carregar_demo`, que preserva os ids).
Estado de cada cadeia fica em scripts/e2e/estado_<cadeia>.json (ou
estado_<cadeia>@<host>.json fora do localhost), então o script pode ser rodado
de novo e retoma da etapa em que parou.
"""
import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests

BASE = os.getenv('WEBBER_API', 'http://localhost:9000/api')
HOJE = date.today()
_tokens = {}


class Falha(Exception):
    pass


def _sufixo():
    """'' no localhost:9000 (arquivos de sempre); '@host' em outro backend, para não misturar estados."""
    host = urlparse(BASE).netloc
    return '' if host == 'localhost:9000' else f'@{host.replace(":", "_")}'


def login(user):
    # Cache em disco: o endpoint de login tem throttle de 5/min.
    cache = Path(__file__).with_name(f'.tokens{_sufixo()}.json')
    if not _tokens and cache.exists():
        _tokens.update(json.loads(cache.read_text()))
    if user not in _tokens:
        while True:
            r = requests.post(f'{BASE}/token/', json={'username': user, 'password': 'admin123'}, timeout=120)
            if r.status_code != 429:
                break
            espera = int(r.headers.get('Retry-After', 60)) + 1
            print(f'  … limite de login atingido, aguardando {espera}s')
            time.sleep(espera)
        if r.status_code != 200:
            raise Falha(f'login {user}: {r.status_code} {r.text[:300]}')
        _tokens[user] = r.json()['access']
        cache.write_text(json.dumps(_tokens))
    return _tokens[user]


def api(user, metodo, caminho, dados=None, esperado=(200, 201)):
    r = requests.request(metodo, f'{BASE}/{caminho.lstrip("/")}', json=dados,
                         headers={'Authorization': f'Bearer {login(user)}'}, timeout=120)
    if r.status_code not in esperado:
        raise Falha(f'{user} {metodo} {caminho} -> {r.status_code}\n{r.text[:1500]}')
    return r.json() if r.content and 'json' in r.headers.get('content-type', '') else {}


class Estado(dict):
    def __init__(self, cadeia):
        self.arquivo = Path(__file__).with_name(f'estado_{cadeia}{_sufixo()}.json')
        super().__init__(json.loads(self.arquivo.read_text(encoding='utf-8')) if self.arquivo.exists() else {})

    def salvar(self):
        self.arquivo.write_text(json.dumps(self, indent=2, ensure_ascii=False), encoding='utf-8')


def deve_falhar(user, metodo, caminho, dados, status_esperado, trecho=''):
    """Checagem negativa: a trava tem que barrar."""
    try:
        api(user, metodo, caminho, dados)
    except Falha as f:
        texto = str(f)
        assert f'-> {status_esperado}' in texto and trecho in texto, texto
        return
    raise Falha(f'Esperava {status_esperado} em {metodo} {caminho}, mas foi aceito.')


def fluxo(url, passos):
    """Executa as transições a partir do status atual (retomável). passos: [(status_de_origem, user, acao, dados)]."""
    for origem, user, acao, dados in passos:
        atual = api(user, 'GET', f'{url}/')['status']
        if atual == origem:
            api(user, 'POST', f'{url}/{acao}/', dados)
    return api(passos[-1][1], 'GET', f'{url}/')['status']


def etapa(nome):
    """Decorador: executa a etapa só se ainda não estiver no estado."""
    def deco(fn):
        def run(e):
            if nome in e:
                print(f'  = {nome} (já feito)')
                return
            e[nome] = fn(e)
            e.salvar()
            print(f'  + {nome}: {e[nome]}')
        run.nome = nome
        run.fn = fn
        return run
    return deco


# ── Fase 1: origem do recurso (Plano de Aplicação) ───────────────────────────
# Papéis: plan_ssp (gestor_planejamento SSP) opera o Plano; ordenador homologa.

PLANEJ = 'plan_ssp'
ORDENADOR = 'ordenador'


@etapa('fonte_financiamento')
def criar_fonte_financiamento(e):
    tipos = api('admin', 'GET', 'orcamento/tipo-fonte/')
    tipos = tipos.get('results', tipos)
    tipo = next((t for t in tipos if 'crédito' in t['descricao'].lower()), None)
    if tipo is None:
        tipo = api('admin', 'POST', 'orcamento/tipo-fonte/', {'descricao': 'Operação de Crédito'})
    fonte = api(PLANEJ, 'POST', 'orcamento/fonte-recurso/', {
        'codigo': 146, 'nome': 'Operação de Crédito — PROSEG BA', 'tipo': tipo['id'],
    })
    return fonte['id']


@etapa('instrumento')
def criar_instrumento_financiamento(e):
    inst = api(PLANEJ, 'POST', 'fesp/instrumento/', {
        'tipo_instrumento': 'financiamento',
        'numero_instrumento': 'BID-5210/OC-BR',
        'objeto': 'Programa de Modernização da Segurança Pública da Bahia (PROSEG BA) — '
                  'financiamento externo para reaparelhamento das forças.',
        'orgao_concedente_nome': 'Banco Interamericano de Desenvolvimento (BID)',
        'fonte_recurso': e['fonte_financiamento'],
        'valor_total_pactuado': '2000000.00',
        'valor_contrapartida': '200000.00',
        'data_assinatura': str(HOJE - timedelta(days=30)),
        'vigencia_inicio': str(HOJE - timedelta(days=30)),
        'vigencia_fim': str(HOJE + timedelta(days=1095)),
        'numero_processo_sei': '020.16859.2026.0009001-21',
        'dados_especificos': {'agente_financeiro': 'BID',
                              'numero_contrato_financiamento': '5210/OC-BR'},
    })
    api(PLANEJ, 'POST', f'fesp/instrumento/{inst["id"]}/ativar/', {})
    return inst['id']


@etapa('plano')
def criar_plano_financiamento(e):
    plano = api(PLANEJ, 'POST', 'fesp/plano-aplicacao/', {
        'natureza': 'financiamento', 'exercicio_fiscal': HOJE.year,
        'ementa': 'PROSEG BA — Reaparelhamento Operacional',
        'descricao': 'Plano de aplicação dos recursos do financiamento BID 5210/OC-BR.',
        'diagnostico': 'Déficit de equipamentos de proteção individual nas unidades operacionais.',
        'meta_geral': 'Equipar 100% do efetivo operacional com EPI adequado até o fim do exercício.',
        'justificativa': 'Redução de afastamentos por acidente em serviço.',
        'declaracao_nao_pessoal': True, 'declaracao_nao_unidade_administrativa': True,
        'declaracao_sem_contingenciamento': True,
        'valor_originario_investimento': '2000000.00',
        'responsavel_gestao_nome': 'Gestor PROSEG', 'responsavel_gestao_email': 'proseg@ssp.ba.gov.br',
        'responsavel_elaboracao_nome': 'Planejamento SSP', 'responsavel_elaboracao_email': 'cplam@ssp.ba.gov.br',
    })
    return plano['id']


@etapa('meta')
def criar_meta(e):
    meta = api(PLANEJ, 'POST', 'fesp/meta-especifica/', {
        'plano': e['plano'], 'titulo': 'Aquisição de coletes balísticos',
        'descricao_meta': 'Substituir coletes com validade vencida.',
        'descricao_indicador': 'Percentual do efetivo com colete dentro da validade',
        'formula_indicador': 'coletes válidos / efetivo operacional', 'periodicidade': 'semestral',
    })
    return meta['id']


@etapa('item_plano')
def criar_item_plano(e):
    catalogo = api(PLANEJ, 'GET', 'core/catalogo/?search=colete')
    catalogo = catalogo.get('results', catalogo)
    item = api(PLANEJ, 'POST', 'fesp/item-plano/', {
        'meta_especifica': e['meta'], 'instrumento': e['instrumento'],
        'org_beneficiaria': 1,
        'item_catalogo': catalogo[0]['id'] if catalogo else None,
        'bem_servico': 'Colete balístico nível III-A', 'natureza': 'investimento',
        'descricao': 'Colete balístico nível III-A, masculino e feminino, com capa.',
        'base_legal': 'Contrato de Empréstimo BID 5210/OC-BR, Componente 2',
        'unidade_medida': 'UN', 'quantidade': '200', 'valor_unitario_estimado': '2500.00',
        'aprovado': True,
    })
    return item['id']


@etapa('plano_aprovado')
def aprovar_plano(e):
    api(PLANEJ, 'POST', f'fesp/plano-aplicacao/{e["plano"]}/aprovar/', {})
    p = api(PLANEJ, 'POST', f'fesp/plano-aplicacao/{e["plano"]}/publicar/', {})
    return p['status']


@etapa('necessidade')
def gerar_necessidade(e):
    r = api(PLANEJ, 'POST', f'fesp/item-plano/{e["item_plano"]}/gerar_necessidade_individual/', {})
    return r['necessidade_id']


# Cadeia FESP: plano e instrumento já existem (PLANFESP-SSP-001/2026, FESP-2026);
# o item pendente beneficia a PMBA e é executado pela SSP (órgão gestor do fundo).

@etapa('instrumento')
def instrumento_fesp(e):
    inst = next(i for i in api(PLANEJ, 'GET', 'fesp/instrumento/').get('results', [])
                if i['tipo_instrumento'] == 'fesp' and i['numero_instrumento'] == f'FESP-{HOJE.year}')
    if not inst['fonte_recurso']:
        tipos = api('admin', 'GET', 'orcamento/tipo-fonte/')
        tipo = next(t for t in tipos.get('results', tipos) if t['descricao'] == 'FESP')
        fonte = api(PLANEJ, 'POST', 'orcamento/fonte-recurso/', {
            'codigo': 128, 'nome': 'FESP — Fundo Estadual de Segurança Pública', 'tipo': tipo['id'],
        })
        inst = api(PLANEJ, 'PATCH', f'fesp/instrumento/{inst["id"]}/', {'fonte_recurso': fonte['id']})
    return inst['id']


@etapa('plano')
def plano_fesp(e):
    plano = next(p for p in api(PLANEJ, 'GET', 'fesp/plano-aplicacao/').get('results', [])
                 if p['natureza'] == 'fesp' and p['exercicio_fiscal'] == HOJE.year)
    if plano['status'] == 'aprovado_conselho':
        # Homologação é ato do Chefe do Executivo, registrada pelo Ordenador
        deve_falhar(PLANEJ, 'POST', f'fesp/plano-aplicacao/{plano["id"]}/homologar/',
                    {'numero_ato': 'x', 'data_ato': str(HOJE)}, 403)
        api(ORDENADOR, 'POST', f'fesp/plano-aplicacao/{plano["id"]}/homologar/', {
            'numero_ato': f'Decreto nº 23.{HOJE.year % 100}1/{HOJE.year}', 'data_ato': str(HOJE),
            'numero_processo_sei_ato': '020.16859.2026.0008800-21',
        })
        plano = api(PLANEJ, 'POST', f'fesp/plano-aplicacao/{plano["id"]}/publicar/', {})
    assert plano['status'] == 'publicado', plano['status']
    return plano['id']


@etapa('item_plano')
def item_fesp(e):
    itens = api(PLANEJ, 'GET', f'fesp/item-plano/?page_size=200').get('results', [])
    item = next(i for i in itens if i['status'] == 'pendente' and i['instrumento'] == e['instrumento'])
    return item['id']


FASE_ORIGEM = {
    'fesp': [instrumento_fesp, plano_fesp, item_fesp, gerar_necessidade],
    'saque': [instrumento_fesp, plano_fesp, item_fesp, gerar_necessidade],
    'financiamento': [criar_fonte_financiamento, criar_instrumento_financiamento,
                      criar_plano_financiamento, criar_meta, criar_item_plano,
                      aprovar_plano, gerar_necessidade],
}


# ── Fase 2: execução (Necessidade → DFD → ... → Pagamento) ───────────────────
SOLICITANTE = 'dem_ssp'
INSTRUMENTO_TR = 'contrato'
GARANTIA = True
SAQUE = False
ANALISTA = 'analista_ssp'
GESTOR = 'gestor'
FISCAL = 'fiscal'


@etapa('dfd')
def iniciar_dfd(e):
    nec = api(PLANEJ, 'GET', f'planejamento/necessidade/{e["necessidade"]}/')
    item = api(PLANEJ, 'GET', f'fesp/item-plano/{e["item_plano"]}/')
    dfd = api(PLANEJ, 'POST', f'planejamento/necessidade/{nec["id"]}/iniciar_dfd/', {
        'numero_sei': f'020.16859.{HOJE.year}.00{9100 + nec["id"]}-21',
        'prazo_necessidade': str(HOJE + timedelta(days=120)),
        'area_aplicacao': ['Ops'],
        'modalidade_aquisicao': 'licitacao',
        'itens': [{
            'item_catalogo_id': item.get('item_catalogo'), 'objeto': item['bem_servico'],
            'unidade_medida': item['unidade_medida'], 'quantidade': item['quantidade'],
            'valor_unitario_estimado': item['valor_unitario_estimado'],
        }],
    })
    return dfd['id']


@etapa('dfd_aprovado')
def aprovar_dfd(e):
    return fluxo(f'demanda/dfd/{e["dfd"]}', [
        ('Rascunho', SOLICITANTE, 'submeter', {}),
        ('Submetida', ANALISTA, 'iniciar_analise', {}),
        ('Em Análise', ANALISTA, 'aprovar', {'motivo': 'Conforme plano.'}),
    ])


@etapa('dotacao')
def criar_dotacao(e):
    inst = api(PLANEJ, 'GET', f'fesp/instrumento/{e["instrumento"]}/')
    acao = api(PLANEJ, 'POST', 'orcamento/acao/', {
        'codigo': f'INST.{e["instrumento"]}.{e["necessidade"]}', 'nome': f'Execução — {inst["numero_instrumento"]}', 'tipo': 4,
    })
    dot = api(PLANEJ, 'POST', 'orcamento/dotacao/', {
        'exercicio_fiscal': HOJE.year, 'acao': acao['id'], 'elemento_despesa': 12,
        'fonte_recurso': inst['fonte_recurso'], 'valor_dotado': inst['valor_total_pactuado'],
    })
    return dot['id']


@etapa('indicacao')
def emitir_dod(e):
    dfd = api(PLANEJ, 'GET', f'demanda/dfd/{e["dfd"]}/')
    ind = api(PLANEJ, 'POST', 'orcamento/indicacao/', {
        'exercicio_fiscal': HOJE.year, 'numero_sei': dfd['numero_sei'],
        'dfd': e['dfd'], 'necessidade': e['necessidade'],
        'observacoes': 'Recurso do financiamento BID 5210/OC-BR.',
    })
    dotacoes = api(PLANEJ, 'GET', f'orcamento/dotacao/?exercicio_fiscal={HOJE.year}&page_size=200').get('results', [])
    minha = next(d for d in dotacoes if d['id'] == e['dotacao'])
    outra = next((d for d in dotacoes if d['fonte_recurso'] != minha['fonte_recurso']), None)
    if outra:
        deve_falhar(PLANEJ, 'POST', f'orcamento/indicacao/{ind["id"]}/vincular-dotacao/',
                    {'dotacao_id': outra['id'], 'valor_indicado': '1.00'}, 400, 'instrumento financeiro')
    api(PLANEJ, 'POST', f'orcamento/indicacao/{ind["id"]}/vincular-dotacao/', {
        'dotacao_id': e['dotacao'], 'valor_indicado': dfd['valor_estimado'],
    })
    api(PLANEJ, 'POST', f'orcamento/indicacao/{ind["id"]}/submeter/', {})
    r = api(ORDENADOR, 'POST', f'orcamento/indicacao/{ind["id"]}/aprovar/', {})
    assert r['status'] == 'Aprovada', r
    return ind['id']


TEXTO = 'Conforme estudo técnico da unidade demandante.'


@etapa('etp')
def elaborar_etp(e):
    dfd = api(SOLICITANTE, 'GET', f'demanda/dfd/{e["dfd"]}/')
    campos = {
        'dfd': e['dfd'], 'numero_sei': dfd['numero_sei'],
        'necessidade_contratacao': 'Substituição de coletes balísticos com validade vencida.',
        'descricao_solucao': 'Aquisição de coletes nível III-A com capa, via pregão eletrônico.',
        'estimativa_valor': dfd['valor_estimado'], 'tipo_objeto': 'bens',
        'tipo_parcelamento': 'lote_unico',
        'parcelamento_justificativa': 'Item único e padronizado — lote único garante uniformidade.',
        'posicionamento_conclusivo': 'A contratação é viável e adequada ao interesse público.',
        'classificacao_sensivel': False, 'alinhamento_planesp': 'Eixo 2 do PLANESP.',
        'contratacoes_correlatas': 'Não há.', 'impacto_ambiental': 'Logística reversa das placas.',
        'providencias_pre_contrato': 'Capacitação dos fiscais.',
    }
    etps = api(SOLICITANTE, 'GET', 'etp/etp/?page_size=500').get('results', [])
    etp_id = next((x['id'] for x in etps if x['dfd'] == e['dfd']), None)
    if etp_id:
        api(SOLICITANTE, 'PATCH', f'etp/etp/{etp_id}/', campos)
    else:
        etp_id = api(SOLICITANTE, 'POST', 'etp/etp/', campos)['id']
    return etp_id


@etapa('etp_aprovado')
def aprovar_etp(e):
    return fluxo(f'etp/etp/{e["etp"]}', [
        ('Rascunho', SOLICITANTE, 'submeter', {}),
        ('Submetido', ANALISTA, 'iniciar_analise', {}),
        ('Em Análise', ANALISTA, 'aprovar', {}),
    ])


@etapa('mapa')
def pesquisar_precos(e):
    """Mapa Comparativo de Preços do DFD: fonte institucional + 3 cotações, aprovado pela licitante."""
    dfd = api(ANALISTA, 'GET', f'demanda/dfd/{e["dfd"]}/')
    item = dfd['itens'][0]
    cat = api(ANALISTA, 'GET', f'core/catalogo/{item["item_catalogo"]}/') if item.get('item_catalogo') else {}
    mapa = api(ANALISTA, 'POST', 'pesquisa/mapa/', {
        'dfd': e['dfd'], 'exercicio_fiscal': HOJE.year, 'objeto': item['objeto'],
        'metodo_calculo': 'mediana',
    })
    base = f'pesquisa/mapa/{mapa["id"]}'
    fonte = api(ANALISTA, 'POST', f'{base}/fontes/', {
        'tipo': 'I', 'descricao': 'Painel de Preços / SIMPAS', 'referencia': 'Consulta por código',
        'data_consulta': str(HOJE),
    })
    im = api(ANALISTA, 'POST', f'{base}/itens/', {
        'ordem': 1, 'descricao': item['objeto'], 'codigo_simpas': cat.get('codigo_simpas', ''),
        'unidade_medida': item['unidade_medida'], 'quantidade': item['quantidade'],
    })
    unit = float(item['valor_unitario_estimado'])
    for fator in (0.95, 0.98, 1.02):
        api(ANALISTA, 'POST', f'{base}/itens/{im["id"]}/precos/', {
            'fonte': fonte['id'], 'valor_unitario': f'{unit * fator:.2f}',
            'origem_orgao_empresa': 'Contratação pública similar', 'data_referencia': str(HOJE),
        })
    for acao in ('submeter', 'iniciar_analise', 'aprovar'):
        api(ANALISTA, 'POST', f'{base}/{acao}/', {})
    return mapa['id']


@etapa('tr')
def elaborar_tr(e):
    etp = api(SOLICITANTE, 'GET', f'etp/etp/{e["etp"]}/')
    existentes = [t for t in api(SOLICITANTE, 'GET', 'tr/tr/?page_size=200').get('results', []) if t['etp'] == e['etp']]
    tr = existentes[0] if existentes else api(SOLICITANTE, 'POST', 'tr/tr/', {
        'etp': e['etp'], 'numero_sei': etp['numero_sei'],
        'objeto_contratacao': 'Aquisição de coletes balísticos nível III-A.',
    })
    tr = api(SOLICITANTE, 'GET', f'tr/tr/{tr["id"]}/')
    # Amarração: cláusula orçamentária deve vir da DOD aprovada
    fonte = api(PLANEJ, 'GET', f'orcamento/dotacao/{e["dotacao"]}/')['fonte_codigo']
    assert 'DOD' in tr['adequacao_orcamentaria'] and f'Fonte {fonte}' in tr['adequacao_orcamentaria'], tr['adequacao_orcamentaria']
    api(SOLICITANTE, 'PATCH', f'tr/tr/{tr["id"]}/', {
        'tipo_prazo_vigencia': 'escopo', 'prazo_meses': 12, 'instrumento_inicio': INSTRUMENTO_TR,
        'req_garantia_contratacao': INSTRUMENTO_TR == 'contrato', 'req_garantia_percentual': '5.00',
        'local_entrega': 'Almoxarifado Central SSP — Salvador/BA',
    })
    return tr['id']


@etapa('lote')
def montar_lote(e):
    tr = api(ANALISTA, 'POST', f'tr/tr/{e["tr"]}/lotes/', {'descricao': 'Lote único — coletes', 'modalidade': 'ampla'})
    lote = tr['lotes'][-1]
    dfd = api(ANALISTA, 'GET', f'demanda/dfd/{e["dfd"]}/')
    item = dfd['itens'][0]
    api(ANALISTA, 'POST', f'tr/tr/{e["tr"]}/lotes/{lote["id"]}/itens/', {
        'item_dfd': item['id'], 'quantidade': item['quantidade'],
    })
    dfd = api(ANALISTA, 'GET', f'demanda/dfd/{e["dfd"]}/')
    assert dfd['itens'][0]['status_execucao'] == 'comprometido_total', dfd['itens'][0]
    # Estimativa do TR = consolidação do Mapa aprovado
    est = api(ANALISTA, 'GET', f'tr/tr/{e["tr"]}/')['estimativa_consolidada']
    linha = est['lotes'][0]['itens'][0]
    assert est['mapa'] and est['mapa']['id'] == e['mapa'] and est['itens_sem_mapa'] == 0, est
    assert linha['origem'] == 'mapa' and linha['codigo_interno'], linha
    return lote['id']


@etapa('tr_aprovado')
def aprovar_tr(e):
    return fluxo(f'tr/tr/{e["tr"]}', [
        ('Rascunho', SOLICITANTE, 'submeter', {}),
        ('Submetido', ANALISTA, 'iniciar_analise', {}),
        ('Em Análise', ANALISTA, 'aprovar', {}),
    ])


@etapa('procedimento')
def abrir_procedimento(e):
    tr = api(ANALISTA, 'GET', f'tr/tr/{e["tr"]}/')
    # Aberto só pelo TR: o DFD deve ser herdado (TR → ETP → DFD) e a DOD conferida
    proc = api(ANALISTA, 'POST', 'licitacao/procedimento/', {
        'exercicio': HOJE.year, 'modalidade': 'pregao_eletronico', 'tr': e['tr'],
        'objeto': tr['objeto_contratacao'], 'valor_estimado': tr['estimativa_valor'],
        'numero_sei': tr['numero_sei'],
    })
    assert proc['dfd'] == e['dfd'], f'Procedimento não herdou o DFD: {proc["dfd"]}'
    return proc['id']


@etapa('homologado')
def licitar(e):
    p = f'licitacao/procedimento/{e["procedimento"]}'
    for acao in ('submeter', 'aprovar', 'publicar', 'iniciar_sessao'):
        api(ANALISTA, 'POST', f'{p}/{acao}/', {})
    lote = api(ANALISTA, 'GET', f'tr/tr/{e["tr"]}/')['lotes'][0]
    acima = f'{lote["valor_total_lote"] * 1.2:.2f}'
    resultado = {'lote': lote['id'], 'resultado': 'homologado', 'fornecedor': 1,
                 'valor_estimado': str(lote['valor_total_lote']), 'valor_final': acima}
    deve_falhar(ANALISTA, 'POST', f'{p}/resultados/', resultado, 400, 'art. 59')
    api(ANALISTA, 'POST', f'{p}/resultados/', {**resultado, 'observacoes': 'Teste de cobertura.'})
    return api(ANALISTA, 'POST', f'{p}/homologar/', {})['status']


@etapa('contrato')
def gerar_contrato(e):
    p = f'licitacao/procedimento/{e["procedimento"]}'
    res = api(ANALISTA, 'GET', f'{p}/resultados/')[0]
    if float(res['valor_final']) > float(res['valor_estimado']):
        deve_falhar(ANALISTA, 'POST', f'{p}/resultados/{res["id"]}/gerar-contrato/', {}, 400, 'cobertura')
        api(ANALISTA, 'PATCH', f'{p}/resultados/{res["id"]}/', {
            'valor_final': f'{float(res["valor_estimado"]) * 0.924:.2f}', 'observacoes': ''})
    r = api(ANALISTA, 'POST', f'{p}/resultados/{res["id"]}/gerar-contrato/', {})
    c = api(GESTOR, 'GET', f'contratos/contrato/{r["contrato_id"]}/')
    assert c['fornecedor'] == res['fornecedor'], 'Contrato sem fornecedor vencedor'
    assert c['dfd'] == e['dfd'], 'Contrato sem DFD de origem'
    assert r['status'] == 'Contratado', r['status']
    # Contrato nasce da minuta (TR): instrumento e garantia
    assert c['tipo_instrumento'] == INSTRUMENTO_TR, c['tipo_instrumento']
    assert c['garantia_exigida'] == GARANTIA, c['garantia_exigida']
    if SAQUE:
        assert c['tipo_origem'] == 'saque_arp', c['tipo_origem']
        ata = api(ANALISTA, 'GET', f'arp/{e["ata"]}/')
        assert all(float(i['quantidade_consumida']) > 0 for i in ata['itens']), 'Saldo da Ata não consumido'
    return r['contrato_id']


def usuario_id(username):
    lista = api('admin', 'GET', 'core/users-list/')
    lista = lista.get('results', lista)
    return next(u['id'] for u in lista if u['username'] == username)


@etapa('contrato_designado')
def designar_contrato(e):
    dados = {
        'fiscal_contrato': usuario_id(FISCAL), 'gestor_contrato': usuario_id(GESTOR),
        'ordenador': usuario_id(ORDENADOR),
        'data_assinatura': str(HOJE), 'data_vigencia_inicio': str(HOJE),
    }
    url = f'contratos/contrato/{e["contrato"]}/'
    if INSTRUMENTO_TR == 'afm':
        deve_falhar(GESTOR, 'PATCH', url, dados, 400, 'numero_afm')
        dados['numero_afm'] = f'AFM-{HOJE.year}-{e["contrato"]:06d}'
    fim = HOJE.replace(year=HOJE.year + 1)  # prazo de 12 meses na minuta
    if SAQUE:  # Ata avulsa (sem procedimento de formação): sem minuta, vigência informada
        dados['data_vigencia_fim'] = str(fim)
    c = api(GESTOR, 'PATCH', url, dados)
    assert c['data_vigencia_fim'] == str(fim), c['data_vigencia_fim']
    return c['numero']


def _linha_dod(e):
    ind = api(ORDENADOR, 'GET', f'orcamento/indicacao/{e["indicacao"]}/')
    return ind['itens'][0]['id']


@etapa('empenho')
def empenhar(e):
    c = api(GESTOR, 'GET', f'contratos/contrato/{e["contrato"]}/')
    deve_falhar(SOLICITANTE, 'POST', f'orcamento/indicacao/{e["indicacao"]}/registrar-empenhos/',
                {'empenhos': []}, 403)
    numero = f'{HOJE.year}NE{e["contrato"]:06d}'
    api(ORDENADOR, 'POST', f'orcamento/indicacao/{e["indicacao"]}/registrar-empenhos/', {'empenhos': [{
        'indicacao_dotacao_id': _linha_dod(e), 'numero_doc': numero,
        'data_emissao': str(HOJE), 'valor': c['valor_contrato'],
    }]})
    return numero


@etapa('medicao')
def medir_e_atestar(e):
    c = api(GESTOR, 'GET', f'contratos/contrato/{e["contrato"]}/')
    base = f'contratos/contrato/{e["contrato"]}/medicoes/'
    # Ateste direto na criação, por quem não é o fiscal: barrado
    deve_falhar(GESTOR, 'POST', base, {
        'competencia_inicio': str(HOJE), 'competencia_fim': str(HOJE), 'data_medicao': str(HOJE),
        'valor_medido': c['valor_contrato'], 'status': 'aprovada', 'parecer_fiscal': 'ok',
    }, 403, 'fiscal designado')
    c = api(GESTOR, 'POST', base, {
        'competencia_inicio': str(HOJE), 'competencia_fim': str(HOJE), 'data_medicao': str(HOJE),
        'valor_medido': c['valor_contrato'], 'percentual_executado': '100.00',
        'numero_processo_sei': c['numero_processo_sei'],
    })
    med = c['medicoes'][-1]
    deve_falhar(FISCAL, 'PATCH', f'{base}{med["id"]}/', {'status': 'aprovada'}, 400, 'parecer_fiscal')
    c = api(FISCAL, 'PATCH', f'{base}{med["id"]}/', {
        'status': 'aprovada',
        'parecer_fiscal': 'Recebidos 200 coletes conforme especificação; lotes e validade conferidos.',
    })
    med = next(m for m in c['medicoes'] if m['id'] == med['id'])
    assert med['fiscal_responsavel'] == usuario_id(FISCAL) and med['data_aprovacao'], med
    return med['id']


@etapa('liquidacao')
def liquidar(e):
    c = api(GESTOR, 'GET', f'contratos/contrato/{e["contrato"]}/')
    api(ORDENADOR, 'POST', f'orcamento/indicacao/{e["indicacao"]}/registrar-liquidacoes/', {'liquidacoes': [{
        'indicacao_dotacao_id': _linha_dod(e), 'numero_doc': f'{HOJE.year}NL{e["contrato"]:06d}',
        'data_emissao': str(HOJE), 'valor': c['valor_contrato'],
    }]})
    return 'ok'


@etapa('pagamento')
def pagar(e):
    c = api(GESTOR, 'GET', f'contratos/contrato/{e["contrato"]}/')
    base = f'contratos/contrato/{e["contrato"]}/pagamentos/'
    dados = {'medicao': e['medicao'], 'valor_pago': c['valor_contrato'], 'status': 'pago',
             'numero_nota_fiscal': 'NF-000871', 'numero_empenho': 'NE-INEXISTENTE'}
    deve_falhar(GESTOR, 'POST', base, dados, 400, 'numero_empenho')
    deve_falhar(GESTOR, 'POST', base, {**dados, 'numero_empenho': e['empenho'],
                                       'valor_pago': str(float(c['valor_contrato']) + 1)}, 400, 'valor_pago')
    c = api(GESTOR, 'POST', base, {**dados, 'numero_empenho': e['empenho']})
    pag = c['pagamentos'][-1]
    api(ORDENADOR, 'POST', f'orcamento/indicacao/{e["indicacao"]}/registrar-pagamentos/', {'pagamentos': [{
        'indicacao_dotacao_id': _linha_dod(e), 'numero_doc': f'{HOJE.year}OB{e["contrato"]:06d}',
        'data_emissao': str(HOJE), 'valor': c['valor_contrato'],
    }]})
    return pag['id']


@etapa('conferencia')
def conferir_cadeia(e):
    """Confere que cada ponta enxerga a outra (a cadeia está 'amarrada')."""
    dot = api(PLANEJ, 'GET', f'orcamento/dotacao/{e["dotacao"]}/')
    c = api(GESTOR, 'GET', f'contratos/contrato/{e["contrato"]}/')
    v = c['valor_contrato']
    assert dot['valor_empenhado'] == v and dot['valor_liquidado'] == v and dot['valor_pago'] == v, dot
    rast = api(PLANEJ, 'GET', f'rastreabilidade/{e["necessidade"]}/')
    etapas = [p['etapa'] for p in rast['cadeia']]
    for esperada in (('Necessidade', 'DFD', 'Procedimento', 'Contrato') if SAQUE else
                     ('Necessidade', 'DFD', 'ETP', 'TR', 'Procedimento', 'Contrato')):
        assert esperada in etapas, (esperada, etapas)
    return ' → '.join(etapas)


FASE_EXECUCAO = [iniciar_dfd, aprovar_dfd, criar_dotacao, emitir_dod, elaborar_etp, aprovar_etp,
                 pesquisar_precos, elaborar_tr, montar_lote, aprovar_tr, abrir_procedimento, licitar, gerar_contrato,
                 designar_contrato, empenhar, medir_e_atestar, liquidar, pagar, conferir_cadeia]


# ── Saque de Ata: sem ETP/TR/Mapa próprios ────────────────────────────────────

@etapa('ata')
def registrar_ata(e):
    """Ata vigente com o item do DFD, fornecedor registrado e saldo."""
    item = api(ANALISTA, 'GET', f'demanda/dfd/{e["dfd"]}/')['itens'][0]
    ata = api(ANALISTA, 'POST', 'arp/', {
        'tipo_origem': 'gerenciador', 'numero_ata': f'ARP-{HOJE.year}-{e["dfd"]:04d}',
        'objeto': f'Registro de preços — {item["objeto"]}',
        'data_assinatura': str(HOJE), 'data_vigencia_inicio': str(HOJE),
        'data_vigencia_fim': str(HOJE + timedelta(days=365)),
    })
    api(ANALISTA, 'POST', f'arp/{ata["id"]}/itens/', {
        'item_catalogo': item['item_catalogo'], 'objeto': item['objeto'], 'unidade_medida': item['unidade_medida'],
        'fornecedor': 2, 'quantidade_registrada': str(float(item['quantidade']) * 3),
        'valor_unitario_registrado': f'{float(item["valor_unitario_estimado"]) * 0.9:.2f}',
    })
    api(ANALISTA, 'POST', f'arp/{ata["id"]}/ativar/', {})
    return ata['id']


@etapa('procedimento')
def abrir_saque(e):
    base = {'exercicio': HOJE.year, 'modalidade': 'saque_arp', 'dfd': e['dfd'],
            'numero_sei': api(ANALISTA, 'GET', f'demanda/dfd/{e["dfd"]}/')['numero_sei']}
    deve_falhar(ANALISTA, 'POST', 'licitacao/procedimento/', base, 400, 'ata')
    outro_tr = next(iter(api(ANALISTA, 'GET', 'tr/tr/').get('results', [])), None)
    if outro_tr:
        deve_falhar(ANALISTA, 'POST', 'licitacao/procedimento/', {**base, 'ata': e['ata'], 'tr': outro_tr['id']}, 400, 'tr')
    proc = api(ANALISTA, 'POST', 'licitacao/procedimento/', {**base, 'ata': e['ata']})
    assert proc['tr'] is None and proc['numero'].startswith('SAQ-'), proc['numero']
    tipos = [p['tipo'] for p in proc['pecas_instutorias']]
    assert 'Ata de Registro de Preços' in tipos and 'TR' not in tipos, tipos
    return proc['id']


@etapa('homologado')
def efetivar_saque(e):
    p = f'licitacao/procedimento/{e["procedimento"]}'
    fluxo(p, [('Em Instrução', ANALISTA, 'submeter', {}), ('Aguardando Aprovação', ANALISTA, 'aprovar', {})])
    r = api(ANALISTA, 'POST', f'{p}/registrar-saque/', {})
    assert r['resultados'] and r['resultados'][0]['resultado'] == 'homologado', r['resultados']
    return r['status']


FASE_SAQUE = [iniciar_dfd, aprovar_dfd, criar_dotacao, emitir_dod, registrar_ata, abrir_saque, efetivar_saque,
              gerar_contrato, designar_contrato, empenhar, medir_e_atestar, liquidar, pagar, conferir_cadeia]


def main():
    global SOLICITANTE, INSTRUMENTO_TR, GARANTIA, SAQUE, BASE
    args = sys.argv[1:]
    conferir = '--conferir' in args
    if conferir:
        args.remove('--conferir')
    if '--api' in args:
        i = args.index('--api')
        BASE = args[i + 1].rstrip('/')
        del args[i:i + 2]
    cadeia = args[0] if args else 'financiamento'
    # FESP: demanda da PMBA (requisitante), licitada/contratada pela SSP (órgão pai)
    SOLICITANTE = {'fesp': 'solicitante_pm'}.get(cadeia, 'dem_ssp')
    INSTRUMENTO_TR = {'fesp': 'afm'}.get(cadeia, 'contrato')
    GARANTIA = cadeia == 'financiamento'
    SAQUE = cadeia == 'saque'
    if conferir:
        # Estado local (ids da carga de demonstração), conferido no backend alvo
        e = dict(json.loads(Path(__file__).with_name(f'estado_{cadeia}.json').read_text(encoding='utf-8')))
        print(f'== Conferindo cadeia {cadeia} em {BASE}')
        try:
            print(f'  ok {conferir_cadeia.fn(e)}')
        except (Falha, AssertionError, KeyError) as f:
            print(f'  X conferencia\n{f!r}')
            sys.exit(1)
        return
    e = Estado(cadeia)
    print(f'== Cadeia {cadeia} em {BASE}')
    for passo in FASE_ORIGEM[cadeia] + (FASE_SAQUE if SAQUE else FASE_EXECUCAO):
        try:
            passo(e)
        except Falha as f:
            print(f'  X {passo.nome}\n{f}')
            sys.exit(1)
    print('== Cadeia completa')



if __name__ == '__main__':
    main()
