from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Orgao, ParametroSistema
from modulo_demanda.models import DFD
from modulo_tramitacao.indicadores import calcular_indicadores


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
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPTRAM', ativa=True)


@pytest.fixture
def outro_org(db):
    return Orgao.objects.create(nome='Outro Órgão Teste', sigla='OUTROTRAM', ativa=True)


def _make_user(orgao, papel, username):
    user = User.objects.create_user(username=username, password='Senha@1234')
    user.profile.papel = papel
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def gestor_user(db, ssp):
    return _make_user(ssp, 'gestor_planejamento', 'gestor_tram')


def _login(api_client, username):
    resp = api_client.post('/api/token/', {
        'username': username, 'password': 'Senha@1234', 'captcha_token': '',
    }, format='json')
    assert resp.status_code == 200, resp.data
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')


class _FakeRequest:
    """calcular_indicadores() só usa .org_id e .query_params — evita subir o
    dispatch completo do DRF quando o teste é sobre a agregação, não sobre a
    view/rota em si (essa parte é coberta separadamente via api_client)."""
    def __init__(self, org_id, **params):
        self.org_id = org_id
        self.query_params = {k: v for k, v in params.items() if v is not None}


def _criar_dfd(org, dias_atras, numero_sei, status='Rascunho'):
    autor, _ = User.objects.get_or_create(username='autor_dfd_teste_tram')
    dfd = DFD.objects.create(
        org_id=org, numero_sei=numero_sei, descricao='Teste indicadores de tramitação',
        valor_estimado=Decimal('1000.00'), area_aplicacao=['TI'],
        prazo_necessidade=date.today() + timedelta(days=90), status=status,
        created_by=autor, updated_by=autor,
    )
    # updated_at é auto_now — força a data "de entrada na fase" pro passado
    # via update() no queryset, que não passa pelo save() (não reaplica auto_now).
    data_passada = timezone.now() - timedelta(days=dias_atras)
    DFD.objects.filter(pk=dfd.pk).update(updated_at=data_passada)
    dfd.refresh_from_db()
    return dfd


@pytest.mark.django_db
class TestClassificacaoIndicadores:
    def test_processo_recente_e_normal(self, ssp):
        _criar_dfd(ssp, dias_atras=2, numero_sei='001.2026.0000001-11')
        ind = calcular_indicadores(_FakeRequest(ssp))
        assert ind['total_processos'] == 1
        assert ind['processos_criticos'] == 0
        assert ind['processos_atencao'] == 0

    def test_processo_acima_do_limiar_atencao(self, ssp):
        _criar_dfd(ssp, dias_atras=20, numero_sei='001.2026.0000002-22')
        ind = calcular_indicadores(_FakeRequest(ssp))
        assert ind['processos_atencao'] == 1
        assert ind['processos_criticos'] == 0

    def test_processo_acima_do_limiar_critico(self, ssp):
        _criar_dfd(ssp, dias_atras=45, numero_sei='001.2026.0000003-33')
        ind = calcular_indicadores(_FakeRequest(ssp))
        assert ind['processos_criticos'] == 1
        assert ind['top_criticos'][0]['numero_sei'] == '001.2026.0000003-33'
        assert ind['top_criticos'][0]['dias_na_fase'] == 45

    def test_limiares_configuraveis_via_parametro_sistema(self, ssp):
        ParametroSistema.objects.create(chave='tramitacao_dias_atencao', valor='5')
        ParametroSistema.objects.create(chave='tramitacao_dias_critico', valor='10')
        _criar_dfd(ssp, dias_atras=7, numero_sei='001.2026.0000004-44')
        ind = calcular_indicadores(_FakeRequest(ssp))
        assert ind['limiar_dias_atencao'] == 5
        assert ind['limiar_dias_critico'] == 10
        assert ind['processos_atencao'] == 1
        assert ind['processos_criticos'] == 0

    def test_tempo_medio_e_etapa_de_maior_tempo(self, ssp):
        _criar_dfd(ssp, dias_atras=10, numero_sei='001.2026.0000005-55')
        _criar_dfd(ssp, dias_atras=30, numero_sei='001.2026.0000006-66')
        ind = calcular_indicadores(_FakeRequest(ssp))
        assert ind['tempo_medio_geral'] == 20.0
        assert ind['etapa_maior_tempo_medio'] == 'DFD'
        assert len(ind['por_etapa']) == 1
        assert ind['por_etapa'][0]['total'] == 2

    def test_isolamento_multi_tenant(self, ssp, outro_org):
        _criar_dfd(ssp, dias_atras=10, numero_sei='001.2026.0000007-77')
        _criar_dfd(outro_org, dias_atras=50, numero_sei='001.2026.0000008-88')
        ind_ssp = calcular_indicadores(_FakeRequest(ssp))
        assert ind_ssp['total_processos'] == 1
        assert ind_ssp['processos_criticos'] == 0

    def test_dfd_rejeitada_nao_aparece(self, ssp):
        _criar_dfd(ssp, dias_atras=100, numero_sei='001.2026.0000009-99', status='Rejeitada')
        ind = calcular_indicadores(_FakeRequest(ssp))
        assert ind['total_processos'] == 0


@pytest.mark.django_db
class TestFiltrosIndicadores:
    def test_filtro_por_etapa(self, ssp):
        _criar_dfd(ssp, dias_atras=10, numero_sei='001.2026.0000011-11')
        ind_dfd = calcular_indicadores(_FakeRequest(ssp, etapa='DFD'))
        ind_etp = calcular_indicadores(_FakeRequest(ssp, etapa='ETP'))
        assert ind_dfd['total_processos'] == 1
        assert ind_etp['total_processos'] == 0

    def test_filtro_por_setor(self, ssp):
        _criar_dfd(ssp, dias_atras=10, numero_sei='001.2026.0000012-12')
        ind = calcular_indicadores(_FakeRequest(ssp))
        setor_real = ind['por_setor'][0]['setor']
        ind_filtrado = calcular_indicadores(_FakeRequest(ssp, setor=setor_real))
        ind_vazio = calcular_indicadores(_FakeRequest(ssp, setor='Setor Que Não Existe'))
        assert ind_filtrado['total_processos'] == 1
        assert ind_vazio['total_processos'] == 0

    def test_filtro_por_periodo(self, ssp):
        hoje = date.today()
        _criar_dfd(ssp, dias_atras=5, numero_sei='001.2026.0000013-13')
        _criar_dfd(ssp, dias_atras=40, numero_sei='001.2026.0000014-14')

        so_recente = calcular_indicadores(_FakeRequest(
            ssp, data_inicio=(hoje - timedelta(days=10)).isoformat(),
        ))
        assert so_recente['total_processos'] == 1

        so_antigo = calcular_indicadores(_FakeRequest(
            ssp, data_fim=(hoje - timedelta(days=10)).isoformat(),
        ))
        assert so_antigo['total_processos'] == 1

    def test_filtro_data_invalida_e_ignorado_sem_erro(self, ssp):
        _criar_dfd(ssp, dias_atras=5, numero_sei='001.2026.0000015-15')
        ind = calcular_indicadores(_FakeRequest(ssp, data_inicio='not-a-date'))
        assert ind['total_processos'] == 1


@pytest.mark.django_db
class TestEndpointIndicadoresTramitacao:
    def test_endpoint_retorna_200_com_forma_esperada(self, api_client, ssp, gestor_user):
        _criar_dfd(ssp, dias_atras=5, numero_sei='001.2026.0000010-10')
        _login(api_client, 'gestor_tram')
        resp = api_client.get('/api/tramitacao/indicadores/')
        assert resp.status_code == 200
        for chave in ('total_processos', 'processos_criticos', 'processos_atencao',
                      'tempo_medio_geral', 'por_setor', 'por_etapa', 'top_criticos'):
            assert chave in resp.data

    def test_endpoint_exige_autenticacao(self, api_client):
        resp = api_client.get('/api/tramitacao/indicadores/')
        assert resp.status_code == 401
