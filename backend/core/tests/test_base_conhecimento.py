from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao, ItemCatalogo
from core.base_conhecimento import buscar_similares
from modulo_demanda.models import DFD, ItemDFD, HistoricoTramitacao


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def ssp(db):
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPBC', ativa=True)


@pytest.fixture
def outro_org(db):
    return Orgao.objects.create(nome='Outro Órgão Teste', sigla='OUTROBC', ativa=True)


def _make_user(orgao, papel, username):
    user = User.objects.create_user(username=username, password='Senha@1234')
    user.profile.papel = papel
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def analista_user(db, ssp):
    return _make_user(ssp, 'analista', 'analista_bc')


def _login(api_client, username):
    resp = api_client.post('/api/token/', {
        'username': username, 'password': 'Senha@1234', 'captcha_token': '',
    }, format='json')
    assert resp.status_code == 200, resp.data
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')


@pytest.fixture
def autor(db):
    return User.objects.create_user(username='autor_bc_teste')


@pytest.fixture
def item_catalogo_a(db):
    return ItemCatalogo.objects.create(nome='Notebook Teste BC', unidade_medida='UN')


@pytest.fixture
def item_catalogo_b(db):
    return ItemCatalogo.objects.create(nome='Monitor Teste BC', unidade_medida='UN')


def _criar_dfd(org, autor, numero_sei, status='Rascunho'):
    return DFD.objects.create(
        org_id=org, numero_sei=numero_sei, descricao=f'DFD teste {numero_sei}',
        valor_estimado=Decimal('1000.00'), area_aplicacao=['TI'],
        prazo_necessidade=date.today(), status=status,
        created_by=autor, updated_by=autor,
    )


def _add_item(dfd, item_catalogo, autor):
    return ItemDFD.objects.create(
        org_id=dfd.org_id, dfd=dfd, item_catalogo=item_catalogo,
        objeto=item_catalogo.nome, justificativa='Teste', unidade_medida='UN',
        quantidade=Decimal('1'), valor_unitario_estimado=Decimal('100.00'),
        valor_total_estimado=Decimal('100.00'),
        created_by=autor, updated_by=autor,
    )


@pytest.mark.django_db
class TestBuscarSimilares:
    def test_sem_itens_de_catalogo_retorna_vazio(self, ssp, autor):
        dfd = _criar_dfd(ssp, autor, '001.2026.0000001-11')
        r = buscar_similares(dfd, ssp)
        assert r['itens_compartilhados'] == []
        assert r['similares'] == []

    def test_encontra_dfd_com_item_compartilhado(self, ssp, autor, item_catalogo_a):
        dfd1 = _criar_dfd(ssp, autor, '001.2026.0000002-22')
        dfd2 = _criar_dfd(ssp, autor, '001.2026.0000003-33')
        _add_item(dfd1, item_catalogo_a, autor)
        _add_item(dfd2, item_catalogo_a, autor)

        r = buscar_similares(dfd1, ssp)
        assert len(r['itens_compartilhados']) == 1
        assert len(r['similares']) == 1
        assert r['similares'][0]['dfd_id'] == dfd2.id
        assert r['similares'][0]['itens_em_comum'] == 1

    def test_nao_inclui_o_proprio_dfd(self, ssp, autor, item_catalogo_a):
        dfd1 = _criar_dfd(ssp, autor, '001.2026.0000004-44')
        _add_item(dfd1, item_catalogo_a, autor)
        r = buscar_similares(dfd1, ssp)
        assert r['similares'] == []

    def test_conta_devolucoes_do_similar(self, ssp, autor, item_catalogo_a):
        dfd1 = _criar_dfd(ssp, autor, '001.2026.0000005-55')
        dfd2 = _criar_dfd(ssp, autor, '001.2026.0000006-66', status='Devolvida')
        _add_item(dfd1, item_catalogo_a, autor)
        _add_item(dfd2, item_catalogo_a, autor)
        HistoricoTramitacao.objects.create(
            dfd=dfd2, status_anterior='Em Análise', status_novo='Devolvida', usuario=autor,
        )
        HistoricoTramitacao.objects.create(
            dfd=dfd2, status_anterior='Submetida', status_novo='Devolvida', usuario=autor,
        )
        r = buscar_similares(dfd1, ssp)
        assert r['similares'][0]['total_devolucoes'] == 2

    def test_ranking_por_itens_em_comum(self, ssp, autor, item_catalogo_a, item_catalogo_b):
        dfd1 = _criar_dfd(ssp, autor, '001.2026.0000007-77')
        _add_item(dfd1, item_catalogo_a, autor)
        _add_item(dfd1, item_catalogo_b, autor)

        dfd_1_item = _criar_dfd(ssp, autor, '001.2026.0000008-88')
        _add_item(dfd_1_item, item_catalogo_a, autor)

        dfd_2_itens = _criar_dfd(ssp, autor, '001.2026.0000009-99')
        _add_item(dfd_2_itens, item_catalogo_a, autor)
        _add_item(dfd_2_itens, item_catalogo_b, autor)

        r = buscar_similares(dfd1, ssp)
        assert r['similares'][0]['dfd_id'] == dfd_2_itens.id
        assert r['similares'][0]['itens_em_comum'] == 2
        assert r['similares'][1]['dfd_id'] == dfd_1_item.id
        assert r['similares'][1]['itens_em_comum'] == 1

    def test_isolamento_multi_tenant(self, ssp, outro_org, autor, item_catalogo_a):
        dfd1 = _criar_dfd(ssp, autor, '001.2026.0000010-10')
        dfd_outro_org = _criar_dfd(outro_org, autor, '001.2026.0000011-11')
        _add_item(dfd1, item_catalogo_a, autor)
        _add_item(dfd_outro_org, item_catalogo_a, autor)

        r = buscar_similares(dfd1, ssp)
        assert r['similares'] == []


@pytest.mark.django_db
class TestEndpointProcessosSimilares:
    def test_exige_parametro_dfd(self, api_client, ssp, analista_user):
        _login(api_client, 'analista_bc')
        resp = api_client.get('/api/base-conhecimento/similares/')
        assert resp.status_code == 400

    def test_dfd_de_outro_org_retorna_404(self, api_client, ssp, outro_org, autor, analista_user):
        dfd_outro = _criar_dfd(outro_org, autor, '001.2026.0000012-12')
        _login(api_client, 'analista_bc')
        resp = api_client.get(f'/api/base-conhecimento/similares/?dfd={dfd_outro.id}')
        assert resp.status_code == 404

    def test_endpoint_retorna_200_com_forma_esperada(self, api_client, ssp, autor, analista_user, item_catalogo_a):
        dfd = _criar_dfd(ssp, autor, '001.2026.0000013-13')
        _add_item(dfd, item_catalogo_a, autor)
        _login(api_client, 'analista_bc')
        resp = api_client.get(f'/api/base-conhecimento/similares/?dfd={dfd.id}')
        assert resp.status_code == 200
        for chave in ('dfd_referencia', 'itens_compartilhados', 'similares'):
            assert chave in resp.data

    def test_endpoint_exige_autenticacao(self, api_client):
        resp = api_client.get('/api/base-conhecimento/similares/?dfd=1')
        assert resp.status_code == 401
