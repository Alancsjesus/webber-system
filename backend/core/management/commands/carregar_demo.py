"""
Instala a carga de demonstração (core/fixtures/demo_webber.json.gz, gerada pelo
`exportar_demo`) — órgãos, usuários de teste, catálogo, orçamento, FESP/
Financiamento, DFD→ETP→Mapa→TR→Procedimento→Contrato→Medição→Pagamento, ARP
e tramitação — para ver e testar todas as funcionalidades.

APAGA todos os dados do banco antes (flush): a carga é um retrato completo e as
chaves de um registro apontam para as de outro.

Uso:
    python manage.py carregar_demo             # só se o banco estiver sem dados
    python manage.py carregar_demo --atualizar # recarrega se a carga mudou desde a última instalação
    python manage.py carregar_demo --forcar    # substitui tudo o que houver

No Render (sem Shell no plano free), pela variável RUN_CARGA_DEMO do serviço
(ver entrypoint.prod.sh): "True" = só com banco vazio; "Atualizar" = recarrega
quando uma carga nova é publicada. Após instalar, a versão (hash da carga) fica
gravada em ParametroSistema, então reinícios não apagam nada.
"""
import hashlib

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.management.commands.exportar_demo import ARQUIVO
from core.models import ParametroSistema
from modulo_demanda.models import DFD

CHAVE_VERSAO = 'carga_demo_versao'


def versao_carga():
    return hashlib.sha256(ARQUIVO.read_bytes()).hexdigest()[:16]


class Command(BaseCommand):
    help = 'Substitui o banco pela carga de demonstração (core/fixtures/demo_webber.json.gz)'

    def add_arguments(self, parser):
        parser.add_argument('--forcar', action='store_true', help='Apaga os dados existentes e carrega')
        parser.add_argument('--atualizar', action='store_true',
                            help='Recarrega se a carga publicada for diferente da instalada')

    def handle(self, *args, **options):
        if not ARQUIVO.exists():
            raise CommandError(f'Carga não encontrada: {ARQUIVO} (gere com: manage.py exportar_demo)')
        versao = versao_carga()
        instalada = ParametroSistema.objects.filter(chave=CHAVE_VERSAO).values_list('valor', flat=True).first()

        if options['forcar']:
            pass
        elif options['atualizar'] and instalada != versao:
            self.stdout.write(f'Carga nova ({versao}; instalada: {instalada or "nenhuma"}) — recarregando.')
        elif DFD.objects.exists():
            self.stdout.write(f'Banco já tem dados (carga instalada: {instalada or "desconhecida"}) — nada a fazer.')
            return

        with transaction.atomic():
            call_command('flush', '--noinput', verbosity=0)
            call_command('loaddata', str(ARQUIVO), verbosity=1, stdout=self.stdout)
            ParametroSistema.objects.update_or_create(chave=CHAVE_VERSAO, defaults={
                'valor': versao,
                'descricao': 'Versão da carga de demonstração instalada (gerida por manage.py carregar_demo).',
            })
        self.stdout.write(self.style.SUCCESS(f'Carga de demonstração {versao} instalada. Usuários de teste: senha admin123.'))
