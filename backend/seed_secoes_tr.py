"""
Insere/atualiza as seções do TR conforme modelos padronizados PGE-BA (OS PA 017/2025).
Execute: python seed_secoes_tr.py
"""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import SecaoArtefato

BENS     = ['bens', 'hibrido']
SERVICOS = ['servicos', 'servicos_engenharia', 'hibrido']
TODOS    = []

def upsert(codigo, titulo, descricao, ordem, obrigatorio=False,
           aplica_modalidades=None, aplica_tipo_objeto=None, ativo=True):
    obj, criado = SecaoArtefato.objects.update_or_create(
        tipo='TR', codigo=codigo,
        defaults=dict(
            titulo=titulo,
            descricao=descricao,
            ordem=ordem,
            ativo=ativo,
            obrigatorio=obrigatorio,
            aplica_modalidades=aplica_modalidades or [],
            aplica_tipo_objeto=aplica_tipo_objeto or [],
        )
    )
    status = 'CRIADO' if criado else 'ATUALIZADO'
    print(f'  [{status}] {ordem:04.1f} — {codigo}: {titulo}')

print('=== Seções comuns (todas as modalidades e tipos) ===')
upsert('cond_gerais',  '1. Condições Gerais da Contratação',
       'Tipo de objeto, prazo de vigência e flags gerais (contratação delegada, SRP).',
       1, obrigatorio=True)

upsert('objeto',       '2. Objeto da Contratação',
       'Descrição precisa e completa do objeto. Para bens: especificações técnicas. Para serviços: escopo da prestação.',
       2, obrigatorio=True)

upsert('fundamentacao','3. Fundamentação e Descrição da Necessidade',
       'Justificativa da contratação e caracterização do objeto como comum ou não. Remissão ao ETP quando obrigatório.',
       3, obrigatorio=True)

upsert('solucao',      '4. Descrição da Solução (ciclo de vida)',
       'Descrição da solução escolhida considerando o ciclo de vida do objeto. Remissão ao ETP quando obrigatório.',
       4)

# Nota: `ordem` é PositiveIntegerField — os números fracionários abaixo (5.1, 5.2,
# 8.1...) existem só no TÍTULO da seção, espelhando a numeração do checklist
# PGE-BA. O campo `ordem` em si precisa ser inteiro e sequencial único (senão o
# Django trunca o valor e várias seções acabam empatadas na mesma posição,
# quebrando a reordenação ▲▼ em Configurações → Estrutura de Artefatos).
print()
print('=== Seção 5 — Requisitos parametrizáveis ===')
upsert('req_sustentabilidade', '5.1 Critérios de Sustentabilidade',
       'Definir se há critérios de sustentabilidade exigidos. Se sim, listar os critérios conforme justificativa no processo (art. 11, IV, Lei 14.133/2021).',
       5)

upsert('req_marca',    '5.2 Indicação de Marca ou Modelo',
       'Indicar se haverá especificação de marca. Se sim, incluir justificativa técnica obrigatória (art. 41, I, Lei 14.133/2021).',
       6)

upsert('req_exame',    '5.3 Exame de Adequação do Objeto',
       'Definir se será exigido exame de adequação: amostra, exame de conformidade, prova de conceito ou certificação CONMETRO (art. 17, §3º).',
       7)

upsert('req_vistoria', '5.4 Vistoria Prévia',
       'Indicar se será exigida vistoria prévia, obrigatória ou facultativa. Se obrigatória, informar endereço, horário e responsável (art. 63, §2º).',
       8)

upsert('req_subcontratacao', '5.5 Subcontratação',
       'Definir se subcontratação será admitida (parcial). Se sim, indicar parcelas permitidas. Pode incluir obrigação de subcontratar ME/EPP (art. 48, II, LC 123/2006).',
       9)

upsert('req_garantia_prop', '5.6.1 Garantia de Proposta',
       'Indicar se será exigida garantia de proposta (art. 58, Lei 14.133/2021).',
       10)

upsert('req_garantia_contr', '5.6.2 Garantia da Contratação',
       'Indicar se será exigida garantia da contratação, percentual (até 5%; até 10% justificado) e modalidade aceita (art. 96, Lei 14.133/2021).',
       11)

print()
print('=== Seção 6 — Modelo de execução ===')
upsert('prazo_vigencia', '6. Forma de Execução e Prazo de Vigência',
       'Selecionar: por escopo (Art. 105), contínuo (Art. 106/107), emergencial (Art. 75, VIII) ou Art. 108. Informar prazo em meses e instrumento de início.',
       12, obrigatorio=True)

upsert('local_entrega', '7. Local de Entrega / Execução',
       'Para bens: endereço e horário de entrega. Para serviços: local(is) de execução, horários, periodicidade.',
       13, obrigatorio=True)

print()
print('=== Seção específica — BENS ===')
upsert('bens_nao_luxo', 'Bens — Declaração de Não Bem de Luxo',
       'O objeto não se enquadra como bem de luxo nos termos do art. 20 da Lei Federal nº 14.133/2021 e sua regulamentação.',
       14, aplica_tipo_objeto=BENS)

upsert('bens_reserva_cota', 'Bens — Reserva de Cota ME/EPP',
       'Para bens de natureza divisível: indicar se haverá reserva de cota (≤25%) para microempresas e EPP (art. 48, III, LC 123/2006). Informar percentual.',
       15, aplica_tipo_objeto=BENS)

upsert('bens_carta_solidariedade', 'Bens — Carta de Solidariedade do Fabricante',
       'Para licitantes revendedores/distribuidores: indicar se será exigida carta de solidariedade do fabricante garantindo o fornecimento.',
       16, aplica_tipo_objeto=BENS)

upsert('bens_validade', 'Bens — Validade de Produtos Perecíveis',
       'Para produtos com prazo de validade: informar validade mínima exigida a contar da data de entrega.',
       17, aplica_tipo_objeto=BENS)

upsert('bens_garantia_tecnica', 'Bens — Garantia Técnica e Assistência',
       'Prazo de garantia técnica (meses), obrigações de assistência técnica, manutenção corretiva e substituição de peças defeituosas.',
       18, aplica_tipo_objeto=BENS)

print()
print('=== Seção específica — SERVIÇOS ===')
upsert('serv_transicao', 'Serviços — Transição Contratual',
       'Indicar se a contratada deverá realizar transição contratual com transferência de conhecimento, tecnologia e técnicas empregadas ao fim do contrato.',
       19, aplica_tipo_objeto=SERVICOS)

upsert('serv_regime_execucao', 'Serviços — Regime de Execução',
       'Cronograma de realização, horários permitidos, frequência, forma de execução (empreitada por preço global/unitário, tarefa) e condições específicas.',
       20, aplica_tipo_objeto=SERVICOS)

upsert('serv_materiais', 'Serviços — Materiais e Equipamentos',
       'Relação de materiais, equipamentos, ferramentas e instalações que a contratada deverá disponibilizar durante a execução.',
       21, aplica_tipo_objeto=SERVICOS)

upsert('serv_qualificacao', 'Serviços — Qualificação Técnica',
       'Comprovação de capacitação técnico-operacional mediante certidões ou atestados do conselho profissional competente. Parcelas de maior relevância e valor significativo.',
       22, aplica_tipo_objeto=SERVICOS, obrigatorio=True)

upsert('serv_parcelas_relevancia', 'Serviços — Parcelas de Maior Relevância',
       'Identificação das parcelas de maior relevância técnica e/ou valor significativo para fins de qualificação técnica (quantitativo mínimo e comprovação exigida).',
       23, aplica_tipo_objeto=SERVICOS)

print()
print('=== Seção 10 — Modelo de gestão do contrato ===')
upsert('modelo_gestao', '10. Modelo de Gestão do Contrato',
       'Procedimentos para recebimento provisório e definitivo. Para serviços: prazo contado da comunicação escrita da contratada e procedimentos estruturados (a→e).',
       24, obrigatorio=True)

upsert('obrigacoes_contratada', '11. Obrigações da Contratada',
       'Listagem das obrigações da parte contratada durante a execução do contrato.',
       25, obrigatorio=True)

upsert('obrigacoes_contratante', '12. Obrigações da Contratante',
       'Listagem das obrigações da Administração durante a execução do contrato.',
       26, obrigatorio=True)

print()
print('=== Seção 13 — Pagamento ===')
upsert('criterios_medicao', '13.1 Critérios de Medição e Pagamento',
       'Forma de aferição da execução, periodicidade de medição, documentos exigidos para faturamento e prazo para pagamento.',
       27, obrigatorio=True)

upsert('criterios_selecao', '13.2 Critérios de Seleção do Fornecedor',
       'Tipo de julgamento (menor preço, maior desconto, melhor técnica, etc.) e critérios de desempate.',
       28, obrigatorio=True)

print()
print('=== Seção 14 — Habilitação ===')
upsert('hab_juridica', '14.1 Habilitação Jurídica',
       'Documentos de constituição da pessoa jurídica: contrato social, estatuto, ata de eleição de diretoria (conforme o caso).',
       29, obrigatorio=True)

upsert('hab_fiscal', '14.2 Habilitação Fiscal, Social e Trabalhista',
       'CNPJ, cadastro de contribuinte estadual ou municipal (conforme esfera definida), regularidade fiscal federal, FGTS e Justiça do Trabalho.',
       30, obrigatorio=True)

upsert('hab_economica', '14.3 Habilitação Econômico-Financeira',
       'Certidão negativa de falência/recuperação judicial. Para contratos de grande vulto: índices contábeis mínimos.',
       31)

upsert('hab_tecnica_bens', '14.4 Qualificação Técnica — Bens',
       'Para bens: declaração de pleno conhecimento das condições de fornecimento (com ou sem vistoria prévia).',
       32, aplica_tipo_objeto=BENS)

upsert('hab_tecnica_servicos', '14.5 Qualificação Técnica — Serviços',
       'Para serviços: comprovação de capacitação técnico-operacional mediante certidões/atestados do conselho profissional. Inscrição no conselho competente. Visto de registro na Bahia se sediado em outra UF.',
       33, aplica_tipo_objeto=SERVICOS)

print()
print('=== Seções finais ===')
upsert('estimativa_valor', '15. Estimativa do Valor da Contratação',
       'Valor estimado global da contratação e metodologia de apuração. Remissão ao Mapa Comparativo de Preços quando aprovado.',
       34, obrigatorio=True)

upsert('adequacao_orcamentaria', '16. Adequação Orçamentária',
       'Indicação dos recursos orçamentários que suportarão a despesa: ação, elemento, natureza e fonte de recurso.',
       35)

upsert('parcelamento_etp', '17. Parcelamento e Adjudicação (ETP)',
       'Decisão sobre parcelamento em lotes/itens ou contratação global, com justificativa. Remissão ao ETP.',
       36)

upsert('lotes', '18. Formação de Lotes da Licitação',
       'Tabela de lotes com itens, quantidades, valores de referência e modalidade de participação (ampla, cota ME/EPP, exclusivo ME/EPP).',
       37)

upsert('observacoes', '19. Observações Gerais',
       'Informações complementares não contempladas nas demais seções.',
       38, ativo=False)

print()
total = SecaoArtefato.objects.filter(tipo='TR').count()
print(f'Total de seções TR: {total}')
print()
print('Seções por tipo de objeto:')
for t in ['', 'bens', 'servicos', 'servicos_engenharia', 'hibrido']:
    if t:
        n = SecaoArtefato.objects.filter(tipo='TR', aplica_tipo_objeto__contains=t).count()
        print(f'  {t}: {n} seção(ões) específica(s)')
    else:
        n = SecaoArtefato.objects.filter(tipo='TR', aplica_tipo_objeto=[]).count()
        print(f'  todas: {n} seção(ões) comuns')
