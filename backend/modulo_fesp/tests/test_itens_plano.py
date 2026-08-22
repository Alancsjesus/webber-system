from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao
from modulo_fesp.models import (
    InstrumentoFinanceiro, ComposicaoConselhoGestor, PlanoAplicacao, MetaEspecifica, ItemPlanoAplicacao,
)


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def orgao(db):
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPTEST2', ativa=True)


@pytest.fixture
def outro_orgao(db):
    return Orgao.objects.create(nome='PMBA Teste', sigla='PMBATEST2', ativa=True)


def _make_user(orgao, papel, username):
    user = User.objects.create_user(username=username, password='Senha@1234')
    user.profile.papel = papel
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def planejamento_user(db, orgao):
    return _make_user(orgao, 'gestor_planejamento', 'plan_test2')


def _login(api_client, username):
    resp = api_client.post('/api/token/', {
        'username': username, 'password': 'Senha@1234', 'captcha_token': '',
    }, format='json')
    assert resp.status_code == 200, resp.data
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')


@pytest.fixture
def instrumento(db, orgao, planejamento_user):
    return InstrumentoFinanceiro.objects.create(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        tipo_instrumento='fesp', numero_instrumento='FESP-2026',
        objeto='Recursos do FESP para 2026.', valor_total_pactuado='1000000.00',
    )


@pytest.fixture
def plano(db, orgao, planejamento_user):
    return PlanoAplicacao.objects.create(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        exercicio_fiscal=2026, ementa='Plano de Aplicação FESP 2026',
    )


@pytest.fixture
def meta(db, orgao, planejamento_user, plano):
    return MetaEspecifica.objects.create(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        plano=plano, titulo='ME 1 — Interior da Bahia',
    )


def _criar_item(orgao, planejamento_user, meta, instrumento, **overrides):
    defaults = dict(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        meta_especifica=meta, instrumento=instrumento, org_beneficiaria=orgao,
        bem_servico='Microcomputador', natureza='investimento',
        unidade_medida='Unidade', quantidade=Decimal('5'), valor_unitario_estimado=Decimal('2000.00'),
    )
    defaults.update(overrides)
    return ItemPlanoAplicacao.objects.create(**defaults)


@pytest.mark.django_db
class TestValorTotalItem:
    def test_valor_total_calculado_no_save(self, orgao, planejamento_user, meta, instrumento):
        item = _criar_item(orgao, planejamento_user, meta, instrumento)
        assert item.valor_total_estimado == 10000

    def test_meta_valor_total_agrega_itens(self, orgao, planejamento_user, meta, instrumento):
        _criar_item(orgao, planejamento_user, meta, instrumento, quantidade=Decimal('5'), valor_unitario_estimado=Decimal('2000.00'))
        _criar_item(orgao, planejamento_user, meta, instrumento, quantidade=Decimal('2'), valor_unitario_estimado=Decimal('500.00'), natureza='custeio')
        meta.refresh_from_db()
        assert meta.valor_total == 11000

    def test_plano_valor_planejado_split_por_natureza(self, orgao, planejamento_user, plano, meta, instrumento):
        _criar_item(orgao, planejamento_user, meta, instrumento, quantidade=Decimal('5'), valor_unitario_estimado=Decimal('2000.00'), natureza='investimento')
        _criar_item(orgao, planejamento_user, meta, instrumento, quantidade=Decimal('2'), valor_unitario_estimado=Decimal('500.00'), natureza='custeio')
        plano.refresh_from_db()
        assert plano.valor_planejado_investimento == 10000
        assert plano.valor_planejado_custeio == 1000

    def test_item_cancelado_nao_conta_no_total(self, orgao, planejamento_user, meta, instrumento):
        item = _criar_item(orgao, planejamento_user, meta, instrumento, quantidade=Decimal('5'), valor_unitario_estimado=Decimal('2000.00'))
        item.status = 'cancelado'
        item.save()
        meta.refresh_from_db()
        assert meta.valor_total == 0


@pytest.mark.django_db
class TestEditabilidadeItem:
    def test_editavel_via_api_enquanto_em_elaboracao(self, api_client, orgao, planejamento_user, plano, meta, instrumento):
        _login(api_client, 'plan_test2')
        resp = api_client.post('/api/fesp/item-plano/', {
            'meta_especifica': meta.id, 'instrumento': instrumento.id, 'org_beneficiaria': orgao.id,
            'bem_servico': 'Notebook', 'natureza': 'investimento',
            'unidade_medida': 'Unidade', 'quantidade': '10', 'valor_unitario_estimado': '3000.00',
        }, format='json')
        assert resp.status_code == 201, resp.data
        assert resp.data['valor_total_estimado'] == '30000.00'

    def test_bloqueado_apos_submissao_ao_conselho(self, api_client, orgao, planejamento_user, plano, meta, instrumento):
        item = _criar_item(orgao, planejamento_user, meta, instrumento)
        ComposicaoConselhoGestor.objects.create(
            org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
            usuario=planejamento_user, cargo='presidente', data_inicio_mandato='2026-01-01', ativo=True,
        )
        plano.declaracao_nao_pessoal = True
        plano.declaracao_nao_unidade_administrativa = True
        plano.declaracao_sem_contingenciamento = True
        plano.save()
        _login(api_client, 'plan_test2')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/submeter_conselho/')
        assert resp.status_code == 200, resp.data

        resp = api_client.patch(f'/api/fesp/item-plano/{item.id}/', {'bem_servico': 'Alterado'}, format='json')
        assert resp.status_code == 400, resp.data


@pytest.mark.django_db
class TestIsolamentoMultiTenantItens:
    def test_outro_orgao_nao_ve_item(self, api_client, outro_orgao, orgao, planejamento_user, meta, instrumento):
        item = _criar_item(orgao, planejamento_user, meta, instrumento)
        outro_user = _make_user(outro_orgao, 'gestor_planejamento', 'outro_org_test2')
        _login(api_client, 'outro_org_test2')
        resp = api_client.get(f'/api/fesp/item-plano/{item.id}/')
        assert resp.status_code == 404
