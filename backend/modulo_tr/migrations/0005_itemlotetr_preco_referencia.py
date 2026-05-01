from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_tr', '0004_loter_itemloter'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemlotetr',
            name='valor_unitario_ref',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=15, null=True,
                verbose_name='Preço unitário de referência (R$)',
            ),
        ),
        migrations.AddField(
            model_name='itemlotetr',
            name='preco_origem',
            field=models.CharField(
                choices=[('mapa', 'Mapa de Preços'), ('dfd', 'Estimativa DFD')],
                default='dfd', max_length=5,
                verbose_name='Origem do preço',
            ),
        ),
    ]
