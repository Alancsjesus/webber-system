"""
Popula lacunas de dados identificadas em 18/09/2026: tabelas que existiam no
schema mas estavam zeradas no banco local (execução contratual, resultado de
licitação, FESP e ARP) — usadas para viabilizar dumpdata/loaddata de um banco
rico o suficiente para popular o Postgres novo, e para permitir análises que
dependem desses módulos.

Cada seção é idempotente por contagem: se a tabela-alvo daquele bloco já tem
registros (por ex. rodou de novo depois de já ter rodado uma vez), o bloco é
pulado com aviso — não duplica.

Uso:
    python manage.py seed_lacunas
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Orgao, UnidadeOrganizacional, ItemCatalogo
from modulo_contrato.models import (
    Contrato, Apostila, Aditivo, CronogramaEntrega, Medicao, Pagamento, Notificacao,
)
from modulo_licitacao.models import Procedimento, ResultadoLote
from modulo_etp.models import ETP, HistoricoNumeroSEI
from modulo_fornecedor.models import Fornecedor
from modulo_fesp.models import (
    InstrumentoFinanceiro, HistoricoInstrumentoFinanceiro, ComposicaoConselhoGestor,
    PlanoAplicacao, HistoricoPlanoAplicacao, MetaEspecifica, GrupoConsolidacaoItem,
    ItemPlanoAplicacao, ReuniaoConselhoGestor,
)
from modulo_arp.models import Ata, ItemAta, HistoricoAta


class Command(BaseCommand):
    help = 'Popula lacunas de dados (execução contratual, resultado de licitação, FESP, ARP)'

    def ok(self, msg):    self.stdout.write(self.style.SUCCESS(f'  ✓  {msg}'))
    def skip(self, msg):  self.stdout.write(self.style.WARNING(f'  ·  {msg}'))
    def info(self, msg):  self.stdout.write(f'     {msg}')
    def sec(self, msg):   self.stdout.write(f'\n── {msg}')

    @transaction.atomic
    def handle(self, *args, **options):
        admin    = User.objects.filter(is_superuser=True).first()
        analista = User.objects.filter(username='analista_ssp').first() or admin
        plan_ssp = User.objects.filter(username='plan_ssp').first() or admin
        gestor   = User.objects.filter(username='gestor').first() or admin

        ssp = Orgao.objects.get(sigla='SSP')
        cbm = Orgao.objects.get(sigla='CBMBA')
        pm  = Orgao.objects.get(sigla='PMBA')

        forn1 = Fornecedor.objects.get(pk=1)
        forn2 = Fornecedor.objects.get(pk=2)

        c1 = Contrato.objects.get(numero='SSP-001/2026')  # serviço de vigilância, Vigente
        c2 = Contrato.objects.get(numero='SSP-001/2025')  # material de escritório, Encerrado
        c3 = Contrato.objects.get(numero='SSP-002/2026')  # material de limpeza, Suspenso
        c4 = Contrato.objects.get(numero='SSP-003/2026')  # suporte sistema legado, Vigente

        # ═══════════════════════════════════════════════════════════════════
        self.sec('Execução Contratual — Apostila, Aditivo, Cronograma, Medição, Pagamento, Notificação')

        if Apostila.objects.exists() or Aditivo.objects.exists() or CronogramaEntrega.objects.exists() \
                or Medicao.objects.exists() or Pagamento.objects.exists() or Notificacao.objects.exists():
            self.skip('já existem registros de execução contratual — pulando bloco inteiro')
        else:
            Apostila.objects.create(
                contrato=c2, objeto='Apostilamento para atualização da dotação orçamentária vinculada, '
                'sem alteração de valor ou objeto contratual (Art. 136, Lei 14.133/2021).',
                data=date(2026, 1, 20), numero_processo_sei='001.2026/00410-2',
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            self.ok('1 Apostila (Contrato SSP-001/2025)')

            Aditivo.objects.create(
                contrato=c4, tipo='valor', valor_acrescimo=Decimal('18000.00'),
                objeto='Acréscimo de 15% do valor contratual para ampliação do escopo de suporte, '
                'incluindo módulo de folha de pagamento não previsto originalmente (Art. 125, §1º, I).',
                data=date(2026, 8, 10), numero_processo_sei='001.2026/00500-1',
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            Aditivo.objects.create(
                contrato=c3, tipo='prazo', nova_vigencia=date(2026, 10, 1),
                objeto='Prorrogação de prazo em decorrência de atraso na entrega, sem prejuízo das '
                'medidas de notificação em curso.',
                data=date(2026, 9, 5), numero_processo_sei='001.2026/00512-9',
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            adt_c1 = Aditivo.objects.create(
                contrato=c1, tipo='objeto',
                objeto='Inclusão de posto adicional de vigilância no turno noturno, sem alteração '
                'do valor mensal, mediante compensação de escopo.',
                data=date(2026, 7, 15), numero_processo_sei='001.2026/00470-5',
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            self.ok('3 Aditivos (valor/Contrato4, prazo/Contrato3, objeto/Contrato1)')

            for desc, prev, real, status, obs in [
                ('1ª parcela — material de escritório e expediente (1º trimestre)', date(2026, 2, 15), date(2026, 2, 14), 'entregue', ''),
                ('2ª parcela — material de escritório e expediente (2º trimestre)', date(2026, 5, 15), date(2026, 5, 18), 'entregue', ''),
                ('3ª parcela — material de escritório e expediente (3º trimestre)', date(2026, 8, 15), date(2026, 8, 20), 'entregue', ''),
            ]:
                CronogramaEntrega.objects.create(
                    contrato=c2, descricao=desc, quantidade=1, unidade_medida='LOTE',
                    data_prevista=prev, data_realizada=real, status=status, observacoes=obs,
                    org_id=ssp, created_by=admin, updated_by=admin,
                )
            CronogramaEntrega.objects.create(
                contrato=c3, descricao='Entrega única de material de limpeza',
                quantidade=1, unidade_medida='LOTE',
                data_prevista=date(2026, 6, 1), data_realizada=None, status='atrasado',
                observacoes='Fornecedor não realizou a entrega na data prevista — objeto de Notificação formal.',
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            self.ok('4 itens de Cronograma de Entrega (3 entregues/Contrato2, 1 atrasado/Contrato3)')

            m1 = Medicao.objects.create(
                contrato=c1, competencia_inicio=date(2026, 4, 1), competencia_fim=date(2026, 4, 30),
                data_medicao=date(2026, 5, 5), percentual_executado=Decimal('100.00'),
                valor_medido=Decimal('28000.00'), fiscal_responsavel=c1.fiscal_contrato,
                status='aprovada', parecer_fiscal='Serviço executado integralmente no período, sem intercorrências.',
                data_aprovacao=date(2026, 5, 8), numero_processo_sei='001.2026/00430-8',
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            m2 = Medicao.objects.create(
                contrato=c1, competencia_inicio=date(2026, 5, 1), competencia_fim=date(2026, 5, 31),
                data_medicao=date(2026, 6, 5), percentual_executado=Decimal('100.00'),
                valor_medido=Decimal('28000.00'), fiscal_responsavel=c1.fiscal_contrato,
                status='aprovada', parecer_fiscal='Serviço executado integralmente no período, sem intercorrências.',
                data_aprovacao=date(2026, 6, 8), numero_processo_sei='001.2026/00445-1',
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            m3 = Medicao.objects.create(
                contrato=c1, competencia_inicio=date(2026, 8, 1), competencia_fim=date(2026, 8, 31),
                data_medicao=date(2026, 9, 5), percentual_executado=Decimal('100.00'),
                valor_medido=Decimal('28000.00'), fiscal_responsavel=c1.fiscal_contrato,
                status='pendente', numero_processo_sei='001.2026/00480-3',
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            m4 = Medicao.objects.create(
                contrato=c4, competencia_inicio=date(2026, 7, 1), competencia_fim=date(2026, 7, 31),
                data_medicao=date(2026, 8, 5), percentual_executado=Decimal('100.00'),
                valor_medido=Decimal('10000.00'), fiscal_responsavel=c4.fiscal_contrato,
                status='aprovada', parecer_fiscal='Suporte prestado dentro do SLA contratado.',
                data_aprovacao=date(2026, 8, 8), numero_processo_sei='001.2026/00481-1',
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            m5 = Medicao.objects.create(
                contrato=c4, competencia_inicio=date(2026, 8, 1), competencia_fim=date(2026, 8, 31),
                data_medicao=date(2026, 9, 5), percentual_executado=Decimal('75.00'),
                valor_medido=Decimal('7500.00'), fiscal_responsavel=c4.fiscal_contrato,
                status='rejeitada',
                parecer_fiscal='Indisponibilidade do suporte acima do SLA contratado no período — '
                'medição rejeitada, glosa aplicada.',
                numero_processo_sei='001.2026/00495-6',
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            self.ok('5 Medições (2 aprovadas + 1 pendente/Contrato1, 1 aprovada + 1 rejeitada/Contrato4)')

            Pagamento.objects.create(
                contrato=c1, medicao=m1, numero_empenho='2026NE000112', numero_nota_fiscal='NF-4501',
                valor_pago=Decimal('28000.00'), data_vencimento=date(2026, 5, 20),
                data_pagamento=date(2026, 5, 20), status='pago',
                numero_processo_sei='001.2026/00430-8', org_id=ssp, created_by=analista, updated_by=analista,
            )
            Pagamento.objects.create(
                contrato=c1, medicao=m2, numero_empenho='2026NE000138', numero_nota_fiscal='NF-4602',
                valor_pago=Decimal('28000.00'), data_vencimento=date(2026, 6, 20),
                data_pagamento=date(2026, 6, 21), status='pago',
                numero_processo_sei='001.2026/00445-1', org_id=ssp, created_by=analista, updated_by=analista,
            )
            Pagamento.objects.create(
                contrato=c1, medicao=m3, numero_empenho='2026NE000201', numero_nota_fiscal='NF-4788',
                valor_pago=Decimal('28000.00'), data_vencimento=date(2026, 9, 25),
                data_pagamento=None, status='pendente',
                numero_processo_sei='001.2026/00480-3', org_id=ssp, created_by=analista, updated_by=analista,
            )
            Pagamento.objects.create(
                contrato=c4, medicao=m4, numero_empenho='2026NE000155', numero_nota_fiscal='NF-3390',
                valor_pago=Decimal('10000.00'), data_vencimento=date(2026, 8, 20),
                data_pagamento=date(2026, 8, 20), status='pago',
                numero_processo_sei='001.2026/00481-1', org_id=ssp, created_by=analista, updated_by=analista,
            )
            Pagamento.objects.create(
                contrato=c3, medicao=None, numero_empenho='2026NE000098', numero_nota_fiscal='NF-2210',
                valor_pago=Decimal('9500.00'), data_vencimento=date(2026, 8, 15),
                data_pagamento=None, status='atrasado',
                observacoes='Pagamento retido em razão de atraso na entrega comprovada — ver Notificação do contrato.',
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            self.ok('5 Pagamentos (3 pagos, 1 pendente, 1 atrasado)')

            Notificacao.objects.create(
                contrato=c3, exercicio=2026, tipo_acao='notificacao', categoria_objeto='aquisicao',
                fornecedor=forn2, numero_processo_sei='001.2026/00512-9',
                numero_sei_comunicacao='001.2026/00505-4', numero_sei_notificacao='001.2026/00509-7',
                data_notificacao=date(2026, 6, 10),
                resumo_fato='Fornecedor não entregou o material de limpeza na data prevista (01/06/2026), '
                'configurando atraso injustificado na execução contratual.',
                status='cpa', org_id=ssp, created_by=analista, updated_by=analista,
            )
            self.ok('1 Notificação Contratual (Contrato SSP-002/2026, em CPA)')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('Resultado de Licitação — ResultadoLote')

        if ResultadoLote.objects.exists():
            self.skip('já existem ResultadoLote — pulando bloco')
        else:
            mapa = [
                ('PE-CLIC-001/2025', 'homologado', 'Lote único — material de escritório e expediente',
                 forn1, Decimal('95000.00'), Decimal('92800.00'), c2, ''),
                ('PE-CLIC-002/2025', 'deserto', 'Lote único — fornecimento de água mineral em galões',
                 None, Decimal('18000.00'), None, None, 'Nenhuma proposta apresentada na sessão pública.'),
                ('PE-CLIC-003/2025', 'fracassado', 'Lote único — equipamentos de comunicação',
                 None, Decimal('380000.00'), None, None,
                 'Todas as propostas foram desclassificadas por não atenderem às especificações '
                 'técnicas mínimas do Termo de Referência.'),
                ('DE-CPLAM-001/2026', 'homologado', 'Lote único — material de limpeza',
                 forn2, Decimal('9500.00'), Decimal('9500.00'), c3, ''),
                ('INEX-CPLAM-001/2026', 'homologado', 'Lote único — suporte ao sistema legado de gestão financeira',
                 forn2, Decimal('120000.00'), Decimal('120000.00'), c4, ''),
                ('PE-CLIC-002/2026', 'cancelado', 'Lote único — notebooks, monitores e periféricos',
                 None, Decimal('480000.00'), None, None,
                 'Procedimento revogado por interesse da Administração antes da fase de julgamento '
                 '(Art. 71, Lei 14.133/2021).'),
            ]
            for numero, resultado, descricao_lote, fornecedor, v_est, v_final, contrato, obs in mapa:
                proc = Procedimento.objects.get(numero=numero)
                ResultadoLote.objects.create(
                    procedimento=proc, descricao_lote=descricao_lote, resultado=resultado,
                    fornecedor=fornecedor,
                    empresa_vencedora=fornecedor.nome_razao_social if fornecedor else '',
                    cnpj_vencedor=fornecedor.documento if fornecedor else '',
                    valor_estimado=v_est, valor_final=v_final, contrato_gerado=contrato,
                    observacoes=obs,
                )
            self.ok(f'{len(mapa)} ResultadoLote (homologado×3, deserto, fracassado, cancelado)')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('ETP — HistoricoNumeroSEI')

        if HistoricoNumeroSEI.objects.exists():
            self.skip('já existe HistoricoNumeroSEI — pulando bloco')
        else:
            etp4 = ETP.objects.get(pk=4)
            HistoricoNumeroSEI.objects.create(
                etp=etp4, numero_anterior='001.2026/00120-0', numero_novo=etp4.numero_sei,
                usuario=analista,
                motivo='Correção do número de processo SEI — autuação inicial com numeração de outro órgão.',
            )
            self.ok('1 HistoricoNumeroSEI (ETP 4)')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('FESP — Instrumentos, Conselho Gestor, Planos, Metas, Itens, Consolidação')

        if InstrumentoFinanceiro.objects.exists():
            self.skip('já existem InstrumentoFinanceiro — pulando bloco FESP inteiro')
        else:
            if1 = InstrumentoFinanceiro.objects.create(
                tipo_instrumento='fesp', numero_instrumento='FESP-2026',
                objeto='Recursos do Fundo Estadual de Segurança Pública destinados a ações de '
                'enfrentamento à violência e modernização operacional das forças de segurança '
                'no exercício de 2026.',
                orgao_concedente_nome='Secretaria de Segurança Pública do Estado da Bahia',
                valor_total_pactuado=Decimal('8000000.00'), valor_contrapartida=Decimal('0.00'),
                data_assinatura=date(2026, 1, 15), vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 12, 31),
                numero_processo_sei='020.16859.2026.0000001-10', status='vigente',
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            if2 = InstrumentoFinanceiro.objects.create(
                tipo_instrumento='convenio', numero_instrumento='SICONV-2026-000123',
                objeto='Convênio com o Ministério da Justiça e Segurança Pública para modernização '
                'de rede integrada de videomonitoramento urbano.',
                orgao_concedente_nome='Ministério da Justiça e Segurança Pública (MJSP)',
                valor_total_pactuado=Decimal('3500000.00'), valor_contrapartida=Decimal('350000.00'),
                data_assinatura=date(2026, 3, 10), vigencia_inicio=date(2026, 3, 10), vigencia_fim=date(2027, 3, 9),
                status='vigente',
                dados_especificos={'banco': 'Banco do Brasil', 'agencia': '3796-8', 'conta_especifica': '12.345-6'},
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            if3 = InstrumentoFinanceiro.objects.create(
                tipo_instrumento='emenda_parlamentar', numero_instrumento='EMENDA-2026-04521',
                objeto='Emenda parlamentar destinada à aquisição de equipamentos de proteção '
                'individual para o policiamento motorizado.',
                orgao_concedente_nome='Bancada Federal da Bahia',
                valor_total_pactuado=Decimal('600000.00'), status='rascunho',
                dados_especificos={'parlamentar_autor': '(a identificar)'},
                org_id=pm, created_by=plan_ssp, updated_by=plan_ssp,
            )
            for inst, motivo in [(if1, 'Instrumento assinado e em execução'), (if2, 'Convênio celebrado e em execução')]:
                HistoricoInstrumentoFinanceiro.objects.create(
                    instrumento=inst, status_anterior='rascunho', status_novo='vigente',
                    usuario=admin, motivo=motivo,
                )
            self.ok('3 Instrumentos Financeiros (FESP vigente, Convênio vigente, Emenda rascunho) + 2 históricos')

            membros = [
                ('presidente', admin, None, ''),
                ('assessor_planejamento', plan_ssp, None, ''),
                ('diretor_geral', gestor, None, ''),
                ('representante_casa_civil', None, None, 'Casa Civil do Estado da Bahia'),
                ('representante_fazenda', None, None, 'Secretaria da Fazenda do Estado da Bahia (SEFAZ-BA)'),
                ('representante_planejamento', None, None, 'Secretaria de Planejamento do Estado da Bahia (SEPLAN)'),
            ]
            conselho = []
            for cargo, usuario, orgao_rep, nome_externo in membros:
                m = ComposicaoConselhoGestor.objects.create(
                    usuario=usuario, cargo=cargo, orgao_representado=orgao_rep,
                    nome_orgao_externo=nome_externo, portaria_nomeacao='Portaria SSP nº 012/2026',
                    data_inicio_mandato=date(2026, 1, 1), ativo=True,
                    org_id=ssp, created_by=admin, updated_by=admin,
                )
                conselho.append(m)
            self.ok('6 membros do Conselho Gestor FESP')

            resp_nome = (admin.get_full_name() if admin and admin.get_full_name() else 'Administrador do Sistema')
            plano1 = PlanoAplicacao.objects.create(
                natureza='fesp', exercicio_fiscal=2026,
                ementa='Enfrentamento à Violência e Modernização Operacional',
                descricao='Plano de Aplicação dos recursos do FESP para o exercício de 2026, com foco '
                'em equipamentos de proteção individual e modernização de videomonitoramento.',
                status='elaboracao',
                declaracao_nao_pessoal=True, declaracao_nao_unidade_administrativa=True,
                declaracao_sem_contingenciamento=True,
                responsavel_gestao_nome=resp_nome, responsavel_gestao_cargo='Secretário de Segurança Pública',
                responsavel_elaboracao_nome=plan_ssp.get_full_name() or plan_ssp.username,
                responsavel_elaboracao_cargo='Assessoria de Planejamento',
                diagnostico='Levantamento interno indica déficit de equipamentos de proteção individual '
                'para o efetivo em policiamento motorizado e cobertura insuficiente de videomonitoramento '
                'no interior do Estado.',
                meta_geral='Reduzir a exposição a risco do efetivo operacional e ampliar a capacidade '
                'de resposta a ocorrências no interior.',
                valor_originario_investimento=Decimal('5000000.00'), valor_originario_custeio=Decimal('2500000.00'),
                valor_rendimento_investimento=Decimal('120000.00'), valor_rendimento_custeio=Decimal('30000.00'),
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            HistoricoPlanoAplicacao.objects.create(
                plano=plano1, status_anterior='', status_novo='elaboracao', usuario=plan_ssp, motivo='Plano criado',
            )
            plano1.status = 'submetido_conselho'
            plano1.save(update_fields=['status'])
            HistoricoPlanoAplicacao.objects.create(
                plano=plano1, status_anterior='elaboracao', status_novo='submetido_conselho',
                usuario=plan_ssp, motivo='Submissão ao Conselho Gestor com declarações de vedação atendidas.',
            )

            reuniao1 = ReuniaoConselhoGestor.objects.create(
                plano=plano1, numero_ata='001/2026', tipo='ordinaria', data_reuniao=date(2026, 2, 20),
                quorum_atingido=True,
                deliberacao='Aprovação do Plano de Aplicação FESP 2026, com recomendação de prioridade '
                'para equipamentos de proteção individual.',
                org_id=ssp, created_by=admin, updated_by=admin,
            )
            reuniao1.presentes.set([conselho[0], conselho[1], conselho[2], conselho[4]])

            plano1.status = 'aprovado_conselho'
            plano1.reuniao_aprovacao = reuniao1
            plano1.save(update_fields=['status', 'reuniao_aprovacao'])
            HistoricoPlanoAplicacao.objects.create(
                plano=plano1, status_anterior='submetido_conselho', status_novo='aprovado_conselho',
                usuario=admin, motivo='Aprovado em reunião ordinária nº 001/2026, conforme ata.',
            )
            self.ok('1 Plano de Aplicação FESP (aprovado_conselho) + 1 Reunião do Conselho + 3 históricos')

            plano2 = PlanoAplicacao.objects.create(
                natureza='convenio', exercicio_fiscal=2026,
                ementa='Modernização de Videomonitoramento — Convênio MJSP',
                descricao='Plano de aplicação dos recursos do Convênio SICONV-2026-000123 para '
                'ampliação da rede integrada de videomonitoramento urbano.',
                status='elaboracao',
                responsavel_gestao_nome=resp_nome, responsavel_elaboracao_nome=plan_ssp.get_full_name() or plan_ssp.username,
                valor_originario_investimento=Decimal('3850000.00'),
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            HistoricoPlanoAplicacao.objects.create(
                plano=plano2, status_anterior='', status_novo='elaboracao', usuario=plan_ssp, motivo='Plano criado',
            )
            plano2.status = 'aprovado'
            plano2.save(update_fields=['status'])
            HistoricoPlanoAplicacao.objects.create(
                plano=plano2, status_anterior='elaboracao', status_novo='aprovado',
                usuario=admin, motivo='Aprovação direta — rito simples (natureza convênio).',
            )
            plano2.status = 'publicado'
            plano2.save(update_fields=['status'])
            HistoricoPlanoAplicacao.objects.create(
                plano=plano2, status_anterior='aprovado', status_novo='publicado',
                usuario=admin, motivo='Publicação do Plano de Aplicação.',
            )
            self.ok('1 Plano de Aplicação — Convênio (publicado) + 3 históricos')

            me1 = MetaEspecifica.objects.create(
                plano=plano1, titulo='Aquisição de Equipamentos de Proteção Individual para '
                'Policiamento Motorizado',
                descricao_meta='Equipar policiais e bombeiros militares que atuam em policiamento '
                'motorizado com itens de proteção individual.',
                status='em_execucao',
                descricao_indicador='Percentual do efetivo de motopatrulhamento/moto-resgate com EPI completo e dentro da validade',
                formula_indicador='(efetivo equipado ÷ efetivo total de motopatrulhamento e moto-resgate) × 100',
                valor_referencia='62%', periodo_referencia='2026',
                fonte_indicador='Levantamento interno PMBA/CBMBA', periodicidade='semestral',
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            me2 = MetaEspecifica.objects.create(
                plano=plano1, titulo='Modernização de Videomonitoramento Urbano — Interior do Estado',
                descricao_meta='Ampliar a cobertura de câmeras de videomonitoramento integradas em '
                'municípios do interior.',
                status='planejada', periodicidade='anual',
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            me3 = MetaEspecifica.objects.create(
                plano=plano2, titulo='Aquisição de Câmeras e Equipamentos de Rede para '
                'Videomonitoramento Integrado',
                status='em_execucao', periodicidade='trimestral',
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            self.ok('3 Metas Específicas (2 no Plano FESP, 1 no Plano Convênio)')

            grupo1 = GrupoConsolidacaoItem.objects.create(
                plano=plano1, chave_agrupamento='42.50',
                titulo='Equipamentos de Sinalização para Policiamento Motorizado (PMBA + CBMBA)',
                descricao='Itens de colete de sinalização demandados por duas forças distintas para '
                'a mesma finalidade — consolidados em um único grupo de compra.',
                status='confirmado',
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )

            dem_pm = UnidadeOrganizacional.objects.filter(orgao=pm, sigla='DEM_PM').first()
            dem_cbm = UnidadeOrganizacional.objects.filter(orgao=cbm, sigla='DEM_CBM').first()

            cat_colete_pm = ItemCatalogo.objects.get(pk=304)
            cat_colete_cbm = ItemCatalogo.objects.get(pk=303)
            cat_capacete = ItemCatalogo.objects.get(pk=317)
            cat_camera = ItemCatalogo.objects.get(pk=10)
            cat_notebook = ItemCatalogo.objects.get(pk=4)

            ItemPlanoAplicacao.objects.create(
                meta_especifica=me1, instrumento=if1, org_beneficiaria=pm, unidade_beneficiaria=dem_pm,
                item_catalogo=cat_colete_pm, bem_servico='Colete refletivo de alta visibilidade — motopatrulhamento (ROCAM)',
                descricao=cat_colete_pm.descricao[:255] if cat_colete_pm.descricao else '',
                base_legal='Lei 14.169/2019, Art. 7º, I, "b"', natureza='custeio', unidade_medida='UN',
                quantidade=Decimal('200'), valor_unitario_estimado=Decimal('98.00'), aprovado=True,
                grupo_consolidacao=grupo1, status='consolidado',
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            ItemPlanoAplicacao.objects.create(
                meta_especifica=me1, instrumento=if1, org_beneficiaria=cbm, unidade_beneficiaria=dem_cbm,
                item_catalogo=cat_colete_cbm, bem_servico='Colete refletivo de alta visibilidade — moto-resgate',
                descricao=cat_colete_cbm.descricao[:255] if cat_colete_cbm.descricao else '',
                base_legal='Lei 14.169/2019, Art. 7º, I, "b"', natureza='custeio', unidade_medida='UN',
                quantidade=Decimal('120'), valor_unitario_estimado=Decimal('95.00'), aprovado=True,
                grupo_consolidacao=grupo1, status='consolidado',
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            ItemPlanoAplicacao.objects.create(
                meta_especifica=me1, instrumento=if1, org_beneficiaria=pm,
                item_catalogo=cat_capacete, bem_servico='Capacete fechado para motopatrulhamento',
                base_legal='Lei 14.169/2019, Art. 7º, I, "b"', natureza='investimento', unidade_medida='UN',
                quantidade=Decimal('150'), valor_unitario_estimado=Decimal('310.00'), aprovado=None,
                status='pendente',
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            ItemPlanoAplicacao.objects.create(
                meta_especifica=me2, instrumento=if1, org_beneficiaria=ssp,
                item_catalogo=cat_camera, bem_servico='Câmera de Videomonitoramento IP 4MP',
                destinacao='Central Integrada de Videomonitoramento — CICOM',
                base_legal='Lei 14.169/2019, Art. 7º, I, "a"', natureza='investimento', unidade_medida='UN',
                quantidade=Decimal('80'), valor_unitario_estimado=Decimal('1850.00'), aprovado=True,
                status='pendente',  # sem grupo: 'consolidado' deixava o item preso
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            ItemPlanoAplicacao.objects.create(
                meta_especifica=me3, instrumento=if2, org_beneficiaria=ssp,
                item_catalogo=cat_camera, bem_servico='Câmera de Videomonitoramento IP 4MP — Convênio MJSP',
                natureza='investimento', unidade_medida='UN',
                quantidade=Decimal('200'), valor_unitario_estimado=Decimal('1780.00'), aprovado=True,
                status='pendente',  # sem grupo: 'consolidado' deixava o item preso
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            ItemPlanoAplicacao.objects.create(
                meta_especifica=me3, instrumento=if2, org_beneficiaria=ssp,
                item_catalogo=cat_notebook,
                bem_servico='Notebook Dell Latitude 5540 i5/16GB/512GB — estações de monitoramento',
                natureza='investimento', unidade_medida='UN',
                quantidade=Decimal('25'), valor_unitario_estimado=Decimal('4200.00'), aprovado=True,
                status='pendente',  # sem grupo: 'consolidado' deixava o item preso
                org_id=ssp, created_by=plan_ssp, updated_by=plan_ssp,
            )
            self.ok('6 Itens do Plano de Aplicação + 1 Grupo de Consolidação')

        # ═══════════════════════════════════════════════════════════════════
        self.sec('ARP — Atas de Registro de Preços')

        if Ata.objects.exists():
            self.skip('já existem Atas — pulando bloco ARP')
        else:
            proc_homologado = Procedimento.objects.get(numero='PE-CLIC-001/2025')

            ata1 = Ata.objects.create(
                tipo_origem='gerenciador', numero_ata='ARP-SSP-2025/001', procedimento=proc_homologado,
                status='vigente', objeto='Registro de preços para aquisição de material de escritório e expediente',
                data_assinatura=date(2025, 12, 1), data_vigencia_inicio=date(2025, 12, 1),
                data_vigencia_fim=date(2026, 12, 1),
                org_id=ssp, created_by=analista, updated_by=analista,
            )
            HistoricoAta.objects.create(ata=ata1, status_anterior='rascunho', status_novo='vigente',
                                         usuario=admin, motivo='Ata assinada e publicada.')
            ItemAta.objects.create(
                ata=ata1, objeto='Papel A4 75g/m² — resma 500 folhas', unidade_medida='RESMA',
                fornecedor=forn1, quantidade_registrada=Decimal('5000'),
                valor_unitario_registrado=Decimal('22.50'), quantidade_consumida=Decimal('1200'),
            )
            ItemAta.objects.create(
                ata=ata1, objeto='Toner para impressora multifuncional', unidade_medida='UN',
                fornecedor=forn2, quantidade_registrada=Decimal('300'),
                valor_unitario_registrado=Decimal('180.00'), quantidade_consumida=Decimal('45'),
            )

            ata2 = Ata.objects.create(
                tipo_origem='carona', numero_ata='(externa)', numero_pncp='90000001/2025',
                orgao_gerenciador_nome='Secretaria de Administração do Estado da Bahia — SAEB',
                orgao_gerenciador_cnpj='13.937.130/0001-70', orgao_gerenciador_uf='BA',
                status='vigente',
                objeto='Registro de preços para aquisição de coletes e equipamentos de sinalização '
                'para motopatrulhamento — adesão como órgão não participante (carona), art. 86, § 2º, da Lei 14.133/2021.',
                data_vigencia_inicio=date(2026, 1, 1), data_vigencia_fim=date(2026, 12, 31),
                org_id=pm, created_by=plan_ssp, updated_by=plan_ssp,
            )
            HistoricoAta.objects.create(ata=ata2, status_anterior='rascunho', status_novo='vigente',
                                         usuario=plan_ssp, motivo='Adesão formalizada e ata vigente.')
            ItemAta.objects.create(
                ata=ata2, item_catalogo=ItemCatalogo.objects.get(pk=304),
                objeto='Colete refletivo de alta visibilidade — motopatrulhamento', unidade_medida='UN',
                fornecedor=forn1, quantidade_registrada=Decimal('500'),
                valor_unitario_registrado=Decimal('98.00'), quantidade_consumida=Decimal('120'),
            )

            ata3 = Ata.objects.create(
                tipo_origem='participante', numero_ata='ARP-SSP-2025/001', numero_pncp='',
                orgao_gerenciador_nome='SSP-BA', orgao_gerenciador_uf='BA',
                status='vigente',
                objeto='Registro de preços para aquisição de material de escritório e expediente — '
                'participação em cota própria (Corpo de Bombeiros Militar).',
                data_vigencia_inicio=date(2025, 12, 1), data_vigencia_fim=date(2026, 12, 1),
                org_id=cbm, created_by=plan_ssp, updated_by=plan_ssp,
            )
            HistoricoAta.objects.create(ata=ata3, status_anterior='rascunho', status_novo='vigente',
                                         usuario=plan_ssp, motivo='Cota própria confirmada na formação da ata.')
            ItemAta.objects.create(
                ata=ata3, objeto='Papel A4 75g/m² — resma 500 folhas', unidade_medida='RESMA',
                fornecedor=forn1, quantidade_registrada=Decimal('1500'),
                valor_unitario_registrado=Decimal('22.50'), quantidade_consumida=Decimal('300'),
            )

            self.ok('3 Atas de Registro de Preços (gerenciador/carona/participante) + 4 Itens + 3 históricos')

        self.stdout.write(self.style.SUCCESS('\nConcluído.'))
