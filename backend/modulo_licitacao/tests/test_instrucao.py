"""
Fase preparatória (Lei 14.133/2021, art. 18 e art. 72, I): licitação só nasce
de TR/Projeto Básico, e o procedimento só sai de "Em Instrução" com DFD, ETP
(aprovado ou dispensado) e TR aprovados.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao, UnidadeOrganizacional
from modulo_demanda.models import DFD
from modulo_etp.models import ETP
from modulo_licitacao.models import Procedimento
from modulo_orcamento.models import IndicacaoOrcamentaria
from modulo_tr.models import TR

SENHA = 'Senha@1234'


@pytest.fixture(autouse=True)
def limpar_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def org(db):
    return Orgao.objects.create(nome='SSP Teste Instrução', sigla='SSPIN', ativa=True)


@pytest.fixture
def analista(org):
    unidade = UnidadeOrganizacional.objects.create(orgao=org, nome='Licitações IN', sigla='CLICIN', tipo='licitante')
    user = User.objects.create_user(username='analista_in', password=SENHA)
    user.profile.papel = 'analista'
    user.profile.org_id = org
    user.profile.unidade = unidade
    user.profile.save()
    return user


@pytest.fixture
def cliente(analista):
    c = APIClient()
    r = c.post('/api/token/', {'username': analista.username, 'password': SENHA, 'captcha_token': ''}, format='json')
    assert r.status_code == 200, r.data
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
    return c


def _cadeia(org, autor, etp_status='Aprovado', tr_status='Aprovado'):
    dfd = DFD.objects.create(
        org_id=org, numero_sei='IN-DFD', descricao='Manutenção da frota', valor_estimado=Decimal('1000.00'),
        area_aplicacao=['Frota'], prazo_necessidade=date.today(), status='Aprovada',
        created_by=autor, updated_by=autor,
    )
    IndicacaoOrcamentaria.objects.create(org_id=org, numero='IND-IN-001', exercicio_fiscal=2026, dfd=dfd,
                                         status='Aprovada', valor_total=Decimal('1000.00'))
    etp = ETP.objects.create(dfd=dfd, numero_sei='IN-ETP', necessidade_contratacao='x', status=etp_status,
                             org_id=org, created_by=autor, updated_by=autor)
    tr = TR.objects.create(etp=etp, numero_sei='IN-TR', objeto_contratacao='Manutenção da frota', status=tr_status,
                           org_id=org, created_by=autor, updated_by=autor)
    return dfd, etp, tr


def test_pregao_sem_tr_e_recusado(cliente, org, analista):
    dfd, _, _ = _cadeia(org, analista)
    r = cliente.post('/api/licitacao/procedimento/', {
        'exercicio': 2026, 'modalidade': 'pregao_eletronico', 'dfd': dfd.pk, 'objeto': 'Manutenção da frota',
    }, format='json')
    assert r.status_code == 400 and 'tr' in r.data, r.data


def test_nao_submete_com_etp_em_rascunho(cliente, org, analista):
    dfd, etp, tr = _cadeia(org, analista, etp_status='Rascunho', tr_status='Rascunho')
    proc = Procedimento.objects.create(org_id=org, exercicio=2026, modalidade='pregao_eletronico',
                                       objeto='Manutenção da frota', tr=tr, dfd=dfd)
    r = cliente.post(f'/api/licitacao/procedimento/{proc.pk}/submeter/', {}, format='json')
    assert r.status_code == 400, r.data
    assert any('ETP' in p for p in r.data['pendencias']) and any('TR' in p for p in r.data['pendencias'])
    proc.refresh_from_db()
    assert proc.status == 'Em Instrução'


def test_submete_com_instrucao_completa(cliente, org, analista):
    dfd, _, tr = _cadeia(org, analista)
    proc = Procedimento.objects.create(org_id=org, exercicio=2026, modalidade='pregao_eletronico',
                                       objeto='Manutenção da frota', tr=tr, dfd=dfd)
    assert proc.pendencias_instrucao() == []
    r = cliente.post(f'/api/licitacao/procedimento/{proc.pk}/submeter/', {}, format='json')
    assert r.status_code == 200, r.data


def test_dispensa_sem_tr_so_exige_dfd(org, analista):
    dfd, _, _ = _cadeia(org, analista)
    proc = Procedimento.objects.create(org_id=org, exercicio=2026, modalidade='dispensa_eletronica',
                                       objeto='Material de consumo', dfd=dfd)
    assert proc.pendencias_instrucao() == []
    proc_sem_dfd = Procedimento.objects.create(org_id=org, exercicio=2026, modalidade='dispensa_eletronica',
                                               objeto='Material de consumo')
    assert any('DFD' in p for p in proc_sem_dfd.pendencias_instrucao())
