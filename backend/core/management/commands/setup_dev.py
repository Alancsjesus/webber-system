"""
Cria dados iniciais para desenvolvimento:
  - Hierarquia de órgãos: SSP (pai) → CBMBA, PMBA (filhos)
  - Unidades organizacionais por tipo (demandante, licitante, contratante, planejamento)
  - Usuários de exemplo para cada perfil

Uso:
    python manage.py setup_dev
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Orgao, UnidadeOrganizacional, UserProfile


ORGAOS = [
    {'sigla': 'SSP',   'nome': 'Secretaria de Segurança Pública',        'parent': None},
    {'sigla': 'CBMBA', 'nome': 'Corpo de Bombeiros Militar da Bahia',    'parent': 'SSP'},
    {'sigla': 'PMBA',  'nome': 'Polícia Militar da Bahia',               'parent': 'SSP'},
]

UNIDADES = [
    # SSP — unidades demandantes
    {'orgao': 'SSP', 'sigla': 'CMP',    'nome': 'Coordenação de Material e Patrimônio',    'tipo': 'demandante'},
    {'orgao': 'SSP', 'sigla': 'CORSEG', 'nome': 'Coordenadoria de Segurança',              'tipo': 'demandante'},
    # SSP — unidade licitante
    {'orgao': 'SSP', 'sigla': 'CLIC',   'nome': 'Coordenadoria de Licitações e Contratos', 'tipo': 'licitante'},
    # SSP — unidade contratante
    {'orgao': 'SSP', 'sigla': 'CCC',    'nome': 'Coordenadoria de Controle de Contratos',  'tipo': 'contratante'},
    # SSP — unidades de planejamento
    {'orgao': 'SSP', 'sigla': 'DG',     'nome': 'Diretoria Geral',                          'tipo': 'planejamento'},
    {'orgao': 'SSP', 'sigla': 'CPLAM',  'nome': 'Coordenadoria de Planejamento',            'tipo': 'planejamento'},
    {'orgao': 'SSP', 'sigla': 'CFCR',   'nome': 'Coordenadoria de Finanças e Controle',     'tipo': 'planejamento'},
    # CBMBA
    {'orgao': 'CBMBA', 'sigla': 'DEM_CBM', 'nome': 'Unidade Demandante CBM',               'tipo': 'demandante'},
    {'orgao': 'CBMBA', 'sigla': 'DEPLAN',  'nome': 'Departamento de Planejamento CBM',     'tipo': 'planejamento'},
    # PMBA
    {'orgao': 'PMBA', 'sigla': 'DEM_PM',   'nome': 'Unidade Demandante PM',                'tipo': 'demandante'},
    {'orgao': 'PMBA', 'sigla': 'DEPLAN',   'nome': 'Departamento de Planejamento PM',      'tipo': 'planejamento'},
]

USUARIOS = [
    # (username, email, papel, orgao_sigla, unidade_sigla, unidade_tipo, superuser)
    ('admin',          'admin@dev.local',       'admin',               'SSP',   'CLIC',    'licitante',    True),
    ('analista_ssp',   'analista@dev.local',    'analista',            'SSP',   'CLIC',    'licitante',    False),
    ('plan_ssp',       'plan@dev.local',        'gestor_planejamento', 'SSP',   'CPLAM',   'planejamento', False),
    ('plan_cbm',       'plan.cbm@dev.local',    'gestor_planejamento', 'CBMBA', 'DEPLAN',  'planejamento', False),
    ('plan_pm',        'plan.pm@dev.local',     'gestor_planejamento', 'PMBA',  'DEPLAN',  'planejamento', False),
    ('solicitante',    'sol@dev.local',         'solicitante',         'CBMBA', 'DEM_CBM', 'demandante',   False),
    ('solicitante_pm', 'sol.pm@dev.local',      'solicitante',         'PMBA',  'DEM_PM',  'demandante',   False),
    ('gestor',         'gestor@dev.local',      'gestor_contrato',     'SSP',   'CCC',     'contratante',  False),
    ('dem_ssp',        'dem@dev.local',         'solicitante',         'SSP',   'CMP',     'demandante',   False),
]


class Command(BaseCommand):
    help = 'Cria dados iniciais para desenvolvimento (órgãos + unidades + usuários)'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='admin123', help='Senha padrão dos usuários')

    def handle(self, *args, **options):
        pw = options['password']

        # Cria órgãos
        orgaos = {}
        for cfg in ORGAOS:
            parent = orgaos.get(cfg['parent']) if cfg['parent'] else None
            orgao, created = Orgao.objects.get_or_create(
                sigla=cfg['sigla'],
                defaults={'nome': cfg['nome'], 'parent': parent, 'ativa': True},
            )
            if not created:
                orgao.parent = parent
                orgao.nome   = cfg['nome']
                orgao.save(update_fields=['nome', 'parent'])
            orgaos[cfg['sigla']] = orgao
            label = 'criado' if created else 'existente'
            self.stdout.write(f'Órgão {label}: {orgao}')

        # Cria unidades
        unidades = {}
        for cfg in UNIDADES:
            orgao = orgaos[cfg['orgao']]
            unidade, created = UnidadeOrganizacional.objects.get_or_create(
                orgao=orgao,
                sigla=cfg['sigla'],
                tipo=cfg['tipo'],
                defaults={'nome': cfg['nome'], 'ativa': True},
            )
            label = 'criada' if created else 'existente'
            self.stdout.write(f'Unidade {label}: {unidade} ({unidade.tipo})')
            key = (cfg['orgao'], cfg['sigla'], cfg['tipo'])
            unidades[key] = unidade

        # Cria usuários
        for username, email, papel, org_sigla, und_sigla, und_tipo, superuser in USUARIOS:
            orgao   = orgaos[org_sigla]
            unidade = unidades.get((org_sigla, und_sigla, und_tipo))

            if User.objects.filter(username=username).exists():
                self.stdout.write(f'Usuário existente: {username}')
                user = User.objects.get(username=username)
            else:
                if superuser:
                    user = User.objects.create_superuser(username=username, password=pw, email=email)
                else:
                    user = User.objects.create_user(username=username, password=pw, email=email)
                self.stdout.write(self.style.SUCCESS(f'Usuário criado: {username} ({papel})'))

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.org_id  = orgao
            profile.unidade = unidade
            profile.papel   = papel
            profile.save()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Setup concluído ==='))
        self.stdout.write(f'  Órgãos:   SSP (pai) → CBMBA, PMBA (filhos)')
        self.stdout.write(f'  Unidades: 11 unidades (demandante/licitante/contratante/planejamento)')
        self.stdout.write('')
        self.stdout.write(f'  admin          / {pw}  → SSP/CLIC   (licitante),    admin')
        self.stdout.write(f'  analista_ssp   / {pw}  → SSP/CLIC   (licitante),    analista')
        self.stdout.write(f'  plan_ssp       / {pw}  → SSP/CPLAM  (planejamento), gestor_planejamento')
        self.stdout.write(f'  plan_cbm       / {pw}  → CBM/DEPLAN (planejamento), gestor_planejamento')
        self.stdout.write(f'  plan_pm        / {pw}  → PM/DEPLAN  (planejamento), gestor_planejamento')
        self.stdout.write(f'  solicitante    / {pw}  → CBM/DEM_CBM(demandante),   solicitante')
        self.stdout.write(f'  solicitante_pm / {pw}  → PM/DEM_PM  (demandante),   solicitante')
        self.stdout.write(f'  gestor         / {pw}  → SSP/CCC    (contratante),  gestor_contrato')
        self.stdout.write(f'  dem_ssp        / {pw}  → SSP/CMP    (demandante),   solicitante')
