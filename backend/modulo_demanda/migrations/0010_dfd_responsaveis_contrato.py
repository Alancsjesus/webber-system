import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_demanda', '0009_dfd_modalidade_aquisicao'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='dfd',
            name='fiscal_contrato',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dfds_como_fiscal',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Fiscal do contrato',
            ),
        ),
        migrations.AddField(
            model_name='dfd',
            name='fiscal_suplente',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dfds_como_fiscal_suplente',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Fiscal suplente',
            ),
        ),
        migrations.AddField(
            model_name='dfd',
            name='gestor_contrato',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dfds_como_gestor',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Gestor do contrato',
            ),
        ),
        migrations.AddField(
            model_name='dfd',
            name='gestor_suplente',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dfds_como_gestor_suplente',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Gestor suplente',
            ),
        ),
    ]
