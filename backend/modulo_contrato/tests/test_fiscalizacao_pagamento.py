"""
Fiscalização e pagamento do contrato: ateste é ato do fiscal designado, e o
pagamento só é efetivado com medição atestada, dentro do valor medido e com
nota de empenho existente na execução orçamentária da DOD do contrato.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao
from modulo_contrato.models import Contrato, Medicao
from modulo_demanda.models import DFD
from modulo_orcamento.models import (
    AcaoOrcamentaria, DotacaoOrcamentaria, ElementoDespesa, EmpenhoOrcamentario, FonteRecurso,
    IndicacaoDotacao, IndicacaoOrcamentaria, TipoAcaoOrcamentaria, TipoFonteRecurso,
)

SENHA = 'Senha@1234'


@pytest.fixture(autouse=True)
def limpar_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def org(db):
    return Orgao.objects.create(nome='SSP Teste Fiscalização', sigla='SSPFZ', ativa=True)


def _usuario(org, username, papel):
    user = User.objects.create_user(username=username, password=SENHA)
    user.profile.papel = papel
    user.profile.org_id = org
    user.profile.save()
    return user


@pytest.fixture
def fiscal(org):
    return _usuario(org, 'fiscal_fz', 'fiscal_contrato')


@pytest.fixture
def gestor(org):
    return _usuario(org, 'gestor_fz', 'gestor_contrato')


def _cliente(user):
    c = APIClient()
    r = c.post('/api/token/', {'username': user.username, 'password': SENHA, 'captcha_token': ''}, format='json')
    assert r.status_code == 200, r.data
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
    return c


@pytest.fixture
def dfd_com_empenho(org, gestor):
    """DFD com DOD aprovada e empenho 2026NE000001 registrado."""
    dfd = DFD.objects.create(
        org_id=org, numero_sei='FZ-DFD', descricao='DFD fiscalização', valor_estimado=Decimal('1000.00'),
        area_aplicacao=['TI'], prazo_necessidade=date.today(), status='Aprovada',
        created_by=gestor, updated_by=gestor,
    )
    tipo_fonte = TipoFonteRecurso.objects.create(descricao='Tesouro FZ')
    fonte = FonteRecurso.objects.create(org_id=org, codigo=100, nome='Ordinários', tipo=tipo_fonte)
    acao = AcaoOrcamentaria.objects.create(
        org_id=org, codigo='FZ.1', nome='Ação FZ', tipo=TipoAcaoOrcamentaria.objects.create(descricao='Equip FZ'))
    elemento = ElementoDespesa.objects.create(codigo=9952, descricao='Equipamento FZ')
    dot = DotacaoOrcamentaria.objects.create(
        org_id=org, exercicio_fiscal=2026, acao=acao, elemento_despesa=elemento,
        fonte_recurso=fonte, valor_dotado=Decimal('5000.00'),
    )
    ind = IndicacaoOrcamentaria.objects.create(
        org_id=org, numero='IND-FZ-001', exercicio_fiscal=2026, dfd=dfd, status='Aprovada',
        valor_total=Decimal('1000.00'),
    )
    linha = IndicacaoDotacao.objects.create(indicacao=ind, dotacao=dot, valor_indicado=Decimal('1000.00'))
    EmpenhoOrcamentario.objects.create(
        indicacao_dotacao=linha, numero_doc='2026NE000001', data_emissao=date.today(), valor=Decimal('1000.00'))
    return dfd


@pytest.fixture
def contrato(org, fiscal, gestor, dfd_com_empenho):
    return Contrato.objects.create(
        org_id=org, exercicio=2026, orgao_executor=org, objeto='Contrato FZ', tipo_origem='licitacao',
        valor_contrato=Decimal('1000.00'), dfd=dfd_com_empenho, fiscal_contrato=fiscal,
        created_by=gestor, updated_by=gestor,
    )


def _medicao(contrato, **extra):
    return Medicao.objects.create(
        contrato=contrato, org_id=contrato.org_id, competencia_inicio=date.today(),
        competencia_fim=date.today(), data_medicao=date.today(), valor_medido=Decimal('1000.00'), **extra,
    )


@pytest.mark.django_db
class TestAteste:
    def test_so_o_fiscal_designado_atesta(self, contrato, gestor):
        med = _medicao(contrato)
        r = _cliente(gestor).patch(f'/api/contratos/contrato/{contrato.pk}/medicoes/{med.pk}/',
                                   {'status': 'aprovada', 'parecer_fiscal': 'ok'}, format='json')
        assert r.status_code == 403

    def test_criar_ja_aprovada_passa_pela_mesma_regra(self, contrato, gestor):
        r = _cliente(gestor).post(f'/api/contratos/contrato/{contrato.pk}/medicoes/', {
            'competencia_inicio': str(date.today()), 'competencia_fim': str(date.today()),
            'data_medicao': str(date.today()), 'valor_medido': '1000.00',
            'status': 'aprovada', 'parecer_fiscal': 'ok',
        }, format='json')
        assert r.status_code == 403

    def test_fiscal_sem_parecer_e_recusado(self, contrato, fiscal):
        med = _medicao(contrato)
        r = _cliente(fiscal).patch(f'/api/contratos/contrato/{contrato.pk}/medicoes/{med.pk}/',
                                   {'status': 'aprovada'}, format='json')
        assert r.status_code == 400 and 'parecer_fiscal' in r.data

    def test_ateste_do_fiscal_registra_responsavel_e_data(self, contrato, fiscal):
        med = _medicao(contrato)
        r = _cliente(fiscal).patch(f'/api/contratos/contrato/{contrato.pk}/medicoes/{med.pk}/',
                                   {'status': 'aprovada', 'parecer_fiscal': 'Conferido.'}, format='json')
        assert r.status_code == 200, r.data
        med.refresh_from_db()
        assert med.fiscal_responsavel_id == fiscal.pk and med.data_aprovacao == date.today()

    def test_medicoes_aprovadas_nao_superam_o_contrato(self, contrato, fiscal):
        _medicao(contrato, status='aprovada')
        med = _medicao(contrato)
        r = _cliente(fiscal).patch(f'/api/contratos/contrato/{contrato.pk}/medicoes/{med.pk}/',
                                   {'status': 'aprovada', 'parecer_fiscal': 'ok'}, format='json')
        assert r.status_code == 400 and 'valor_medido' in r.data


@pytest.mark.django_db
class TestPagamento:
    def _pagar(self, user, contrato, **dados):
        base = {'valor_pago': '1000.00', 'status': 'pago', 'numero_nota_fiscal': 'NF-1',
                'numero_empenho': '2026NE000001'}
        return _cliente(user).post(f'/api/contratos/contrato/{contrato.pk}/pagamentos/',
                                   {**base, **dados}, format='json')

    def test_sem_medicao_atestada_nao_paga(self, contrato, gestor):
        med = _medicao(contrato)  # pendente
        r = self._pagar(gestor, contrato, medicao=med.pk)
        assert r.status_code == 400 and 'medicao' in r.data

    def test_empenho_inexistente_na_dod_nao_paga(self, contrato, gestor):
        med = _medicao(contrato, status='aprovada')
        r = self._pagar(gestor, contrato, medicao=med.pk, numero_empenho='NE-QUALQUER')
        assert r.status_code == 400 and 'numero_empenho' in r.data

    def test_pagamento_acima_do_medido_e_recusado(self, contrato, gestor):
        med = _medicao(contrato, status='aprovada')
        r = self._pagar(gestor, contrato, medicao=med.pk, valor_pago='1000.01')
        assert r.status_code == 400 and 'valor_pago' in r.data

    def test_pagamento_regular(self, contrato, gestor):
        med = _medicao(contrato, status='aprovada')
        r = self._pagar(gestor, contrato, medicao=med.pk)
        assert r.status_code == 201, r.data
        pag = contrato.pagamentos.get()
        assert pag.status == 'pago' and pag.data_pagamento == date.today()
