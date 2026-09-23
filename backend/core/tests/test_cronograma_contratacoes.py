from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Orgao, ItemCatalogo
from core.cronograma_contratacoes import (
    duracao_media_modalidade, opcoes_modalidade, montar_cronograma, TETO_DISPENSA_COMPRAS,
    estatisticas_duracao_por_modalidade,
)
from modulo_licitacao.models import Procedimento, ResultadoLote
from modulo_contrato.models import Contrato
from modulo_arp.models import Ata, ItemAta
from modulo_mapa_precos.models import MapaComparativoPrecos, ItemMapa
from modulo_demanda.models import DFD, ItemDFD


@pytest.fixture
def ssp(db):
    return Orgao.objects.create(nome='SSP Teste Cronograma', sigla='SSPCR', ativa=True)


@pytest.fixture
def outro_org(db):
    return Orgao.objects.create(nome='Outro Órgão Cronograma', sigla='OUTROCR', ativa=True)


@pytest.fixture
def autor(db):
    return User.objects.create_user(username='autor_cronograma_teste')


@pytest.fixture
def item_catalogo(db):
    return ItemCatalogo.objects.create(
        nome='Colete Balístico Teste', unidade_medida='UN', codigo_simpas='42.99.00.00001-1',
    )


def _procedimento(org, modalidade, dias_atras, exercicio=2026):
    p = Procedimento.objects.create(
        org_id=org, exercicio=exercicio, modalidade=modalidade,
        objeto='Procedimento teste cronograma',
    )
    # created_at é auto_now_add — ajustar direto via update() para simular abertura no passado.
    Procedimento.objects.filter(pk=p.pk).update(created_at=timezone.now() - timedelta(days=dias_atras))
    return Procedimento.objects.get(pk=p.pk)


def _contrato_assinado(org, data_assinatura, valor='10000.00'):
    return Contrato.objects.create(
        org_id=org, exercicio=2026, orgao_executor=org, objeto='Contrato teste cronograma',
        tipo_origem='licitacao', valor_contrato=Decimal(valor), data_assinatura=data_assinatura,
    )


def _resultado_concluido(procedimento, contrato):
    return ResultadoLote.objects.create(
        procedimento=procedimento, resultado='homologado', contrato_gerado=contrato,
    )


def _dfd(org, autor, prazo, numero_sei):
    return DFD.objects.create(
        org_id=org, numero_sei=numero_sei, descricao='DFD teste cronograma',
        valor_estimado=Decimal('1000.00'), area_aplicacao=['TI'],
        prazo_necessidade=prazo, status='Aprovada', created_by=autor, updated_by=autor,
    )


def _item_dfd(dfd, item_catalogo, autor, valor_unitario='100.00', quantidade='10'):
    return ItemDFD.objects.create(
        org_id=dfd.org_id, dfd=dfd, item_catalogo=item_catalogo,
        objeto=item_catalogo.nome, justificativa='Teste', unidade_medida='UN',
        quantidade=Decimal(quantidade), valor_unitario_estimado=Decimal(valor_unitario),
        valor_total_estimado=Decimal(valor_unitario) * Decimal(quantidade),
        created_by=autor, updated_by=autor,
    )


def _ata_vigente(org, item_catalogo, valor_unitario_registrado, saldo=100):
    ata = Ata.objects.create(
        org_id=org, tipo_origem='gerenciador', numero_ata='ATA-TESTE-001',
        objeto='Ata teste cronograma', status='vigente',
    )
    ItemAta.objects.create(
        ata=ata, item_catalogo=item_catalogo, objeto=item_catalogo.nome, unidade_medida='UN',
        quantidade_registrada=Decimal(saldo), valor_unitario_registrado=Decimal(str(valor_unitario_registrado)),
    )
    return ata


def _referencia_mercado(org, item_catalogo, valor_unitario_calculado):
    mapa = MapaComparativoPrecos.objects.create(
        org_id=org, objeto='Mapa teste cronograma', exercicio_fiscal=2026,
    )
    return ItemMapa.objects.create(
        mapa=mapa, descricao=item_catalogo.nome, codigo_simpas=item_catalogo.codigo_simpas,
        unidade_medida='UN', quantidade=Decimal('1'),
        valor_unitario_calculado=Decimal(str(valor_unitario_calculado)),
    )


@pytest.mark.django_db
class TestDuracaoMediaModalidade:
    def test_sem_amostra_retorna_none(self, ssp):
        assert duracao_media_modalidade('pregao_eletronico', ssp.id) is None

    def test_amostra_abaixo_do_minimo_retorna_none(self, ssp):
        proc = _procedimento(ssp, 'pregao_eletronico', dias_atras=90)
        contrato = _contrato_assinado(ssp, date.today())
        _resultado_concluido(proc, contrato)
        # só 1 amostra, mínimo default é 3
        assert duracao_media_modalidade('pregao_eletronico', ssp.id) is None

    def test_calcula_media_com_amostra_suficiente(self, ssp):
        for dias in (60, 80, 100):
            proc = _procedimento(ssp, 'pregao_eletronico', dias_atras=dias)
            contrato = _contrato_assinado(ssp, date.today())
            _resultado_concluido(proc, contrato)
        media = duracao_media_modalidade('pregao_eletronico', ssp.id, minimo=3)
        assert media == 80  # (60+80+100)/3

    def test_ignora_duracao_negativa_dado_inconsistente(self, ssp):
        # contrato assinado ANTES da abertura do procedimento — dado ruim, deve ser ignorado
        proc = _procedimento(ssp, 'pregao_eletronico', dias_atras=10)
        contrato = _contrato_assinado(ssp, date.today() - timedelta(days=100))
        _resultado_concluido(proc, contrato)
        assert duracao_media_modalidade('pregao_eletronico', ssp.id, minimo=1) is None

    def test_isolamento_multi_tenant(self, ssp, outro_org):
        for dias in (60, 80, 100):
            proc = _procedimento(outro_org, 'pregao_eletronico', dias_atras=dias)
            contrato = _contrato_assinado(outro_org, date.today())
            _resultado_concluido(proc, contrato)
        assert duracao_media_modalidade('pregao_eletronico', ssp.id, minimo=3) is None


@pytest.mark.django_db
class TestEstatisticasDuracaoPorModalidade:
    def test_traz_todas_as_modalidades_mesmo_sem_amostra(self, ssp):
        stats = estatisticas_duracao_por_modalidade(ssp.id)
        modalidades = {s['modalidade'] for s in stats}
        assert modalidades == {
            'pregao_eletronico', 'concorrencia', 'dispensa_eletronica',
            'dispensa_tradicional', 'inexigibilidade',
        }
        pregao = next(s for s in stats if s['modalidade'] == 'pregao_eletronico')
        assert pregao['amostra_suficiente'] is False
        assert pregao['duracao_media'] is None
        assert pregao['quantidade_amostra'] == 0

    def test_estatisticas_com_amostra_suficiente(self, ssp):
        for dias in (60, 80, 100):
            proc = _procedimento(ssp, 'pregao_eletronico', dias_atras=dias)
            _resultado_concluido(proc, _contrato_assinado(ssp, date.today()))
        stats = estatisticas_duracao_por_modalidade(ssp.id)
        pregao = next(s for s in stats if s['modalidade'] == 'pregao_eletronico')
        assert pregao['amostra_suficiente'] is True
        assert pregao['quantidade_amostra'] == 3
        assert pregao['duracao_media'] == 80
        assert pregao['duracao_min'] == 60
        assert pregao['duracao_max'] == 100
        assert pregao['modalidade_label'] == 'Pregão Eletrônico'

    def test_min_max_aparecem_mesmo_abaixo_do_minimo(self, ssp):
        # amostra insuficiente pra média não deve esconder que já existe alguma
        # observação — min/máx ajudam o gestor a ver a variação existente.
        proc = _procedimento(ssp, 'dispensa_eletronica', dias_atras=40)
        _resultado_concluido(proc, _contrato_assinado(ssp, date.today()))
        stats = estatisticas_duracao_por_modalidade(ssp.id)
        dispensa = next(s for s in stats if s['modalidade'] == 'dispensa_eletronica')
        assert dispensa['amostra_suficiente'] is False
        assert dispensa['duracao_media'] is None
        assert dispensa['duracao_min'] == 40
        assert dispensa['duracao_max'] == 40


@pytest.mark.django_db
class TestOpcoesModalidade:
    def test_valor_alto_sem_ata_so_lista_pregao(self, ssp, item_catalogo):
        opcoes = opcoes_modalidade(item_catalogo, Decimal('500000.00'), ssp.id, {})
        modalidades = [o['modalidade'] for o in opcoes]
        assert modalidades == ['pregao_eletronico']

    def test_valor_dentro_do_teto_lista_dispensa_e_pregao(self, ssp, item_catalogo):
        valor = TETO_DISPENSA_COMPRAS - Decimal('1.00')
        opcoes = opcoes_modalidade(item_catalogo, valor, ssp.id, {})
        modalidades = {o['modalidade'] for o in opcoes}
        assert modalidades == {'dispensa_eletronica', 'pregao_eletronico'}

    def test_valor_unitario_baixo_mas_total_alto_nao_sugere_dispensa(self, ssp, item_catalogo):
        # Regressão de um erro real de conformidade: 80 unidades a R$ 1.850,00 somam
        # R$ 148.000,00 — muito acima do teto do Art. 75, II (R$ 57.277,08) — mesmo
        # com preço unitário baixo. O parâmetro já É o valor total (ver docstring
        # de opcoes_modalidade); este teste existe para nunca deixar alguém voltar
        # a passar o valor unitário aqui sem perceber a quebra de conformidade.
        valor_total = Decimal('80') * Decimal('1850.00')
        opcoes = opcoes_modalidade(item_catalogo, valor_total, ssp.id, {})
        modalidades = [o['modalidade'] for o in opcoes]
        assert 'dispensa_eletronica' not in modalidades
        assert modalidades == ['pregao_eletronico']

    def test_ata_vigente_com_saldo_adiciona_opcao_adesao(self, ssp, item_catalogo):
        ata = _ata_vigente(ssp, item_catalogo, valor_unitario_registrado='50.00')
        item_ata = ata.itens.first()
        opcoes = opcoes_modalidade(item_catalogo, Decimal('500000.00'), ssp.id, {item_catalogo.id: [item_ata]})
        adesao = next(o for o in opcoes if o['modalidade'] == 'adesao_arp')
        assert adesao['valor_unitario_ata'] == 50.0
        assert adesao['duracao_dias'] is None  # sem marco de início — nunca inventado

    def test_preco_da_ata_compativel_com_referencia_de_mercado(self, ssp, item_catalogo):
        ata = _ata_vigente(ssp, item_catalogo, valor_unitario_registrado='50.00')
        _referencia_mercado(ssp, item_catalogo, valor_unitario_calculado='60.00')
        item_ata = ata.itens.first()
        opcoes = opcoes_modalidade(item_catalogo, Decimal('500000.00'), ssp.id, {item_catalogo.id: [item_ata]})
        adesao = next(o for o in opcoes if o['modalidade'] == 'adesao_arp')
        assert adesao['preco_compativel'] is True

    def test_preco_da_ata_acima_da_referencia_de_mercado(self, ssp, item_catalogo):
        ata = _ata_vigente(ssp, item_catalogo, valor_unitario_registrado='90.00')
        _referencia_mercado(ssp, item_catalogo, valor_unitario_calculado='60.00')
        item_ata = ata.itens.first()
        opcoes = opcoes_modalidade(item_catalogo, Decimal('500000.00'), ssp.id, {item_catalogo.id: [item_ata]})
        adesao = next(o for o in opcoes if o['modalidade'] == 'adesao_arp')
        assert adesao['preco_compativel'] is False

    def test_sem_referencia_de_mercado_nao_afirma_compatibilidade(self, ssp, item_catalogo):
        ata = _ata_vigente(ssp, item_catalogo, valor_unitario_registrado='90.00')
        item_ata = ata.itens.first()
        opcoes = opcoes_modalidade(item_catalogo, Decimal('500000.00'), ssp.id, {item_catalogo.id: [item_ata]})
        adesao = next(o for o in opcoes if o['modalidade'] == 'adesao_arp')
        assert adesao['preco_compativel'] is None

    def test_sugere_a_opcao_medivel_mais_rapida(self, ssp, item_catalogo):
        valor = TETO_DISPENSA_COMPRAS - Decimal('1.00')
        for dias in (30, 40, 50):
            proc = _procedimento(ssp, 'dispensa_eletronica', dias_atras=dias)
            _resultado_concluido(proc, _contrato_assinado(ssp, date.today()))
        for dias in (90, 100, 110):
            proc = _procedimento(ssp, 'pregao_eletronico', dias_atras=dias)
            _resultado_concluido(proc, _contrato_assinado(ssp, date.today()))
        opcoes = opcoes_modalidade(item_catalogo, valor, ssp.id, {})
        sugerida = next(o for o in opcoes if o.get('sugerida'))
        assert sugerida['modalidade'] == 'dispensa_eletronica'

    def test_nao_sugere_adesao_com_preco_desfavoravel(self, ssp, item_catalogo):
        # adesão sem duração medível + preço acima do mercado não deve virar "sugerida"
        # mesmo sendo a única opção com sinal de vantajosidade ruim.
        ata = _ata_vigente(ssp, item_catalogo, valor_unitario_registrado='90.00')
        _referencia_mercado(ssp, item_catalogo, valor_unitario_calculado='60.00')
        item_ata = ata.itens.first()
        for dias in (30, 40, 50):
            proc = _procedimento(ssp, 'pregao_eletronico', dias_atras=dias)
            _resultado_concluido(proc, _contrato_assinado(ssp, date.today()))
        opcoes = opcoes_modalidade(item_catalogo, Decimal('500000.00'), ssp.id, {item_catalogo.id: [item_ata]})
        sugerida = next(o for o in opcoes if o.get('sugerida'))
        assert sugerida['modalidade'] == 'pregao_eletronico'


@pytest.mark.django_db
class TestMontarCronograma:
    def test_muitas_unidades_baratas_nao_sugere_dispensa_pelo_total(self, ssp, autor, item_catalogo):
        # Mesma regressão de TestOpcoesModalidade, agora na integração completa
        # (consolidação de ItemDFD → valor_total): 80 unidades a R$ 1.850,00.
        dfd = _dfd(ssp, autor, date.today() + timedelta(days=90), '001.2026.0000005-55')
        _item_dfd(dfd, item_catalogo, autor, valor_unitario='1850.00', quantidade='80')
        r = montar_cronograma(ssp.id)
        modalidades = [o['modalidade'] for o in r['itens'][0]['opcoes_modalidade']]
        assert 'dispensa_eletronica' not in modalidades

    def test_isolamento_multi_tenant(self, ssp, outro_org, autor, item_catalogo):
        dfd = _dfd(outro_org, autor, date.today() + timedelta(days=90), '001.2026.0000001-11')
        _item_dfd(dfd, item_catalogo, autor)
        r = montar_cronograma(ssp.id)
        assert r['itens'] == []

    def test_item_sem_duracao_medivel_cai_em_sem_prazo(self, ssp, autor, item_catalogo):
        dfd = _dfd(ssp, autor, date.today() + timedelta(days=90), '001.2026.0000002-22')
        _item_dfd(dfd, item_catalogo, autor)
        r = montar_cronograma(ssp.id)
        assert len(r['itens']) == 1
        assert r['itens'][0]['data_inicio_sugerida'] is None
        sem_prazo = next(p for p in r['periodos'] if p['periodo'] == 'sem_prazo')
        assert len(sem_prazo['itens']) == 1

    def test_item_com_duracao_medivel_calcula_data_e_periodo_com_ano(self, ssp, autor, item_catalogo):
        valor = TETO_DISPENSA_COMPRAS - Decimal('1.00')
        for dias in (20, 25, 30):
            proc = _procedimento(ssp, 'dispensa_eletronica', dias_atras=dias)
            _resultado_concluido(proc, _contrato_assinado(ssp, date.today()))
        prazo = date.today() + timedelta(days=120)
        dfd = _dfd(ssp, autor, prazo, '001.2026.0000003-33')
        # quantidade=1: o valor TOTAL do item consolidado (não o unitário) é o que
        # decide o teto de dispensa — ver TestOpcoesModalidade.test_valor_total_alto_...
        _item_dfd(dfd, item_catalogo, autor, valor_unitario=str(valor), quantidade='1')
        r = montar_cronograma(ssp.id)
        item = r['itens'][0]
        assert item['data_inicio_sugerida'] is not None
        inicio = date.fromisoformat(item['data_inicio_sugerida'])
        assert item['periodo'] == f'{inicio.year}-Q{(inicio.month - 1) // 3 + 1}'
        assert str(inicio.year) in item['periodo_label']

    def test_periodo_carrega_o_ano_real_do_inicio_nao_o_exercicio_filtrado(self, ssp, autor, item_catalogo):
        # Regressão: um prazo em janeiro/2027 com duração medida de ~90 dias
        # empurra o início pra outubro/2026 — rotular isso de "4º Trimestre"
        # sem ano dava a entender que é o mesmo período de um item que de fato
        # começa no 4º trimestre de 2027.
        for dias in (80, 90, 100):
            proc = _procedimento(ssp, 'pregao_eletronico', dias_atras=dias)
            _resultado_concluido(proc, _contrato_assinado(ssp, date.today()))
        prazo = date(date.today().year + 1, 1, 15)
        dfd = _dfd(ssp, autor, prazo, '001.2027.0000009-99')
        _item_dfd(dfd, item_catalogo, autor, valor_unitario='500000.00', quantidade='1')
        r = montar_cronograma(ssp.id, exercicio=prazo.year)
        item = r['itens'][0]
        inicio = date.fromisoformat(item['data_inicio_sugerida'])
        assert inicio.year == prazo.year - 1  # início cai no ano anterior ao exercício filtrado
        assert item['periodo'] == f'{inicio.year}-Q4'
        assert item['periodo_label'] == f'4º Trimestre de {inicio.year}'

    def test_item_atrasado_quando_data_sugerida_ja_passou(self, ssp, autor, item_catalogo):
        valor = TETO_DISPENSA_COMPRAS - Decimal('1.00')
        for dias in (20, 25, 30):
            proc = _procedimento(ssp, 'dispensa_eletronica', dias_atras=dias)
            _resultado_concluido(proc, _contrato_assinado(ssp, date.today()))
        # prazo já muito próximo — início sugerido cai no passado
        prazo = date.today() + timedelta(days=5)
        dfd = _dfd(ssp, autor, prazo, '001.2026.0000004-44')
        _item_dfd(dfd, item_catalogo, autor, valor_unitario=str(valor), quantidade='1')
        r = montar_cronograma(ssp.id)
        assert r['itens'][0]['atrasado'] is True
        assert r['itens'][0]['periodo'] is None
        atrasado = next(p for p in r['periodos'] if p['periodo'] == 'atrasado')
        assert len(atrasado['itens']) == 1

    def test_resposta_traz_aviso_de_direcionamento(self, ssp):
        r = montar_cronograma(ssp.id)
        assert 'direcionamento' in r['aviso'].lower()
