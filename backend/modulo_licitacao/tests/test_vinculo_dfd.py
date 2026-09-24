"""
C-Trace.3 (escopo revisado): Procedimento aberto só pelo TR herda o DFD
(TR → ETP → DFD), para que `dfd.procedimentos` o enxergue e a exigência de
DOD não seja pulada.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User

from core.models import Orgao
from modulo_demanda.models import DFD
from modulo_etp.models import ETP
from modulo_licitacao.models import Procedimento
from modulo_licitacao.serializers import ProcedimentoSerializer
from modulo_tr.models import TR


@pytest.fixture
def org(db):
    return Orgao.objects.create(nome='SSP Teste Vínculo DFD', sigla='SSPVD', ativa=True)


@pytest.fixture
def autor(db):
    return User.objects.create_user(username='autor_vinculo_dfd_teste')


def _dfd(org, autor, numero):
    return DFD.objects.create(
        org_id=org, numero_sei=f'{numero}-DFD', descricao='DFD teste vínculo',
        valor_estimado=Decimal('1000.00'), area_aplicacao=['TI'],
        prazo_necessidade=date.today(), status='Aprovada', created_by=autor, updated_by=autor,
    )


def _tr(org, autor, numero, dfd=None, srp=False):
    dfd = dfd or _dfd(org, autor, numero)
    etp = ETP.objects.create(
        dfd=dfd, numero_sei=f'{numero}-ETP', necessidade_contratacao='Teste', status='Aprovado',
        org_id=org, created_by=autor, updated_by=autor,
    )
    return TR.objects.create(
        etp=etp, numero_sei=f'{numero}-TR', objeto_contratacao='Teste', status='Aprovado',
        sistema_registro_precos=srp, org_id=org, created_by=autor, updated_by=autor,
    )


def _serializer(org, dados):
    request = SimpleNamespace(org_id=org, data=dados, user=None)
    return ProcedimentoSerializer(data=dados, context={'request': request})


def test_procedimento_so_com_tr_herda_dfd_do_etp(org, autor):
    tr = _tr(org, autor, 'VD-1')
    proc = Procedimento.objects.create(
        org_id=org, exercicio=2026, modalidade='pregao_eletronico', objeto='Teste', tr=tr,
    )
    assert proc.dfd_id == tr.etp.dfd_id
    assert list(tr.etp.dfd.procedimentos.all()) == [proc]


def test_dfd_informado_nao_e_sobrescrito(org, autor):
    tr = _tr(org, autor, 'VD-2')
    outro = _dfd(org, autor, 'VD-2-outro')
    proc = Procedimento.objects.create(
        org_id=org, exercicio=2026, modalidade='pregao_eletronico', objeto='Teste', tr=tr, dfd=outro,
    )
    assert proc.dfd_id == outro.pk


def test_procedimento_sem_tr_nem_dfd_continua_sem_dfd(org):
    proc = Procedimento.objects.create(
        org_id=org, exercicio=2026, modalidade='pregao_eletronico', objeto='Teste',
    )
    assert proc.dfd_id is None


def test_abrir_so_pelo_tr_exige_dod_do_dfd_herdado(org, autor):
    tr = _tr(org, autor, 'VD-3')
    s = _serializer(org, {
        'exercicio': 2026, 'modalidade': 'pregao_eletronico', 'objeto': 'Teste', 'tr': tr.pk,
    })
    assert not s.is_valid()
    assert 'dfd' in s.errors
    assert 'Indicação Orçamentária' in str(s.errors['dfd'])


def test_tr_de_registro_de_precos_continua_dispensado_de_dod(org, autor):
    tr = _tr(org, autor, 'VD-4', srp=True)
    s = _serializer(org, {
        'exercicio': 2026, 'modalidade': 'pregao_eletronico', 'objeto': 'Teste', 'tr': tr.pk,
    })
    assert s.is_valid(), s.errors
    assert s.validated_data['dfd'] == tr.etp.dfd
