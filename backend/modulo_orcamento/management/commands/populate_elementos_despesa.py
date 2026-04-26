from django.core.management.base import BaseCommand
from modulo_orcamento.models import ElementoDespesa

ELEMENTOS = [
    (39, 'Outros Serviços de Terceiros - Pessoa Jurídica'),
    (40, 'Serviços de Tecnologia da Informação e Comunicação - Pessoa Jurídica'),
    (41, 'Contribuições'),
    (42, 'Auxílios'),
    (43, 'Subvenções Sociais'),
    (45, 'Subvenções Econômicas'),
    (46, 'Auxílio - Alimentação'),
    (47, 'Obrigações Tributárias e Contributivas'),
    (48, 'Outros Auxílios Financeiros a Pessoas Físicas'),
    (49, 'Auxílio - Transporte'),
    (51, 'Obras e Instalações'),
    (52, 'Equipamento e Material Permanente'),
    (59, 'Pensões Especiais'),
    (61, 'Aquisição de Imóveis'),
    (62, 'Aquisição de Produtos para Revenda'),
    (63, 'Aquisição de Títulos de Crédito'),
    (64, 'Aquisição de Títulos Representativos de Capital já Integralizado'),
    (65, 'Constituição ou Aumento de Capital de Empresas'),
    (66, 'Concessão de Empréstimos e Financiamentos'),
    (67, 'Depósitos Compulsórios'),
    (70, 'Rateio pela participação em Consórcio Público'),
    (71, 'Principal da Dívida Contratual Resgatado'),
    (72, 'Principal da Dívida Mobiliária Resgatado'),
    (73, 'Correção Monetária ou Cambial da Dívida Contratual Resgatada'),
    (74, 'Correção Monetária ou Cambial da Dívida Mobiliária Resgatada'),
    (75, 'Correção Monetária da Dívida de Operações de Crédito por Antecipação da Receita'),
    (76, 'Principal Corrigido da Dívida Mobiliária Refinanciado'),
    (77, 'Principal Corrigido da Dívida Contratual Refinanciado'),
    (81, 'Distribuição Constitucional ou Legal de Receitas'),
    (82, 'Aporte de Recursos pelo Parceiro Público em Favor do Parceiro Privado Decorrente de Contrato de PPP'),
    (83, 'Despesas Decorrentes de Contrato de PPP, Exceto Subvenções Econômicas, Aporte e Fundo Garantidor'),
    (84, 'Despesas Decorrentes da Participação em Fundo, Organismo ou Entidade Assemelhada, Nacional e Internacional'),
    (85, 'Contrato de Gestão'),
    (86, 'Compensações a Regimes de Previdência'),
    (91, 'Sentenças Judiciais'),
    (92, 'Despesas de Exercícios Anteriores'),
    (93, 'Indenizações e Restituições'),
    (94, 'Indenizações e Restituições Trabalhistas'),
    (95, 'Indenização pela Execução de Trabalhos de Campo'),
    (96, 'Ressarcimento de Despesas de Pessoal Requisitado'),
    (97, 'Aporte para Cobertura do Déficit Atuarial do RPPS'),
    (98, 'Compensação do RGPS'),
    (99, 'A Classificar'),
]


class Command(BaseCommand):
    help = 'Popula ElementoDespesa com os códigos padronizados da Lei 14.133/2021'

    def handle(self, *args, **options):
        criados = 0
        atualizados = 0
        for codigo, descricao in ELEMENTOS:
            obj, created = ElementoDespesa.objects.get_or_create(
                codigo=codigo,
                defaults={'descricao': descricao, 'ativo': True},
            )
            if created:
                criados += 1
            else:
                if obj.descricao != descricao:
                    obj.descricao = descricao
                    obj.save(update_fields=['descricao'])
                    atualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Elementos de Despesa: {criados} criados, {atualizados} atualizados.'
            )
        )
