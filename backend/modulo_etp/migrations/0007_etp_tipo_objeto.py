from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_etp', '0006_historicoetp_categoria_motivo'),
    ]

    operations = [
        migrations.AddField(
            model_name='etp',
            name='tipo_objeto',
            field=models.CharField(
                blank=True, default='', max_length=25,
                choices=[
                    ('bens', 'Bens'),
                    ('servicos', 'Serviços Comuns'),
                    ('servicos_engenharia', 'Serviços de Engenharia'),
                    ('obras', 'Obras'),
                ],
                verbose_name='Tipo de objeto',
            ),
        ),
    ]
