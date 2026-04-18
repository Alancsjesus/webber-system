import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_demanda', '0004_dfd_justificativa_sem_planejamento'),
        ('core', '0005_orgao_unidade_organizacional'),
    ]

    operations = [
        migrations.AddField(
            model_name='dfd',
            name='unidade_demandante',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dfds_demandados',
                to='core.unidadeorganizacional',
            ),
        ),
        migrations.AddField(
            model_name='dfd',
            name='unidade_licitante',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dfds_licitados',
                to='core.unidadeorganizacional',
            ),
        ),
        migrations.AddField(
            model_name='dfd',
            name='unidade_contratante',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dfds_contratados',
                to='core.unidadeorganizacional',
            ),
        ),
    ]
