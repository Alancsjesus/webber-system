# Generated manually — adds numero_sei to IndicacaoOrcamentaria

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_orcamento', '0011_item_indicacao_dotacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicacaoorcamentaria',
            name='numero_sei',
            field=models.CharField(
                blank=True, default='', max_length=50,
                help_text='Processo SEI da própria indicação/DOD (distinto do SEI do DFD vinculado).',
                verbose_name='Processo SEI',
            ),
        ),
    ]
