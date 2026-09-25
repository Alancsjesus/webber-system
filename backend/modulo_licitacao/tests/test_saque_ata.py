"""
Saque de Ata de Registro de Preços: procedimento sem TR/ETP/Mapa próprios,
com Ata vigente, DFD aprovado com DOD e saldo; contrato consome o saldo.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from core.models import ItemCatalogo, Orgao, UnidadeOrganizacional
from modulo_arp.models import Ata, ItemAta
from modulo_demanda.models import DFD, ItemDFD
from modulo_etp.models import ETP
from modulo_fornecedor.models import Fornecedor
from modulo_orcamento.models import IndicacaoOrcamentaria
from modulo_tr.models import TR

SENHA = 'Senha@1234'
URL = '/api/licitacao/procedimento/'


@pytest.fixture(autouse=True)
def limpar_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def c(db):
    org = Orgao.objects.create(nome='SSP Teste Saque', sigla='SSPSQ', ativa=True)
    unidade = UnidadeOrganizacional.objects.create(orgao=org, nome='Licitações SQ', sigla='CLICSQ', tipo='licitante')
    user = User.objects.create_user(username='analista_sq', password=SENHA)
    user.profile.papel, user.profile.org_id, user.profile.unidade = 'analista', org, unidade
    user.profile.save()
    cat = ItemCatalogo.objects.create(nome='Pneu Saque', unidade_medida='UN', codigo_simpas='31.10.00.00555-1')
    dfd = DFD.objects.create(
        org_id=org, numero_sei='SQ-DFD', descricao='DFD saque', valor_estimado=Decimal('800.00'),
        area_aplicacao=['Frota'], prazo_necessidade=date.today(), status='Aprovada', created_by=user, updated_by=user,
    )
    ItemDFD.objects.create(
        org_id=org, dfd=dfd, item_catalogo=cat, objeto='Pneu Saque', justificativa='x', unidade_medida='UN',
        quantidade=Decimal('8'), valor_unitario_estimado=Decimal('100.00'), valor_total_estimado=Decimal('800.00'),
        created_by=user, updated_by=user,
    )
    IndicacaoOrcamentaria.objects.create(org_id=org, numero='IND-SQ-001', exercicio_fiscal=2026, dfd=dfd,
                                         status='Aprovada', valor_total=Decimal('800.00'))
    fornecedor = Fornecedor.objects.create(tipo_pessoa='PJ', documento='77.666.555/0001-44', nome_razao_social='Pneus SQ')
    ata = Ata.objects.create(org_id=org, tipo_origem='gerenciador', numero_ata='ARP-SQ-1', objeto='Pneus',
                             status='vigente', data_vigencia_fim=date.today() + timedelta(days=90))
    item_ata = ItemAta.objects.create(ata=ata, item_catalogo=cat, objeto='Pneu', unidade_medida='UN',
                                      fornecedor=fornecedor, quantidade_registrada=Decimal('20'),
                                      valor_unitario_registrado=Decimal('90.00'))
    cli = APIClient()
    r = cli.post('/api/token/', {'username': user.username, 'password': SENHA, 'captcha_token': ''}, format='json')
    cli.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
    return {'cli': cli, 'org': org, 'dfd': dfd, 'ata': ata, 'item_ata': item_ata, 'user': user}


def _base(c, **extra):
    return {'exercicio': 2026, 'modalidade': 'saque_arp', 'dfd': c['dfd'].pk, **extra}


@pytest.mark.django_db
class TestSaqueAta:
    def test_sem_ata_e_recusado(self, c):
        r = c['cli'].post(URL, _base(c), format='json')
        assert r.status_code == 400 and 'ata' in r.data

    def test_com_tr_e_recusado(self, c):
        etp = ETP.objects.create(dfd=c['dfd'], numero_sei='SQ-ETP', necessidade_contratacao='x', status='Aprovado',
                                 org_id=c['org'], created_by=c['user'], updated_by=c['user'])
        tr = TR.objects.create(etp=etp, numero_sei='SQ-TR', objeto_contratacao='x', org_id=c['org'],
                               created_by=c['user'], updated_by=c['user'])
        r = c['cli'].post(URL, _base(c, ata=c['ata'].pk, tr=tr.pk), format='json')
        assert r.status_code == 400 and 'tr' in r.data

    def test_sem_saldo_na_ata_e_recusado(self, c):
        ItemAta.objects.filter(pk=c['item_ata'].pk).update(quantidade_consumida=Decimal('15'))
        r = c['cli'].post(URL, _base(c, ata=c['ata'].pk), format='json')
        assert r.status_code == 400 and 'saldo' in str(r.data['ata'])

    def test_saque_completo_sem_pecas_de_formacao(self, c):
        r = c['cli'].post(URL, _base(c, ata=c['ata'].pk), format='json')
        assert r.status_code == 201, r.data
        proc = r.data
        assert proc['numero'].startswith('SAQ-') and proc['tr'] is None
        assert proc['valor_estimado'] == '720.00' and 'ARP-SQ-1' in proc['objeto']
        tipos = [p['tipo'] for p in proc['pecas_instutorias']]
        assert 'Ata de Registro de Preços' in tipos and 'TR' not in tipos and 'ETP' not in tipos
        for acao in ('submeter', 'aprovar'):
            assert c['cli'].post(f'{URL}{proc["id"]}/{acao}/', {}, format='json').status_code == 200
        det = c['cli'].get(f'{URL}{proc["id"]}/').data
        assert 'Publicado' not in det['transicoes_disponiveis']
        r = c['cli'].post(f'{URL}{proc["id"]}/registrar-saque/', {}, format='json')
        assert r.status_code == 201, r.data
        res = r.data['resultados'][0]
        assert res['valor_final'] == '720.00' and res['fornecedor'] == c['item_ata'].fornecedor_id
        r = c['cli'].post(f'{URL}{proc["id"]}/resultados/{res["id"]}/gerar-contrato/', {}, format='json')
        assert r.status_code == 201, r.data
        assert r.data['status'] == 'Contratado'
        c['item_ata'].refresh_from_db()
        assert c['item_ata'].quantidade_consumida == Decimal('8')
        from modulo_contrato.models import Contrato
        contrato = Contrato.objects.get(pk=r.data['contrato_id'])
        assert contrato.tipo_origem == 'saque_arp' and contrato.dfd_id == c['dfd'].pk
