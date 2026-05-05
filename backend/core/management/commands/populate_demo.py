"""
Popula o banco com dados de demonstração coerentes para avaliação do sistema.

Cobre o fluxo completo:
  Necessidade → DFD → Mapa de Preços → ETP → TR (com lotes) →
  Orçamento (dotação → indicação → NPO → concessão) → Contrato

Formato SEI SSP-BA: 020.16859.AAAA.NNNNNNN-VD

Uso:
    python manage.py populate_demo
    python manage.py populate_demo --limpar    # limpa dados transacionais antes
"""
from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from core.models import Orgao, UnidadeOrganizacional, ItemCatalogo
from modulo_planejamento.models import NecessidadePlanejamento
from modulo_demanda.models import DFD, ItemDFD, NumeroProcesso
from modulo_etp.models import ETP, HistoricoETP
from modulo_tr.models import TR, LoteTR, ItemLoteTR, HistoricoTR
from modulo_mapa_precos.models import (
    MapaComparativoPrecos, FonteConsultada, ItemMapa, PrecoColetado
)
from modulo_orcamento.models import (
    AcaoOrcamentaria, ElementoDespesa, NaturezaDespesa, FonteRecurso,
    DotacaoOrcamentaria, IndicacaoOrcamentaria, IndicacaoDotacao,
    DescentralizacaoOrcamentaria, ConcessaoOrcamentaria, HistoricoIndicacao,
)
from modulo_contrato.models import Contrato


# ── Gerador de número SEI SSP-BA ──────────────────────────────────────────
_seq = [4491]

def sei(ano=2026):
    """Formato oficial SSP-BA: 020.16859.AAAA.NNNNNNN-VD"""
    _seq[0] += 1
    n = _seq[0]
    base = int(f'0201685900{ano}{n:07d}') % 97
    dv = (base % 89) + 10   # dígito entre 10-98
    return f'020.16859.{ano}.{n:07d}-{dv:02d}'


class Command(BaseCommand):
    help = 'Popula banco com dados de demonstração coerentes (fluxo completo)'

    def add_arguments(self, parser):
        parser.add_argument('--limpar', action='store_true', default=False,
                            help='Limpa dados transacionais antes de popular')

    def ok(self, msg):   self.stdout.write(self.style.SUCCESS(f'  ✓  {msg}'))
    def info(self, msg): self.stdout.write(f'     {msg}')
    def sec(self, msg):  self.stdout.write(f'\n── {msg}')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['limpar']:
            self._limpar()

        # ── Referências ───────────────────────────────────────────────────
        admin    = User.objects.filter(is_superuser=True).first()
        analista = User.objects.filter(username='analista_ssp').first() or admin
        dem_ssp  = User.objects.filter(username='dem_ssp').first() or admin
        plan_ssp = User.objects.filter(username='plan_ssp').first() or admin
        gestor   = User.objects.filter(username='gestor').first() or admin
        sol_cbm  = User.objects.filter(username='solicitante').first() or admin

        ssp = Orgao.objects.get(sigla='SSP')
        cbm = Orgao.objects.get(sigla='CBMBA')

        hoje = date.today()

        # ── Catálogo SIMPAS ───────────────────────────────────────────────
        self.sec('Catálogo SIMPAS')
        CAT = [
            ('65.10.19.00120553-6', 'Notebook Dell Latitude 5540 i5/16GB/512GB SSD', 'UN'),
            ('65.10.19.00120554-4', 'Monitor 24" Full HD IPS 75Hz',                  'UN'),
            ('65.10.19.00120555-2', 'Mouse Óptico USB',                              'UN'),
            ('65.10.19.00120556-0', 'Teclado ABNT2 USB',                             'UN'),
            ('38.20.15.00030100-1', 'Câmera de Videomonitoramento IP 4MP',            'UN'),
            ('38.20.15.00030101-9', 'Switch PoE Gerenciável 24 Portas 370W',          'UN'),
            ('38.20.15.00030102-7', 'NVR 32 Canais 4K 32TB RAID',                    'UN'),
            ('74.60.10.00071200-4', 'Serviço de Manutenção Preventiva de Viaturas',  'SVC'),
            ('42.40.20.00016900-5', 'Kit IFAK Individual First Aid Kit',              'UN'),
        ]
        cat = {}
        for simpas, nome, unid in CAT:
            obj, _ = ItemCatalogo.objects.get_or_create(
                codigo_simpas=simpas,
                defaults={'nome': nome, 'unidade_medida': unid, 'ativo': True}
            )
            cat[simpas] = obj
            self.ok(f'[{obj.familia}] {nome[:50]}')

        # ── Estrutura Orçamentária ────────────────────────────────────────
        self.sec('Estrutura Orçamentária 2026')

        elem52, _ = ElementoDespesa.objects.get_or_create(
            codigo=52, defaults={'descricao': 'Equipamentos e Material Permanente', 'ativo': True})
        elem39, _ = ElementoDespesa.objects.get_or_create(
            codigo=39, defaults={'descricao': 'Outros Serviços de Terceiros — PJ', 'ativo': True})

        nat449052, _ = NaturezaDespesa.objects.get_or_create(
            codigo='449052',
            defaults={'descricao': 'Equipamentos e Material Permanente',
                      'elemento_despesa': elem52, 'ativa': True})
        nat339039, _ = NaturezaDespesa.objects.get_or_create(
            codigo='339039',
            defaults={'descricao': 'Outros Serviços de Terceiros — PJ',
                      'elemento_despesa': elem39, 'ativa': True})

        acao2001, _ = AcaoOrcamentaria.objects.get_or_create(
            codigo='2001', org_id=ssp,
            defaults={'nome': 'Modernização Tecnológica da Segurança Pública',
                      'tipo': 'Projeto', 'ativa': True,
                      'org_id': ssp, 'created_by': admin, 'updated_by': admin})
        acao2002, _ = AcaoOrcamentaria.objects.get_or_create(
            codigo='2002', org_id=ssp,
            defaults={'nome': 'Manutenção das Atividades Operacionais',
                      'tipo': 'Atividade', 'ativa': True,
                      'org_id': ssp, 'created_by': admin, 'updated_by': admin})

        fonte100, _ = FonteRecurso.objects.get_or_create(
            codigo=100, org_id=ssp,
            defaults={'nome': 'Recursos do Tesouro Estadual', 'tipo': 'proprio',
                      'org_id': ssp, 'created_by': admin, 'updated_by': admin})
        fonte200, _ = FonteRecurso.objects.get_or_create(
            codigo=200, org_id=ssp,
            defaults={'nome': 'Transferências Federais — FPM/FPE', 'tipo': 'transferencia',
                      'org_id': ssp, 'created_by': admin, 'updated_by': admin})

        dot_ti, _ = DotacaoOrcamentaria.objects.get_or_create(
            exercicio_fiscal=2026, acao=acao2001, elemento_despesa=elem52,
            fonte_recurso=fonte100, org_id=ssp,
            defaults={
                'natureza_despesa': nat449052,
                'valor_dotado': Decimal('1_500_000.00'),
                'status': 'Aprovada',
                'eixo': 'Segurança Pública',
                'objetivo_estrategico': 'Modernização do aparato tecnológico das forças de segurança',
                'org_id': ssp, 'created_by': admin, 'updated_by': admin,
            })
        dot_svc, _ = DotacaoOrcamentaria.objects.get_or_create(
            exercicio_fiscal=2026, acao=acao2002, elemento_despesa=elem39,
            fonte_recurso=fonte200, org_id=ssp,
            defaults={
                'natureza_despesa': nat339039,
                'valor_dotado': Decimal('800_000.00'),
                'status': 'Aprovada',
                'eixo': 'Operações',
                'objetivo_estrategico': 'Manutenção da capacidade operacional das forças de campo',
                'org_id': ssp, 'created_by': admin, 'updated_by': admin,
            })

        self.ok(f'Dotação TI  Ação {acao2001.codigo}/Elem {elem52.codigo} — R$ {dot_ti.valor_dotado:,.0f}')
        self.ok(f'Dotação SVC Ação {acao2002.codigo}/Elem {elem39.codigo} — R$ {dot_svc.valor_dotado:,.0f}')

        # ── Necessidades de Planejamento ──────────────────────────────────
        self.sec('Necessidades de Planejamento 2026')

        nec_ti, _ = NecessidadePlanejamento.objects.get_or_create(
            titulo='Modernização do Parque de Equipamentos de TI — SSP-BA',
            org_id=ssp,
            defaults={
                'descricao': (
                    'Renovação do parque de notebooks, monitores e periféricos da SSP-BA, '
                    'visando atender às necessidades operacionais das unidades e garantir '
                    'desempenho adequado para os sistemas corporativos.'
                ),
                'valor_estimado': Decimal('480_000.00'),
                'departamento_solicitante': 'Coordenação de Material e Patrimônio — CMP/SSP',
                'exercicio_fiscal': 2026,
                'area_aplicacao': ['TI'],
                'prioridade': 'alta',
                'tipo_execucao': 'interna',
                'status': 'Aprovada',
                'org_id': ssp, 'created_by': plan_ssp, 'updated_by': plan_ssp,
            })
        self.ok(f'NEC-TI    [{nec_ti.status}] {nec_ti.titulo[:55]}')

        nec_frota, _ = NecessidadePlanejamento.objects.get_or_create(
            titulo='Contratação de Serviço de Manutenção de Frota Operacional',
            org_id=ssp,
            defaults={
                'descricao': (
                    'Contratação de empresa especializada para manutenção preventiva e '
                    'corretiva da frota de viaturas operacionais, garantindo disponibilidade '
                    'mínima de 85% da frota ao longo do exercício.'
                ),
                'valor_estimado': Decimal('360_000.00'),
                'departamento_solicitante': 'Coordenadoria de Segurança — CORSEG/SSP',
                'exercicio_fiscal': 2026,
                'area_aplicacao': ['Frota'],
                'prioridade': 'alta',
                'tipo_execucao': 'interna',
                'status': 'Aprovada',
                'org_id': ssp, 'created_by': plan_ssp, 'updated_by': plan_ssp,
            })
        self.ok(f'NEC-FROTA [{nec_frota.status}] {nec_frota.titulo[:55]}')

        nec_cbm, _ = NecessidadePlanejamento.objects.get_or_create(
            titulo='Aquisição de Kits IFAK para Operações do CBM-BA',
            org_id=cbm,
            defaults={
                'descricao': (
                    'Aquisição de kits IFAK e materiais de primeiros socorros para reposição '
                    'dos estoques operacionais das companhias do CBM-BA.'
                ),
                'valor_estimado': Decimal('90_000.00'),
                'departamento_solicitante': 'Unidade Demandante CBM — DEM_CBM',
                'exercicio_fiscal': 2026,
                'area_aplicacao': ['Ops'],
                'prioridade': 'media',
                'tipo_execucao': 'externa',
                'status': 'Aprovada',
                'org_id': cbm, 'created_by': sol_cbm, 'updated_by': sol_cbm,
            })
        self.ok(f'NEC-CBM   [{nec_cbm.status}] {nec_cbm.titulo[:55]}')

        # ── DFDs ─────────────────────────────────────────────────────────
        self.sec('Documentos de Formalização de Demanda')

        def _dfd(numero_sei, descricao, valor, area, prazo, nec, org, user_c, user_u, status='Aprovada'):
            obj, created = DFD.objects.get_or_create(
                numero_sei=numero_sei,
                defaults={
                    'descricao': descricao,
                    'valor_estimado': Decimal(str(valor)),
                    'area_aplicacao': area,
                    'prazo_necessidade': prazo,
                    'status': status,
                    'orgao_compras': ssp,
                    'org_id': org, 'created_by': user_c, 'updated_by': user_u,
                })
            if created:
                NumeroProcesso.objects.create(
                    dfd=obj, etapa='dfd', numero=numero_sei,
                    org_id=org, created_by=user_c, updated_by=user_c)
                # Vincular necessidade ao DFD (OneToOne está em NecessidadePlanejamento.dfd)
                if nec and not nec.dfd_id:
                    nec.dfd = obj
                    nec.status = 'DFD Criado'
                    nec.save(update_fields=['dfd', 'status'])
            return obj, created

        # DFD 1 — Notebooks (fluxo completo)
        sei_dfd1 = sei()
        dfd1, c1 = _dfd(sei_dfd1,
            'Aquisição de notebooks, monitores e periféricos para modernização do parque de TI da SSP-BA',
            '420000.00', ['TI'], date(2026, 6, 30), nec_ti, ssp, dem_ssp, analista)
        if c1:
            it_nb, _   = ItemDFD.objects.get_or_create(dfd=dfd1, objeto='Notebook Dell Latitude 5540 i5/16GB/512GB SSD', defaults={
                'unidade_medida': 'UN', 'quantidade': Decimal('50'), 'valor_unitario_estimado': Decimal('5_200.00'),
                'item_catalogo': cat.get('65.10.19.00120553-6'), 'justificativa': 'Substituição de equipamentos com mais de 5 anos.',
                'org_id': ssp, 'created_by': dem_ssp, 'updated_by': dem_ssp})
            it_mon, _  = ItemDFD.objects.get_or_create(dfd=dfd1, objeto='Monitor 24" Full HD IPS 75Hz', defaults={
                'unidade_medida': 'UN', 'quantidade': Decimal('50'), 'valor_unitario_estimado': Decimal('890.00'),
                'item_catalogo': cat.get('65.10.19.00120554-4'),
                'org_id': ssp, 'created_by': dem_ssp, 'updated_by': dem_ssp})
            it_mouse, _ = ItemDFD.objects.get_or_create(dfd=dfd1, objeto='Mouse Óptico USB', defaults={
                'unidade_medida': 'UN', 'quantidade': Decimal('50'), 'valor_unitario_estimado': Decimal('45.00'),
                'item_catalogo': cat.get('65.10.19.00120555-2'),
                'org_id': ssp, 'created_by': dem_ssp, 'updated_by': dem_ssp})
            it_teclado, _ = ItemDFD.objects.get_or_create(dfd=dfd1, objeto='Teclado ABNT2 USB', defaults={
                'unidade_medida': 'UN', 'quantidade': Decimal('50'), 'valor_unitario_estimado': Decimal('55.00'),
                'item_catalogo': cat.get('65.10.19.00120556-0'),
                'org_id': ssp, 'created_by': dem_ssp, 'updated_by': dem_ssp})
        else:
            it_nb    = ItemDFD.objects.filter(dfd=dfd1, objeto__icontains='Notebook').first()
            it_mon   = ItemDFD.objects.filter(dfd=dfd1, objeto__icontains='Monitor').first()
            it_mouse = ItemDFD.objects.filter(dfd=dfd1, objeto__icontains='Mouse').first()
            it_teclado = ItemDFD.objects.filter(dfd=dfd1, objeto__icontains='Teclado').first()
        self.ok(f'DFD-1 {sei_dfd1}  Notebooks TI ({dfd1.itens.count()} itens) [{dfd1.status}]')

        # DFD 2 — Videomonitoramento
        sei_dfd2 = sei()
        dfd2, c2 = _dfd(sei_dfd2,
            'Aquisição de sistema de videomonitoramento IP para ampliação da segurança eletrônica',
            '240000.00', ['TI'], date(2026, 8, 31), nec_ti, ssp, dem_ssp, analista)
        if c2:
            ItemDFD.objects.create(dfd=dfd2, objeto='Câmera de Videomonitoramento IP 4MP', unidade_medida='UN',
                quantidade=Decimal('80'), valor_unitario_estimado=Decimal('1_450.00'),
                item_catalogo=cat.get('38.20.15.00030100-1'),
                org_id=ssp, created_by=dem_ssp, updated_by=dem_ssp)
            ItemDFD.objects.create(dfd=dfd2, objeto='Switch PoE Gerenciável 24 Portas 370W', unidade_medida='UN',
                quantidade=Decimal('10'), valor_unitario_estimado=Decimal('3_200.00'),
                item_catalogo=cat.get('38.20.15.00030101-9'),
                org_id=ssp, created_by=dem_ssp, updated_by=dem_ssp)
            ItemDFD.objects.create(dfd=dfd2, objeto='NVR 32 Canais 4K 32TB RAID', unidade_medida='UN',
                quantidade=Decimal('5'), valor_unitario_estimado=Decimal('8_800.00'),
                item_catalogo=cat.get('38.20.15.00030102-7'),
                org_id=ssp, created_by=dem_ssp, updated_by=dem_ssp)
        self.ok(f'DFD-2 {sei_dfd2}  Videomonitoramento ({dfd2.itens.count()} itens) [{dfd2.status}]')

        # DFD 3 — Manutenção de Frota (contrato gerado)
        sei_dfd3 = sei()
        dfd3, c3 = _dfd(sei_dfd3,
            'Contratação de serviço continuado de manutenção preventiva e corretiva da frota operacional de viaturas',
            '360000.00', ['Frota'], date(2026, 3, 31), nec_frota, ssp, analista, analista)
        if c3:
            ItemDFD.objects.create(dfd=dfd3, objeto='Serviço de Manutenção Preventiva e Corretiva de Viaturas',
                unidade_medida='MÊS', quantidade=Decimal('12'), valor_unitario_estimado=Decimal('30_000.00'),
                item_catalogo=cat.get('74.60.10.00071200-4'),
                justificativa='12 meses de contrato de serviço continuado.',
                org_id=ssp, created_by=analista, updated_by=analista)
        self.ok(f'DFD-3 {sei_dfd3}  Manutenção Frota ({dfd3.itens.count()} itens) [{dfd3.status}]')

        # DFD 4 — IFAK CBM (órgão filho, demanda externa)
        sei_dfd4 = sei()
        dfd4, c4 = _dfd(sei_dfd4,
            'Aquisição de kits IFAK e materiais de primeiros socorros para operações do CBM-BA',
            '90000.00', ['Ops'], date(2026, 5, 31), nec_cbm, cbm, sol_cbm, sol_cbm)
        if c4:
            ItemDFD.objects.create(dfd=dfd4, objeto='Kit IFAK Individual First Aid Kit',
                unidade_medida='UN', quantidade=Decimal('200'), valor_unitario_estimado=Decimal('420.00'),
                item_catalogo=cat.get('42.40.20.00016900-5'),
                org_id=cbm, created_by=sol_cbm, updated_by=sol_cbm)
        self.ok(f'DFD-4 {sei_dfd4}  IFAK CBM ({dfd4.itens.count()} itens) [{dfd4.status}] [org: CBMBA]')

        # ── Mapa de Preços — DFD 1 ─────────────────────────────────────
        self.sec('Mapa Comparativo de Preços — DFD 1')

        mapa1, cm = MapaComparativoPrecos.objects.get_or_create(
            dfd=dfd1,
            defaults={
                'objeto': 'Pesquisa de preços — Equipamentos de TI (notebooks, monitores e periféricos)',
                'exercicio_fiscal': 2026,
                'status': 'Aprovado',
                'metodo_calculo': 'media',          # choices: media, mediana, menor_valido
                'responsavel': analista,
                'aprovador': admin,
                'data_aprovacao': date(2026, 2, 20),
                'org_id': ssp, 'created_by': analista, 'updated_by': analista,
            })
        if cm:
            f_simpas = FonteConsultada.objects.create(mapa=mapa1, tipo='I',
                descricao='SIMPAS/Comprasnet.BA — Painel de preços 2025',
                data_consulta=date(2026, 2, 15), referencia='Acesso em 15/02/2026')
            f_gov = FonteConsultada.objects.create(mapa=mapa1, tipo='II',
                descricao='PE SSP-RS 012/2025 e TRE-PA 008/2025 — contratos similares',
                data_consulta=date(2026, 2, 16), referencia='PNCP — pesquisa em 16/02/2026')
            f_web = FonteConsultada.objects.create(mapa=mapa1, tipo='III',
                descricao='Kabum.com.br, Magazine Luiza, Fast Shop — cotação on-line',
                data_consulta=date(2026, 2, 17), referencia='Sites especializados — fev/2026')

            # codigo_simpas permite match no histórico WEBBER
            nb_simpas = cat.get('65.10.19.00120553-6')
            mon_simpas = cat.get('65.10.19.00120554-4')
            im_nb = ItemMapa.objects.create(mapa=mapa1,
                descricao='Notebook Dell Latitude 5540 i5/16GB/512GB SSD',
                codigo_simpas=(nb_simpas.codigo_simpas if nb_simpas else ''),
                unidade_medida='UN', quantidade=Decimal('50'), ordem=1)
            im_mon = ItemMapa.objects.create(mapa=mapa1,
                descricao='Monitor 24" Full HD IPS, 75Hz, HDMI+DP',
                codigo_simpas=(mon_simpas.codigo_simpas if mon_simpas else ''),
                unidade_medida='UN', quantidade=Decimal('50'), ordem=2)

            # Preços coletados — Notebook
            for v, f in [(Decimal('5080'), f_simpas), (Decimal('5350'), f_gov), (Decimal('5190'), f_web)]:
                PrecoColetado.objects.create(item=im_nb, fonte=f, valor_unitario=v,
                    data_referencia=f.data_consulta, valido=True)
            # Preços coletados — Monitor
            for v, f in [(Decimal('875'), f_simpas), (Decimal('910'), f_gov), (Decimal('860'), f_web)]:
                PrecoColetado.objects.create(item=im_mon, fonte=f, valor_unitario=v,
                    data_referencia=f.data_consulta, valido=True)

            # Usar método calcular() do próprio model
            for im in [im_nb, im_mon]:
                im.calcular(metodo='media')

            total_mapa = sum(
                (i.valor_total_calculado or Decimal('0')) for i in mapa1.itens.all()
            )
            mapa1.valor_estimado_total = total_mapa
            mapa1.save(update_fields=['valor_estimado_total'])
            self.ok(f'Mapa ID={mapa1.pk}  [{mapa1.status}] R$ {total_mapa:,.0f} (3 fontes, média aritmética)')
        else:
            im_nb  = ItemMapa.objects.filter(mapa=mapa1, descricao__icontains='Notebook').first()
            im_mon = ItemMapa.objects.filter(mapa=mapa1, descricao__icontains='Monitor').first()
            self.info(f'Mapa ID={mapa1.pk} já existe [{mapa1.status}]')

        preco_nb_ref  = (im_nb.valor_unitario_calculado  if im_nb  else Decimal('5206.67'))
        preco_mon_ref = (im_mon.valor_unitario_calculado if im_mon else Decimal('881.67'))

        # ── ETP — DFD 1 (Aprovado) ─────────────────────────────────────
        self.sec('ETP — DFD 1 (Aprovado)')

        sei_etp1 = sei()
        etp1_qs = ETP.objects.filter(dfd=dfd1)
        if not etp1_qs.exists():
            etp1 = ETP.objects.create(
                dfd=dfd1, numero_sei=sei_etp1,
                necessidade_contratacao=(
                    'A SSP-BA possui 320 estações de trabalho com mais de 5 anos, com degradação de '
                    'desempenho que compromete a eficiência operacional. A renovação é necessária '
                    'para atender os requisitos dos sistemas corporativos SICRIM, SIVISA e BPNET.'
                ),
                requisitos_contratacao=(
                    'Notebook: processador Intel Core i5-1235U ou superior, 16GB DDR5, SSD 512GB NVMe, '
                    'display 15.6" FHD, WiFi 6, Bluetooth 5.2, garantia 3 anos on-site NBD. '
                    'Monitor: painel IPS 24", 1920×1080, 75Hz, HDMI+DisplayPort, VESA 100×100, '
                    'certificação Energy Star. Periféricos: mouse e teclado ABNT2 USB.'
                ),
                levantamento_mercado=(
                    'Pesquisa realizada conforme Decreto Estadual 22.886/2024 em 3 parâmetros distintos: '
                    'Parâmetro I (SIMPAS/Comprasnet.BA): R$ 5.080,00/UN. '
                    'Parâmetro II (contratos similares — SSP-RS e TRE-PA): R$ 5.350,00/UN. '
                    'Parâmetro III (sites especializados): R$ 5.190,00/UN. '
                    'Valor médio apurado no Mapa de Preços: R$ 5.206,67/UN (notebooks) e '
                    'R$ 881,67/UN (monitores).'
                ),
                estimativa_valor=Decimal('310_834.00'),
                descricao_solucao=(
                    'Aquisição de 50 notebooks, 50 monitores, 50 mouses e 50 teclados, '
                    'agrupados em 2 lotes: Lote 1 (microcomputadores + monitores) e Lote 2 '
                    '(periféricos), com reserva de cota de 25% para ME/EPP no Lote 1.'
                ),
                justificativa_solucao=(
                    'O agrupamento por afinidade técnica (notebooks+monitores no Lote 1; '
                    'periféricos no Lote 2) viabiliza competição por segmento e economias de escala, '
                    'conforme Art. 40, V da Lei 14.133/2021.'
                ),
                riscos=(
                    'R1 — Atraso na entrega: multa de 0,5%/dia. '
                    'R2 — Incompatibilidade técnica: exigência de amostra prévia. '
                    'R3 — Descontinuidade do modelo: cláusula de equivalência técnica.'
                ),
                sustentabilidade=(
                    'Exigência de certificação Energy Star para monitores. '
                    'Descarte conforme Res. CONAMA 401/2008. '
                    'Preferência por fornecedores certificados ISO 14001.'
                ),
                tipo_objeto='bens',
                tipo_parcelamento='lotes',
                parcelamento_justificativa=(
                    'Divisão em 2 lotes por afinidade técnica: Lote 1 (computadores+monitores) '
                    'e Lote 2 (periféricos). Permite competição especializada por segmento.'
                ),
                reserva_cota_me_epp=True,
                reserva_cota_justificativa='',
                licitacao_exclusiva_me_epp=False,
                status='Aprovado',
                org_id=ssp, created_by=analista, updated_by=admin,
            )
            for ant, nov, usr, mot in [
                ('Rascunho', 'Submetido',   dem_ssp,  'Documentação técnica elaborada pela CMP.'),
                ('Submetido', 'Em Análise', analista, 'Recebido para análise pela CLIC.'),
                ('Em Análise', 'Aprovado',  admin,    'Estimativa fundamentada no Mapa de Preços aprovado. ETP aprovado.'),
            ]:
                HistoricoETP.objects.create(etp=etp1, status_anterior=ant,
                    status_novo=nov, usuario=usr, motivo=mot)
            NumeroProcesso.objects.get_or_create(dfd=dfd1, etapa='etp',
                defaults={'numero': sei_etp1, 'org_id': ssp, 'created_by': analista, 'updated_by': analista})
            self.ok(f'ETP {sei_etp1}  tipo_objeto=bens | parcelamento=lotes | cota=Sim [{etp1.status}]')
        else:
            etp1 = etp1_qs.first()
            self.info(f'ETP DFD-1 já existe: {etp1.numero_sei} [{etp1.status}]')

        # ── ETP — DFD 2 (Em Análise) ───────────────────────────────────
        self.sec('ETP — DFD 2 (Em Análise)')

        sei_etp2 = sei()
        etp2_qs = ETP.objects.filter(dfd=dfd2)
        if not etp2_qs.exists():
            etp2 = ETP.objects.create(
                dfd=dfd2, numero_sei=sei_etp2,
                necessidade_contratacao=(
                    'Ampliação do sistema de videomonitoramento da SSP-BA para cobertura de '
                    'novas áreas críticas identificadas no Plano Estadual de Segurança Pública 2026-2029.'
                ),
                requisitos_contratacao=(
                    'Câmeras IP 4MP, H.265+, infravermelho 30m, IP66. '
                    'Switch PoE gerenciável 24 portas 370W. '
                    'NVR 32 canais 4K, RAID 5, 32TB.'
                ),
                levantamento_mercado='Pesquisa em andamento: SIMPAS (Parâmetro I) e fornecedores diretos (Parâmetro IV).',
                estimativa_valor=Decimal('240_000.00'),
                descricao_solucao='Sistema integrado de câmeras, switches PoE e NVRs — lote único por interdependência técnica.',
                justificativa_solucao='Itens tecnicamente interdependentes — sistema integrado. Lote único conforme Art. 40 §1º Lei 14.133.',
                tipo_objeto='bens',
                tipo_parcelamento='lote_unico',
                parcelamento_justificativa='Itens formam um sistema integrado interdependente. Parcelamento inviabilizaria a funcionalidade.',
                reserva_cota_me_epp=False,
                reserva_cota_justificativa=(
                    'Sistema especializado de videomonitoramento com requisitos técnicos complexos '
                    'incompatíveis com o porte de ME/EPP. Art. 49, II da LC 123/2006.'
                ),
                licitacao_exclusiva_me_epp=False,
                status='Em Análise',
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            for ant, nov, usr in [
                ('Rascunho', 'Submetido',   dem_ssp),
                ('Submetido', 'Em Análise', analista),
            ]:
                HistoricoETP.objects.create(etp=etp2, status_anterior=ant,
                    status_novo=nov, usuario=usr)
            NumeroProcesso.objects.get_or_create(dfd=dfd2, etapa='etp',
                defaults={'numero': sei_etp2, 'org_id': ssp, 'created_by': analista, 'updated_by': analista})
            self.ok(f'ETP {sei_etp2}  tipo_objeto=bens | lote_unico | sem cota [{etp2.status}]')
        else:
            etp2 = etp2_qs.first()
            self.info(f'ETP DFD-2 já existe [{etp2.status}]')

        # ── TR — DFD 1 (Rascunho com lotes) ──────────────────────────────
        self.sec('TR — DFD 1 (Rascunho com lotes formados)')

        sei_tr1 = sei()
        tr1_qs = TR.objects.filter(etp=etp1)
        if not tr1_qs.exists():
            tr1 = TR.objects.create(
                etp=etp1, numero_sei=sei_tr1,
                objeto_contratacao=(
                    'Aquisição de equipamentos de informática — notebooks, monitores e periféricos — '
                    'para modernização do parque tecnológico da SSP-BA, conforme especificações '
                    'técnicas deste Termo de Referência.'
                ),
                justificativa=(
                    'Renovação do parque de TI da SSP-BA para garantir desempenho adequado aos '
                    'sistemas corporativos, conforme Necessidade de Planejamento registrada no WEBBER '
                    f'e DFD SEI nº {dfd1.numero_sei}.'
                ),
                requisitos_contratacao=(
                    'Notebook: Intel Core i5-1235U+, 16GB DDR5, 512GB NVMe, 15.6" FHD, WiFi 6, '
                    'garantia 3 anos on-site NBD. Monitor: IPS 24" 1920×1080 75Hz HDMI+DP, Energy Star. '
                    'Mouse USB ≥1000DPI. Teclado ABNT2 USB.'
                ),
                obrigacoes_contratada=(
                    'Entregar os equipamentos nos locais indicados no prazo de 30 dias após AFM. '
                    'Garantir assistência técnica on-site durante o período de garantia. '
                    'Substituir equipamentos com defeito em até 5 dias úteis.'
                ),
                obrigacoes_contratante=(
                    'Designar servidor responsável pelo recebimento e conferência. '
                    'Efetuar pagamento em até 30 dias após liquidação da nota fiscal. '
                    'Comunicar defeitos ou inconformidades imediatamente.'
                ),
                criterios_selecao=(
                    'Menor preço por lote. Habilitação: regularidade fiscal, atestado de fornecimento '
                    'de ≥30 UNs de equipamentos similares. Amostra: 1 unidade de cada item '
                    'apresentada em até 5 dias úteis pelo provisoriamente vencedor.'
                ),
                criterios_medicao=(
                    'Pagamento único após entrega integral e aceite pela Comissão de Recebimento. '
                    'NF-e discriminando itens e quantidades.'
                ),
                tipo_prazo_vigencia='escopo',
                prazo_meses=None,
                instrumento_inicio='afm',
                prazo_observacao=(
                    'Entrega única em até 30 (trinta) dias corridos após emissão da '
                    'Autorização de Fornecimento de Material — AFM (Art. 105 Lei 14.133/2021).'
                ),
                local_entrega=(
                    'Sede da SSP-BA: Av. Almirante Marques de Leão, 222, Barris, Salvador-BA, CEP 40.070-280. '
                    'Responsável: Coordenação de Material e Patrimônio (CMP). '
                    'Horário: 08h às 17h, dias úteis.'
                ),
                estimativa_valor=Decimal('310_834.00'),
                status='Rascunho',
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            NumeroProcesso.objects.get_or_create(dfd=dfd1, etapa='tr',
                defaults={'numero': sei_tr1, 'org_id': ssp, 'created_by': analista, 'updated_by': analista})

            # Lote 1 — Notebooks + Monitores (ampla)
            lote1 = LoteTR.objects.create(tr=tr1,
                descricao='Lote 1 — Microcomputadores (Notebooks + Monitores)',
                modalidade='ampla', ordem=1,
                justificativa_agrupamento=(
                    'Notebook e monitor compõem a estação de trabalho completa. Agrupamento '
                    'garante compatibilidade técnica e reduz o número de contratos a gerenciar.'
                ),
                org_id=ssp, created_by=analista, updated_by=analista)
            ItemLoteTR.objects.create(lote=lote1, item_dfd=it_nb,
                quantidade=Decimal('50'), valor_unitario_ref=preco_nb_ref, preco_origem='mapa')
            ItemLoteTR.objects.create(lote=lote1, item_dfd=it_mon,
                quantidade=Decimal('50'), valor_unitario_ref=preco_mon_ref, preco_origem='mapa')

            # Lote 1-Cota — 25% ME/EPP (13 unidades = 25% de 50 arredondado)
            lote1c = LoteTR.objects.create(tr=tr1,
                descricao='Lote 1-Cota — Microcomputadores — Reserva ME/EPP (25%)',
                modalidade='cota_me_epp', percentual_cota=25, lote_origem=lote1, ordem=2,
                org_id=ssp, created_by=analista, updated_by=analista)
            ItemLoteTR.objects.create(lote=lote1c, item_dfd=it_nb,
                quantidade=Decimal('13'), valor_unitario_ref=preco_nb_ref, preco_origem='mapa')
            ItemLoteTR.objects.create(lote=lote1c, item_dfd=it_mon,
                quantidade=Decimal('13'), valor_unitario_ref=preco_mon_ref, preco_origem='mapa')

            # Lote 2 — Periféricos (ampla)
            lote2 = LoteTR.objects.create(tr=tr1,
                descricao='Lote 2 — Periféricos (Mouse e Teclado)',
                modalidade='ampla', ordem=3,
                justificativa_agrupamento=(
                    'Mouse e teclado são periféricos de mesma natureza de uso, '
                    'fornecidos pelo mesmo segmento de mercado.'
                ),
                org_id=ssp, created_by=analista, updated_by=analista)
            ItemLoteTR.objects.create(lote=lote2, item_dfd=it_mouse,
                quantidade=Decimal('50'), valor_unitario_ref=Decimal('45.00'), preco_origem='dfd')
            ItemLoteTR.objects.create(lote=lote2, item_dfd=it_teclado,
                quantidade=Decimal('50'), valor_unitario_ref=Decimal('55.00'), preco_origem='dfd')

            self.ok(f'TR {sei_tr1}  3 lotes (2 ampla + 1 cota ME/EPP) | AFM | tipo=bens [{tr1.status}]')
        else:
            tr1 = tr1_qs.first()
            self.info(f'TR DFD-1 já existe [{tr1.status}]')

        # ── Orçamento — Indicação aprovada (frota, contrato vigente) ─────
        self.sec('Orçamento — DOD Aprovada + NPO + Concessão (DFD Frota)')

        ind1_qs = IndicacaoOrcamentaria.objects.filter(dfd=dfd3, org_id=ssp)
        if not ind1_qs.exists():
            ind1 = IndicacaoOrcamentaria.objects.create(
                numero='DOD-2026-001', exercicio_fiscal=2026, dfd=dfd3,
                valor_total=Decimal('360_000.00'), status='Aprovada',
                ordenador=admin, data_aprovacao=date(2026, 3, 10),
                observacoes='DOD aprovada em reunião orçamentária de 10/03/2026 — Serviço continuado de manutenção de frota.',
                org_id=ssp, created_by=plan_ssp, updated_by=admin,
            )
            for ant, nov, usr in [
                ('Rascunho', 'Submetida', plan_ssp),
                ('Submetida', 'Aprovada', admin),
            ]:
                HistoricoIndicacao.objects.create(indicacao=ind1,
                    status_anterior=ant, status_novo=nov, usuario=usr)
            idot1 = IndicacaoDotacao.objects.create(
                indicacao=ind1, dotacao=dot_svc, valor_indicado=Decimal('360_000.00'))
            dot_svc.valor_indicado = Decimal('360_000.00')
            dot_svc.save(update_fields=['valor_indicado'])
            DescentralizacaoOrcamentaria.objects.create(
                indicacao_dotacao=idot1,
                numero_npo='NPO-2026-00124',
                numero_ne='NE-2026-00348',
                data_emissao=date(2026, 3, 15),
                valor=Decimal('360_000.00'),
                observacoes='NPO emitida via FIPLAN — contrato manutenção frota SSP-BA.',
                registrada_por=plan_ssp,
            )
            dot_svc.valor_descentralizado = Decimal('360_000.00')
            dot_svc.save(update_fields=['valor_descentralizado'])
            ConcessaoOrcamentaria.objects.create(
                indicacao_dotacao=idot1,
                numero_doc='CONC-2026-00087',
                data_emissao=date(2026, 3, 20),
                valor=Decimal('30_000.00'),
                observacoes='1ª parcela mensal — março/2026.',
                registrada_por=plan_ssp,
            )
            dot_svc.valor_concedido = Decimal('30_000.00')
            dot_svc.save(update_fields=['valor_concedido'])
            self.ok('DOD-2026-001  R$ 360k [Aprovada] | NPO R$ 360k | Concessão R$ 30k (1ª parcela/mar.2026)')
        else:
            self.info('DOD frota já existe.')

        # Indicação em Rascunho — DFD 1 TI (para testar fluxo interativo)
        ind2_qs = IndicacaoOrcamentaria.objects.filter(dfd=dfd1, org_id=ssp)
        if not ind2_qs.exists():
            IndicacaoOrcamentaria.objects.create(
                numero='DOD-2026-002', exercicio_fiscal=2026, dfd=dfd1,
                valor_total=Decimal('0'), status='Rascunho',
                observacoes='Indicação orçamentária para aquisição de TI — vincule a dotação TI e submeta ao ordenador.',
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            self.ok('DOD-2026-002  Rascunho (vincule a Dotação TI e submeta)')
        else:
            self.info('DOD TI já existe.')

        # ── Contrato — Manutenção Frota ───────────────────────────────────
        self.sec('Contrato — Manutenção de Frota (Vigente)')

        if not Contrato.objects.filter(dfd=dfd3).exists():
            sei_ct = sei()
            ct = Contrato.objects.create(
                exercicio=2026,
                orgao_executor=ssp,
                objeto=(
                    'Contratação de empresa especializada para prestação de serviços continuados '
                    'de manutenção preventiva e corretiva da frota operacional de viaturas da SSP-BA.'
                ),
                tipo_origem='licitacao',
                dfd=dfd3,
                numero_processo_sei=sei_ct,
                valor_contrato=Decimal('336_000.00'),
                data_assinatura=date(2026, 3, 25),
                data_vigencia_inicio=date(2026, 4, 1),
                data_vigencia_fim=date(2027, 3, 31),
                status='Vigente',
                fiscal_contrato=analista,
                gestor_contrato=gestor,
                ordenador=admin,
                observacoes='Pregão Eletrônico SSP-BA nº 003/2026. Empresa: Auto Serviços Bahia Ltda. CNPJ 12.345.678/0001-90.',
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            NumeroProcesso.objects.get_or_create(dfd=dfd3, etapa='contrato',
                defaults={'numero': sei_ct, 'org_id': ssp, 'created_by': admin, 'updated_by': admin})
            self.ok(f'{ct.numero}  R$ {ct.valor_contrato:,.0f} | vigência: {ct.data_vigencia_inicio} → {ct.data_vigencia_fim}')
        else:
            self.info(f'Contrato frota já existe: {Contrato.objects.get(dfd=dfd3).numero}')

        # ── Resumo ────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 62))
        self.stdout.write(self.style.SUCCESS('  BANCO POPULADO — CENÁRIOS PARA AVALIAÇÃO'))
        self.stdout.write(self.style.SUCCESS('═' * 62))
        self.stdout.write(f'')
        self.stdout.write(f'  DFD-1 ({sei_dfd1})')
        self.stdout.write(f'  Notebooks TI: DFD✓ → Mapa✓ → ETP✓(aprovado) → TR(rascunho)')
        self.stdout.write(f'  3 lotes | tipo=bens | AFM | cota ME/EPP 25%')
        self.stdout.write(f'')
        self.stdout.write(f'  DFD-2 ({sei_dfd2})')
        self.stdout.write(f'  Videomonitoramento: DFD✓ → ETP(em análise — devolver ou aprovar)')
        self.stdout.write(f'')
        self.stdout.write(f'  DFD-3 ({sei_dfd3})')
        self.stdout.write(f'  Manutenção Frota: DFD✓ → DOD✓ → NPO✓ → Concessão✓ → Contrato✓(vigente)')
        self.stdout.write(f'')
        self.stdout.write(f'  DFD-4 ({sei_dfd4})')
        self.stdout.write(f'  IFAK CBM: demanda externa CBMBA aguardando instrução SSP')
        self.stdout.write(f'')
        self.stdout.write(f'  Orçamento: DOD-2026-002 em Rascunho pronto para testar fluxo')
        self.stdout.write(self.style.SUCCESS('═' * 62))

    def _limpar(self):
        self.sec('Limpando dados transacionais...')
        from modulo_contrato.models import Apostila, Aditivo
        from modulo_mapa_precos.models import PrecoColetado, ItemMapa, FonteConsultada, MapaComparativoPrecos
        from modulo_tr.models import ItemLoteTR, LoteTR, HistoricoTR
        from modulo_etp.models import HistoricoETP, HistoricoNumeroSEI
        from modulo_orcamento.models import (
            ConcessaoOrcamentaria, DescentralizacaoOrcamentaria,
            IndicacaoDotacao, HistoricoIndicacao, IndicacaoOrcamentaria,
        )
        for model in [
            Aditivo, Apostila, Contrato,
            ConcessaoOrcamentaria, DescentralizacaoOrcamentaria,
            IndicacaoDotacao, HistoricoIndicacao, IndicacaoOrcamentaria,
            DotacaoOrcamentaria, FonteRecurso, AcaoOrcamentaria,
            ItemLoteTR, LoteTR, HistoricoTR, TR,
            HistoricoETP, HistoricoNumeroSEI, ETP,
            PrecoColetado, ItemMapa, FonteConsultada, MapaComparativoPrecos,
            NumeroProcesso, ItemDFD, DFD,
            NecessidadePlanejamento,
        ]:
            n = model.objects.all().delete()[0]
            if n:
                self.info(f'Removidos {n} de {model.__name__}')
        DotacaoOrcamentaria.objects.update(
            valor_indicado=0, valor_descentralizado=0, valor_concedido=0)
        self.ok('Limpeza concluída.')
