"""
Encerramento sem prosseguimento (ETP/TR/Mapa) e tempos de instrução por ano.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Orgao, UnidadeOrganizacional
from modulo_demanda.models import DFD
from modulo_etp.models import ETP, HistoricoETP
from modulo_tr.models import TR

SENHA = 'Senha@1234'


@pytest.fixture(autouse=True)
def limpar_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def org(db):
    return Orgao.objects.create(nome='SSP Teste Encerramento', sigla='SSPEN', ativa=True)


@pytest.fixture
def analista(org):
    unidade = UnidadeOrganizacional.objects.create(orgao=org, nome='Licitações EN', sigla='CLICEN', tipo='licitante')
    user = User.objects.create_user(username='analista_en', password=SENHA)
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


def _etp(org, autor, status='Devolvido'):
    dfd = DFD.objects.create(org_id=org, numero_sei='EN-DFD', descricao='Aquisição de drones', valor_estimado=Decimal('1000'),
                             area_aplicacao=['Ops'], prazo_necessidade=date.today(), status='Aprovada',
                             created_by=autor, updated_by=autor)
    return ETP.objects.create(dfd=dfd, numero_sei='EN-ETP', necessidade_contratacao='x', status=status,
                              org_id=org, created_by=autor, updated_by=autor)


def test_encerra_etp_com_motivo_no_historico(cliente, org, analista):
    etp = _etp(org, analista)
    r = cliente.post(f'/api/etp/etp/{etp.pk}/encerrar/', {'categoria': 'enc_sem_orcamento', 'motivo': 'Dotação remanejada.'}, format='json')
    assert r.status_code == 200, r.data
    etp.refresh_from_db()
    assert etp.status == 'Encerrado'
    h = etp.historico.get(status_novo='Encerrado')
    assert h.categoria_motivo == 'enc_sem_orcamento' and 'Dotação remanejada' in h.motivo


def test_encerramento_exige_categoria_e_referencia(cliente, org, analista):
    etp = _etp(org, analista)
    r = cliente.post(f'/api/etp/etp/{etp.pk}/encerrar/', {'motivo': 'x'}, format='json')
    assert r.status_code == 400
    r = cliente.post(f'/api/etp/etp/{etp.pk}/encerrar/', {'categoria': 'enc_aproveitada', 'motivo': 'x'}, format='json')
    assert r.status_code == 400 and 'processo' in r.data['detail'].lower()


def test_nao_encerra_etp_com_tr_ativo(cliente, org, analista):
    etp = _etp(org, analista, status='Aprovado')
    TR.objects.create(etp=etp, numero_sei='EN-TR', objeto_contratacao='x', status='Rascunho',
                      org_id=org, created_by=analista, updated_by=analista)
    r = cliente.post(f'/api/etp/etp/{etp.pk}/encerrar/', {'categoria': 'enc_desistencia', 'motivo': 'x'}, format='json')
    assert r.status_code == 400 and 'TR' in r.data['detail']


def test_tempos_por_ano_separa_concluidas_e_encerradas(cliente, org, analista):
    agora = timezone.now()
    aprovado = _etp(org, analista, status='Aprovado')
    ETP.objects.filter(pk=aprovado.pk).update(created_at=agora - timedelta(days=30))
    h = HistoricoETP.objects.create(etp=aprovado, status_anterior='Em Análise', status_novo='Aprovado', usuario=analista)
    HistoricoETP.objects.filter(pk=h.pk).update(criado_em=agora - timedelta(days=10))

    dfd2 = DFD.objects.create(org_id=org, numero_sei='EN-DFD2', descricao='y', valor_estimado=Decimal('1'),
                              area_aplicacao=['Ops'], prazo_necessidade=date.today(), status='Aprovada',
                              created_by=analista, updated_by=analista)
    enc = ETP.objects.create(dfd=dfd2, numero_sei='EN-ETP2', necessidade_contratacao='y', status='Encerrado',
                             org_id=org, created_by=analista, updated_by=analista)
    HistoricoETP.objects.create(etp=enc, status_anterior='Devolvido', status_novo='Encerrado', usuario=analista)

    r = cliente.get('/api/tramitacao/tempos-por-ano/')
    assert r.status_code == 200, r.data
    etp_m = next(m for m in r.data['metricas'] if m['chave'] == 'ETP')
    ano = (agora - timedelta(days=10)).year
    assert etp_m['por_ano'][ano]['n'] == 1 and etp_m['por_ano'][ano]['mediana'] == 20
    assert sum(v['encerradas'] for v in etp_m['por_ano'].values()) == 1
