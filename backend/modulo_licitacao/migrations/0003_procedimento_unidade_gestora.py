from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_areaatuacao_id_and_more'),
        ('modulo_licitacao', '0002_alter_procedimento_modalidade'),
    ]

    operations = [
        migrations.AddField(
            model_name='procedimento',
            name='unidade_gestora',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='procedimentos_gestora',
                to='core.unidadeorganizacional',
                verbose_name='Unidade gestora',
            ),
        ),
        migrations.AlterField(
            model_name='procedimento',
            name='numero',
            field=models.CharField(
                editable=False,
                max_length=30,
                unique=True,
                verbose_name='Número do procedimento',
            ),
        ),
    ]
