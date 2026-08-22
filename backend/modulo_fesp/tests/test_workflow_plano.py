import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao
from modulo_fesp.models import (
    InstrumentoFinanceiro, ComposicaoConselhoGestor, PlanoAplicacao, MetaEspecifica,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Isola o throttle de login entre testes — vários testes fazem múltiplos logins."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def orgao(db):
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPTEST', ativa=True)


@pytest.fixture
def outro_orgao(db):
    return Orgao.objects.create(nome='PMBA Teste', sigla='PMBATEST', ativa=True)


def _make_user(orgao, papel, username):
    user = User.objects.create_user(username=username, password='Senha@1234')
    user.profile.papel = papel
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def planejamento_user(db, orgao):
    return _make_user(orgao, 'gestor_planejamento', 'plan_test')


@pytest.fixture
def ordenador_user(db, orgao):
    return _make_user(orgao, 'ordenador', 'ordenador_test')


@pytest.fixture
def conselho_user(db, orgao):
    """Usuário com papel operacional comum, mas registrado como presidente do Conselho Gestor."""
    user = _make_user(orgao, 'analista', 'conselho_test')
    ComposicaoConselhoGestor.objects.create(
        org_id=orgao, created_by=user, updated_by=user,
        usuario=user, cargo='presidente', data_inicio_mandato='2026-01-01', ativo=True,
    )
    return user


@pytest.fixture
def outro_org_user(db, outro_orgao):
    return _make_user(outro_orgao, 'gestor_planejamento', 'outro_org_test')


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
        objeto='Recursos do Fundo Estadual de Segurança Pública para 2026.',
        valor_total_pactuado='1000000.00',
    )


@pytest.fixture
def plano(db, orgao, planejamento_user):
    return PlanoAplicacao.objects.create(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        exercicio_fiscal=2026, ementa='Plano de Aplicação FESP 2026',
    )


# ---------------------------------------------------------------------------
# Numeração e transições básicas
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPlanoAplicacaoNumeracao:
    def test_numero_gerado_automaticamente(self, plano):
        assert plano.numero.startswith('PLANFESP-SSPTEST-001/2026')

    def test_segundo_plano_mesmo_org_outro_exercicio(self, orgao, planejamento_user, plano):
        plano2 = PlanoAplicacao.objects.create(
            org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
            exercicio_fiscal=2027, ementa='Plano 2027',
        )
        assert plano2.numero.startswith('PLANFESP-SSPTEST-001/2027')


# ---------------------------------------------------------------------------
# Checklist / submissão ao Conselho
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSubmeterConselho:
    def test_bloqueado_sem_declaracoes_nem_conselho(self, api_client, planejamento_user, plano):
        """Sem declarações respondidas, sem presidente do conselho e sem Meta Específica, não pode submeter."""
        _login(api_client, 'plan_test')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/submeter_conselho/')
        assert resp.status_code == 400, resp.data
        assert len(resp.data['bloqueadores']) >= 5

    def test_permitido_com_declaracoes_presidente_e_meta(self, api_client, planejamento_user, conselho_user, plano):
        plano.declaracao_nao_pessoal = True
        plano.declaracao_nao_unidade_administrativa = True
        plano.declaracao_sem_contingenciamento = False  # resposta "não" também é aceita — é atestação, não bloqueio de mérito
        plano.save()
        MetaEspecifica.objects.create(
            org_id=plano.org_id, created_by=planejamento_user, updated_by=planejamento_user,
            plano=plano, titulo='ME 1 — Interior da Bahia',
        )

        _login(api_client, 'plan_test')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/submeter_conselho/')
        assert resp.status_code == 200, resp.data
        assert resp.data['status'] == 'submetido_conselho'

    def test_transicao_invalida_rejeitada(self, api_client, planejamento_user, conselho_user, plano):
        plano.declaracao_nao_pessoal = True
        plano.declaracao_nao_unidade_administrativa = True
        plano.declaracao_sem_contingenciamento = True
        plano.save()
        _login(api_client, 'plan_test')
        # Plano ainda em elaboração — homologar direto não é uma transição permitida.
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/homologar/', {
            'numero_ato': 'ATO-1', 'data_ato': '2026-01-01',
        })
        # homologar exige papel ordenador/admin primeiro (403) — gestor_planejamento não tem esse papel.
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Aprovação pelo Conselho Gestor (restrita a membros)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAprovarConselho:
    def _submeter(self, api_client, plano, planejamento_user):
        plano.declaracao_nao_pessoal = True
        plano.declaracao_nao_unidade_administrativa = True
        plano.declaracao_sem_contingenciamento = True
        plano.save()
        MetaEspecifica.objects.create(
            org_id=plano.org_id, created_by=planejamento_user, updated_by=planejamento_user,
            plano=plano, titulo='ME 1 — Interior da Bahia',
        )
        _login(api_client, 'plan_test')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/submeter_conselho/')
        assert resp.status_code == 200, resp.data

    def test_nao_membro_nao_pode_aprovar(self, api_client, planejamento_user, conselho_user, plano):
        self._submeter(api_client, plano, planejamento_user)
        # planejamento_user não é membro do conselho
        _login(api_client, 'plan_test')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/aprovar_conselho/', {
            'numero_ata': 'ATA-001', 'data_reuniao': '2026-02-01',
        })
        assert resp.status_code == 403

    def test_membro_do_conselho_pode_aprovar(self, api_client, planejamento_user, conselho_user, plano):
        self._submeter(api_client, plano, planejamento_user)
        _login(api_client, 'conselho_test')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/aprovar_conselho/', {
            'numero_ata': 'ATA-001', 'data_reuniao': '2026-02-01',
        })
        assert resp.status_code == 200, resp.data
        assert resp.data['status'] == 'aprovado_conselho'
        assert resp.data['reuniao_aprovacao_detail']['numero_ata'] == 'ATA-001'

    def test_homologacao_por_ordenador(self, api_client, planejamento_user, conselho_user, ordenador_user, plano):
        self._submeter(api_client, plano, planejamento_user)
        _login(api_client, 'conselho_test')
        api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/aprovar_conselho/', {
            'numero_ata': 'ATA-001', 'data_reuniao': '2026-02-01',
        })
        _login(api_client, 'ordenador_test')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano.id}/homologar/', {
            'numero_ato': 'ATO-2026-01', 'data_ato': '2026-02-10',
        })
        assert resp.status_code == 200, resp.data
        assert resp.data['status'] == 'homologado'


# ---------------------------------------------------------------------------
# Isolamento multi-tenant
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestIsolamentoMultiTenant:
    def test_outro_orgao_nao_ve_plano(self, api_client, outro_org_user, plano):
        _login(api_client, 'outro_org_test')
        resp = api_client.get(f'/api/fesp/plano-aplicacao/{plano.id}/')
        assert resp.status_code == 404

    def test_outro_orgao_nao_lista_plano(self, api_client, outro_org_user, plano):
        _login(api_client, 'outro_org_test')
        resp = api_client.get('/api/fesp/plano-aplicacao/')
        assert resp.status_code == 200
        ids = [p['id'] for p in resp.data.get('results', resp.data)]
        assert plano.id not in ids
