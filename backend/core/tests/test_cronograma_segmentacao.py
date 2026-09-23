"""
Testes da segmentação de duração por natureza do objeto (TR.tipo_objeto) e
por impacto de tramitação externa — pedido explícito do usuário depois de ver
que uma média só por modalidade escondia a diferença real entre um pregão de
bens comuns e um pregão de viaturas que passa pela Casa Civil.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Orgao
from core.cronograma_contratacoes import (
    estatisticas_duracao_por_tipo_objeto, estatisticas_impacto_tramitacao_externa,
)
from modulo_demanda.models import DFD
from modulo_etp.models import ETP
from modulo_tr.models import TR
from modulo_licitacao.models import Procedimento, ResultadoLote, TramitacaoExterna
from modulo_contrato.models import Contrato


@pytest.fixture
def ssp(db):
    return Orgao.objects.create(nome='SSP Teste Segmentação', sigla='SSPSG', ativa=True)


@pytest.fixture
def autor(db):
    return User.objects.create_user(username='autor_segmentacao_teste')


def _tr(org, autor, tipo_objeto, numero):
    dfd = DFD.objects.create(
        org_id=org, numero_sei=f'{numero}-DFD', descricao='DFD teste segmentação',
        valor_estimado=Decimal('1000.00'), area_aplicacao=['TI'],
        prazo_necessidade=date.today(), status='Aprovada', created_by=autor, updated_by=autor,
    )
    etp = ETP.objects.create(
        dfd=dfd, numero_sei=f'{numero}-ETP', necessidade_contratacao='Teste', status='Aprovado',
        org_id=org, created_by=autor, updated_by=autor,
    )
    return TR.objects.create(
        etp=etp, numero_sei=f'{numero}-TR', objeto_contratacao='Teste',
        tipo_objeto=tipo_objeto, status='Aprovado', org_id=org, created_by=autor, updated_by=autor,
    )


def _procedimento_concluido(org, dias_atras, autor, tr=None, externas=None):
    proc = Procedimento.objects.create(
        org_id=org, exercicio=2026, modalidade='pregao_eletronico',
        objeto='Procedimento teste segmentação', tr=tr, created_by=autor, updated_by=autor,
    )
    abertura = timezone.now() - timedelta(days=dias_atras)
    Procedimento.objects.filter(pk=proc.pk).update(created_at=abertura)
    for orgao_externo, dias_tramite in (externas or []):
        data_envio = abertura.date() + timedelta(days=5)
        TramitacaoExterna.objects.create(
            procedimento=proc, orgao_externo=orgao_externo, tipo='anuencia',
            data_envio=data_envio, data_retorno=data_envio + timedelta(days=dias_tramite),
        )
    contrato = Contrato.objects.create(
        org_id=org, exercicio=2026, orgao_executor=org, objeto='Contrato teste segmentação',
        tipo_origem='licitacao', valor_contrato=Decimal('10000.00'), data_assinatura=date.today(),
        created_by=autor, updated_by=autor,
    )
    ResultadoLote.objects.create(procedimento=proc, resultado='homologado', contrato_gerado=contrato)
    return proc, contrato


@pytest.mark.django_db
class TestEstatisticasDuracaoPorTipoObjeto:
    def test_ignora_procedimento_sem_tr(self, ssp, autor):
        _procedimento_concluido(ssp, 90, autor, tr=None)
        stats = estatisticas_duracao_por_tipo_objeto(ssp.id)
        assert stats == []

    def test_agrupa_por_tipo_objeto(self, ssp, autor):
        for i, dias in enumerate((80, 90, 100)):
            tr = _tr(ssp, autor, 'bens', f'020.{i}')
            _procedimento_concluido(ssp, dias, autor, tr=tr)
        for i, dias in enumerate((150, 160, 170)):
            tr = _tr(ssp, autor, 'obras', f'030.{i}')
            _procedimento_concluido(ssp, dias, autor, tr=tr)
        stats = estatisticas_duracao_por_tipo_objeto(ssp.id)
        bens = next(s for s in stats if s['tipo_objeto'] == 'bens')
        obras = next(s for s in stats if s['tipo_objeto'] == 'obras')
        assert bens['duracao_media'] == 90
        assert obras['duracao_media'] == 160
        # ordenado do mais lento pro mais rápido
        assert stats[0]['tipo_objeto'] == 'obras'


@pytest.mark.django_db
class TestEstatisticasImpactoTramitacaoExterna:
    def test_sem_amostra_retorna_lista_vazia(self, ssp):
        assert estatisticas_impacto_tramitacao_externa(ssp.id) == []

    def test_mede_dias_a_mais_com_tramitacao_externa(self, ssp, autor):
        for dias in (80, 90, 100):
            _procedimento_concluido(ssp, dias, autor)  # sem trâmite externo
        for dias in (150, 160, 170):
            _procedimento_concluido(ssp, dias, autor, externas=[('CasaCivil', 30)])
        r = estatisticas_impacto_tramitacao_externa(ssp.id)
        pregao = next(g for g in r if g['modalidade'] == 'pregao_eletronico')
        assert pregao['sem_tramitacao_externa']['duracao_media'] == 90
        assert pregao['com_tramitacao_externa']['duracao_media'] == 160
        assert pregao['impacto_dias'] == 70

    def test_nunca_mistura_modalidades_diferentes(self, ssp, autor):
        # 3 dispensas rápidas sem trâmite externo + 3 pregões lentos com trâmite —
        # a comparação tem que ficar DENTRO de cada modalidade, nunca a dispensa
        # rápida "sem" contra o pregão lento "com" (isso inflaria o impacto medido
        # por uma diferença que é de modalidade, não de trâmite externo).
        for dias in (20, 25, 30):
            proc = Procedimento.objects.create(
                org_id=ssp, exercicio=2026, modalidade='dispensa_eletronica',
                objeto='Dispensa teste', created_by=autor, updated_by=autor,
            )
            Procedimento.objects.filter(pk=proc.pk).update(created_at=timezone.now() - timedelta(days=dias))
            contrato = Contrato.objects.create(
                org_id=ssp, exercicio=2026, orgao_executor=ssp, objeto='Contrato dispensa teste',
                tipo_origem='dispensa', valor_contrato=Decimal('5000.00'), data_assinatura=date.today(),
                created_by=autor, updated_by=autor,
            )
            ResultadoLote.objects.create(procedimento=proc, resultado='homologado', contrato_gerado=contrato)
        for dias in (150, 160, 170):
            _procedimento_concluido(ssp, dias, autor, externas=[('CasaCivil', 30)])

        r = estatisticas_impacto_tramitacao_externa(ssp.id)
        dispensa = next(g for g in r if g['modalidade'] == 'dispensa_eletronica')
        pregao = next(g for g in r if g['modalidade'] == 'pregao_eletronico')
        # dispensa só tem amostra "sem"; pregão só tem amostra "com" — cada uma
        # isolada na sua modalidade, nenhuma pisando na média da outra.
        assert dispensa['sem_tramitacao_externa']['duracao_media'] == 25
        assert dispensa['com_tramitacao_externa']['quantidade_amostra'] == 0
        assert pregao['com_tramitacao_externa']['duracao_media'] == 160
        assert pregao['sem_tramitacao_externa']['quantidade_amostra'] == 0
