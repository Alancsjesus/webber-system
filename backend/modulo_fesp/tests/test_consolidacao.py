from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao, ItemCatalogo, CategoriaItem
from modulo_fesp.models import (
    InstrumentoFinanceiro, PlanoAplicacao, MetaEspecifica, ItemPlanoAplicacao,
    GrupoConsolidacaoItem,
)
from modulo_planejamento.models import NecessidadePlanejamento


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
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPCONS', ativa=True)


@pytest.fixture
def pmba(db, ssp):
    return Orgao.objects.create(nome='PMBA Teste', sigla='PMBACONS', ativa=True, parent=ssp)


@pytest.fixture
def cbmba(db, ssp):
    return Orgao.objects.create(nome='CBMBA Teste', sigla='CBMBACONS', ativa=True, parent=ssp)


def _make_user(orgao, papel, username):
    user = User.objects.create_user(username=username, password='Senha@1234')
    user.profile.papel = papel
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def planejamento_user(db, ssp):
    return _make_user(ssp, 'gestor_planejamento', 'plan_cons')


def _login(api_client, username):
    resp = api_client.post('/api/token/', {
        'username': username, 'password': 'Senha@1234', 'captcha_token': '',
    }, format='json')
    assert resp.status_code == 200, resp.data
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')


@pytest.fixture
def instrumento(db, ssp, planejamento_user):
    return InstrumentoFinanceiro.objects.create(
        org_id=ssp, created_by=planejamento_user, updated_by=planejamento_user,
        tipo_instrumento='fesp', numero_instrumento='FESP-2026',
        objeto='Recursos do FESP para 2026.', valor_total_pactuado='1000000.00',
    )


@pytest.fixture
def plano(db, ssp, planejamento_user):
    return PlanoAplicacao.objects.create(
        org_id=ssp, created_by=planejamento_user, updated_by=planejamento_user,
        exercicio_fiscal=2026, ementa='Plano de Aplicação FESP 2026',
    )


@pytest.fixture
def meta(db, ssp, planejamento_user, plano):
    return MetaEspecifica.objects.create(
        org_id=ssp, created_by=planejamento_user, updated_by=planejamento_user,
        plano=plano, titulo='ME 1 — Enfrentamento à violência',
    )


@pytest.fixture
def item_catalogo(db):
    categoria = CategoriaItem.objects.create(nome='Viaturas')
    return ItemCatalogo.objects.create(
        nome='Viatura policial', codigo_simpas='25.10.30.00012345-6',
        categoria=categoria, unidade_medida='Unidade',
    )


def _criar_item(ssp, planejamento_user, meta, instrumento, org_beneficiaria, **overrides):
    defaults = dict(
        org_id=ssp, created_by=planejamento_user, updated_by=planejamento_user,
        meta_especifica=meta, instrumento=instrumento, org_beneficiaria=org_beneficiaria,
        bem_servico='Viatura policial', natureza='investimento', codigo_senasp='MAT.09.001.0002',
        unidade_medida='Unidade', quantidade=Decimal('2'), valor_unitario_estimado=Decimal('190000.00'),
    )
    defaults.update(overrides)
    return ItemPlanoAplicacao.objects.create(**defaults)


@pytest.mark.django_db
class TestSugestoesConsolidacao:
    def test_agrupa_itens_de_orgaos_diferentes_pela_mesma_chave(
        self, api_client, ssp, pmba, cbmba, planejamento_user, plano, meta, instrumento,
    ):
        _criar_item(ssp, planejamento_user, meta, instrumento, pmba)
        _criar_item(ssp, planejamento_user, meta, instrumento, cbmba)

        _login(api_client, 'plan_cons')
        resp = api_client.get(f'/api/fesp/plano-aplicacao/{plano.id}/sugestoes_consolidacao/')
        assert resp.status_code == 200, resp.data
        grupos = resp.data['grupos_sugeridos']
        assert len(grupos) == 1
        grupo = grupos[0]
        assert grupo['chave_agrupamento'] == 'MAT.09'
        assert grupo['total_itens'] == 2
        assert grupo['total_orgaos'] == 2
        assert grupo['multi_orgao'] is True

    def test_itens_do_mesmo_orgao_nao_sao_multi_orgao(
        self, api_client, ssp, pmba, planejamento_user, plano, meta, instrumento,
    ):
        _criar_item(ssp, planejamento_user, meta, instrumento, pmba)
        _criar_item(ssp, planejamento_user, meta, instrumento, pmba)

        _login(api_client, 'plan_cons')
        resp = api_client.get(f'/api/fesp/plano-aplicacao/{plano.id}/sugestoes_consolidacao/')
        grupo = resp.data['grupos_sugeridos'][0]
        assert grupo['total_orgaos'] == 1
        assert grupo['multi_orgao'] is False

    def test_usa_familia_simpas_quando_item_catalogo_presente(
        self, api_client, ssp, pmba, planejamento_user, plano, meta, instrumento, item_catalogo,
    ):
        _criar_item(ssp, planejamento_user, meta, instrumento, pmba, item_catalogo=item_catalogo)
        _login(api_client, 'plan_cons')
        resp = api_client.get(f'/api/fesp/plano-aplicacao/{plano.id}/sugestoes_consolidacao/')
        grupo = resp.data['grupos_sugeridos'][0]
        assert grupo['chave_agrupamento'] == item_catalogo.familia


@pytest.mark.django_db
class TestGerarNecessidadesDeGrupo:
    def test_gera_uma_necessidade_por_orgao_beneficiario(
        self, api_client, ssp, pmba, cbmba, planejamento_user, plano, meta, instrumento,
    ):
        item_pmba = _criar_item(ssp, planejamento_user, meta, instrumento, pmba)
        item_cbmba = _criar_item(ssp, planejamento_user, meta, instrumento, cbmba)

        _login(api_client, 'plan_cons')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
            'titulo': 'Viaturas consolidadas',
            'item_ids': [item_pmba.id, item_cbmba.id],
        }, format='json')
        assert resp.status_code == 201, resp.data
        grupo_id = resp.data['grupo']['id']

        resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')
        assert resp.status_code == 200, resp.data
        assert len(resp.data['necessidades_ids']) == 2

        necessidades = NecessidadePlanejamento.objects.filter(id__in=resp.data['necessidades_ids'])
        by_org = {n.org_id_id: n for n in necessidades}

        nec_pmba = by_org[pmba.id]
        assert nec_pmba.tipo_execucao == 'externa'
        assert nec_pmba.aceite_pai == 'aceita'
        assert nec_pmba.org_gestor_id == ssp.id
        assert nec_pmba.orgao_executor_id == ssp.id
        assert nec_pmba.origem_plano_aplicacao_fesp_id == plano.id
        assert nec_pmba.status == 'Aprovada'
        assert nec_pmba.valor_estimado == Decimal('380000.00')

        nec_cbmba = by_org[cbmba.id]
        assert nec_cbmba.tipo_execucao == 'externa'
        assert nec_cbmba.aceite_pai == 'aceita'

        item_pmba.refresh_from_db()
        assert item_pmba.status == 'necessidade_gerada'
        assert item_pmba.necessidade_gerada_id == nec_pmba.id

        grupo = GrupoConsolidacaoItem.objects.get(id=grupo_id)
        assert grupo.status == 'processado'

    def test_necessidade_propria_org_gestora_e_interna(
        self, api_client, ssp, planejamento_user, plano, meta, instrumento,
    ):
        item = _criar_item(ssp, planejamento_user, meta, instrumento, ssp)
        _login(api_client, 'plan_cons')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
            'titulo': 'Item da própria SSP',
            'item_ids': [item.id],
        }, format='json')
        grupo_id = resp.data['grupo']['id']

        resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')
        nec = NecessidadePlanejamento.objects.get(id=resp.data['necessidades_ids'][0])
        assert nec.tipo_execucao == 'interna'
        assert nec.aceite_pai is None
        assert nec.org_gestor is None
        assert nec.orgao_executor_id == ssp.id

    def test_grupo_ja_processado_nao_gera_de_novo(
        self, api_client, ssp, pmba, planejamento_user, plano, meta, instrumento,
    ):
        item = _criar_item(ssp, planejamento_user, meta, instrumento, pmba)
        _login(api_client, 'plan_cons')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
            'titulo': 'Grupo único', 'item_ids': [item.id],
        }, format='json')
        grupo_id = resp.data['grupo']['id']
        api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')

        resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')
        assert resp.status_code == 400

    def test_necessidade_gerada_visivel_para_org_filha_e_para_ssp(
        self, api_client, ssp, pmba, planejamento_user, plano, meta, instrumento,
    ):
        """A necessidade externa gerada deve aparecer tanto para o órgão filho quanto para o pai (SSP)."""
        item = _criar_item(ssp, planejamento_user, meta, instrumento, pmba)
        _login(api_client, 'plan_cons')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
            'titulo': 'Grupo', 'item_ids': [item.id],
        }, format='json')
        grupo_id = resp.data['grupo']['id']
        resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')
        nec_id = resp.data['necessidades_ids'][0]

        # Visível para a SSP (pai/gestora) via listagem já existente
        resp = api_client.get('/api/planejamento/necessidade/')
        ids = [n['id'] for n in resp.data.get('results', resp.data)]
        assert nec_id in ids

        # Visível para a PMBA (org de origem da necessidade)
        pmba_user = _make_user(pmba, 'gestor_planejamento', 'plan_pmba_cons')
        _login(api_client, 'plan_pmba_cons')
        resp = api_client.get('/api/planejamento/necessidade/')
        ids = [n['id'] for n in resp.data.get('results', resp.data)]
        assert nec_id in ids

    def test_iniciar_dfd_funciona_sem_alteracao_sobre_necessidade_fesp(
        self, api_client, ssp, planejamento_user, plano, meta, instrumento,
    ):
        """Regressão: iniciar_dfd (fluxo já existente) continua funcionando para necessidades de origem FESP."""
        item = _criar_item(ssp, planejamento_user, meta, instrumento, ssp)
        _login(api_client, 'plan_cons')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
            'titulo': 'Grupo', 'item_ids': [item.id],
        }, format='json')
        grupo_id = resp.data['grupo']['id']
        resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')
        nec_id = resp.data['necessidades_ids'][0]

        resp = api_client.post(f'/api/planejamento/necessidade/{nec_id}/iniciar_dfd/', {
            'numero_sei': '099.0000.2026.0000001-11',
            'prazo_necessidade': '2026-12-31',
            'area_aplicacao': ['Ops'],
            'itens': [{
                'objeto': 'Viatura policial', 'unidade_medida': 'Unidade',
                'quantidade': 2, 'valor_unitario_estimado': 190000.00,
            }],
        }, format='json')
        assert resp.status_code in (200, 201), resp.data


@pytest.mark.django_db
class TestGerarNecessidadeIndividual:
    def test_item_singleton_gera_grupo_de_um_e_necessidade(
        self, api_client, ssp, pmba, planejamento_user, plano, meta, instrumento,
    ):
        item = _criar_item(ssp, planejamento_user, meta, instrumento, pmba, bem_servico='Item avulso')
        _login(api_client, 'plan_cons')
        resp = api_client.post(f'/api/fesp/item-plano/{item.id}/gerar_necessidade_individual/')
        assert resp.status_code == 200, resp.data
        assert resp.data['necessidade_id'] is not None

        item.refresh_from_db()
        assert item.status == 'necessidade_gerada'
        assert item.grupo_consolidacao is not None
        assert item.grupo_consolidacao.status == 'processado'


@pytest.mark.django_db
class TestDesfazerConsolidacao:
    def test_desfazer_libera_itens_para_pendente(
        self, api_client, ssp, pmba, planejamento_user, plano, meta, instrumento,
    ):
        item = _criar_item(ssp, planejamento_user, meta, instrumento, pmba)
        _login(api_client, 'plan_cons')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
            'titulo': 'Grupo', 'item_ids': [item.id],
        }, format='json')
        grupo_id = resp.data['grupo']['id']

        resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/desfazer/')
        assert resp.status_code == 200, resp.data

        item.refresh_from_db()
        assert item.status == 'pendente'
        assert item.grupo_consolidacao is None
        assert not GrupoConsolidacaoItem.objects.filter(id=grupo_id).exists()

    def test_nao_pode_desfazer_grupo_ja_processado(
        self, api_client, ssp, pmba, planejamento_user, plano, meta, instrumento,
    ):
        item = _criar_item(ssp, planejamento_user, meta, instrumento, pmba)
        _login(api_client, 'plan_cons')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
            'titulo': 'Grupo', 'item_ids': [item.id],
        }, format='json')
        grupo_id = resp.data['grupo']['id']
        api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')

        resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/desfazer/')
        assert resp.status_code == 400
