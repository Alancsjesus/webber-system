"""
Popula o banco com dados de demonstração cobrindo todo o fluxo do WEBBER:
  Necessidades > DFDs > ETPs > TRs > Dotações > Indicações/DOD > Mapa de Preços

Uso:
    python manage.py populate_demo
    python manage.py populate_demo --limpar   # apaga tudo antes de popular
"""
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Orgao, UnidadeOrganizacional, AreaAtuacao
from modulo_planejamento.models import NecessidadePlanejamento
from modulo_demanda.models import DFD, ItemDFD
from modulo_orcamento.models import (
    AcaoOrcamentaria, ElementoDespesa, NaturezaDespesa,
    FonteRecurso, DotacaoOrcamentaria,
)


HOJE = date.today()
ANO  = HOJE.year


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração para todos os módulos'

    def add_arguments(self, parser):
        parser.add_argument('--limpar', action='store_true',
                            help='Remove dados de demo existentes antes de popular')

    def log(self, msg):
        self.stdout.write(msg)

    def ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f'  [OK] {msg}'))

    def handle(self, *args, **options):
        if options['limpar']:
            self._limpar()

        self.log('\n=== POPULATE DEMO ===\n')
        self._orcamento()
        self._necessidades()
        self._dfds()
        self.log('')
        self.stdout.write(self.style.SUCCESS('=== Dados de demo criados com sucesso! ==='))
        self._resumo()

    # ── Limpeza ───────────────────────────────────────────────────────────────

    def _limpar(self):
        self.log('Limpando dados de demo...')
        from modulo_etp.models import ETP
        from modulo_tr.models import TR
        ETP.objects.filter(numero_sei__startswith='DEMO-').delete()
        TR.objects.filter(numero_sei__startswith='DEMO-').delete()
        DFD.objects.filter(numero_sei__startswith='DEMO-').delete()
        NecessidadePlanejamento.objects.filter(titulo__startswith='[DEMO]').delete()
        DotacaoOrcamentaria.objects.filter(observacoes__contains='[demo]').delete()
        self.ok('Dados de demo removidos')

    # ── Orçamento ─────────────────────────────────────────────────────────────

    def _orcamento(self):
        self.log('Criando dados orçamentários...')
        ssp  = Orgao.objects.filter(sigla='SSP').first()
        admin = User.objects.filter(is_superuser=True).first()
        if not ssp or not admin:
            self.stdout.write(self.style.WARNING('  Execute setup_dev antes de populate_demo'))
            return

        # Elemento de despesa
        el30, _ = ElementoDespesa.objects.get_or_create(
            codigo=30, defaults={'descricao': 'Material de Consumo', 'ativo': True}
        )
        el39, _ = ElementoDespesa.objects.get_or_create(
            codigo=39, defaults={'descricao': 'Outros Serviços de Terceiros - PJ', 'ativo': True}
        )
        el52, _ = ElementoDespesa.objects.get_or_create(
            codigo=52, defaults={'descricao': 'Equipamentos e Material Permanente', 'ativo': True}
        )

        # Naturezas de despesa
        nat339030, _ = NaturezaDespesa.objects.get_or_create(
            codigo='339030',
            defaults={'descricao': 'Material de Consumo', 'elemento_despesa': el30, 'ativa': True}
        )
        nat339039, _ = NaturezaDespesa.objects.get_or_create(
            codigo='339039',
            defaults={'descricao': 'Outros Serviços de Terceiros - PJ', 'elemento_despesa': el39, 'ativa': True}
        )
        nat449052, _ = NaturezaDespesa.objects.get_or_create(
            codigo='449052',
            defaults={'descricao': 'Equipamentos e Material Permanente', 'elemento_despesa': el52, 'ativa': True}
        )

        # Ações orçamentárias
        acao1, _ = AcaoOrcamentaria.objects.get_or_create(
            org_id=ssp, codigo='2001',
            defaults={
                'nome': 'Manutenção das Atividades Operacionais de Segurança Pública',
                'tipo': 'Funcionamento / Operação', 'ativa': True,
                'created_by': admin, 'updated_by': admin,
            }
        )
        acao2, _ = AcaoOrcamentaria.objects.get_or_create(
            org_id=ssp, codigo='2002',
            defaults={
                'nome': 'Aquisição de Equipamentos e Materiais Operacionais',
                'tipo': 'Equipamento', 'ativa': True,
                'created_by': admin, 'updated_by': admin,
            }
        )

        # Fontes de recurso
        fonte1, _ = FonteRecurso.objects.get_or_create(
            org_id=ssp, codigo=100,
            defaults={
                'nome': 'Tesouro Estadual', 'tipo': 'Tesouro',
                'exercicio_anterior': False,
                'created_by': admin, 'updated_by': admin,
            }
        )
        fonte2, _ = FonteRecurso.objects.get_or_create(
            org_id=ssp, codigo=342,
            defaults={
                'nome': 'FESP - Fundo Estadual de Segurança Pública', 'tipo': 'FESP',
                'exercicio_anterior': False,
                'created_by': admin, 'updated_by': admin,
            }
        )

        # Dotações orçamentárias
        dot1, created = DotacaoOrcamentaria.objects.get_or_create(
            org_id=ssp, exercicio_fiscal=ANO, acao=acao1,
            elemento_despesa=el30, fonte_recurso=fonte1,
            defaults={
                'natureza_despesa': nat339030,
                'valor_dotado': Decimal('500000.00'),
                'status': 'Aprovada',
                'eixo': 'Segurança Pública',
                'observacoes': 'Dotação para material de consumo [demo]',
                'created_by': admin, 'updated_by': admin,
            }
        )
        if created: self.ok(f'Dotação criada: {dot1}')

        dot2, created = DotacaoOrcamentaria.objects.get_or_create(
            org_id=ssp, exercicio_fiscal=ANO, acao=acao2,
            elemento_despesa=el52, fonte_recurso=fonte2,
            defaults={
                'natureza_despesa': nat449052,
                'valor_dotado': Decimal('1200000.00'),
                'status': 'Aprovada',
                'eixo': 'Modernização Tecnológica',
                'observacoes': 'Dotação para equipamentos [demo]',
                'created_by': admin, 'updated_by': admin,
            }
        )
        if created: self.ok(f'Dotação criada: {dot2}')

        self._dot1 = dot1
        self._dot2 = dot2

    # ── Necessidades ──────────────────────────────────────────────────────────

    def _necessidades(self):
        self.log('Criando necessidades de planejamento...')
        ssp   = Orgao.objects.filter(sigla='SSP').first()
        cbmba = Orgao.objects.filter(sigla='CBMBA').first()
        pmba  = Orgao.objects.filter(sigla='PMBA').first()
        admin = User.objects.filter(is_superuser=True).first()
        und_dem_ssp = UnidadeOrganizacional.objects.filter(orgao=ssp, tipo='demandante').first()
        und_dem_cbm = UnidadeOrganizacional.objects.filter(orgao=cbmba, tipo='demandante').first()
        und_dem_pm  = UnidadeOrganizacional.objects.filter(orgao=pmba,  tipo='demandante').first()

        necessidades_demo = [
            {
                'titulo': '[DEMO] Aquisição de Kits de Primeiros Socorros Táticos (IFAK)',
                'descricao': (
                    'Aquisição de 6.400 kits individuais de primeiros socorros táticos para equipes '
                    'operacionais da SSP-BA, composto por torniquete tático, bandagem de combate, '
                    'gazes hemostáticas, tesoura ponta romba, cânula nasofaríngea, selo de tórax, '
                    'manta térmica e bolsa modular MOLLE.'
                ),
                'area_aplicacao': ['Ops', 'Formação'],
                'valor_estimado': Decimal('5400000.00'),
                'departamento_solicitante': 'CFCR - Coordenadoria de Finanças e Controle',
                'exercicio_fiscal': ANO,
                'prioridade': 'Alta',
                'status': 'Aprovada',
                'tipo_execucao': 'interna',
                'prazo_desejado': HOJE + timedelta(days=180),
                'org': ssp,
                'unidade': und_dem_ssp,
                'criador': admin,
            },
            {
                'titulo': '[DEMO] Contratação de Sistema de Videomonitoramento Urbano',
                'descricao': (
                    'Contratação de serviços de implantação, operação e manutenção de sistema '
                    'integrado de videomonitoramento urbano com 200 câmeras PTZ IP de alta resolução, '
                    'central de monitoramento e integração com sistemas de segurança pública.'
                ),
                'area_aplicacao': ['TI', 'Rede'],
                'valor_estimado': Decimal('3800000.00'),
                'departamento_solicitante': 'CPLAM - Coordenadoria de Planejamento',
                'exercicio_fiscal': ANO,
                'prioridade': 'Alta',
                'status': 'Aprovada',
                'tipo_execucao': 'interna',
                'prazo_desejado': HOJE + timedelta(days=270),
                'org': ssp,
                'unidade': und_dem_ssp,
                'criador': admin,
            },
            {
                'titulo': '[DEMO] Aquisição de Viaturas Operacionais',
                'descricao': (
                    'Aquisição de 45 viaturas do tipo caminhonete cabine dupla 4x4 para reposição '
                    'de frota operacional do CBMBA, com implementação de equipamentos de primeiros '
                    'socorros e resgate veicular.'
                ),
                'area_aplicacao': ['Frota', 'Ops'],
                'valor_estimado': Decimal('7200000.00'),
                'departamento_solicitante': 'DEPLAN - Departamento de Planejamento CBM',
                'exercicio_fiscal': ANO,
                'prioridade': 'Alta',
                'status': 'Aprovada',
                'tipo_execucao': 'externa',
                'prazo_desejado': HOJE + timedelta(days=210),
                'org': cbmba,
                'unidade': und_dem_cbm,
                'criador': admin,
            },
            {
                'titulo': '[DEMO] Aquisição de Combustível e Derivados de Petróleo',
                'descricao': (
                    'Registro de preços para aquisição de combustíveis (gasolina, diesel S-10 e GNV) '
                    'para abastecimento da frota operacional da PMBA, estimativa de 2.400.000 litros '
                    'durante o exercício.'
                ),
                'area_aplicacao': ['Derivados', 'Frota'],
                'valor_estimado': Decimal('9600000.00'),
                'departamento_solicitante': 'DEPLAN - Departamento de Planejamento PM',
                'exercicio_fiscal': ANO,
                'prioridade': 'Alta',
                'status': 'Em Análise',
                'tipo_execucao': 'externa',
                'prazo_desejado': HOJE + timedelta(days=90),
                'org': pmba,
                'unidade': und_dem_pm,
                'criador': admin,
            },
            {
                'titulo': '[DEMO] Capacitação em Gestão de Contratos (Lei 14.133/2021)',
                'descricao': (
                    'Contratação de empresa especializada para ministrar cursos de capacitação '
                    'em gestão e fiscalização de contratos conforme a Nova Lei de Licitações '
                    '(Lei 14.133/2021) para 120 servidores da SSP.'
                ),
                'area_aplicacao': ['Formação'],
                'valor_estimado': Decimal('240000.00'),
                'departamento_solicitante': 'DG - Diretoria Geral',
                'exercicio_fiscal': ANO,
                'prioridade': 'Média',
                'status': 'Identificada',
                'tipo_execucao': 'interna',
                'prazo_desejado': HOJE + timedelta(days=150),
                'org': ssp,
                'unidade': und_dem_ssp,
                'criador': admin,
            },
        ]

        self._necessidades_criadas = {}
        for cfg in necessidades_demo:
            nec, created = NecessidadePlanejamento.objects.get_or_create(
                titulo=cfg['titulo'],
                defaults={
                    'descricao':                cfg['descricao'],
                    'area_aplicacao':           cfg['area_aplicacao'],
                    'valor_estimado':           cfg['valor_estimado'],
                    'departamento_solicitante': cfg['departamento_solicitante'],
                    'exercicio_fiscal':         cfg['exercicio_fiscal'],
                    'prioridade':               cfg['prioridade'],
                    'status':                   cfg['status'],
                    'tipo_execucao':            cfg['tipo_execucao'],
                    'prazo_desejado':           cfg['prazo_desejado'],
                    'org_id':                   cfg['org'],
                    'unidade_demandante':       cfg['unidade'],
                    'created_by':               cfg['criador'],
                    'updated_by':               cfg['criador'],
                }
            )
            if created:
                # Vincula às dotações aprovadas
                if hasattr(self, '_dot1') and cfg['status'] == 'Aprovada':
                    self._dot1.necessidades.add(nec)
                self.ok(f'Necessidade criada: {nec.titulo[:60]}')
            self._necessidades_criadas[cfg['titulo']] = nec

    # ── DFDs ─────────────────────────────────────────────────────────────────

    def _dfds(self):
        self.log('Criando DFDs de demonstração...')
        ssp   = Orgao.objects.filter(sigla='SSP').first()
        admin = User.objects.filter(is_superuser=True).first()
        und_lic = UnidadeOrganizacional.objects.filter(orgao=ssp, tipo='licitante').first()
        und_con = UnidadeOrganizacional.objects.filter(orgao=ssp, tipo='contratante').first()
        und_dem = UnidadeOrganizacional.objects.filter(orgao=ssp, tipo='demandante').first()

        nec_ifak    = self._necessidades_criadas.get('[DEMO] Aquisição de Kits de Primeiros Socorros Táticos (IFAK)')
        nec_video   = self._necessidades_criadas.get('[DEMO] Contratação de Sistema de Videomonitoramento Urbano')

        dfds_demo = [
            {
                'numero_sei': f'DEMO-{ANO}-DFD-001',
                'descricao': 'Aquisição de 6.400 Kits Individuais de Primeiros Socorros Táticos (IFAK) para equipes operacionais',
                'area_aplicacao': ['Ops', 'Formação'],
                'modalidade_aquisicao': 'licitacao',
                'prazo_necessidade': HOJE + timedelta(days=180),
                'valor_estimado': Decimal('5382752.00'),
                'status': 'Aprovada',
                'observacoes': 'Pregão eletrônico com SRP. Pesquisa de preços realizada conforme Decreto 22.886/2024.',
                'necessidade': nec_ifak,
                'itens': [
                    ('Torniquete Tático de Combate Sistema Windlass', 'UND', 6400, Decimal('257.92')),
                    ('Porta-Torniquete MOLLE Cordura 500D', 'UND', 6400, Decimal('82.33')),
                    ('Bandagem de Combate Tipo Emergencial', 'UND', 6400, Decimal('60.00')),
                    ('Gaze Hidrófila com Agente Hemostático', 'UND', 6400, Decimal('100.74')),
                    ('Tesoura Ponta Romba para Trauma', 'UND', 6400, Decimal('27.96')),
                    ('Cânula de Combate Nasofaríngea com Lubrificante', 'UND', 6400, Decimal('60.32')),
                    ('Selo de Tórax Valvulado (par)', 'UND', 6400, Decimal('100.99')),
                    ('Manta Térmica de Emergência', 'UND', 6400, Decimal('6.26')),
                    ('Luva de Procedimento Nitrílica (caixa c/50 pares)', 'CX', 128, Decimal('20.25')),
                    ('Pincel Marcador Permanente', 'UND', 6400, Decimal('3.00')),
                    ('Bolso Modular IFAK MOLLE', 'UND', 6400, Decimal('141.13')),
                ],
            },
            {
                'numero_sei': f'DEMO-{ANO}-DFD-002',
                'descricao': 'Contratação de serviços de implantação de sistema integrado de videomonitoramento urbano — 200 câmeras PTZ IP',
                'area_aplicacao': ['TI', 'Rede'],
                'modalidade_aquisicao': 'licitacao',
                'prazo_necessidade': HOJE + timedelta(days=270),
                'valor_estimado': Decimal('3800000.00'),
                'status': 'Submetida',
                'observacoes': 'Serviço contínuo com dedicação exclusiva. Inclui fornecimento de equipamentos, instalação e manutenção.',
                'necessidade': nec_video,
                'itens': [
                    ('Câmera PTZ IP 4MP Full HD 36x Zoom Óptico', 'UND', 200, Decimal('8500.00')),
                    ('Servidor de Gravação e Gerenciamento 8TB', 'UND', 10, Decimal('35000.00')),
                    ('Switch PoE Gerenciável 24 portas Gigabit', 'UND', 20, Decimal('4200.00')),
                    ('Poste de Concreto Duplo T 9m', 'UND', 150, Decimal('1800.00')),
                    ('Serviço de Implantação e Configuração', 'SERV', 1, Decimal('450000.00')),
                    ('Manutenção Mensal Preventiva e Corretiva', 'MÊS', 24, Decimal('25000.00')),
                ],
            },
            {
                'numero_sei': f'DEMO-{ANO}-DFD-003',
                'descricao': 'Capacitação de servidores em gestão e fiscalização de contratos — Lei 14.133/2021',
                'area_aplicacao': ['Formação'],
                'modalidade_aquisicao': 'dispensa_valor',
                'prazo_necessidade': HOJE + timedelta(days=150),
                'valor_estimado': Decimal('58000.00'),
                'status': 'Rascunho',
                'justificativa_sem_planejamento': (
                    'Demanda urgente para qualificação dos servidores antes do início do exercício licitatório. '
                    'Valor abaixo do limite de R$ 62.000,00 para dispensa por valor (art. 75, I, Lei 14.133/2021).'
                ),
                'necessidade': None,
                'itens': [
                    ('Curso de Gestão de Contratos - 40h (turma de 30 alunos)', 'TURMA', 2, Decimal('18000.00')),
                    ('Apostilas e Material Didático por participante', 'UND', 120, Decimal('85.00')),
                    ('Certificação e Emissão de Diplomas', 'UND', 120, Decimal('45.00')),
                ],
            },
        ]

        for cfg in dfds_demo:
            dfd, created = DFD.objects.get_or_create(
                numero_sei=cfg['numero_sei'],
                defaults={
                    'descricao':              cfg['descricao'],
                    'area_aplicacao':         cfg['area_aplicacao'],
                    'modalidade_aquisicao':   cfg['modalidade_aquisicao'],
                    'prazo_necessidade':      cfg['prazo_necessidade'],
                    'valor_estimado':         cfg['valor_estimado'],
                    'status':                 cfg['status'],
                    'observacoes':            cfg.get('observacoes', ''),
                    'justificativa_sem_planejamento': cfg.get('justificativa_sem_planejamento', ''),
                    'org_id':                ssp,
                    'unidade_demandante':    und_dem,
                    'unidade_licitante':     und_lic,
                    'unidade_contratante':   und_con,
                    'created_by':            admin,
                    'updated_by':            admin,
                }
            )

            if created:
                # Vincula necessidade
                if cfg['necessidade']:
                    cfg['necessidade'].dfd = dfd
                    cfg['necessidade'].status = 'DFD Criado'
                    cfg['necessidade'].save(update_fields=['dfd', 'status'])

                # Cria itens
                for objeto, unidade, qtd, valor_unit in cfg['itens']:
                    ItemDFD.objects.get_or_create(
                        dfd=dfd, objeto=objeto,
                        defaults={
                            'unidade_medida':          unidade,
                            'quantidade':              Decimal(str(qtd)),
                            'valor_unitario_estimado': valor_unit,
                            'valor_total_estimado':    valor_unit * Decimal(str(qtd)),
                            'org_id':                  ssp,
                            'created_by':              admin,
                            'updated_by':              admin,
                        }
                    )
                self.ok(f'DFD criado: {dfd.numero_sei} ({dfd.status}) — {len(cfg["itens"])} item(s)')

    # ── Resumo ────────────────────────────────────────────────────────────────

    def _resumo(self):
        from modulo_demanda.models import DFD
        self.stdout.write('\nDados criados:')
        self.stdout.write(f'  Necessidades : {NecessidadePlanejamento.objects.filter(titulo__startswith="[DEMO]").count()}')
        self.stdout.write(f'  DFDs         : {DFD.objects.filter(numero_sei__startswith="DEMO-").count()}')
        self.stdout.write(f'  Dotacoes     : {DotacaoOrcamentaria.objects.filter(observacoes__contains="[demo]").count()}')
        self.stdout.write('')
        self.stdout.write('Para remover os dados de demo:')
        self.stdout.write('  python manage.py populate_demo --limpar')
