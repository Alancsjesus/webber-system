"""
Pesquisa de preços via Compras.gov.br (Dados Abertos) — a API externa é sempre
simulada: nenhum teste sai para a rede.
"""
import json
import ssl
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock
from urllib.parse import urlparse, parse_qs

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao
from modulo_mapa_precos.models import MapaComparativoPrecos, ItemMapa, PrecoColetado
from modulo_pncp import comprasgov


@pytest.fixture(autouse=True)
def limpar_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def org(db):
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPCG', ativa=True)


@pytest.fixture
def cliente(org):
    user = User.objects.create_user(username='pesq_cg', password='Senha@1234')
    user.profile.papel = 'analista'
    user.profile.org_id = org
    user.profile.save()
    c = APIClient()
    resp = c.post('/api/token/', {'username': 'pesq_cg', 'password': 'Senha@1234', 'captcha_token': ''}, format='json')
    assert resp.status_code == 200, resp.data
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')
    return c


@pytest.fixture
def mapa(org):
    return MapaComparativoPrecos.objects.create(org_id=org, objeto='Coletes balísticos', exercicio_fiscal=2026)


@pytest.fixture
def item(mapa):
    return ItemMapa.objects.create(
        mapa=mapa, descricao='Colete balístico nível III-A', unidade_medida='UN', quantidade=Decimal('10'),
    )


def _reg(id_item, preco, unidade='UN', dias=30, **extra):
    d = (date.today() - timedelta(days=dias)).isoformat()
    return {
        'idCompraItem': id_item, 'idCompra': '1600', 'numeroItemCompra': 1,
        'precoUnitario': preco, 'quantidade': 50, 'siglaUnidadeFornecimento': unidade,
        'descricaoItem': 'COLETE', 'nomeFornecedor': 'Fornecedor X', 'niFornecedor': '00000000000191',
        'nomeOrgao': 'POLICIA MILITAR', 'codigoUasg': '925000', 'municipio': 'SALVADOR', 'estado': 'BA',
        'forma': 'SISRP', 'dataResultado': d, 'dataCompra': d, **extra,
    }


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode('utf-8')

    def read(self, n=-1):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(registros, chamadas):
    def _urlopen(req, timeout=None, context=None):
        chamadas.append((req.full_url, context))
        return _Resp({'resultado': registros, 'totalRegistros': len(registros), 'paginasRestantes': 0})
    return _urlopen


AMOSTRA = [
    _reg('A1', 1000), _reg('A2', 1050), _reg('A3', 980), _reg('A4', 1900),  # A4 excessivo (>+30%)
    _reg('A5', 1010, unidade='CX'),
]


def test_consulta_envia_so_codigo_periodo_uf_com_ssl_verificado(cliente, mapa, item):
    chamadas = []
    with mock.patch('urllib.request.urlopen', _fake_urlopen(AMOSTRA, chamadas)):
        resp = cliente.post(f'/api/pesquisa/mapa/{mapa.pk}/comprasgov/precos/', {
            'item_mapa_id': item.pk, 'tipo': 'material', 'codigo': '461633', 'uf': 'ba',
        }, format='json')
    assert resp.status_code == 200, resp.data
    url, ctx = chamadas[0]
    u = urlparse(url)
    assert u.scheme == 'https' and u.hostname == 'dadosabertos.compras.gov.br'
    q = parse_qs(u.query)
    assert set(q) == {'tamanhoPagina', 'dataCompraInicio', 'dataCompraFim', 'tipo', 'codigo', 'estado', 'pagina'}
    assert q['codigo'] == ['461633'] and q['estado'] == ['BA']
    assert 'colete' not in url.lower()  # descrição do item não sai do sistema
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname

    por_id = {r['id']: r for r in resp.data['registros']}
    assert por_id['A4']['situacao'] == 'excessivo'
    assert por_id['A1']['situacao'] == 'ok'
    assert por_id['A5']['unidade_diverge'] is True
    assert resp.data['estatistica']['n'] == 4  # estatística só com a mesma unidade do item


@pytest.mark.parametrize('codigo', ['abc', '12;DROP', '', '1234567890'])
def test_codigo_invalido_nao_chama_api(cliente, mapa, item, codigo):
    with mock.patch('urllib.request.urlopen') as up:
        resp = cliente.post(f'/api/pesquisa/mapa/{mapa.pk}/comprasgov/precos/', {
            'item_mapa_id': item.pk, 'tipo': 'material', 'codigo': codigo,
        }, format='json')
    assert resp.status_code == 400
    up.assert_not_called()


def test_importa_valores_oficiais_e_ignora_duplicata(cliente, mapa, item):
    chamadas = []
    with mock.patch('urllib.request.urlopen', _fake_urlopen(AMOSTRA, chamadas)):
        url = f'/api/pesquisa/mapa/{mapa.pk}/comprasgov/importar/'
        body = {'item_mapa_id': item.pk, 'tipo': 'material', 'codigo': '461633',
                'ids': ['A1', 'A2', 'A3', 'FORJADO'], 'valor_unitario': '1'}
        resp = cliente.post(url, body, format='json')
        assert resp.status_code == 200, resp.data
        assert resp.data['importados'] == 3
        resp2 = cliente.post(url, body, format='json')
    assert resp2.data['importados'] == 0
    assert len(chamadas) == 2  # compras + atas de RP; a segunda importação veio do cache

    precos = PrecoColetado.objects.filter(item=item).order_by('valor_unitario')
    assert [p.valor_unitario for p in precos] == [Decimal('980.00'), Decimal('1000.00'), Decimal('1050.00')]
    assert precos[0].fonte.tipo == 'II' and 'CATMAT 461633' in precos[0].fonte.referencia
    item.refresh_from_db()
    assert item.qtd_precos_validos == 3 and item.valor_unitario_calculado is not None


def test_importacao_bloqueada_fora_de_rascunho(cliente, mapa, item):
    mapa.status = 'Aprovado'
    mapa.save()
    with mock.patch('urllib.request.urlopen') as up:
        resp = cliente.post(f'/api/pesquisa/mapa/{mapa.pk}/comprasgov/importar/', {
            'item_mapa_id': item.pk, 'tipo': 'material', 'codigo': '461633', 'ids': ['A1'],
        }, format='json')
    assert resp.status_code == 400
    up.assert_not_called()


def test_mapa_de_outro_orgao_inacessivel(cliente, item):
    outro = Orgao.objects.create(nome='Outro', sigla='OUT', ativa=True)
    alheio = MapaComparativoPrecos.objects.create(org_id=outro, objeto='x', exercicio_fiscal=2026)
    resp = cliente.post(f'/api/pesquisa/mapa/{alheio.pk}/comprasgov/precos/', {
        'item_mapa_id': item.pk, 'tipo': 'material', 'codigo': '461633',
    }, format='json')
    assert resp.status_code == 404


def test_estatistica_coeficiente_variacao():
    est = comprasgov.estatistica([100, 100, 100])
    assert est['coef_variacao_pct'] == 0.0 and est['mediana'] == 100
    assert est['limite_inferior'] == 70 and est['limite_superior'] == 130


def test_pncp_nao_usa_valor_global_como_preco_unitario(org, mapa, item):
    from modulo_pncp.models import PNCPImportacao, PNCPRegistro
    from modulo_pncp.services import ImportadorPNCP
    imp = PNCPImportacao.objects.create(
        org_id=org, mapa=mapa, periodo_inicio=date.today(), periodo_fim=date.today(),
    )
    sem_unit = PNCPRegistro.objects.create(importacao=imp, numero_pncp='C1', objeto='x', valor_global=Decimal('500000'))
    com_unit = PNCPRegistro.objects.create(importacao=imp, numero_pncp='C2', objeto='y', valor_unitario=Decimal('1200'))
    res = ImportadorPNCP().executar(imp, [sem_unit.pk, com_unit.pk])
    assert res['importados'] == 1
    assert list(PrecoColetado.objects.filter(item=item).values_list('valor_unitario', flat=True)) == [Decimal('1200.00')]


# ── PNCP sem CNPJ, ancorado no item do mapa ──────────────────────────────────

def _contratacao(seq, objeto, uf='BA'):
    return {
        'numeroControlePNCP': f'13937032000160-1-{seq:06d}/2026', 'objetoCompra': objeto,
        'orgaoEntidade': {'cnpj': '13937032000160', 'razaoSocial': 'ESTADO DA BAHIA'},
        'unidadeOrgao': {'ufSigla': uf}, 'dataPublicacaoPncp': '2026-09-01T10:00:00',
        'modalidadeNome': 'Pregão - Eletrônico', 'valorTotalHomologado': 90000,
    }


def _fake_pncp(urls):
    def _get(url, timeout, tentativas=3):
        urls.append(url)
        if '/contratacoes/publicacao' in url:
            return {'totalPaginas': 1, 'totalRegistros': 3, 'data': [
                _contratacao(1, 'Aquisição de coletes balísticos nível III-A'),
                _contratacao(2, 'Aquisição de material de expediente'),
                _contratacao(3, 'Registro de preços de colete balistico feminino'),
            ]}
        if url.endswith('/resultados'):
            return [{'valorUnitarioHomologado': 1500.5, 'quantidadeHomologada': 100,
                     'nomeRazaoSocialFornecedor': 'Fornecedor Y', 'niFornecedor': '11111111000111',
                     'dataInclusao': '2026-09-20T10:00:00'}]
        if '/itens' in url:
            return [
                {'numeroItem': 1, 'descricao': 'Colete balístico nível III-A masculino', 'unidadeMedida': 'Unidade', 'temResultado': True},
                {'numeroItem': 2, 'descricao': 'Capacete balístico', 'unidadeMedida': 'Unidade', 'temResultado': False},
            ]
        raise AssertionError(url)
    return _get


def test_pncp_exige_item_e_uf_sem_cnpj(cliente, mapa, item):
    url = f'/api/pesquisa/mapa/{mapa.pk}/pncp/preview/'
    base = {'periodo_inicio': '2026-08-01', 'periodo_fim': '2026-10-01'}
    assert cliente.post(url, base, format='json').status_code == 404  # sem item do mapa
    resp = cliente.post(url, {**base, 'item_mapa_id': item.pk, 'uf': ''}, format='json')
    assert resp.status_code == 400 and 'UF' in resp.data['detail']


def test_pncp_sem_cnpj_ranqueia_por_similaridade_e_importa_no_item(cliente, mapa, item):
    urls = []
    espelho = {'resultado': [{
        'numeroControlePNCP': '13937032000160-1-000001/2026',  # repetida do PNCP → não duplica
        'objetoCompra': 'Aquisição de coletes balísticos nível III-A', 'unidadeOrgaoUfSigla': 'BA',
        'orgaoEntidadeRazaoSocial': 'ESTADO DA BAHIA', 'orgaoEntidadeCnpj': '13937032000160',
        'dataPublicacaoPncp': '2026-09-01T10:00:00', 'modalidadeNome': 'Pregão - Eletrônico',
    }], 'paginasRestantes': 0}
    with mock.patch('modulo_pncp.services._get_json_pncp', _fake_pncp(urls)),          mock.patch('modulo_pncp.comprasgov._get_json', return_value=espelho):
        resp = cliente.post(f'/api/pesquisa/mapa/{mapa.pk}/pncp/preview/', {
            'item_mapa_id': item.pk, 'periodo_inicio': '2026-08-01', 'periodo_fim': '2026-10-01', 'uf': 'BA',
        }, format='json')
        assert resp.status_code == 200, resp.data
        assert resp.data['termo_usado'] == item.descricao  # palavra-chave padrão = item do mapa
        objetos = [r['objeto'] for r in resp.data['registros']]
        assert 'Aquisição de material de expediente' not in objetos
        assert len(objetos) == len(set(r['numero_pncp'] for r in resp.data['registros'])) == 2
        assert resp.data['registros'][0]['similaridade'] >= resp.data['registros'][-1]['similaridade']
        q = parse_qs(urlparse(urls[0]).query)
        assert q['uf'] == ['BA'] and 'cnpj' not in q

        contratacao = resp.data['registros'][0]
        resp_it = cliente.post(f'/api/pesquisa/mapa/{mapa.pk}/pncp/itens/', {
            'importacao_id': resp.data['importacao_id'], 'registro_id': contratacao['id'], 'item_mapa_id': item.pk,
        }, format='json')
    assert resp_it.status_code == 200, resp_it.data
    linhas = resp_it.data['itens']
    assert len(linhas) == 1 and linhas[0]['valor_unitario'] == '1500.5'

    resp_imp = cliente.post(f'/api/pesquisa/mapa/{mapa.pk}/pncp/confirmar/', {
        'importacao_id': resp.data['importacao_id'], 'ids': [linhas[0]['id']], 'item_mapa_id': item.pk,
    }, format='json')
    assert resp_imp.status_code == 200 and resp_imp.data['importados'] == 1
    preco = PrecoColetado.objects.get(item=item)
    assert preco.valor_unitario == Decimal('1500.50') and preco.fonte.tipo == 'II'


def test_similaridade_numeros_e_plural():
    from modulo_pncp.similaridade import ranquear
    regs = [{'t': 'condicionadores de ar split 24.000 BTUs'}, {'t': 'ar condicionado janela 12000 btu'},
            {'t': 'coletes balísticos'}]
    out = ranquear(regs, 'Ar-condicionado split 24000 BTU', 't', minimo=1)
    assert [r['t'] for r in out][0].startswith('condicionadores') and len(out) == 2
