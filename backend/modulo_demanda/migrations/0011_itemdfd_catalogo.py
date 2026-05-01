import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_item_catalogo'),
        ('modulo_demanda', '0010_dfd_responsaveis_contrato'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemdfd',
            name='item_catalogo',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='itens_dfd',
                to='core.itemcatalogo',
                verbose_name='Item do catálogo',
            ),
        ),
    ]
