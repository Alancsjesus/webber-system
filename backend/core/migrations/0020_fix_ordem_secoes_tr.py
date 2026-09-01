"""
Corrige `ordem` das seções do TR: o campo é PositiveIntegerField, mas
seed_secoes_tr.py usava números fracionários (5.1, 5.2, 8.1...) para espelhar a
numeração do checklist PGE-BA nos TÍTULOS — o Django truncava o valor ao salvar,
então 22 das 38 seções do TR ficavam com `ordem` duplicada (ex: 7 seções
diferentes com ordem=5), quebrando a reordenação ▲▼ em Configurações →
Estrutura de Artefatos (achado de auditoria, 01/09/2026).

Também desativa `OBJETO_DESC` — seção órfã (fora de seed_secoes_tr.py, sem
mapeamento em document_engine.py) que duplicava `cond_gerais` na mesma posição.
"""
from django.db import migrations

ORDEM_SEQUENCIAL_TR = [
    'cond_gerais', 'objeto', 'fundamentacao', 'solucao',
    'req_sustentabilidade', 'req_marca', 'req_exame', 'req_vistoria',
    'req_subcontratacao', 'req_garantia_prop', 'req_garantia_contr',
    'prazo_vigencia', 'local_entrega',
    'bens_nao_luxo', 'bens_reserva_cota', 'bens_carta_solidariedade',
    'bens_validade', 'bens_garantia_tecnica',
    'serv_transicao', 'serv_regime_execucao', 'serv_materiais',
    'serv_qualificacao', 'serv_parcelas_relevancia',
    'modelo_gestao', 'obrigacoes_contratada', 'obrigacoes_contratante',
    'criterios_medicao', 'criterios_selecao',
    'hab_juridica', 'hab_fiscal', 'hab_economica',
    'hab_tecnica_bens', 'hab_tecnica_servicos',
    'estimativa_valor', 'adequacao_orcamentaria', 'parcelamento_etp',
    'lotes', 'observacoes',
]

OBJETO_DESC_ORFAO = 'OBJETO_DESC'


def corrigir(apps, schema_editor):
    SecaoArtefato = apps.get_model('core', 'SecaoArtefato')
    for i, codigo in enumerate(ORDEM_SEQUENCIAL_TR, start=1):
        SecaoArtefato.objects.filter(tipo='TR', codigo=codigo).update(ordem=i)
    SecaoArtefato.objects.filter(tipo='TR', codigo=OBJETO_DESC_ORFAO).update(ativo=False)


def reverter(apps, schema_editor):
    # Não recompõe os valores fracionários antigos — eram o próprio bug.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_desativa_secoes_tr_legadas'),
    ]

    operations = [
        migrations.RunPython(corrigir, reverter),
    ]
