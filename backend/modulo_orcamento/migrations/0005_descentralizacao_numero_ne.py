from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_orcamento', '0004_npo_concessao'),
    ]

    operations = [
        migrations.AddField(
            model_name='descentralizacaoorcamentaria',
            name='numero_ne',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Número da NE (FIPLAN)'),
        ),
    ]
