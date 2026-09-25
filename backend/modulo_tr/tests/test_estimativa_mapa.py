"""
Estimativa do TR = consolidação dos lotes precificados pelo Mapa de Preços
aprovado do DFD (itens, códigos, quantidade, unidade, valor unitário e total).
"""
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from core.checklist_engine import ChecklistEngine
from core.models import ItemCatalogo, Orgao
from modulo_demanda.models import DFD, ItemDFD
from modulo_etp.models import ETP
from modulo_mapa_precos.models import ItemMapa, MapaComparativoPrecos
from modulo_tr.models import TR, ItemLoteTR, LoteTR
from modulo_tr.precos import atualizar_precos, consolidar


@pytest.fixture
def cenario(db):
    org = Orgao.objects.create(nome='SSP Teste Estimativa', sigla='SSPEST', ativa=True)
    autor = User.objects.create_user(username='autor_estimativa')
    cat = ItemCatalogo.objects.create(nome='Colete Estimativa', unidade_medida='UN', codigo_simpas='42.10.00.00777-1')
    dfd = DFD.objects.create(
        org_id=org, numero_sei='EST-DFD', descricao='DFD estimativa', valor_estimado=Decimal('1000.00'),
        area_aplicacao=['TI'], prazo_necessidade=date.today(), status='Aprovada', created_by=autor, updated_by=autor,
    )
    item = ItemDFD.objects.create(
        org_id=org, dfd=dfd, item_catalogo=cat, objeto='Colete Estimativa', justificativa='x',
        unidade_medida='UN', quantidade=Decimal('10'), valor_unitario_estimado=Decimal('100.00'),
        valor_total_estimado=Decimal('1000.00'), created_by=autor, updated_by=autor,
    )
    etp = ETP.objects.create(dfd=dfd, numero_sei='EST-ETP', necessidade_contratacao='x', status='Aprovado',
                             org_id=org, created_by=autor, updated_by=autor)
    tr = TR.objects.create(etp=etp, numero_sei='EST-TR', objeto_contratacao='x', org_id=org,
                           created_by=autor, updated_by=autor)
    lote = LoteTR.objects.create(tr=tr, org_id=org, descricao='Lote único')
    ItemLoteTR.objects.create(lote=lote, item_dfd=item, quantidade=Decimal('10'),
                              valor_unitario_ref=Decimal('100.00'), preco_origem='dfd')
    return {'org': org, 'dfd': dfd, 'tr': tr, 'lote': lote, 'cat': cat}


def _mapa_aprovado(c, valor):
    mapa = MapaComparativoPrecos.objects.create(
        org_id=c['org'], dfd=c['dfd'], exercicio_fiscal=2026, objeto='Pesquisa', status='Aprovado',
        metodo_calculo='mediana', data_aprovacao=date.today(),
    )
    ItemMapa.objects.create(mapa=mapa, ordem=1, descricao='Colete Estimativa', codigo_simpas=c['cat'].codigo_simpas,
                            unidade_medida='UN', quantidade=Decimal('10'), valor_unitario_calculado=Decimal(valor),
                            metodo_aplicado='mediana')
    return mapa


@pytest.mark.django_db
class TestEstimativaConsolidada:
    def test_sem_mapa_aprovado_fica_pendente_e_bloqueia_o_checklist(self, cenario):
        est = consolidar(cenario['tr'])
        assert est['mapa'] is None and est['itens_sem_mapa'] == 1
        assert est['lotes'][0]['itens'][0]['origem'] == 'dfd'
        bloqueios = [b.campo for b in ChecklistEngine.avaliar_tr(cenario['tr']).bloqueadores]
        assert 'estimativa_valor' in bloqueios

    def test_mapa_aprovado_reprecifica_e_consolida(self, cenario):
        mapa = _mapa_aprovado(cenario, '87.50')
        atualizar_precos(cenario['tr'])
        cenario['tr'].refresh_from_db()
        est = consolidar(cenario['tr'])
        linha = est['lotes'][0]['itens'][0]
        assert est['mapa']['id'] == mapa.id and est['itens_sem_mapa'] == 0
        assert linha['origem'] == 'mapa' and linha['valor_unitario'] == '87.50' and linha['valor_total'] == '875.00'
        assert linha['codigo_simpas'] == cenario['cat'].codigo_simpas and linha['codigo_interno']
        assert linha['quantidade'] == '10' and linha['unidade'] == 'UN'
        assert est['total'] == '875.00' and cenario['tr'].estimativa_valor == Decimal('875.00')
        assert cenario['lote'].valor_total == Decimal('875.00')  # antes somava a estimativa do DFD
        bloqueios = [b.campo for b in ChecklistEngine.avaliar_tr(cenario['tr']).bloqueadores]
        assert 'estimativa_valor' not in bloqueios

    def test_lote_de_cota_nao_soma_ao_total(self, cenario):
        _mapa_aprovado(cenario, '100.00')
        cota = LoteTR.objects.create(tr=cenario['tr'], org_id=cenario['org'], modalidade='cota_me_epp',
                                     lote_origem=cenario['lote'])
        ItemLoteTR.objects.create(lote=cota, item_dfd=cenario['lote'].itens.get().item_dfd,
                                  quantidade=Decimal('2.5'), valor_unitario_ref=Decimal('100.00'), preco_origem='mapa')
        atualizar_precos(cenario['tr'])
        est = consolidar(cenario['tr'])
        assert est['total'] == '1000.00' and est['lotes'][1]['cota'] and est['lotes'][1]['subtotal'] == '250.00'
