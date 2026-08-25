from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import Orgao, ItemCatalogo
from modulo_demanda.models import DFD, ItemDFD
from modulo_arp.models import Ata, ItemAta


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
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPARP', ativa=True)


def _make_user(orgao, papel, username):
    user = User.objects.create_user(username=username, password='Senha@1234')
    user.profile.papel = papel
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def analista_user(db, ssp):
    return _make_user(ssp, 'analista', 'analista_arp')


def _login(api_client, username):
    resp = api_client.post('/api/token/', {
        'username': username, 'password': 'Senha@1234', 'captcha_token': '',
    }, format='json')
    assert resp.status_code == 200, resp.data
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')


@pytest.fixture
def catalogo_item(db):
    return ItemCatalogo.objects.create(
        nome='Notebook Dell Latitude', unidade_medida='UN', codigo_simpas='65.10.19.00120553-6',
    )


def _criar_ata(api_client, org_id, tipo_origem='propria', numero='ATA-001', **extra):
    payload = {
        'tipo_origem': tipo_origem,
        'numero_ata': numero,
        'objeto': 'Aquisição de notebooks',
        **extra,
    }
    resp = api_client.post('/api/arp/', payload, format='json')
    assert resp.status_code == 201, resp.data
    return resp.data


@pytest.mark.django_db
def test_criar_ata_e_ativar(api_client, ssp, analista_user):
    _login(api_client, 'analista_arp')
    ata = _criar_ata(api_client, ssp.id)
    assert ata['status'] == 'rascunho'

    resp = api_client.post(f'/api/arp/{ata["id"]}/ativar/')
    assert resp.status_code == 200, resp.data
    assert resp.data['status'] == 'vigente'
    assert len(resp.data['historico']) == 1


@pytest.mark.django_db
def test_transicao_invalida_rejeitada(api_client, ssp, analista_user):
    _login(api_client, 'analista_arp')
    ata = _criar_ata(api_client, ssp.id)

    # rascunho -> encerrada não é permitido (precisa passar por vigente)
    resp = api_client.post(f'/api/arp/{ata["id"]}/encerrar/')
    assert resp.status_code == 400


@pytest.mark.django_db
def test_ata_carona_exige_numero_pncp_e_orgao(api_client, ssp, analista_user):
    _login(api_client, 'analista_arp')
    resp = api_client.post('/api/arp/', {
        'tipo_origem': 'carona', 'numero_ata': 'ATA-CARONA-001', 'objeto': 'Carona em ata de outro órgão',
    }, format='json')
    assert resp.status_code == 400
    assert 'numero_pncp' in resp.data
    assert 'orgao_gerenciador_nome' in resp.data


@pytest.mark.django_db
def test_confronto_sugere_ata_com_saldo(api_client, ssp, analista_user, catalogo_item):
    _login(api_client, 'analista_arp')
    ata = _criar_ata(api_client, ssp.id)
    api_client.post(f'/api/arp/{ata["id"]}/ativar/')

    item_ata_resp = api_client.post(f'/api/arp/{ata["id"]}/itens/', {
        'item_catalogo': catalogo_item.id, 'objeto': catalogo_item.nome, 'unidade_medida': 'UN',
        'quantidade_registrada': '100.0000', 'valor_unitario_registrado': '5200.00',
    }, format='json')
    assert item_ata_resp.status_code == 201, item_ata_resp.data

    dfd = DFD.objects.create(
        org_id=ssp, created_by=analista_user, updated_by=analista_user,
        numero_sei='020.0001.2026.0000001-01', descricao='Notebooks para SSP',
        valor_estimado=Decimal('260000.00'), prazo_necessidade=date(2026, 12, 31),
        area_aplicacao=['TI'],
    )
    ItemDFD.objects.create(
        org_id=ssp, created_by=analista_user, updated_by=analista_user,
        dfd=dfd, item_catalogo=catalogo_item, objeto=catalogo_item.nome,
        unidade_medida='UN', quantidade=Decimal('50.0000'), valor_unitario_estimado=Decimal('5200.00'),
    )

    resp = api_client.get('/api/arp/confronto/')
    assert resp.status_code == 200, resp.data
    assert len(resp.data) == 1
    assert resp.data[0]['item_dfd']['dfd_id'] == dfd.id
    assert len(resp.data[0]['sugestoes']) == 1
    assert resp.data[0]['sugestoes'][0]['ata_numero'] == 'ATA-001'
    assert Decimal(resp.data[0]['sugestoes'][0]['saldo_disponivel']) == Decimal('100.0000')


@pytest.mark.django_db
def test_confronto_ignora_item_sem_saldo(api_client, ssp, analista_user, catalogo_item):
    _login(api_client, 'analista_arp')
    ata = _criar_ata(api_client, ssp.id)
    api_client.post(f'/api/arp/{ata["id"]}/ativar/')
    item_ata = ItemAta.objects.create(
        ata=Ata.objects.get(pk=ata['id']), item_catalogo=catalogo_item, objeto=catalogo_item.nome,
        unidade_medida='UN', quantidade_registrada=Decimal('10.0000'),
        valor_unitario_registrado=Decimal('5200.00'), quantidade_consumida=Decimal('10.0000'),
    )

    dfd = DFD.objects.create(
        org_id=ssp, created_by=analista_user, updated_by=analista_user,
        numero_sei='020.0001.2026.0000002-01', descricao='Notebooks para SSP',
        valor_estimado=Decimal('52000.00'), prazo_necessidade=date(2026, 12, 31),
        area_aplicacao=['TI'],
    )
    ItemDFD.objects.create(
        org_id=ssp, created_by=analista_user, updated_by=analista_user,
        dfd=dfd, item_catalogo=catalogo_item, objeto=catalogo_item.nome,
        unidade_medida='UN', quantidade=Decimal('10.0000'), valor_unitario_estimado=Decimal('5200.00'),
    )

    resp = api_client.get('/api/arp/confronto/')
    assert resp.status_code == 200, resp.data
    assert resp.data == []


@pytest.mark.django_db
def test_confronto_ignora_dfd_ja_com_contrato(api_client, ssp, analista_user, catalogo_item):
    from modulo_contrato.models import Contrato

    _login(api_client, 'analista_arp')
    ata = _criar_ata(api_client, ssp.id)
    api_client.post(f'/api/arp/{ata["id"]}/ativar/')
    ItemAta.objects.create(
        ata=Ata.objects.get(pk=ata['id']), item_catalogo=catalogo_item, objeto=catalogo_item.nome,
        unidade_medida='UN', quantidade_registrada=Decimal('10.0000'),
        valor_unitario_registrado=Decimal('5200.00'),
    )

    dfd = DFD.objects.create(
        org_id=ssp, created_by=analista_user, updated_by=analista_user,
        numero_sei='020.0001.2026.0000003-01', descricao='Notebooks para SSP',
        valor_estimado=Decimal('52000.00'), prazo_necessidade=date(2026, 12, 31),
        area_aplicacao=['TI'],
    )
    ItemDFD.objects.create(
        org_id=ssp, created_by=analista_user, updated_by=analista_user,
        dfd=dfd, item_catalogo=catalogo_item, objeto=catalogo_item.nome,
        unidade_medida='UN', quantidade=Decimal('10.0000'), valor_unitario_estimado=Decimal('5200.00'),
    )
    Contrato.objects.create(
        org_id=ssp, created_by=analista_user, updated_by=analista_user,
        exercicio=2026, orgao_executor=ssp, objeto='Contrato existente',
        tipo_origem='licitacao', dfd=dfd, valor_contrato=Decimal('52000.00'),
    )

    resp = api_client.get('/api/arp/confronto/')
    assert resp.status_code == 200, resp.data
    assert resp.data == []
