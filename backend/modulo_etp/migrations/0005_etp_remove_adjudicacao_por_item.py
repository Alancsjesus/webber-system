from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_etp', '0004_etp_parcelamento_cota_meepp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='etp',
            name='adjudicacao_por_item',
        ),
    ]
