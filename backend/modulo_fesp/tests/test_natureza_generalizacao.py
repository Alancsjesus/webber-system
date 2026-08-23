from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from core.models import Orgao
from core.checklist_engine import ChecklistEngine
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
    return Orgao.objects.create(nome='SSP Teste Natureza', sigla='SSPNAT', ativa=True)


def _make_user(orgao, papel, username):
    user = User.objects.create_user(username=username, password='Senha@1234')
    user.profile.papel = papel
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def planejamento_user(db, orgao):
    return _make_user(orgao, 'gestor_planejamento', 'plan_natureza')


@pytest.fixture
def ordenador_user(db, orgao):
    return _make_user(orgao, 'ordenador', 'ordenador_natureza')


@pytest.fixture
def conselho_user(db, orgao):
    user = _make_user(orgao, 'analista', 'conselho_natureza')
    ComposicaoConselhoGestor.objects.create(
        org_id=orgao, created_by=user, updated_by=user,
        usuario=user, cargo='presidente', data_inicio_mandato='2026-01-01', ativo=True,
    )
    return user


def _login(api_client, username):
    resp = api_client.post('/api/token/', {
        'username': username, 'password': 'Senha@1234', 'captcha_token': '',
    }, format='json')
    assert resp.status_code == 200, resp.data
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')


@pytest.fixture
def plano_fesp(db, orgao, planejamento_user):
    return PlanoAplicacao.objects.create(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        exercicio_fiscal=2026, ementa='Plano FESP 2026', natureza='fesp',
    )


@pytest.fixture
def plano_convenio(db, orgao, planejamento_user):
    return PlanoAplicacao.objects.create(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        exercicio_fiscal=2026, ementa='Plano de Convênio 2026', natureza='convenio',
    )


@pytest.fixture
def instrumento_convenio(db, orgao, planejamento_user):
    return InstrumentoFinanceiro.objects.create(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        tipo_instrumento='convenio', numero_instrumento='CONV-2026',
        objeto='Convênio de teste.', valor_total_pactuado='500000.00',
    )


@pytest.fixture
def instrumento_fesp(db, orgao, planejamento_user):
    return InstrumentoFinanceiro.objects.create(
        org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
        tipo_instrumento='fesp', numero_instrumento='FESP-2026',
        objeto='Recursos do FESP.', valor_total_pactuado='1000000.00',
    )


# ---------------------------------------------------------------------------
# unique_together e numeração por natureza
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUniqueTogetherPorNatureza:
    def test_permite_duas_naturezas_mesmo_org_exercicio(self, orgao, planejamento_user, plano_fesp):
        plano2 = PlanoAplicacao.objects.create(
            org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
            exercicio_fiscal=2026, ementa='Plano de Emenda 2026', natureza='emenda_parlamentar',
        )
        assert plano2.natureza == 'emenda_parlamentar'

    def test_duplicar_mesma_natureza_mesmo_org_exercicio_falha(self, orgao, planejamento_user, plano_fesp):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                PlanoAplicacao.objects.create(
                    org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
                    exercicio_fiscal=2026, ementa='Outro Plano FESP 2026', natureza='fesp',
                )


@pytest.mark.django_db
class TestNumeroPorNatureza:
    def test_prefixo_por_natureza(self, plano_convenio):
        assert plano_convenio.numero.startswith('PLANCONV-SSPNAT-001/2026')

    def test_sequencia_independente_por_natureza(self, orgao, planejamento_user, plano_fesp, plano_convenio):
        plano_fesp2 = PlanoAplicacao.objects.create(
            org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
            exercicio_fiscal=2027, ementa='Plano FESP 2027', natureza='fesp',
        )
        assert plano_fesp2.numero.startswith('PLANFESP-SSPNAT-001/2027')


# ---------------------------------------------------------------------------
# Compatibilidade instrumento <-> natureza do plano
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCompatibilidadeInstrumento:
    def test_item_rejeita_instrumento_de_natureza_incompativel(
        self, api_client, orgao, planejamento_user, plano_convenio, instrumento_fesp,
    ):
        meta = MetaEspecifica.objects.create(
            org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
            plano=plano_convenio, titulo='ME 1',
        )
        _login(api_client, 'plan_natureza')
        resp = api_client.post('/api/fesp/item-plano/', {
            'meta_especifica': meta.id, 'instrumento': instrumento_fesp.id, 'org_beneficiaria': orgao.id,
            'bem_servico': 'Equipamento', 'natureza': 'investimento',
            'unidade_medida': 'Unidade', 'quantidade': '1', 'valor_unitario_estimado': '1000.00',
        }, format='json')
        assert resp.status_code == 400, resp.data
        assert 'instrumento' in resp.data

    def test_item_aceita_instrumento_compativel(
        self, api_client, orgao, planejamento_user, plano_convenio, instrumento_convenio,
    ):
        meta = MetaEspecifica.objects.create(
            org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
            plano=plano_convenio, titulo='ME 1',
        )
        _login(api_client, 'plan_natureza')
        resp = api_client.post('/api/fesp/item-plano/', {
            'meta_especifica': meta.id, 'instrumento': instrumento_convenio.id, 'org_beneficiaria': orgao.id,
            'bem_servico': 'Equipamento', 'natureza': 'investimento',
            'unidade_medida': 'Unidade', 'quantidade': '1', 'valor_unitario_estimado': '1000.00',
        }, format='json')
        assert resp.status_code == 201, resp.data


# ---------------------------------------------------------------------------
# Checklist do rito simples
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChecklistRitoSimples:
    def test_nao_exige_declaracoes_nem_conselho(self, orgao, planejamento_user, plano_convenio):
        MetaEspecifica.objects.create(
            org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
            plano=plano_convenio, titulo='ME 1',
        )
        resultado = ChecklistEngine.avaliar_plano_aplicacao(plano_convenio)
        assert resultado.pode_submeter is True

    def test_exige_ao_menos_uma_meta(self, plano_convenio):
        resultado = ChecklistEngine.avaliar_plano_aplicacao(plano_convenio)
        assert resultado.pode_submeter is False


# ---------------------------------------------------------------------------
# Fluxo do rito simples: aprovar -> publicar -> encerrar
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFluxoRitoSimples:
    def test_aprovar_publicar_encerrar(self, api_client, orgao, planejamento_user, plano_convenio):
        MetaEspecifica.objects.create(
            org_id=orgao, created_by=planejamento_user, updated_by=planejamento_user,
            plano=plano_convenio, titulo='ME 1',
        )
        _login(api_client, 'plan_natureza')

        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/aprovar/')
        assert resp.status_code == 200, resp.data
        assert resp.data['status'] == 'aprovado'

        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/publicar/')
        assert resp.status_code == 200, resp.data
        assert resp.data['status'] == 'publicado'

        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/encerrar/')
        assert resp.status_code == 200, resp.data
        assert resp.data['status'] == 'encerrado'

    def test_aprovar_bloqueado_sem_meta(self, api_client, planejamento_user, plano_convenio):
        _login(api_client, 'plan_natureza')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/aprovar/')
        assert resp.status_code == 400, resp.data


# ---------------------------------------------------------------------------
# Ações do rito FESP bloqueadas fora do FESP, e vice-versa
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGuardasDeNatureza:
    def test_submeter_conselho_bloqueado_fora_fesp(self, api_client, planejamento_user, plano_convenio):
        _login(api_client, 'plan_natureza')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/submeter_conselho/')
        assert resp.status_code == 400, resp.data

    def test_aprovar_conselho_bloqueado_fora_fesp(self, api_client, conselho_user, plano_convenio):
        _login(api_client, 'conselho_natureza')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/aprovar_conselho/', {
            'numero_ata': 'ATA-001', 'data_reuniao': '2026-02-01',
        })
        assert resp.status_code == 400, resp.data

    def test_devolver_bloqueado_fora_fesp(self, api_client, conselho_user, plano_convenio):
        _login(api_client, 'conselho_natureza')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/devolver/', {'motivo': 'x'})
        assert resp.status_code == 400, resp.data

    def test_homologar_bloqueado_fora_fesp(self, api_client, ordenador_user, plano_convenio):
        _login(api_client, 'ordenador_natureza')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/homologar/', {
            'numero_ato': 'ATO-1', 'data_ato': '2026-01-01',
        })
        assert resp.status_code == 400, resp.data

    def test_aprovar_bloqueado_dentro_fesp(self, api_client, planejamento_user, plano_fesp):
        _login(api_client, 'plan_natureza')
        resp = api_client.post(f'/api/fesp/plano-aplicacao/{plano_fesp.id}/aprovar/')
        assert resp.status_code == 400, resp.data


# ---------------------------------------------------------------------------
# PDF para natureza fora do FESP
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestExportPdfNaturezaSimples:
    def test_pdf_gera_sem_erro_para_convenio(self, api_client, planejamento_user, plano_convenio):
        _login(api_client, 'plan_natureza')
        resp = api_client.get(f'/api/fesp/plano-aplicacao/{plano_convenio.id}/export/pdf/')
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'application/pdf'
        assert resp.content[:4] == b'%PDF'
        assert len(resp.content) > 500
