"""
Cria (ou atualiza) as 37 seções oficiais do checklist PGE-BA do TR
(OS PA 017/2025) via migração de dados — mesmo conteúdo de
`seed_secoes_tr.py`, mas rodando automaticamente em qualquer ambiente
(inclusive produção, via `migrate --noinput` no deploy).

Descoberto em 01/09/2026: `seed_secoes_tr.py` é um script standalone, nunca
executado em produção — as seções de TR foram adicionadas ao `setup_dev.py`
DEPOIS da única vez que ele rodou lá (RUN_SETUP_DEV=True), então produção
tinha 0 seções de TR cadastradas, enquanto DFD/ETP já estavam populados.
A migração 0020 (correção de `ordem` duplicada) não teve efeito nesse
ambiente por não haver linhas para atualizar.
"""
from django.db import migrations

BENS     = ['bens', 'hibrido']
SERVICOS = ['servicos', 'servicos_engenharia', 'hibrido']

SECOES_TR = [
    # (codigo, titulo, descricao, ordem, obrigatorio, aplica_tipo_objeto, ativo)
    ('cond_gerais', '1. Condições Gerais da Contratação',
     'Tipo de objeto, prazo de vigência e flags gerais (contratação delegada, SRP).',
     1, True, [], True),
    ('objeto', '2. Objeto da Contratação',
     'Descrição precisa e completa do objeto. Para bens: especificações técnicas. Para serviços: escopo da prestação.',
     2, True, [], True),
    ('fundamentacao', '3. Fundamentação e Descrição da Necessidade',
     'Justificativa da contratação e caracterização do objeto como comum ou não. Remissão ao ETP quando obrigatório.',
     3, True, [], True),
    ('solucao', '4. Descrição da Solução (ciclo de vida)',
     'Descrição da solução escolhida considerando o ciclo de vida do objeto. Remissão ao ETP quando obrigatório.',
     4, False, [], True),

    ('req_sustentabilidade', '5.1 Critérios de Sustentabilidade',
     'Definir se há critérios de sustentabilidade exigidos. Se sim, listar os critérios conforme justificativa no processo (art. 11, IV, Lei 14.133/2021).',
     5, False, [], True),
    ('req_marca', '5.2 Indicação de Marca ou Modelo',
     'Indicar se haverá especificação de marca. Se sim, incluir justificativa técnica obrigatória (art. 41, I, Lei 14.133/2021).',
     6, False, [], True),
    ('req_exame', '5.3 Exame de Adequação do Objeto',
     'Definir se será exigido exame de adequação: amostra, exame de conformidade, prova de conceito ou certificação CONMETRO (art. 17, §3º).',
     7, False, [], True),
    ('req_vistoria', '5.4 Vistoria Prévia',
     'Indicar se será exigida vistoria prévia, obrigatória ou facultativa. Se obrigatória, informar endereço, horário e responsável (art. 63, §2º).',
     8, False, [], True),
    ('req_subcontratacao', '5.5 Subcontratação',
     'Definir se subcontratação será admitida (parcial). Se sim, indicar parcelas permitidas. Pode incluir obrigação de subcontratar ME/EPP (art. 48, II, LC 123/2006).',
     9, False, [], True),
    ('req_garantia_prop', '5.6.1 Garantia de Proposta',
     'Indicar se será exigida garantia de proposta (art. 58, Lei 14.133/2021).',
     10, False, [], True),
    ('req_garantia_contr', '5.6.2 Garantia da Contratação',
     'Indicar se será exigida garantia da contratação, percentual (até 5%; até 10% justificado) e modalidade aceita (art. 96, Lei 14.133/2021).',
     11, False, [], True),

    ('prazo_vigencia', '6. Forma de Execução e Prazo de Vigência',
     'Selecionar: por escopo (Art. 105), contínuo (Art. 106/107), emergencial (Art. 75, VIII) ou Art. 108. Informar prazo em meses e instrumento de início.',
     12, True, [], True),
    ('local_entrega', '7. Local de Entrega / Execução',
     'Para bens: endereço e horário de entrega. Para serviços: local(is) de execução, horários, periodicidade.',
     13, True, [], True),

    ('bens_nao_luxo', 'Bens — Declaração de Não Bem de Luxo',
     'O objeto não se enquadra como bem de luxo nos termos do art. 20 da Lei Federal nº 14.133/2021 e sua regulamentação.',
     14, False, BENS, True),
    ('bens_reserva_cota', 'Bens — Reserva de Cota ME/EPP',
     'Para bens de natureza divisível: indicar se haverá reserva de cota (≤25%) para microempresas e EPP (art. 48, III, LC 123/2006). Informar percentual.',
     15, False, BENS, True),
    ('bens_carta_solidariedade', 'Bens — Carta de Solidariedade do Fabricante',
     'Para licitantes revendedores/distribuidores: indicar se será exigida carta de solidariedade do fabricante garantindo o fornecimento.',
     16, False, BENS, True),
    ('bens_validade', 'Bens — Validade de Produtos Perecíveis',
     'Para produtos com prazo de validade: informar validade mínima exigida a contar da data de entrega.',
     17, False, BENS, True),
    ('bens_garantia_tecnica', 'Bens — Garantia Técnica e Assistência',
     'Prazo de garantia técnica (meses), obrigações de assistência técnica, manutenção corretiva e substituição de peças defeituosas.',
     18, False, BENS, True),

    ('serv_transicao', 'Serviços — Transição Contratual',
     'Indicar se a contratada deverá realizar transição contratual com transferência de conhecimento, tecnologia e técnicas empregadas ao fim do contrato.',
     19, False, SERVICOS, True),
    ('serv_regime_execucao', 'Serviços — Regime de Execução',
     'Cronograma de realização, horários permitidos, frequência, forma de execução (empreitada por preço global/unitário, tarefa) e condições específicas.',
     20, False, SERVICOS, True),
    ('serv_materiais', 'Serviços — Materiais e Equipamentos',
     'Relação de materiais, equipamentos, ferramentas e instalações que a contratada deverá disponibilizar durante a execução.',
     21, False, SERVICOS, True),
    ('serv_qualificacao', 'Serviços — Qualificação Técnica',
     'Comprovação de capacitação técnico-operacional mediante certidões ou atestados do conselho profissional competente. Parcelas de maior relevância e valor significativo.',
     22, True, SERVICOS, True),
    ('serv_parcelas_relevancia', 'Serviços — Parcelas de Maior Relevância',
     'Identificação das parcelas de maior relevância técnica e/ou valor significativo para fins de qualificação técnica (quantitativo mínimo e comprovação exigida).',
     23, False, SERVICOS, True),

    ('modelo_gestao', '10. Modelo de Gestão do Contrato',
     'Procedimentos para recebimento provisório e definitivo. Para serviços: prazo contado da comunicação escrita da contratada e procedimentos estruturados (a→e).',
     24, True, [], True),
    ('obrigacoes_contratada', '11. Obrigações da Contratada',
     'Listagem das obrigações da parte contratada durante a execução do contrato.',
     25, True, [], True),
    ('obrigacoes_contratante', '12. Obrigações da Contratante',
     'Listagem das obrigações da Administração durante a execução do contrato.',
     26, True, [], True),

    ('criterios_medicao', '13.1 Critérios de Medição e Pagamento',
     'Forma de aferição da execução, periodicidade de medição, documentos exigidos para faturamento e prazo para pagamento.',
     27, True, [], True),
    ('criterios_selecao', '13.2 Critérios de Seleção do Fornecedor',
     'Tipo de julgamento (menor preço, maior desconto, melhor técnica, etc.) e critérios de desempate.',
     28, True, [], True),

    ('hab_juridica', '14.1 Habilitação Jurídica',
     'Documentos de constituição da pessoa jurídica: contrato social, estatuto, ata de eleição de diretoria (conforme o caso).',
     29, True, [], True),
    ('hab_fiscal', '14.2 Habilitação Fiscal, Social e Trabalhista',
     'CNPJ, cadastro de contribuinte estadual ou municipal (conforme esfera definida), regularidade fiscal federal, FGTS e Justiça do Trabalho.',
     30, True, [], True),
    ('hab_economica', '14.3 Habilitação Econômico-Financeira',
     'Certidão negativa de falência/recuperação judicial. Para contratos de grande vulto: índices contábeis mínimos.',
     31, False, [], True),
    ('hab_tecnica_bens', '14.4 Qualificação Técnica — Bens',
     'Para bens: declaração de pleno conhecimento das condições de fornecimento (com ou sem vistoria prévia).',
     32, False, BENS, True),
    ('hab_tecnica_servicos', '14.5 Qualificação Técnica — Serviços',
     'Para serviços: comprovação de capacitação técnico-operacional mediante certidões/atestados do conselho profissional. Inscrição no conselho competente. Visto de registro na Bahia se sediado em outra UF.',
     33, False, SERVICOS, True),

    ('estimativa_valor', '15. Estimativa do Valor da Contratação',
     'Valor estimado global da contratação e metodologia de apuração. Remissão ao Mapa Comparativo de Preços quando aprovado.',
     34, True, [], True),
    ('adequacao_orcamentaria', '16. Adequação Orçamentária',
     'Indicação dos recursos orçamentários que suportarão a despesa: ação, elemento, natureza e fonte de recurso.',
     35, False, [], True),
    ('parcelamento_etp', '17. Parcelamento e Adjudicação (ETP)',
     'Decisão sobre parcelamento em lotes/itens ou contratação global, com justificativa. Remissão ao ETP.',
     36, False, [], True),
    ('lotes', '18. Formação de Lotes da Licitação',
     'Tabela de lotes com itens, quantidades, valores de referência e modalidade de participação (ampla, cota ME/EPP, exclusivo ME/EPP).',
     37, False, [], True),
    ('observacoes', '19. Observações Gerais',
     'Informações complementares não contempladas nas demais seções.',
     38, False, [], False),
]


def seedar(apps, schema_editor):
    SecaoArtefato = apps.get_model('core', 'SecaoArtefato')
    for codigo, titulo, descricao, ordem, obrigatorio, aplica_tipo_objeto, ativo in SECOES_TR:
        SecaoArtefato.objects.update_or_create(
            tipo='TR', codigo=codigo,
            defaults=dict(
                titulo=titulo,
                descricao=descricao,
                ordem=ordem,
                ativo=ativo,
                obrigatorio=obrigatorio,
                aplica_modalidades=[],
                aplica_tipo_objeto=aplica_tipo_objeto,
            ),
        )


def reverter(apps, schema_editor):
    # Não remove — pode já existir conteúdo/uso real associado à seção.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_fix_ordem_secoes_tr'),
    ]

    operations = [
        migrations.RunPython(seedar, reverter),
    ]
