from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_parametro_sistema'),
    ]

    operations = [
        migrations.AddField(
            model_name='parametrosistema',
            name='norma_base',
            field=models.CharField(
                blank=True, default='', max_length=500,
                verbose_name='Norma / Legislação base',
            ),
        ),
        migrations.AddField(
            model_name='parametrosistema',
            name='data_vigencia',
            field=models.DateField(
                blank=True, null=True,
                verbose_name='Data de vigência da norma',
            ),
        ),
        migrations.AlterField(
            model_name='parametrosistema',
            name='descricao',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
