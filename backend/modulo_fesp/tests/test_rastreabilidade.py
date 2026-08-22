from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao
from modulo_fesp.models import InstrumentoFinanceiro, PlanoAplicacao, MetaEspecifica, ItemPlanoAplicacao, GrupoConsolidacaoItem


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
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPRAST', ativa=True)


@pytest.fixture
def cbmba(db, ssp):
    return Orgao.objects.create(nome='CBMBA Teste', sigla='CBMBARAST', ativa=True, parent=ssp)


def _make_user(orgao, papel, username):
    user = User.objects.create_user(username=username, password='Senha@1234')
    user.profile.papel = papel
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def planejamento_user(db, ssp):
    return _make_user(ssp, 'gestor_planejamento', 'plan_rast')


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
        plano=plano, titulo='ME 1',
    )


@pytest.fixture
def necessidade_fesp(db, api_client, ssp, planejamento_user, plano, meta, instrumento):
    """Necessidade gerada via consolidação — mesmo caminho usado pelos usuários reais."""
    item = ItemPlanoAplicacao.objects.create(
        org_id=ssp, created_by=planejamento_user, updated_by=planejamento_user,
        meta_especifica=meta, instrumento=instrumento, org_beneficiaria=ssp,
        bem_servico='Viatura', natureza='investimento', codigo_senasp='MAT.09.001.0002',
        unidade_medida='Unidade', quantidade=Decimal('1'), valor_unitario_estimado=Decimal('190000.00'),
    )
    _login(api_client, 'plan_rast')
    resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
        'titulo': 'Viatura', 'item_ids': [item.id],
    }, format='json')
    grupo_id = resp.data['grupo']['id']
    resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')
    from modulo_planejamento.models import NecessidadePlanejamento
    return NecessidadePlanejamento.objects.get(id=resp.data['necessidades_ids'][0])


@pytest.fixture
def necessidade_fesp_externa(db, api_client, ssp, cbmba, planejamento_user, plano, meta, instrumento):
    """Necessidade externa (org_beneficiaria=CBMBA) gerada a partir do plano gerido pela SSP."""
    item = ItemPlanoAplicacao.objects.create(
        org_id=ssp, created_by=planejamento_user, updated_by=planejamento_user,
        meta_especifica=meta, instrumento=instrumento, org_beneficiaria=cbmba,
        bem_servico='Viatura CBM', natureza='investimento', codigo_senasp='MAT.09.001.0003',
        unidade_medida='Unidade', quantidade=Decimal('1'), valor_unitario_estimado=Decimal('90000.00'),
    )
    _login(api_client, 'plan_rast')
    resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/confirmar_consolidacao/', {
        'titulo': 'Viatura CBM', 'item_ids': [item.id],
    }, format='json')
    grupo_id = resp.data['grupo']['id']
    resp = api_client.post(f'/api/fesp/grupo-consolidacao/{grupo_id}/gerar_necessidades/')
    from modulo_planejamento.models import NecessidadePlanejamento
    return NecessidadePlanejamento.objects.get(id=resp.data['necessidades_ids'][0])


@pytest.mark.django_db
class TestOrigemRecursoNaRastreabilidade:
    def test_detail_traz_origem_recurso(self, api_client, planejamento_user, necessidade_fesp, plano):
        _login(api_client, 'plan_rast')
        resp = api_client.get(f'/api/rastreabilidade/{necessidade_fesp.id}/')
        assert resp.status_code == 200, resp.data
        origem = resp.data['origem_recurso']
        assert origem is not None
        assert origem['plano_id'] == plano.id
        assert origem['plano_numero'] == plano.numero
        assert len(origem['instrumentos']) == 1
        assert origem['instrumentos'][0]['tipo'] == 'FESP — Fundo Estadual de Segurança Pública'

    def test_list_traz_origem_recurso(self, api_client, planejamento_user, necessidade_fesp):
        _login(api_client, 'plan_rast')
        resp = api_client.get('/api/rastreabilidade/')
        assert resp.status_code == 200, resp.data
        linha = next(r for r in resp.data['results'] if r['id'] == necessidade_fesp.id)
        assert linha['origem_recurso'] is not None

    def test_necessidade_comum_nao_traz_origem_recurso(self, api_client, ssp, planejamento_user):
        from modulo_planejamento.models import NecessidadePlanejamento
        nec = NecessidadePlanejamento.objects.create(
            org_id=ssp, created_by=planejamento_user, updated_by=planejamento_user,
            titulo='Necessidade comum', descricao='Sem relação com FESP.',
            valor_estimado=Decimal('1000.00'), departamento_solicitante='TI',
            exercicio_fiscal=2026, status='Identificada',
        )
        _login(api_client, 'plan_rast')
        resp = api_client.get(f'/api/rastreabilidade/{nec.id}/')
        assert resp.status_code == 200, resp.data
        assert resp.data['origem_recurso'] is None


@pytest.mark.django_db
class TestVisibilidadeCrossOrgNaRastreabilidade:
    """
    A SSP (org gestora do fundo) precisa enxergar, na rastreabilidade, as
    necessidades externas que ela mesma gerou para órgãos filhos (CBMBA) a
    partir de um Plano de Aplicação FESP — mesmo critério de visibilidade já
    usado por NecessidadeViewSet.get_queryset.
    """
    def test_ssp_ve_necessidade_externa_na_lista(self, api_client, planejamento_user, necessidade_fesp_externa):
        _login(api_client, 'plan_rast')
        resp = api_client.get('/api/rastreabilidade/')
        assert resp.status_code == 200, resp.data
        ids = [r['id'] for r in resp.data['results']]
        assert necessidade_fesp_externa.id in ids

    def test_ssp_ve_necessidade_externa_no_detalhe(self, api_client, planejamento_user, necessidade_fesp_externa, plano):
        _login(api_client, 'plan_rast')
        resp = api_client.get(f'/api/rastreabilidade/{necessidade_fesp_externa.id}/')
        assert resp.status_code == 200, resp.data
        assert resp.data['origem_recurso']['plano_id'] == plano.id

    def test_org_nao_relacionada_nao_ve_necessidade_externa(self, api_client, necessidade_fesp_externa):
        outra_org = Orgao.objects.create(nome='Outro Órgão', sigla='OUTRORAST', ativa=True)
        outro_user = User.objects.create_user(username='outro_rast', password='Senha@1234')
        outro_user.profile.papel = 'gestor_planejamento'
        outro_user.profile.org_id = outra_org
        outro_user.profile.save()
        _login(api_client, 'outro_rast')
        resp = api_client.get(f'/api/rastreabilidade/{necessidade_fesp_externa.id}/')
        assert resp.status_code == 404


@pytest.mark.django_db
class TestExecucaoPlano:
    def test_resumo_execucao_reflete_valor_planejado(self, api_client, planejamento_user, necessidade_fesp, plano):
        _login(api_client, 'plan_rast')
        resp = api_client.get(f'/api/fesp/plano-aplicacao/{plano.id}/execucao/')
        assert resp.status_code == 200, resp.data
        assert resp.data['resumo']['total_necessidades'] == 1
        assert Decimal(resp.data['resumo']['valor_planejado']) == Decimal('190000.00')
        assert Decimal(resp.data['resumo']['valor_em_dfd']) == Decimal('0')
        assert len(resp.data['necessidades']) == 1
        assert resp.data['necessidades'][0]['etapa_atual'] == 'Necessidade'

    def test_plano_sem_necessidades_retorna_resumo_zerado(self, api_client, ssp, planejamento_user):
        plano_vazio = PlanoAplicacao.objects.create(
            org_id=ssp, created_by=planejamento_user, updated_by=planejamento_user,
            exercicio_fiscal=2027, ementa='Plano vazio',
        )
        _login(api_client, 'plan_rast')
        resp = api_client.get(f'/api/fesp/plano-aplicacao/{plano_vazio.id}/execucao/')
        assert resp.status_code == 200, resp.data
        assert resp.data['resumo']['total_necessidades'] == 0
        assert Decimal(resp.data['resumo']['valor_planejado']) == Decimal('0')


@pytest.mark.django_db
class TestExportPdf:
    def test_export_pdf_gera_bytes_validos(self, api_client, planejamento_user, plano):
        _login(api_client, 'plan_rast')
        resp = api_client.get(f'/api/fesp/plano-aplicacao/{plano.id}/export/pdf/')
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'application/pdf'
        assert resp.content[:4] == b'%PDF'
        assert len(resp.content) > 500
