from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_etp', '0003_etp_dispensado_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='etp',
            name='tipo_parcelamento',
            field=models.CharField(
                blank=True, default='', max_length=20,
                choices=[
                    ('lote_unico', 'Lote único — contratação global'),
                    ('lotes',      'Dividido em lotes — adjudicação por lote'),
                    ('por_item',   'Por item — adjudicação individualizada'),
                ],
                verbose_name='Tipo de parcelamento',
            ),
        ),
        migrations.AddField(
            model_name='etp',
            name='parcelamento_justificativa',
            field=models.TextField(blank=True, default='', verbose_name='Justificativa do parcelamento (Art. 40, V)'),
        ),
        migrations.AddField(
            model_name='etp',
            name='adjudicacao_por_item',
            field=models.BooleanField(default=False, verbose_name='Adjudicação por item'),
        ),
        migrations.AddField(
            model_name='etp',
            name='reserva_cota_me_epp',
            field=models.BooleanField(default=False, verbose_name='Reserva de cota 25% para ME/EPP'),
        ),
        migrations.AddField(
            model_name='etp',
            name='reserva_cota_justificativa',
            field=models.TextField(blank=True, default='', verbose_name='Justificativa da não-reserva de cota'),
        ),
        migrations.AddField(
            model_name='etp',
            name='licitacao_exclusiva_me_epp',
            field=models.BooleanField(default=False, verbose_name='Licitação exclusiva ME/EPP (até R$80.000)'),
        ),
    ]
