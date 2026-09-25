"""
Popula dados para simular o Cronograma de Início Sugerido (Plano de Compras)
e a medição de duração por modalidade/natureza do objeto (Painel Gerencial de
Tramitação): amostra histórica real e cronologicamente consistente de
Procedimento → Contrato, segmentada por tipo de objeto (via TR) e por
passagem por órgãos externos (TramitacaoExterna) — um pregão de bens comuns
não leva o mesmo tempo que um pregão de viaturas que tramita pela Casa Civil
e pela PGE, e medir os dois juntos como se fossem a mesma coisa escondia
exatamente essa diferença.

Sempre recria do zero (apaga o que esta simulação criou antes de inserir de
novo) — é dado de demonstração, não histórico real; rodar de novo depois de
mudar o script deve refletir a mudança, não pular por já existir.

Os registros são identificados pelos processos SEI reservados 020.9999x (e
pelas Atas/códigos de catálogo listados abaixo), não por um prefixo no texto:
na tela, precisam ler como contratações reais da SSP.

Uso:
    python manage.py seed_cronograma_contratacoes
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Orgao, ItemCatalogo
from modulo_demanda.models import DFD, ItemDFD
from modulo_etp.models import ETP
from modulo_tr.models import TR
from modulo_licitacao.models import Procedimento, ResultadoLote, TramitacaoExterna
from modulo_contrato.models import Contrato
from modulo_arp.models import Ata, ItemAta, HistoricoAta
from modulo_mapa_precos.models import MapaComparativoPrecos, ItemMapa

MARCADOR = '[Simulação Cronograma]'  # versões antigas marcavam o texto; limpo por compatibilidade
SEI_SIMULACAO = ('020.99991.', '020.99992.', '020.99993.', '020.99999.')
ATAS_SIMULACAO = ('ARP-SSP-031/2026', 'ARP-SSP-032/2026', 'ARP-SIM-001/2026', 'ARP-SIM-002/2026')
CATALOGO_SIMULACAO = ('42.60.10.90001-1', '42.60.20.90002-2', '42.60.30.90003-3', '25.10.10.90004-4',
                      '42.50.40.90005-5', '42.50.50.90006-6')

MODALIDADE_LABEL = {'pregao_eletronico': 'Pregão Eletrônico', 'dispensa_eletronica': 'Dispensa Eletrônica'}


class Command(BaseCommand):
    help = 'Popula (recriando do zero) dados para simular o Cronograma de Início Sugerido e a medição de duração segmentada'

    def ok(self, msg):    self.stdout.write(self.style.SUCCESS(f'  ✓  {msg}'))
    def info(self, msg):  self.stdout.write(f'     {msg}')
    def sec(self, msg):   self.stdout.write(f'\n── {msg}')

    def _limpar(self):
        from django.db.models import Q
        sei = Q()
        for prefixo in SEI_SIMULACAO:
            sei |= Q(numero_sei__startswith=prefixo)
        proc_q = Q(objeto__startswith=MARCADOR) | sei
        Contrato.objects.filter(Q(objeto__startswith=MARCADOR) | Q(resultado_licitacao__procedimento__in=Procedimento.objects.filter(proc_q))).delete()
        Procedimento.objects.filter(proc_q).delete()  # cascata: ResultadoLote, TramitacaoExterna
        TR.objects.filter(Q(objeto_contratacao__startswith=MARCADOR) | sei).delete()
        ETP.objects.filter(Q(necessidade_contratacao__startswith=MARCADOR) | sei).delete()
        DFD.objects.filter(Q(descricao__startswith=MARCADOR) | sei).delete()  # cascata: ItemDFD
        Ata.objects.filter(Q(objeto__startswith=MARCADOR) | Q(numero_ata__in=ATAS_SIMULACAO)).delete()
        MapaComparativoPrecos.objects.filter(
            Q(objeto__startswith=MARCADOR) | Q(itens__codigo_simpas__in=CATALOGO_SIMULACAO)).delete()
        ItemCatalogo.objects.filter(Q(nome__startswith=MARCADOR) | Q(codigo_simpas__in=CATALOGO_SIMULACAO)).delete()

    def _dfd_etp_tr(self, org, autor, numero_base, objeto, tipo_objeto, valor, exercicio=2026):
        """Cadeia mínima DFD→ETP→TR para o Procedimento poder carregar um
        tipo_objeto real — sem isso não há como segmentar a medição por
        natureza da contratação."""
        dfd = DFD.objects.create(
            org_id=org, numero_sei=f'{numero_base}-DFD', descricao=objeto,
            valor_estimado=Decimal(valor), area_aplicacao=['Ops'],
            prazo_necessidade=date.today() + timedelta(days=180), status='Aprovada',
            created_by=autor, updated_by=autor,
        )
        etp = ETP.objects.create(
            dfd=dfd, numero_sei=f'{numero_base}-ETP',
            necessidade_contratacao=objeto, status='Aprovado',
            org_id=org, created_by=autor, updated_by=autor,
        )
        tr = TR.objects.create(
            etp=etp, numero_sei=f'{numero_base}-TR', objeto_contratacao=objeto,
            tipo_objeto=tipo_objeto, status='Aprovado',
            org_id=org, created_by=autor, updated_by=autor,
        )
        return tr

    def _procedimento_concluido(self, org, modalidade, dias_ate_assinatura, autor, objeto, numero_sei, valor,
                                 exercicio=2026, tr=None, tramitacoes_externas=None):
        """Cria Procedimento → ResultadoLote(homologado) → Contrato assinado
        HOJE, com o Procedimento aberto `dias_ate_assinatura` dias antes —
        amostra cronologicamente consistente. `tramitacoes_externas` é uma
        lista de (orgao_externo, dias_de_ida_e_volta) que, quando presente,
        é o motivo real de o processo levar mais tempo — não um número
        arbitrário aplicado por categoria."""
        proc = Procedimento.objects.create(
            org_id=org, exercicio=exercicio, modalidade=modalidade,
            objeto=objeto, tr=tr, numero_sei=numero_sei, valor_estimado=Decimal(valor),
            created_by=autor, updated_by=autor,
        )
        abertura = timezone.now() - timedelta(days=dias_ate_assinatura)
        Procedimento.objects.filter(pk=proc.pk).update(created_at=abertura)

        for orgao_externo, dias_tramite, offset_envio in (tramitacoes_externas or []):
            data_envio = (abertura + timedelta(days=offset_envio)).date()
            TramitacaoExterna.objects.create(
                procedimento=proc, orgao_externo=orgao_externo, tipo='anuencia',
                data_envio=data_envio, data_retorno=data_envio + timedelta(days=dias_tramite),
                observacoes='Anuência prévia' if orgao_externo == 'CasaCivil' else 'Parecer jurídico',
                registrado_por=autor,
            )

        contrato = Contrato.objects.create(
            org_id=org, exercicio=exercicio, orgao_executor=org,
            objeto=objeto, numero_processo_sei=numero_sei,
            tipo_origem='licitacao' if modalidade == 'pregao_eletronico' else 'dispensa',
            valor_contrato=Decimal(valor) * Decimal('0.94'), data_assinatura=date.today(),
            created_by=autor, updated_by=autor,
        )
        ResultadoLote.objects.create(
            procedimento=proc, resultado='homologado', contrato_gerado=contrato,
            descricao_lote='Lote único',
        )
        return proc, contrato

    def _item_catalogo_simulado(self, nome, codigo_simpas):
        return ItemCatalogo.objects.create(
            nome=nome, unidade_medida='UN',
            codigo_simpas=codigo_simpas, classificacao_tipo='permanente',
        )

    def _dfd_pendente(self, org, numero_sei, prazo, autor, descricao):
        return DFD.objects.create(
            org_id=org, numero_sei=numero_sei, descricao=descricao,
            valor_estimado=Decimal('50000.00'), area_aplicacao=['Ops'],
            prazo_necessidade=prazo, status='Aprovada', created_by=autor, updated_by=autor,
        )

    def _item_dfd(self, dfd, item_catalogo, valor_unitario, quantidade, autor):
        return ItemDFD.objects.create(
            org_id=dfd.org_id, dfd=dfd, item_catalogo=item_catalogo,
            objeto=item_catalogo.nome, justificativa=dfd.descricao,
            unidade_medida='UN', quantidade=Decimal(str(quantidade)),
            valor_unitario_estimado=Decimal(str(valor_unitario)),
            valor_total_estimado=Decimal(str(valor_unitario)) * Decimal(str(quantidade)),
            created_by=autor, updated_by=autor,
        )

    def _ata_com_item(self, org, numero_ata, item_catalogo, valor_unitario_registrado, autor):
        ata = Ata.objects.create(
            org_id=org, tipo_origem='gerenciador', numero_ata=numero_ata,
            objeto=f'Registro de preços — {item_catalogo.nome}', status='vigente',
            data_assinatura=date.today() - timedelta(days=60),
            data_vigencia_inicio=date.today() - timedelta(days=60),
            data_vigencia_fim=date.today() + timedelta(days=305),
            created_by=autor, updated_by=autor,
        )
        HistoricoAta.objects.create(ata=ata, status_anterior='rascunho', status_novo='vigente',
                                     usuario=autor, motivo='Ata assinada e publicada.')
        ItemAta.objects.create(
            ata=ata, item_catalogo=item_catalogo, objeto=item_catalogo.nome, unidade_medida='UN',
            quantidade_registrada=Decimal('500'),
            valor_unitario_registrado=Decimal(str(valor_unitario_registrado)),
        )
        return ata

    def _referencia_mercado(self, org, item_catalogo, valor_unitario_calculado, autor):
        mapa = MapaComparativoPrecos.objects.create(
            org_id=org, objeto=f'Pesquisa de preços de referência — {item_catalogo.nome}',
            exercicio_fiscal=2026, created_by=autor, updated_by=autor,
        )
        return ItemMapa.objects.create(
            mapa=mapa, descricao=item_catalogo.nome, codigo_simpas=item_catalogo.codigo_simpas,
            unidade_medida='UN', quantidade=Decimal('1'),
            valor_unitario_calculado=Decimal(str(valor_unitario_calculado)),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        admin = User.objects.filter(is_superuser=True).first()
        autor = User.objects.filter(username='analista_ssp').first() or admin
        ssp = Orgao.objects.get(sigla='SSP')

        self.sec('Limpando simulação anterior (se houver)')
        self._limpar()
        self.ok('limpo')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('Duração medida — Pregão Eletrônico de bens comuns (sem trâmite externo)')
        objetos_comuns = [
            ('Aquisição de mobiliário para as unidades administrativas da SSP', 80, '180000.00'),
            ('Aquisição de material de expediente para as unidades da SSP', 90, '95000.00'),
            ('Aquisição de microcomputadores para as unidades administrativas da SSP', 100, '420000.00'),
        ]
        for i, (objeto, dias, valor) in enumerate(objetos_comuns, start=1):
            base = f'020.99991.2026.{i:07d}'
            tr = self._dfd_etp_tr(ssp, autor, base, objeto, 'bens', valor)
            self._procedimento_concluido(ssp, 'pregao_eletronico', dias, autor, objeto, f'{base}-PE', valor, tr=tr)
        self.ok('3 Pregões de bens comuns concluídos (80, 90, 100 dias) — sem tramitação externa')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('Duração medida — Pregão Eletrônico de viaturas (COM trâmite externo: Casa Civil + PGE)')
        objetos_viaturas = [
            ('Aquisição de viaturas policiais caracterizadas 4x4 para o policiamento ostensivo', 150, '1850000.00'),
            ('Aquisição de motocicletas para o motopatrulhamento (ROCAM)', 165, '980000.00'),
            ('Aquisição de viaturas para transporte de custodiados', 180, '1450000.00'),
        ]
        for i, (objeto, dias, valor) in enumerate(objetos_viaturas, start=1):
            base = f'020.99992.2026.{i:07d}'
            tr = self._dfd_etp_tr(ssp, autor, base, objeto, 'bens', valor)
            # Casa Civil (anuência prévia, ~30 dias) e PGE (aprovação jurídica, ~20 dias),
            # enviados logo após a abertura — é isso que empurra a duração total pra cima,
            # não uma categoria "veículo" tratada como número mágico.
            self._procedimento_concluido(
                ssp, 'pregao_eletronico', dias, autor, objeto, f'{base}-PE', valor, tr=tr,
                tramitacoes_externas=[('CasaCivil', 30, 10), ('PGE', 20, 45)],
            )
        self.ok('3 Pregões de viaturas concluídos (150, 165, 180 dias) — com Casa Civil + PGE')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('Duração medida — Dispensa Eletrônica por valor (sem TR/ETP — dispensado por valor)')
        dispensas = [
            ('Aquisição de material de limpeza para a sede da SSP', '38000.00'),
            ('Aquisição de toner e cartuchos para as unidades administrativas', '42000.00'),
            ('Aquisição de material elétrico para manutenção predial', '29500.00'),
        ]
        for i, (dias, (objeto, valor)) in enumerate(zip((22, 25, 28), dispensas), start=1):
            self._procedimento_concluido(ssp, 'dispensa_eletronica', dias, autor, objeto,
                                         f'020.99993.2026.{i:07d}-DE', valor)
        self.ok('3 processos de Dispensa Eletrônica concluídos (22, 25, 28 dias)')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('Itens pendentes do PCA — variados prazos, para popular os trimestres')

        hoje = date.today()
        cat_a = self._item_catalogo_simulado('Bebedouro industrial em aço inox, 100 litros', '42.60.10.90001-1')
        cat_b = self._item_catalogo_simulado('Cadeira giratória ergonômica com apoio de braços', '42.60.20.90002-2')
        cat_c = self._item_catalogo_simulado('Ar-condicionado split 24.000 BTUs, inverter', '42.60.30.90003-3')
        cat_d = self._item_catalogo_simulado('Viatura policial caracterizada 4x4, cabine dupla', '25.10.10.90004-4')

        dfd_a = self._dfd_pendente(ssp, '020.99999.2026.0000001-01', hoje + timedelta(days=73), autor,
                                   'Aquisição de bebedouros industriais para as unidades operacionais da SSP')
        self._item_dfd(dfd_a, cat_a, '2300.00', 12, autor)

        dfd_b = self._dfd_pendente(ssp, '020.99999.2026.0000002-02', hoje + timedelta(days=32), autor,
                                   'Aquisição de cadeiras ergonômicas para a Central de Operações (CICOM)')
        self._item_dfd(dfd_b, cat_b, '1250.00', 40, autor)

        dfd_c = self._dfd_pendente(ssp, '020.99999.2026.0000003-03', hoje + timedelta(days=7), autor,
                                   'Aquisição de aparelhos de ar-condicionado para a sala de servidores')
        self._item_dfd(dfd_c, cat_c, '4200.00', 6, autor)

        dfd_d = self._dfd_pendente(ssp, '020.99999.2027.0000004-04', date(2027, 3, 15), autor,
                                   'Recomposição da frota de viaturas 4x4 para o policiamento no interior')
        self._item_dfd(dfd_d, cat_d, '185000.00', 6, autor)

        self.ok('4 DFDs pendentes com itens de catálogo (1 urgente/atrasado, 1 ~Q3, 1 ~Q4, 1 exercício 2027)')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('Adesão a ARP — um caso de preço compatível e outro acima do mercado')

        cat_colete = self._item_catalogo_simulado('Colete balístico nível III-A, com capa, masculino e feminino', '42.50.40.90005-5')
        self._ata_com_item(ssp, 'ARP-SSP-031/2026', cat_colete, '2450.00', autor)
        self._referencia_mercado(ssp, cat_colete, '2600.00', autor)
        dfd_e = self._dfd_pendente(ssp, '020.99999.2026.0000005-05', hoje + timedelta(days=55), autor,
                                   'Substituição de coletes balísticos com validade vencida')
        self._item_dfd(dfd_e, cat_colete, '2450.00', 150, autor)

        cat_radio = self._item_catalogo_simulado('Rádio transceptor digital portátil padrão P25', '42.50.50.90006-6')
        self._ata_com_item(ssp, 'ARP-SSP-032/2026', cat_radio, '8900.00', autor)
        self._referencia_mercado(ssp, cat_radio, '6200.00', autor)
        dfd_f = self._dfd_pendente(ssp, '020.99999.2026.0000006-06', hoje + timedelta(days=83), autor,
                                   'Aquisição de rádios digitais portáteis para as equipes de rua')
        self._item_dfd(dfd_f, cat_radio, '8900.00', 30, autor)

        self.ok('2 Atas vigentes com Mapa de referência (1 compatível, 1 acima do mercado) + 2 DFDs pendentes')

        self.stdout.write(self.style.SUCCESS(
            '\nConcluído. Veja em Plano de Compras → "Cronograma de Início Sugerido" e em '
            'Tramitação → Indicadores → "Duração por Modalidade" (exercício 2026 para a maioria '
            'dos itens; 2027 para o item de Pregão/viatura pendente).'
        ))
