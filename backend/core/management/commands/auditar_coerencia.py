"""
Audita a coerência das cadeias de contratação já gravadas no banco — o que as
regras da API impedem hoje, mas que pode existir em dados antigos, importados
ou criados por seed direto no ORM.

Checa (Lei 14.133/2021):
  - Procedimento além de "Em Instrução" sem fase preparatória completa (art. 18 / art. 72, I)
  - Procedimento cujo DFD diverge do DFD do seu TR
  - Contrato de procedimento ainda não homologado/aprovado
  - Contrato assinado antes da abertura do procedimento
  - Contrato cujo DFD diverge do DFD do procedimento
  - Peças fora de ordem: ETP/TR aprovados com DFD/ETP não aprovados; datas regressivas

Uso:
    python manage.py auditar_coerencia          # lista; código de saída 1 se houver problema
"""
import sys

from django.core.management.base import BaseCommand

from modulo_contrato.models import Contrato
from modulo_etp.models import ETP
from modulo_licitacao.models import Procedimento
from modulo_tr.models import TR

STATUS_POS_INSTRUCAO = ('Aguardando Aprovação', 'Aprovado', 'Publicado', 'Em Sessão', 'Homologado', 'Contratado')
STATUS_COM_CONTRATO = ('Homologado', 'Contratado')


class Command(BaseCommand):
    help = 'Audita a coerência das cadeias DFD → ETP → TR → Procedimento → Contrato'

    def handle(self, *args, **options):
        problemas = []

        def p(tipo, ref, msg):
            problemas.append((tipo, ref, msg))

        for proc in Procedimento.objects.select_related('dfd', 'tr__etp__dfd', 'ata'):
            ref = proc.numero
            if proc.status in STATUS_POS_INSTRUCAO:
                for pend in proc.pendencias_instrucao():
                    p('instrução', ref, f'{proc.status}, mas: {pend}')
            if proc.tr_id and proc.tr.etp_id and proc.dfd_id and proc.tr.etp.dfd_id != proc.dfd_id:
                p('vínculo', ref, f'DFD do procedimento ({proc.dfd.numero_sei}) difere do DFD do TR ({proc.tr.etp.dfd.numero_sei}).')

        for c in Contrato.objects.select_related('dfd'):
            res = c.resultado_licitacao.select_related('procedimento').first()
            if res is None:
                # sem resultado de origem: se o DFD tem procedimento, algum precisa ter chegado ao fim
                procs = list(Procedimento.objects.filter(dfd_id=c.dfd_id)) if c.dfd_id else []
                if procs and not any(pr.status in STATUS_COM_CONTRATO for pr in procs):
                    p('contrato', c.numero, 'contrato do DFD ' + c.dfd.numero_sei + ' sem procedimento concluído ('
                      + ', '.join(f'{pr.numero}: {pr.status}' for pr in procs) + ').')
                continue
            proc = res.procedimento
            ok = STATUS_COM_CONTRATO + (('Aprovado',) if not proc.eh_licitacao else ())
            if proc.status not in ok:
                p('contrato', c.numero, f'gerado de {proc.numero}, que está "{proc.status}" (sem homologação).')
            if c.data_assinatura and c.data_assinatura < proc.created_at.date():
                p('cronologia', c.numero, f'assinado em {c.data_assinatura:%d/%m/%Y}, antes da abertura de '
                                          f'{proc.numero} ({proc.created_at:%d/%m/%Y}).')
            if c.dfd_id and proc.dfd_id and c.dfd_id != proc.dfd_id:
                p('vínculo', c.numero, f'DFD do contrato difere do DFD de {proc.numero}.')

        for etp in ETP.objects.select_related('dfd'):
            if etp.status == 'Aprovado' and etp.dfd_id and etp.dfd.status != 'Aprovada':
                p('ordem', etp.numero_sei, f'ETP aprovado com DFD "{etp.dfd.status}".')
            if etp.dfd_id and etp.created_at < etp.dfd.created_at:
                p('cronologia', etp.numero_sei, 'ETP criado antes do DFD.')
        for tr in TR.objects.select_related('etp'):
            if tr.status == 'Aprovado' and tr.etp_id and tr.etp.status not in ('Aprovado', 'Dispensado'):
                p('ordem', tr.numero_sei, f'TR aprovado com ETP "{tr.etp.status}".')
            if tr.etp_id and tr.created_at < tr.etp.created_at:
                p('cronologia', tr.numero_sei, 'TR criado antes do ETP.')

        for tipo, ref, msg in problemas:
            self.stdout.write(f'  [{tipo}] {ref}: {msg}')
        if problemas:
            self.stdout.write(self.style.ERROR(f'{len(problemas)} incoerência(s).'))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS('Nenhuma incoerência encontrada.'))
