"""
Preenche Procedimento.dfd dos procedimentos abertos só a partir do TR — mesma
regra de `dfd_do_tr()` (models.py): TR → ETP → DFD.
"""
from django.db import migrations


def preencher_dfd(apps, schema_editor):
    Procedimento = apps.get_model('modulo_licitacao', 'Procedimento')
    for proc in Procedimento.objects.filter(dfd__isnull=True, tr__isnull=False).select_related('tr__etp'):
        Procedimento.objects.filter(pk=proc.pk).update(dfd_id=proc.tr.etp.dfd_id)


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_licitacao', '0006_procedimento_data_mesa_atual_and_more'),
        ('modulo_etp', '0010_etp_data_mesa_atual_etp_mesa_atual_content_type_and_more'),
        ('modulo_tr', '0012_tr_data_mesa_atual_tr_mesa_atual_content_type_and_more'),
    ]

    operations = [
        migrations.RunPython(preencher_dfd, migrations.RunPython.noop),
    ]
