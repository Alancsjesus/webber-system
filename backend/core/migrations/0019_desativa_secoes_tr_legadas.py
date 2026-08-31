"""
Desativa seções do TR criadas pelo seed antigo de setup_dev.py ('justificativa',
'requisitos', 'garantia') que colidem com o checklist oficial PGE-BA (seed_secoes_tr.py)
e apareciam como seções soltas/redundantes nas peças geradas — achado de auditoria
31/08/2026 (usuário reportou pontos "desnecessários e não solicitados" no TR).

Os demais códigos do seed antigo (objeto, obrigacoes_contratada/contratante,
criterios_selecao, criterios_medicao, prazo_vigencia, local_entrega, estimativa_valor,
parcelamento_etp, lotes, observacoes) coincidem em nome com códigos oficiais — o
seed_secoes_tr.py já sobrescreve título/ordem desses via update_or_create, então
não são desativados aqui (são as seções oficiais de verdade, só com o mesmo nome
de código por coincidência histórica).
"""
from django.db import migrations

CODIGOS_LEGADOS = ['justificativa', 'requisitos', 'garantia']


def desativar(apps, schema_editor):
    SecaoArtefato = apps.get_model('core', 'SecaoArtefato')
    SecaoArtefato.objects.filter(tipo='TR', codigo__in=CODIGOS_LEGADOS).update(ativo=False)


def reverter(apps, schema_editor):
    # Não reativa — a desativação é a correção; reverter a migração não deve
    # reintroduzir seções duplicadas no documento.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_secaoartefato_template_texto'),
    ]

    operations = [
        migrations.RunPython(desativar, reverter),
    ]
