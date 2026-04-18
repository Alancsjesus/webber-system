import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_planejamento', '0002_necessidade_unidades_plano_orcamentario'),
        ('core', '0005_orgao_unidade_organizacional'),
    ]

    operations = [
        migrations.AddField(
            model_name='necessidadeplanejamento',
            name='org_gestor',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='necessidades_gerenciadas',
                to='core.orgao',
                verbose_name='Órgão gestor',
            ),
        ),
    ]
