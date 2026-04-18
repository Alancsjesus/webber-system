import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_demanda', '0005_dfd_unidades_organizacionais'),
        ('core', '0005_orgao_unidade_organizacional'),
    ]

    operations = [
        migrations.AddField(
            model_name='dfd',
            name='org_gestor',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dfds_gerenciados',
                to='core.orgao',
            ),
        ),
    ]
