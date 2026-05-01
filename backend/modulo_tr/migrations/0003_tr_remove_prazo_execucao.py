from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_tr', '0002_tr_prazo_vigencia'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tr',
            name='prazo_execucao',
        ),
    ]
