"""
Regressão: PlanoComprasView.get() não tinha `return Response(dados)` no caminho
normal (sem ?export=pdf) — a view retornava None e o DRF quebrava com
AssertionError, sempre 500 para qualquer usuário real. Só foi descoberto por
teste manual via HTTP real (Playwright) ao validar outra feature na mesma
tela — nenhum teste automatizado cobria este endpoint antes.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao, ItemCatalogo
from modulo_demanda.models import DFD, ItemDFD


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
    return Orgao.objects.create(nome='SSP Teste PlanoCompras', sigla='SSPPC', ativa=True)


@pytest.fixture
def autor(db):
    return User.objects.create_user(username='autor_plano_compras_teste')


@pytest.fixture
def analista_user(db, ssp):
    user = User.objects.create_user(username='analista_pc', password='Senha@1234')
    user.profile.papel = 'analista'
    user.profile.org_id = ssp
    user.profile.save()
    return user


def _login(api_client, username):
    resp = api_client.post('/api/token/', {
        'username': username, 'password': 'Senha@1234', 'captcha_token': '',
    }, format='json')
    assert resp.status_code == 200, resp.data
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')


@pytest.mark.django_db
class TestPlanoComprasViewEndpoint:
    def test_get_sem_export_retorna_200_com_forma_esperada(self, api_client, ssp, autor, analista_user):
        item_catalogo = ItemCatalogo.objects.create(
            nome='Item Teste PC', unidade_medida='UN', codigo_simpas='42.40.10.00001-1',
        )
        dfd = DFD.objects.create(
            org_id=ssp, numero_sei='001.2026.0000001-11', descricao='DFD teste PC',
            valor_estimado=Decimal('1000.00'), area_aplicacao=['TI'],
            prazo_necessidade=date.today(), status='Aprovada', created_by=autor, updated_by=autor,
        )
        ItemDFD.objects.create(
            org_id=ssp, dfd=dfd, item_catalogo=item_catalogo, objeto=item_catalogo.nome,
            justificativa='Teste', unidade_medida='UN', quantidade=Decimal('5'),
            valor_unitario_estimado=Decimal('100.00'), valor_total_estimado=Decimal('500.00'),
            created_by=autor, updated_by=autor,
        )
        _login(api_client, 'analista_pc')
        resp = api_client.get('/api/indicadores/plano-compras/')
        assert resp.status_code == 200
        for chave in ('exercicio', 'limite_dispensa', 'total_familias', 'valor_total', 'familias'):
            assert chave in resp.data

    def test_get_sem_itens_ainda_retorna_200(self, api_client, ssp, analista_user):
        """Mesmo sem nenhum item pendente, a view precisa responder — antes do
        fix, faltava o `return` também neste caminho (lista de famílias vazia)."""
        _login(api_client, 'analista_pc')
        resp = api_client.get('/api/indicadores/plano-compras/')
        assert resp.status_code == 200
        assert resp.data['familias'] == []
