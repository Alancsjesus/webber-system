"""
Popula dados de orçamento e inicia demandas de teste para verificar o fluxo completo:
  Necessidade → DFD → ETP

Uso:
    python manage.py populate_orcamento
    python manage.py populate_orcamento --reset   # limpa dados antes de recriar
"""
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Orgao, UnidadeOrganizacional, UserProfile
from modulo_orcamento.models import AcaoOrcamentaria, ElementoDespesa, FonteRecurso, DotacaoOrcamentaria
from modulo_planejamento.models import NecessidadePlanejamento, PlanoOrcamentario, ItemPlanoOrcamentario
from modulo_demanda.models import DFD
from modulo_etp.models import ETP


ELEMENTOS_DESPESA = [
    (33901,  'Locação de Mão de Obra'),
    (33903,  'Passagens e Despesas com Locomoção'),
    (33904,  'Contratação por Tempo Determinado'),
    (33913,  'Obrigações Patronais'),
    (33914,  'Diárias – Civil'),
    (33930,  'Material de Consumo'),
    (33931,  'Premiações Culturais, Artísticas, Científicas, Desportivas e Outras'),
    (33936,  'Outros Serviços de Terceiros – Pessoa Física'),
    (33939,  'Outros Serviços de Terceiros – Pessoa Jurídica'),
    (44905,  'Equipamentos e Material Permanente'),
    (44906,  'Equipamentos e Material Permanente – Leasing'),
    (44909,  'Software'),
]

ACOES = {
    'SSP': [
        ('2024.001', 'Modernização Tecnológica da SSP',        'Serviço'),
        ('2024.002', 'Manutenção de Frota SSP',                'Funcionamento / Operação'),
        ('2024.003', 'Capacitação Corporativa SSP',            'Capacitação'),
        ('2024.004', 'Infraestrutura de Rede SSP',             'Obra / Equipamento'),
    ],
    'CBMBA': [
        ('2024.101', 'Equipamentos de Combate a Incêndio',     'Equipamento'),
        ('2024.102', 'Manutenção Operacional CBM',             'Funcionamento / Operação'),
        ('2024.103', 'Capacitação Bombeiros',                  'Capacitação'),
    ],
    'PMBA': [
        ('2024.201', 'Viaturas Policiais PMBA',                'Obra / Equipamento'),
        ('2024.202', 'Derivados de Petróleo PMBA',             'Funcionamento / Operação'),
        ('2024.203', 'Tecnologia de Segurança PMBA',           'Serviço'),
    ],
}

FONTES = {
    'SSP':   [(100, 'Recursos Ordinários', 'Tesouro'), (110, 'Recursos Próprios SSP', 'Tesouro')],
    'CBMBA': [(100, 'Recursos Ordinários', 'Tesouro'), (200, 'Fundo Especial CBM', 'FUNEBOM')],
    'PMBA':  [(100, 'Recursos Ordinários', 'Tesouro'), (300, 'Fundo FESP PMBA', 'FESP')],
}


class Command(BaseCommand):
    help = 'Popula dados de orçamento, necessidades e DFDs para teste de fluxo completo'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Limpa dados existentes antes de recriar')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Limpando dados de teste...')
            ETP.objects.all().delete()
            DFD.objects.all().delete()
            NecessidadePlanejamento.objects.all().delete()
            PlanoOrcamentario.objects.all().delete()
            DotacaoOrcamentaria.objects.all().delete()
            FonteRecurso.objects.all().delete()
            AcaoOrcamentaria.objects.all().delete()
            ElementoDespesa.objects.all().delete()
            self.stdout.write(self.style.WARNING('Dados limpos.'))

        orgaos = {o.sigla: o for o in Orgao.objects.all()}
        if not orgaos:
            self.stderr.write('Execute setup_dev primeiro.')
            return

        # 1. Elementos de despesa (global)
        self.stdout.write('\n--- Elementos de Despesa ---')
        elementos = {}
        for cod, desc in ELEMENTOS_DESPESA:
            el, created = ElementoDespesa.objects.get_or_create(
                codigo=cod, defaults={'descricao': desc, 'ativo': True}
            )
            elementos[cod] = el
            self.stdout.write(f'  {"+" if created else "·"} {cod} — {desc}')

        # 2. Ações Orçamentárias por órgão
        self.stdout.write('\n--- Ações Orçamentárias ---')
        acoes = {}
        for sigla, lista in ACOES.items():
            orgao = orgaos.get(sigla)
            if not orgao:
                continue
            for codigo, nome, tipo in lista:
                acao, created = AcaoOrcamentaria.objects.get_or_create(
                    org_id=orgao, codigo=codigo,
                    defaults={'nome': nome, 'tipo': tipo, 'ativa': True}
                )
                acoes[(sigla, codigo)] = acao
                self.stdout.write(f'  {"+" if created else "·"} {sigla}/{codigo} — {nome}')

        # 3. Fontes de Recurso por órgão
        self.stdout.write('\n--- Fontes de Recurso ---')
        fontes = {}
        for sigla, lista in FONTES.items():
            orgao = orgaos.get(sigla)
            if not orgao:
                continue
            for cod, nome, tipo in lista:
                fonte, created = FonteRecurso.objects.get_or_create(
                    org_id=orgao, codigo=cod,
                    defaults={'nome': nome, 'tipo': tipo, 'exercicio_anterior': False}
                )
                fontes[(sigla, cod)] = fonte
                self.stdout.write(f'  {"+" if created else "·"} {sigla}/{cod} — {nome} ({tipo})')

        # 4. Dotações Orçamentárias
        self.stdout.write('\n--- Dotações Orçamentárias ---')
        dotacoes = {}
        dotacao_specs = [
            # (sigla_org, codigo_acao, cod_elem, cod_fonte, valor, status)
            ('SSP',   '2024.001', 33939, 100, 1_500_000.00, 'Aprovada'),
            ('SSP',   '2024.002', 33930, 100,   800_000.00, 'Aprovada'),
            ('SSP',   '2024.003', 33939, 110,   300_000.00, 'Em Análise'),
            ('SSP',   '2024.004', 44905, 100, 2_000_000.00, 'Aprovada'),
            ('CBMBA', '2024.101', 44905, 100,   600_000.00, 'Aprovada'),
            ('CBMBA', '2024.102', 33930, 200,   250_000.00, 'Aprovada'),
            ('CBMBA', '2024.103', 33939, 100,   150_000.00, 'Proposta'),
            ('PMBA',  '2024.201', 44905, 100, 1_200_000.00, 'Aprovada'),
            ('PMBA',  '2024.202', 33930, 100,   400_000.00, 'Aprovada'),
            ('PMBA',  '2024.203', 33939, 300,   500_000.00, 'Aprovada'),
        ]
        for sigla, cod_acao, cod_elem, cod_fonte, valor, status in dotacao_specs:
            orgao = orgaos.get(sigla)
            acao  = acoes.get((sigla, cod_acao))
            elem  = elementos.get(cod_elem)
            fonte = fontes.get((sigla, cod_fonte))
            if not all([orgao, acao, elem, fonte]):
                continue
            dot, created = DotacaoOrcamentaria.objects.get_or_create(
                org_id=orgao, acao=acao, elemento_despesa=elem, fonte_recurso=fonte,
                exercicio_fiscal=2024,
                defaults={'valor_dotado': valor, 'status': status}
            )
            dotacoes[(sigla, cod_acao)] = dot
            self.stdout.write(f'  {"+" if created else "·"} {sigla}/{cod_acao} R${valor:,.0f} ({status})')

        # 5. Necessidades de Planejamento
        self.stdout.write('\n--- Necessidades de Planejamento ---')
        unidades = {(u.orgao.sigla, u.sigla): u for u in UnidadeOrganizacional.objects.select_related('orgao')}

        necessidade_specs = [
            # (titulo, orgao, unidade, valor, area, prioridade, tipo_execucao, status)
            (
                'Contratação de Serviço de Suporte TI',
                'SSP', 'CMP', 450_000.00, ['TI'], 'Alta', 'interna', 'Aprovada',
            ),
            (
                'Aquisição de Equipamentos de Segurança',
                'SSP', 'CORSEG', 320_000.00, ['Ops'], 'Alta', 'interna', 'Aprovada',
            ),
            (
                'Manutenção de Frota SSP',
                'SSP', 'CMP', 180_000.00, ['Frota'], 'Média', 'interna', 'Identificada',
            ),
            (
                'Equipamentos de Combate a Incêndio CBM',
                'CBMBA', 'DEM_CBM', 580_000.00, ['Ops'], 'Alta', 'externa', 'Aprovada',
            ),
            (
                'Capacitação de Bombeiros 2024',
                'CBMBA', 'DEM_CBM', 140_000.00, ['Formação'], 'Média', 'interna', 'Aprovada',
            ),
            (
                'Aquisição de Viaturas PM',
                'PMBA', 'DEM_PM', 1_100_000.00, ['Frota'], 'Alta', 'externa', 'Aprovada',
            ),
            (
                'Sistema de Monitoramento PMBA',
                'PMBA', 'DEM_PM', 480_000.00, ['TI'], 'Alta', 'interna', 'Aprovada',
            ),
            (
                'Derivados de Petróleo PMBA',
                'PMBA', 'DEM_PM', 390_000.00, ['Derivados'], 'Média', 'interna', 'Em Análise',
            ),
        ]

        necessidades = {}
        prazo = datetime.date(2024, 12, 31)
        for titulo, org_sigla, und_sigla, valor, areas, prio, tipo_exec, status in necessidade_specs:
            orgao   = orgaos.get(org_sigla)
            unidade = unidades.get((org_sigla, und_sigla))
            if not orgao:
                continue

            # orgao_executor: pai se externa
            orgao_executor = None
            aceite_pai = None
            if tipo_exec == 'externa':
                orgao_executor = orgao.parent
                aceite_pai = 'pendente'

            nec, created = NecessidadePlanejamento.objects.get_or_create(
                org_id=orgao, titulo=titulo,
                defaults={
                    'descricao': f'Necessidade de planejamento: {titulo}',
                    'area_aplicacao': areas,
                    'valor_estimado': valor,
                    'departamento_solicitante': unidade.nome if unidade else org_sigla,
                    'exercicio_fiscal': 2024,
                    'prioridade': prio,
                    'status': status,
                    'prazo_desejado': prazo,
                    'tipo_execucao': tipo_exec,
                    'unidade_demandante': unidade,
                    'orgao_executor': orgao_executor,
                    'aceite_pai': aceite_pai,
                }
            )
            necessidades[titulo] = nec
            self.stdout.write(f'  {"+" if created else "·"} [{org_sigla}] {titulo} ({status}, {tipo_exec})')

        # 6. Planos Orçamentários + vinculação
        self.stdout.write('\n--- Planos Orçamentários ---')
        planos = {}
        plano_specs = [
            ('SSP',   2024, 'Plano Anual SSP 2024',   4_600_000.00),
            ('CBMBA', 2024, 'Plano Anual CBM 2024',   1_000_000.00),
            ('PMBA',  2024, 'Plano Anual PMBA 2024',  2_100_000.00),
        ]
        for sigla, exercicio, descricao, dotacao in plano_specs:
            orgao = orgaos.get(sigla)
            if not orgao:
                continue
            plano, created = PlanoOrcamentario.objects.get_or_create(
                orgao=orgao, exercicio_fiscal=exercicio,
                defaults={'descricao': descricao, 'dotacao_total': dotacao}
            )
            planos[sigla] = plano
            self.stdout.write(f'  {"+" if created else "·"} {sigla}/{exercicio} — {descricao}')

        # Vincular necessidades aos planos
        vincular = [
            # (plano_sigla, titulo_necessidade, origem)
            ('SSP',   'Contratação de Serviço de Suporte TI',      'propria'),
            ('SSP',   'Aquisição de Equipamentos de Segurança',     'propria'),
            ('SSP',   'Equipamentos de Combate a Incêndio CBM',     'orgao_filho'),
            ('SSP',   'Aquisição de Viaturas PM',                   'orgao_filho'),
            ('CBMBA', 'Capacitação de Bombeiros 2024',              'propria'),
            ('PMBA',  'Sistema de Monitoramento PMBA',              'propria'),
        ]
        for plano_sigla, titulo, origem in vincular:
            plano = planos.get(plano_sigla)
            nec   = necessidades.get(titulo)
            if plano and nec:
                _, created = ItemPlanoOrcamentario.objects.get_or_create(
                    plano=plano, necessidade=nec, defaults={'origem': origem}
                )
                self.stdout.write(f'  {"+" if created else "·"} {plano_sigla} ← {titulo[:40]} [{origem}]')

        # 7. DFDs de teste
        self.stdout.write('\n--- DFDs de Teste ---')
        dfd_specs = [
            # (numero_sei, necessidade_titulo, org_sigla, valor, status)
            ('SEI-001/2024-SUPORTE-TI',  'Contratação de Serviço de Suporte TI',  'SSP',   450_000.00, 'Rascunho'),
            ('SEI-002/2024-EQUIP-SEG',   'Aquisição de Equipamentos de Segurança', 'SSP',  320_000.00, 'Aprovada'),
            ('SEI-003/2024-INCENDIO',    'Equipamentos de Combate a Incêndio CBM', 'CBMBA',580_000.00, 'Aprovada'),
            ('SEI-004/2024-VIATURAS',    'Aquisição de Viaturas PM',              'PMBA', 1_100_000.00,'Aprovada'),
            ('SEI-005/2024-MONITOR',     'Sistema de Monitoramento PMBA',         'PMBA',  480_000.00, 'Em Análise'),
        ]

        admin_user = User.objects.filter(username='admin').first()
        unidade_licitante_ssp = unidades.get(('SSP', 'CLIC'))
        dfds = {}
        for numero_sei, nec_titulo, org_sigla, valor, status in dfd_specs:
            orgao = orgaos.get(org_sigla)
            nec   = necessidades.get(nec_titulo)
            if not orgao:
                continue
            dfd, created = DFD.objects.get_or_create(
                numero_sei=numero_sei,
                defaults={
                    'org_id': orgao,
                    'descricao': f'DFD referente a: {nec_titulo}',
                    'valor_estimado': valor,
                    'area_aplicacao': nec.area_aplicacao if nec else ['Ops'],
                    'prazo_necessidade': prazo,
                    'status': status,
                    'local_entrega': f'Sede do órgão — {orgao.sigla}',
                    'unidade_licitante': unidade_licitante_ssp,
                    'created_by': admin_user,
                    'updated_by': admin_user,
                }
            )
            dfds[numero_sei] = dfd
            # vincular necessidade ao DFD
            if nec and not nec.dfd_id:
                nec.dfd = dfd
                if status in ('Aprovada', 'Em Análise') and nec.status == 'Aprovada':
                    nec.status = 'DFD Criado'
                nec.save(update_fields=['dfd', 'status'])
            self.stdout.write(f'  {"+" if created else "·"} {numero_sei} ({status})')

        # 8. ETPs de teste (apenas para DFDs Aprovados)
        self.stdout.write('\n--- ETPs de Teste ---')
        etp_specs = [
            # (dfd_numero_sei, numero_sei_etp, status)
            ('SEI-002/2024-EQUIP-SEG',  'ETP-002/2024-EQUIP-SEG',  'Rascunho'),
            ('SEI-003/2024-INCENDIO',   'ETP-003/2024-INCENDIO',   'Submetido'),
            ('SEI-004/2024-VIATURAS',   'ETP-004/2024-VIATURAS',   'Aprovado'),
        ]
        for dfd_sei, etp_sei, etp_status in etp_specs:
            dfd = dfds.get(dfd_sei)
            if not dfd:
                continue
            etp, created = ETP.objects.get_or_create(
                dfd=dfd,
                defaults={
                    'org_id': dfd.org_id,
                    'numero_sei': etp_sei,
                    'necessidade_contratacao': f'Necessidade de contratação para {dfd.descricao}',
                    'requisitos_contratacao': 'Empresa com experiência comprovada na área, certificações exigidas pela legislação vigente.',
                    'levantamento_mercado': 'Pesquisa de mercado realizada junto a 3 fornecedores. Valores compatíveis com o praticado no mercado.',
                    'estimativa_valor': dfd.valor_estimado,
                    'descricao_solucao': 'Contratação de empresa especializada mediante processo licitatório na modalidade Pregão Eletrônico.',
                    'justificativa_solucao': 'Solução mais adequada considerando custo-benefício e legislação aplicável.',
                    'status': etp_status,
                }
            )
            self.stdout.write(f'  {"+" if created else "·"} {etp_sei} ({etp_status})')

        # Resumo final
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Orçamento populado ==='))
        self.stdout.write(f'  Elementos de despesa : {ElementoDespesa.objects.count()}')
        self.stdout.write(f'  Ações orçamentárias  : {AcaoOrcamentaria.objects.count()}')
        self.stdout.write(f'  Fontes de recurso    : {FonteRecurso.objects.count()}')
        self.stdout.write(f'  Dotações             : {DotacaoOrcamentaria.objects.count()}')
        self.stdout.write(f'  Necessidades         : {NecessidadePlanejamento.objects.count()}')
        self.stdout.write(f'  Planos orçamentários : {PlanoOrcamentario.objects.count()}')
        self.stdout.write(f'  DFDs                 : {DFD.objects.count()}')
        self.stdout.write(f'  ETPs                 : {ETP.objects.count()}')
        self.stdout.write('')
        self.stdout.write('  Fluxo disponível para teste:')
        self.stdout.write('  SEI-001/2024-SUPORTE-TI → Rascunho  (submeter → analisar → aprovar → criar ETP)')
        self.stdout.write('  SEI-002/2024-EQUIP-SEG  → Aprovada  (ETP em Rascunho, submeter ETP)')
        self.stdout.write('  SEI-003/2024-INCENDIO   → Aprovada  (ETP Submetido, iniciar análise)')
        self.stdout.write('  SEI-004/2024-VIATURAS   → Aprovada  (ETP Aprovado)')
        self.stdout.write('  SEI-005/2024-MONITOR    → Em Análise')
