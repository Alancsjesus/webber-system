from django.core.management.base import BaseCommand
from modulo_orcamento.models import ElementoDespesa

# Elementos de despesa — Portaria Interministerial STN/SOF nº 163/2001, Anexo II.
# Elemento tem 2 dígitos; 4.4.90.52 (categoria.grupo.modalidade.elemento) é a NATUREZA.
ELEMENTOS = [
    (1, 'Aposentadorias do RPPS, Reserva Remunerada e Reformas dos Militares'),
    (3, 'Pensões do RPPS e do Militar'),
    (4, 'Contratação por Tempo Determinado'),
    (5, 'Outros Benefícios Previdenciários do Servidor ou do Militar'),
    (6, 'Benefício Mensal ao Deficiente e ao Idoso'),
    (7, 'Contribuição a Entidades Fechadas de Previdência'),
    (8, 'Outros Benefícios Assistenciais do Servidor e do Militar'),
    (9, 'Salário-Família'),
    (10, 'Seguro Desemprego e Abono Salarial'),
    (11, 'Vencimentos e Vantagens Fixas - Pessoal Civil'),
    (12, 'Vencimentos e Vantagens Fixas - Pessoal Militar'),
    (13, 'Obrigações Patronais'),
    (14, 'Diárias - Civil'),
    (15, 'Diárias - Militar'),
    (16, 'Outras Despesas Variáveis - Pessoal Civil'),
    (17, 'Outras Despesas Variáveis - Pessoal Militar'),
    (18, 'Auxílio Financeiro a Estudantes'),
    (19, 'Auxílio-Fardamento'),
    (20, 'Auxílio Financeiro a Pesquisadores'),
    (21, 'Juros sobre a Dívida por Contrato'),
    (22, 'Outros Encargos sobre a Dívida por Contrato'),
    (23, 'Juros, Deságios e Descontos da Dívida Mobiliária'),
    (24, 'Outros Encargos sobre a Dívida Mobiliária'),
    (25, 'Encargos sobre Operações de Crédito por Antecipação da Receita'),
    (26, 'Obrigações Decorrentes de Política Monetária'),
    (27, 'Encargos pela Honra de Avais, Garantias, Seguros e Similares'),
    (28, 'Remuneração de Cotas de Fundos Autárquicos'),
    (29, 'Distribuição de Resultado de Empresas Estatais Dependentes'),
    (30, 'Material de Consumo'),
    (31, 'Premiações Culturais, Artísticas, Científicas, Desportivas e Outras'),
    (32, 'Material, Bem ou Serviço para Distribuição Gratuita'),
    (33, 'Passagens e Despesas com Locomoção'),
    (34, 'Outras Despesas de Pessoal Decorrentes de Contratos de Terceirização'),
    (35, 'Serviços de Consultoria'),
    (36, 'Outros Serviços de Terceiros - Pessoa Física'),
    (37, 'Locação de Mão-de-Obra'),
    (38, 'Arrendamento Mercantil'),
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

# Códigos de 5 dígitos criados por seeds antigos (pedaço da natureza, não elemento)
# → elemento correto. As dotações/naturezas são remapeadas e o código legado sai.
LEGADOS = {
    33901: 37, 33903: 33, 33904: 4, 33913: 13, 33914: 14, 33930: 30, 33931: 31,
    33936: 36, 33939: 39, 44905: 52, 44906: 38, 44909: 40,
}


class Command(BaseCommand):
    help = 'Popula ElementoDespesa (Portaria STN/SOF 163/2001) e normaliza códigos legados'

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

        remapeados = 0
        for legado, oficial in LEGADOS.items():
            velho = ElementoDespesa.objects.filter(codigo=legado).first()
            if velho is None:
                continue
            novo = ElementoDespesa.objects.get(codigo=oficial)
            remapeados += velho.dotacoes.update(elemento_despesa=novo)
            velho.naturezas.update(elemento_despesa=novo)
            velho.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Elementos de Despesa: {criados} criados, {atualizados} atualizados, '
                f'{remapeados} dotação(ões) remapeada(s) de códigos legados.'
            )
        )
