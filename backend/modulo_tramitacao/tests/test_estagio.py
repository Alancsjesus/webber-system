from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from core.models import Orgao, UnidadeOrganizacional
from modulo_demanda.models import DFD
from modulo_tramitacao.estagio import resolver_item_painel


@pytest.fixture
def ssp(db):
    return Orgao.objects.create(nome='SSP Teste', sigla='SSPEST', ativa=True)


@pytest.fixture
def unidade_clic(ssp):
    return UnidadeOrganizacional.objects.create(orgao=ssp, nome='Coordenadoria de Licitações', sigla='CLIC', tipo='licitante')


@pytest.fixture
def unidade_cmp(ssp):
    return UnidadeOrganizacional.objects.create(orgao=ssp, nome='Comando de Policiamento', sigla='CMP', tipo='demandante')


def _autor_sem_perfil():
    return User.objects.create_user(username=f'autor_sem_perfil_{User.objects.count()}')


def _autor_com_unidade(unidade):
    user = User.objects.create_user(username=f'autor_com_unidade_{User.objects.count()}')
    user.profile.unidade = unidade
    user.profile.save()
    return user


def _criar_dfd(org, autor, numero_sei, unidade_demandante=None, unidade_licitante=None):
    return DFD.objects.create(
        org_id=org, numero_sei=numero_sei, descricao='Teste estagio',
        valor_estimado=Decimal('1000.00'), area_aplicacao=['TI'],
        prazo_necessidade=date.today() + timedelta(days=90), status='Rascunho',
        unidade_demandante=unidade_demandante, unidade_licitante=unidade_licitante,
        created_by=autor, updated_by=autor,
    )


@pytest.mark.django_db
class TestResolverItemPainelSetor:
    def test_usa_unidade_demandante_quando_preenchida(self, ssp, unidade_cmp):
        autor = _autor_sem_perfil()
        dfd = _criar_dfd(ssp, autor, '001.2026.0000101-11', unidade_demandante=unidade_cmp)
        item = resolver_item_painel(dfd, ssp)
        assert item['setor'] == str(unidade_cmp)
        assert item['etapa_atual'] == 'DFD'

    def test_usa_unidade_de_criacao_quando_fk_estrutural_vazia(self, ssp, unidade_clic):
        autor = _autor_com_unidade(unidade_clic)
        dfd = _criar_dfd(ssp, autor, '001.2026.0000102-22')
        item = resolver_item_painel(dfd, ssp)
        assert item['setor'] == str(unidade_clic)
        assert item['setor'] != 'DFD'

    def test_cai_para_etapa_apenas_sem_nenhuma_unidade_disponivel(self, ssp):
        autor = _autor_sem_perfil()
        dfd = _criar_dfd(ssp, autor, '001.2026.0000103-33')
        item = resolver_item_painel(dfd, ssp)
        assert item['setor'] == 'DFD'

    def test_unidade_demandante_tem_prioridade_sobre_unidade_de_criacao(self, ssp, unidade_cmp, unidade_clic):
        autor = _autor_com_unidade(unidade_clic)
        dfd = _criar_dfd(ssp, autor, '001.2026.0000104-44', unidade_demandante=unidade_cmp)
        item = resolver_item_painel(dfd, ssp)
        assert item['setor'] == str(unidade_cmp)
