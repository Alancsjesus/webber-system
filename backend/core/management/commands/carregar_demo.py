"""
Instala a carga de demonstração (core/fixtures/demo_webber.json.gz, gerada pelo
`exportar_demo`) — órgãos, usuários de teste, catálogo, orçamento, FESP/
Financiamento, DFD→ETP→Mapa→TR→Procedimento→Contrato→Medição→Pagamento, ARP,
PNCP e tramitação — para ver e testar todas as funcionalidades.

APAGA todos os dados do banco antes (flush): a carga é um retrato completo e as
chaves de um registro apontam para as de outro. Por isso só roda com banco sem
DFD, ou com --forcar.

Uso:
    python manage.py carregar_demo            # só se o banco estiver sem dados
    python manage.py carregar_demo --forcar   # substitui tudo o que houver

No Render (sem Shell no plano free): RUN_CARGA_DEMO=True no serviço (ver
entrypoint.prod.sh). Seguro de deixar ligado — com dados, não faz nada.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.management.commands.exportar_demo import ARQUIVO
from modulo_demanda.models import DFD


class Command(BaseCommand):
    help = 'Substitui o banco pela carga de demonstração (core/fixtures/demo_webber.json.gz)'

    def add_arguments(self, parser):
        parser.add_argument('--forcar', action='store_true', help='Apaga os dados existentes e carrega')

    def handle(self, *args, **options):
        if not ARQUIVO.exists():
            raise CommandError(f'Carga não encontrada: {ARQUIVO} (gere com: manage.py exportar_demo)')
        if DFD.objects.exists() and not options['forcar']:
            self.stdout.write('Banco já tem dados — carga de demonstração ignorada (use --forcar para substituir).')
            return

        with transaction.atomic():
            call_command('flush', '--noinput', verbosity=0)
            call_command('loaddata', str(ARQUIVO), verbosity=1, stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS('Carga de demonstração instalada. Usuários de teste: senha admin123.'))
