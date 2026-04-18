from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_demanda', '0007_dfd_orgao_compras'),
    ]

    operations = [
        migrations.AddField(
            model_name='dfd',
            name='local_entrega',
            field=models.TextField(blank=True, default='', verbose_name='Local de entrega'),
        ),
    ]
