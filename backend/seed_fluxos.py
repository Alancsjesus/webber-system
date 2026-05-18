"""
Seed de dados para fluxos não cobertos.
Execute: python seed_fluxos.py
"""
import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from datetime import date
from django.contrib.auth.models import User
from core.models import Orgao, UnidadeOrganizacional
from modulo_demanda.models import DFD
from modulo_etp.models import ETP
from modulo_tr.models import TR
from modulo_licitacao.models import Procedimento
from modulo_contrato.models import Contrato

admin    = User.objects.get(username="admin")
analista = User.objects.get(username="analista_ssp")
gestor   = User.objects.get(username="gestor")

ssp  = Orgao.objects.get(sigla="SSP")
cbm  = Orgao.objects.get(sigla="CBMBA")
pmba = Orgao.objects.get(sigla="PMBA")

cplam = UnidadeOrganizacional.objects.get(sigla="CPLAM", orgao=ssp)
clic  = UnidadeOrganizacional.objects.filter(tipo="licitante",   orgao=ssp).first()
ccc   = UnidadeOrganizacional.objects.filter(tipo="contratante", orgao=ssp).first()

dfd1 = DFD.objects.get(id=1)   # Aprovada, SSP — notebooks/TI
dfd2 = DFD.objects.get(id=2)   # Aprovada, SSP — videomonitoramento
dfd3 = DFD.objects.get(id=3)   # Aprovada, SSP — manutenção predial
dfd4 = DFD.objects.get(id=4)   # Aprovada, CBMBA — kits IFAK

# ── helpers ─────────────────────────────────────────────────────────────────

def dfd_existe(desc_fragment):
    return DFD.objects.filter(descricao__icontains=desc_fragment).first()

def etp_existe(dfd):
    try: return dfd.etp
    except ETP.DoesNotExist: return None

def tr_existe(etp):
    try: return etp.tr
    except TR.DoesNotExist: return None

def proc_existe(objeto_fragment):
    return Procedimento.objects.filter(objeto__icontains=objeto_fragment).first()

def contrato_existe(objeto_fragment):
    return Contrato.objects.filter(objeto__icontains=objeto_fragment).first()

print("=" * 60)
print("=== ETPs nos estágios intermediários ===")
print("=" * 60)

# ── ETP Rascunho → DFD 3 (manutenção predial) ───────────────────────────────
if not etp_existe(dfd3):
    etp_rasc = ETP.objects.create(
        org_id=ssp, created_by=analista, updated_by=analista,
        dfd=dfd3,
        numero_sei="",
        necessidade_contratacao="Contratação de serviço de manutenção predial preventiva e corretiva.",
        requisitos_contratacao="Empresa com CREA/CAU ativo; mínimo 3 anos de experiência comprovada.",
        levantamento_mercado="Pesquisa em 3 fornecedores: R$ 180.000, R$ 195.000, R$ 210.000.",
        estimativa_valor=185000.00,
        descricao_solucao="Contratação via Pregão Eletrônico, serviço continuado 12 meses.",
        justificativa_solucao="Inexistência de servidores com qualificação técnica para execução direta.",
        riscos="Atraso na mobilização; mitigação: exigir início em até 10 dias úteis.",
        sustentabilidade="Uso de produtos com certificação ambiental.",
        tipo_objeto="servico_continuo",
        tipo_parcelamento="nao_parcelado",
        parcelamento_justificativa="Serviço de natureza unitária.",
        reserva_cota_me_epp=True,
        reserva_cota_justificativa="Compatível com capacidade operacional de ME/EPP.",
        licitacao_exclusiva_me_epp=False,
        status="Rascunho",
    )
    print(f"  [CRIADO] ETP Rascunho id={etp_rasc.id} (DFD {dfd3.id})")
else:
    print(f"  [JÁ EXISTE] ETP para DFD {dfd3.id}")
    etp_rasc = etp_existe(dfd3)

# ── ETP Submetido → DFD 4 (kits IFAK, CBMBA) ────────────────────────────────
if not etp_existe(dfd4):
    etp_sub = ETP.objects.create(
        org_id=cbm, created_by=analista, updated_by=analista,
        dfd=dfd4,
        numero_sei="001.2026/00123-4",
        necessidade_contratacao="Aquisição de materiais de primeiros socorros e kits IFAK para o CBMBA.",
        requisitos_contratacao="Materiais certificados ANVISA; validade mínima de 24 meses.",
        levantamento_mercado="3 distribuidores consultados: R$ 95.000, R$ 102.000, R$ 98.500.",
        estimativa_valor=96000.00,
        descricao_solucao="Aquisição via Pregão Eletrônico — registro de preços.",
        justificativa_solucao="Reposição de estoque esgotado; impacto direto na capacidade operacional.",
        riscos="Atraso na entrega; mitigação: entrega parcelada com prazo máximo de 30 dias.",
        sustentabilidade="Preferência por produtos com menor geração de resíduos plásticos.",
        tipo_objeto="material",
        tipo_parcelamento="parcelado",
        parcelamento_justificativa="Lotes permitem melhor gestão do estoque.",
        reserva_cota_me_epp=True,
        reserva_cota_justificativa="Valor por lote compatível com porte de ME/EPP.",
        licitacao_exclusiva_me_epp=False,
        status="Submetido",
    )
    print(f"  [CRIADO] ETP Submetido id={etp_sub.id} (DFD {dfd4.id})")
else:
    print(f"  [JÁ EXISTE] ETP para DFD {dfd4.id}")
    etp_sub = etp_existe(dfd4)

# ── DFD auxiliar + ETP Em Análise ────────────────────────────────────────────
dfd_mob = dfd_existe("mobiliário e equipamentos para reforma")
if not dfd_mob:
    dfd_mob = DFD.objects.create(
        org_id=ssp, created_by=analista, updated_by=analista,
        numero_sei="001.2026/00200-5",
        descricao="Aquisição de mobiliário e equipamentos para reforma das salas operacionais da SSP",
        status="Aprovada",
        valor_estimado=320000.00,
        area_aplicacao=["TI"],
        prazo_necessidade=date(2026, 9, 30),
        modalidade_aquisicao="licitacao",
        org_gestor=ssp,
        unidade_demandante=cplam,
    )
    print(f"  [CRIADO] DFD auxiliar id={dfd_mob.id}")
else:
    print(f"  [JÁ EXISTE] DFD mobiliário id={dfd_mob.id}")

if not etp_existe(dfd_mob):
    etp_anl = ETP.objects.create(
        org_id=ssp, created_by=analista, updated_by=analista,
        dfd=dfd_mob,
        numero_sei="001.2026/00200-6",
        necessidade_contratacao="Aquisição de mobiliário ergonômico e equipamentos de TI para as salas operacionais.",
        requisitos_contratacao="Mobiliário INMETRO; equipamentos com garantia mínima de 36 meses.",
        levantamento_mercado="4 fornecedores consultados; média de R$ 310.000.",
        estimativa_valor=312000.00,
        descricao_solucao="Pregão Eletrônico com adjudicação por lote.",
        justificativa_solucao="Laudo técnico de vistoria apontou precariedade das instalações.",
        riscos="Descontinuidade de modelos; mitigação: aceitar equivalentes técnicos comprovados.",
        sustentabilidade="Preferência por mobiliário com certificação FSC.",
        tipo_objeto="material",
        tipo_parcelamento="parcelado",
        parcelamento_justificativa="Lotes separados para mobiliário (L1) e equipamentos TI (L2).",
        reserva_cota_me_epp=False,
        reserva_cota_justificativa="Valor total inviabiliza participação exclusiva de ME/EPP.",
        licitacao_exclusiva_me_epp=False,
        status="Em Análise",
    )
    print(f"  [CRIADO] ETP Em Análise id={etp_anl.id} (DFD {dfd_mob.id})")
else:
    print(f"  [JÁ EXISTE] ETP para DFD mobiliário")
    etp_anl = etp_existe(dfd_mob)

print()
print("=" * 60)
print("=== TR Aprovado ===")
print("=" * 60)

# Para TR Aprovado precisamos de ETP Aprovado sem TR existente.
dfd_cftv = dfd_existe("segurança eletrônica — câmeras e monitoramento")
if not dfd_cftv:
    dfd_cftv = DFD.objects.create(
        org_id=ssp, created_by=admin, updated_by=admin,
        numero_sei="001.2026/00300-1",
        descricao="Contratação de serviço de segurança eletrônica — câmeras e monitoramento para unidades da SSP",
        status="Aprovada",
        valor_estimado=750000.00,
        area_aplicacao=["TI"],
        prazo_necessidade=date(2026, 8, 31),
        modalidade_aquisicao="licitacao",
        org_gestor=ssp,
        unidade_demandante=cplam,
        unidade_licitante=clic,
        unidade_contratante=ccc,
    )
    print(f"  [CRIADO] DFD CFTV id={dfd_cftv.id}")
else:
    print(f"  [JÁ EXISTE] DFD CFTV id={dfd_cftv.id}")

if not etp_existe(dfd_cftv):
    etp_cftv = ETP.objects.create(
        org_id=ssp, created_by=admin, updated_by=admin,
        dfd=dfd_cftv,
        numero_sei="001.2026/00300-2",
        necessidade_contratacao="Sistema integrado de CFTV e monitoramento para 12 unidades da SSP.",
        requisitos_contratacao="CREA ativo; sistema compatível com central de monitoramento existente.",
        levantamento_mercado="3 propostas: R$ 720.000, R$ 750.000, R$ 810.000.",
        estimativa_valor=735000.00,
        descricao_solucao="Pregão Eletrônico — serviço contínuo 36 meses.",
        justificativa_solucao="Ampliação da cobertura conforme plano estratégico de segurança 2026–2029.",
        riscos="Falha de integração entre sistemas; mitigação: exigir teste de integração antes da aceitação.",
        sustentabilidade="Equipamentos com certificação de eficiência energética classe A.",
        tipo_objeto="servico_continuo",
        tipo_parcelamento="nao_parcelado",
        parcelamento_justificativa="Serviço integrado; parcelamento prejudicaria interoperabilidade.",
        reserva_cota_me_epp=False,
        reserva_cota_justificativa="Complexidade técnica incompatível com porte de ME/EPP.",
        licitacao_exclusiva_me_epp=False,
        status="Aprovado",
    )
    print(f"  [CRIADO] ETP Aprovado id={etp_cftv.id}")
else:
    etp_cftv = etp_existe(dfd_cftv)
    print(f"  [JÁ EXISTE] ETP CFTV id={etp_cftv.id}")

if not tr_existe(etp_cftv):
    tr_aprov = TR.objects.create(
        org_id=ssp, created_by=admin, updated_by=admin,
        etp=etp_cftv,
        numero_sei="001.2026/00300-3",
        objeto_contratacao="Contratação de empresa para fornecimento, instalação e manutenção de sistema de CFTV e monitoramento para 12 unidades da SSP.",
        justificativa="Ampliação da cobertura de monitoramento conforme diagnóstico de segurança pública.",
        requisitos_contratacao="CREA ativo; atestado de serviços similares; equipe técnica comprovada.",
        obrigacoes_contratada="Instalar, configurar, manter e fornecer suporte 24/7 ao sistema.",
        obrigacoes_contratante="Disponibilizar acesso às unidades e nomear fiscal técnico.",
        criterios_selecao="Menor preço global.",
        criterios_medicao="Medição mensal por disponibilidade do sistema (SLA mínimo 99%).",
        tipo_prazo_vigencia="meses",
        prazo_meses=36,
        instrumento_inicio="ordem_servico",
        prazo_observacao="Mobilização em até 15 dias úteis após emissão da OS.",
        local_entrega="12 unidades da SSP — Salvador/BA, conforme Anexo I.",
        garantia_contrato="5% do valor do contrato (art. 96, Lei 14.133/2021).",
        estimativa_valor=735000.00,
        status="Aprovado",
    )
    print(f"  [CRIADO] TR Aprovado id={tr_aprov.id}")
else:
    tr_aprov = tr_existe(etp_cftv)
    print(f"  [JÁ EXISTE] TR CFTV id={tr_aprov.id}")

# ── TR Submetido (PMBA — viaturas) ───────────────────────────────────────────
print()
print("=== TR Submetido ===")

dfd_vtr = dfd_existe("viaturas para policiamento ostensivo")
if not dfd_vtr:
    dfd_vtr = DFD.objects.create(
        org_id=pmba, created_by=admin, updated_by=admin,
        numero_sei="002.2026/00100-1",
        descricao="Aquisição de viaturas para policiamento ostensivo — PMBA",
        status="Aprovada",
        valor_estimado=4200000.00,
        area_aplicacao=["Frota"],
        prazo_necessidade=date(2026, 10, 31),
        modalidade_aquisicao="licitacao",
        org_gestor=ssp,
    )
    print(f"  [CRIADO] DFD viaturas id={dfd_vtr.id}")
else:
    print(f"  [JÁ EXISTE] DFD viaturas id={dfd_vtr.id}")

if not etp_existe(dfd_vtr):
    etp_vtr = ETP.objects.create(
        org_id=pmba, created_by=admin, updated_by=admin,
        dfd=dfd_vtr,
        numero_sei="002.2026/00100-2",
        necessidade_contratacao="Aquisição de 40 viaturas para recomposição da frota operacional da PMBA.",
        requisitos_contratacao="Veículos 0km, motor mínimo 1.6, ar-condicionado, câmera de ré.",
        levantamento_mercado="Pesquisa SIASG — valor médio R$ 105.000/unidade.",
        estimativa_valor=4200000.00,
        descricao_solucao="Pregão Eletrônico — ata de registro de preços.",
        justificativa_solucao="Frota atual com 65% de sucateamento conforme laudo técnico.",
        riscos="Atraso na entrega; mitigação: entrega parcelada em lotes de 10 unidades.",
        sustentabilidade="Veículos dentro dos limites PROCONVE P7.",
        tipo_objeto="material",
        tipo_parcelamento="parcelado",
        parcelamento_justificativa="Entregas mensais de 10 unidades facilitam a gestão da frota.",
        reserva_cota_me_epp=False,
        reserva_cota_justificativa="Volume incompatível com porte de ME/EPP.",
        licitacao_exclusiva_me_epp=False,
        status="Aprovado",
    )
    print(f"  [CRIADO] ETP viaturas id={etp_vtr.id}")
else:
    etp_vtr = etp_existe(dfd_vtr)
    print(f"  [JÁ EXISTE] ETP viaturas id={etp_vtr.id}")

if not tr_existe(etp_vtr):
    tr_sub = TR.objects.create(
        org_id=pmba, created_by=admin, updated_by=admin,
        etp=etp_vtr,
        numero_sei="002.2026/00100-3",
        objeto_contratacao="Aquisição de 40 viaturas policiais para recomposição da frota operacional da PMBA.",
        justificativa="Frota com 65% sucateada; comprometimento direto da atividade-fim.",
        requisitos_contratacao="Veículos 0km; motor mínimo 1.6; certificação INMETRO.",
        obrigacoes_contratada="Entregar os veículos licenciados e emplacados dentro do prazo.",
        obrigacoes_contratante="Realizar vistoria de recebimento e emitir termo de aceite por lote.",
        criterios_selecao="Menor preço por unidade.",
        criterios_medicao="Aceite por lote após vistoria técnica.",
        tipo_prazo_vigencia="meses",
        prazo_meses=12,
        instrumento_inicio="nota_empenho",
        prazo_observacao="Lotes de 10 unidades a cada 60 dias corridos.",
        local_entrega="Pátio do DEPLAN/PMBA, Salvador-BA.",
        garantia_contrato="5% conforme art. 96 da Lei 14.133/2021.",
        estimativa_valor=4200000.00,
        status="Submetido",
    )
    print(f"  [CRIADO] TR Submetido id={tr_sub.id}")
else:
    tr_sub = tr_existe(etp_vtr)
    print(f"  [JÁ EXISTE] TR viaturas id={tr_sub.id}")

print()
print("=" * 60)
print("=== Procedimentos — todos os estágios ===")
print("=" * 60)

def criar_proc(objeto_frag, **kwargs):
    p = proc_existe(objeto_frag)
    if p:
        print(f"  [JÁ EXISTE] Procedimento '{objeto_frag[:40]}...' id={p.id}")
        return p
    p = Procedimento.objects.create(**kwargs)
    print(f"  [CRIADO] Procedimento {p.status} id={p.id} — {p.numero}")
    return p

p_instrucao = criar_proc(
    "segurança eletrônica com fornecimento",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026, modalidade="pregao_eletronico", status="Em Instrução",
    dfd=dfd_cftv, tr=tr_aprov,
    objeto="Contratação de empresa para fornecimento, instalação e manutenção de sistema de segurança eletrônica com fornecimento de CFTV.",
    valor_estimado=735000.00,
    fundamento_dispensa="", fundamento_inexigibilidade="",
    justificativa="Ampliação do monitoramento conforme planejamento estratégico.",
    numero_sei="001.2026/00300-4",
    unidade_gestora=clic,
)

p_ag_aprov = criar_proc(
    "notebooks, monitores e periféricos para a SSP",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026, modalidade="pregao_eletronico", status="Aguardando Aprovação",
    dfd=dfd1,
    objeto="Aquisição de notebooks, monitores e periféricos para a SSP.",
    valor_estimado=480000.00,
    fundamento_dispensa="", fundamento_inexigibilidade="",
    justificativa="Reposição de equipamentos com obsolescência comprovada por laudo técnico.",
    numero_sei="001.2026/00001-9",
    unidade_gestora=clic,
)

p_aprov = criar_proc(
    "sistema de videomonitoramento IP para SSP",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026, modalidade="pregao_eletronico", status="Aprovado",
    dfd=dfd2,
    objeto="Aquisição de sistema de videomonitoramento IP para SSP.",
    valor_estimado=1200000.00,
    fundamento_dispensa="", fundamento_inexigibilidade="",
    justificativa="Expansão do monitoramento conforme plano de segurança pública 2026.",
    numero_sei="001.2026/00002-8",
    unidade_gestora=clic,
)

p_publicado = criar_proc(
    "manutenção predial preventiva e corretiva para unidades da SSP",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026, modalidade="pregao_eletronico", status="Publicado",
    dfd=dfd3,
    objeto="Contratação de serviço de manutenção predial preventiva e corretiva para unidades da SSP.",
    valor_estimado=185000.00,
    fundamento_dispensa="", fundamento_inexigibilidade="",
    justificativa="Manutenção das condições de funcionamento das instalações da SSP.",
    numero_sei="001.2026/00003-7",
    unidade_gestora=clic,
    data_publicacao=date(2026, 4, 10),
    data_abertura=date(2026, 5, 20),
)

p_sessao = criar_proc(
    "mobiliário ergonômico para salas operacionais",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026, modalidade="pregao_eletronico", status="Em Sessão",
    dfd=dfd_mob,
    objeto="Aquisição de mobiliário ergonômico para salas operacionais da SSP.",
    valor_estimado=312000.00,
    fundamento_dispensa="", fundamento_inexigibilidade="",
    justificativa="Modernização das instalações conforme laudo técnico.",
    numero_sei="001.2026/00200-7",
    unidade_gestora=clic,
    data_publicacao=date(2026, 4, 20),
    data_abertura=date(2026, 5, 14),
)

p_homologado = criar_proc(
    "material de escritório e expediente para SSP — exercício 2025",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2025, modalidade="pregao_eletronico", status="Homologado",
    objeto="Aquisição de material de escritório e expediente para SSP — exercício 2025.",
    valor_estimado=95000.00,
    fundamento_dispensa="", fundamento_inexigibilidade="",
    justificativa="Reposição de estoque de material de consumo.",
    numero_sei="001.2025/00500-1",
    unidade_gestora=clic,
    data_publicacao=date(2025, 10, 5),
    data_abertura=date(2025, 10, 20),
    data_homologacao=date(2025, 11, 2),
)

p_deserto = criar_proc(
    "água mineral em galões para unidades da SSP",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2025, modalidade="pregao_eletronico", status="Deserto",
    objeto="Fornecimento de água mineral em galões para unidades da SSP.",
    valor_estimado=18000.00,
    fundamento_dispensa="", fundamento_inexigibilidade="",
    justificativa="Abastecimento de água para servidores e visitantes.",
    numero_sei="001.2025/00501-2",
    unidade_gestora=clic,
    data_publicacao=date(2025, 9, 1),
    data_abertura=date(2025, 9, 15),
    observacoes="Nenhum licitante compareceu à sessão; procedimento declarado deserto.",
)

p_fracassado = criar_proc(
    "equipamentos de comunicação rádio para SSP",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2025, modalidade="pregao_eletronico", status="Fracassado",
    objeto="Aquisição de equipamentos de comunicação rádio para SSP.",
    valor_estimado=380000.00,
    fundamento_dispensa="", fundamento_inexigibilidade="",
    justificativa="Modernização do sistema de comunicação das unidades operacionais.",
    numero_sei="001.2025/00502-3",
    unidade_gestora=clic,
    data_publicacao=date(2025, 8, 1),
    data_abertura=date(2025, 8, 20),
    observacoes="Todas as propostas superaram o valor estimado; declarado fracassado.",
)

p_dispensa = criar_proc(
    "material de limpeza para SSP",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026, modalidade="dispensa_eletronica", status="Contratado",
    objeto="Aquisição emergencial de material de limpeza para SSP.",
    valor_estimado=9500.00,
    fundamento_dispensa="art. 75, II — valor abaixo do limite para dispensa",
    fundamento_inexigibilidade="",
    justificativa="Necessidade urgente de reposição para continuidade dos serviços.",
    numero_sei="001.2026/00010-1",
    unidade_gestora=cplam,
)

p_inex = criar_proc(
    "suporte ao sistema legado de gestão financeira",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026, modalidade="inexigibilidade", status="Contratado",
    objeto="Contratação de suporte ao sistema legado de gestão financeira da SSP.",
    valor_estimado=120000.00,
    fundamento_dispensa="",
    fundamento_inexigibilidade="art. 74, I — fornecedor exclusivo; sistema proprietário.",
    justificativa="Apenas o fabricante possui domínio técnico do sistema legado.",
    numero_sei="001.2026/00011-2",
    unidade_gestora=cplam,
)

print()
print("=" * 60)
print("=== Contratos adicionais ===")
print("=" * 60)

def criar_contrato(objeto_frag, **kwargs):
    c = contrato_existe(objeto_frag)
    if c:
        print(f"  [JÁ EXISTE] Contrato '{objeto_frag[:40]}' id={c.id}")
        return c
    c = Contrato.objects.create(**kwargs)
    print(f"  [CRIADO] Contrato {c.status} id={c.id} — {c.numero}")
    return c

criar_contrato(
    "material de escritório e expediente",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2025,
    orgao_executor=ssp,
    objeto="Fornecimento de material de escritório e expediente para SSP — exercício 2025.",
    tipo_origem="licitacao",
    dfd=dfd1,
    numero_processo_sei="001.2025/00500-9",
    valor_contrato=92800.00,
    data_assinatura=date(2025, 11, 15),
    data_vigencia_inicio=date(2025, 11, 15),
    data_vigencia_fim=date(2026, 11, 14),
    status="Encerrado",
    fiscal_contrato=analista,
    gestor_contrato=gestor,
    garantia_exigida=False,
)

criar_contrato(
    "material de limpeza para SSP",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026,
    orgao_executor=ssp,
    objeto="Fornecimento de material de limpeza para SSP.",
    tipo_origem="dispensa",
    numero_processo_sei="001.2026/00010-9",
    valor_contrato=9500.00,
    data_assinatura=date(2026, 3, 1),
    data_vigencia_inicio=date(2026, 3, 1),
    data_vigencia_fim=date(2026, 9, 1),
    status="Suspenso",
    fiscal_contrato=analista,
    gestor_contrato=gestor,
    garantia_exigida=False,
    observacoes="Contrato suspenso por irregularidade fiscal da contratada. Aguardando regularização.",
)

criar_contrato(
    "suporte ao sistema legado de gestão financeira",
    org_id=ssp, created_by=admin, updated_by=admin,
    exercicio=2026,
    orgao_executor=ssp,
    objeto="Contratação de suporte ao sistema legado de gestão financeira da SSP.",
    tipo_origem="inexigibilidade",
    numero_processo_sei="001.2026/00011-9",
    valor_contrato=120000.00,
    data_assinatura=date(2026, 2, 1),
    data_vigencia_inicio=date(2026, 2, 1),
    data_vigencia_fim=date(2027, 1, 31),
    status="Vigente",
    fiscal_contrato=analista,
    gestor_contrato=gestor,
    garantia_exigida=False,
)

print()
print("=" * 60)
print("=== RESUMO FINAL ===")
print("=" * 60)
from modulo_demanda.models import DFD
from modulo_planejamento.models import NecessidadePlanejamento
print(f"  NecessidadePlanejamento : {NecessidadePlanejamento.objects.count()}")
print(f"  DFDs                    : {DFD.objects.count()}")
print(f"  ETPs                    : {ETP.objects.count()}")
print(f"  TRs                     : {TR.objects.count()}")
print(f"  Procedimentos           : {Procedimento.objects.count()}")
print(f"  Contratos               : {Contrato.objects.count()}")
print()
print("ETPs por status:")
for s in ["Rascunho", "Submetido", "Em Análise", "Devolvido", "Aprovado", "Dispensado"]:
    n = ETP.objects.filter(status=s).count()
    if n: print(f"  {s:15} : {n}")
print()
print("TRs por status:")
for s in ["Rascunho", "Submetido", "Em Análise", "Devolvido", "Aprovado"]:
    n = TR.objects.filter(status=s).count()
    if n: print(f"  {s:15} : {n}")
print()
print("Procedimentos por status:")
for s in Procedimento.objects.values_list("status", flat=True).distinct():
    print(f"  {s:25} : {Procedimento.objects.filter(status=s).count()}")
print()
print("Contratos por status:")
for s in ["Vigente", "Encerrado", "Suspenso", "Rescindido"]:
    n = Contrato.objects.filter(status=s).count()
    if n: print(f"  {s:15} : {n}")
