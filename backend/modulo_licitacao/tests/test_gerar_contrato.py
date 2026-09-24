"""
Contrato gerado a partir do resultado homologado segue a minuta (TR):
instrumento (art. 95) e garantia (art. 96); exige cobertura orçamentária
das DODs do DFD (art. 150); e procedimento de SRP gera Ata, não contrato.
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
from modulo_fornecedor.models import Fornecedor
from modulo_licitacao.models import Procedimento, ResultadoLote
from modulo_orcamento.models import IndicacaoOrcamentaria
from modulo_tr.models import TR, LoteTR

SENHA = 'Senha@1234'


@pytest.fixture(autouse=True)
def limpar_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def org(db):
    return Orgao.objects.create(nome='SSP Teste Gerar Contrato', sigla='SSPGC', ativa=True)


@pytest.fixture
def analista(org):
    unidade = UnidadeOrganizacional.objects.create(orgao=org, nome='Licitações GC', sigla='CLICGC', tipo='licitante')
    user = User.objects.create_user(username='analista_gc', password=SENHA)
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


def _cenario(org, autor, valor_dod='1000.00', valor_final='900.00', **tr_extra):
    dfd = DFD.objects.create(
        org_id=org, numero_sei='GC-DFD', descricao='DFD GC', valor_estimado=Decimal('1000.00'),
        area_aplicacao=['TI'], prazo_necessidade=date.today(), status='Aprovada',
        created_by=autor, updated_by=autor,
    )
    if valor_dod:
        IndicacaoOrcamentaria.objects.create(
            org_id=org, numero='IND-GC-001', exercicio_fiscal=2026, dfd=dfd, status='Aprovada',
            valor_total=Decimal(valor_dod),
        )
    etp = ETP.objects.create(dfd=dfd, numero_sei='GC-ETP', necessidade_contratacao='x', status='Aprovado',
                             org_id=org, created_by=autor, updated_by=autor)
    tr = TR.objects.create(etp=etp, numero_sei='GC-TR', objeto_contratacao='Objeto GC', status='Aprovado',
                           org_id=org, created_by=autor, updated_by=autor, **tr_extra)
    lote = LoteTR.objects.create(tr=tr, org_id=org, numero=1, descricao='Lote GC')
    proc = Procedimento.objects.create(org_id=org, exercicio=2026, modalidade='pregao_eletronico',
                                       objeto='Objeto GC', tr=tr, status='Homologado')
    fornecedor = Fornecedor.objects.create(tipo_pessoa='PJ', documento='99.888.777/0001-66', nome_razao_social='Fornecedor GC')
    res = ResultadoLote.objects.create(procedimento=proc, lote=lote, resultado='homologado', fornecedor=fornecedor,
                                       valor_estimado=Decimal('1000.00'), valor_final=Decimal(valor_final))
    return proc, res


def _gerar(cliente, proc, res):
    return cliente.post(f'/api/licitacao/procedimento/{proc.pk}/resultados/{res.pk}/gerar-contrato/', {}, format='json')


@pytest.mark.django_db
class TestGerarContrato:
    def test_segue_instrumento_e_garantia_da_minuta(self, org, analista, cliente):
        proc, res = _cenario(org, analista, instrumento_inicio='afm', req_garantia_contratacao=True,
                             req_garantia_percentual=Decimal('5.00'), req_garantia_modalidade='titulos')
        r = _gerar(cliente, proc, res)
        assert r.status_code == 201, r.data
        c = res.__class__.objects.get(pk=res.pk).contrato_gerado
        assert c.tipo_instrumento == 'afm'
        assert c.garantia_exigida and c.garantia_percentual == Decimal('5.00') and c.garantia_tipo == 'caucao_titulos'
        assert c.fornecedor_id == res.fornecedor_id and c.dfd_id == proc.dfd_id

    def test_sem_cobertura_da_dod_nao_contrata(self, org, analista, cliente):
        proc, res = _cenario(org, analista, valor_dod='500.00', valor_final='900.00')
        r = _gerar(cliente, proc, res)
        assert r.status_code == 400 and 'cobertura' in r.data['detail']

    def test_registro_de_precos_gera_ata_nao_contrato(self, org, analista, cliente):
        proc, res = _cenario(org, analista, sistema_registro_precos=True)
        r = _gerar(cliente, proc, res)
        assert r.status_code == 400 and 'Ata' in r.data['detail']

    def test_resultado_com_sobrepreco_exige_justificativa(self, org, analista, cliente):
        proc, res = _cenario(org, analista)
        dados = {'lote': res.lote_id, 'resultado': 'homologado', 'valor_estimado': '1000.00', 'valor_final': '1200.00'}
        url = f'/api/licitacao/procedimento/{proc.pk}/resultados/'
        r = cliente.post(url, dados, format='json')
        assert r.status_code == 400 and 'valor_final' in r.data
        r = cliente.post(url, {**dados, 'observacoes': 'Preço de mercado reajustado — nova pesquisa anexa.'}, format='json')
        assert r.status_code == 201, r.data
