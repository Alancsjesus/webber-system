from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_secao_artefato'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemCatalogo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_interno', models.CharField(editable=False, max_length=20, unique=True, verbose_name='Código interno')),
                ('codigo_simpas', models.CharField(blank=True, default='', max_length=40, verbose_name='Código SIMPAS')),
                ('familia', models.CharField(blank=True, db_index=True, default='', max_length=15, verbose_name='Família SIMPAS')),
                ('nome', models.CharField(max_length=300, verbose_name='Descrição do item')),
                ('descricao', models.TextField(blank=True, default='', verbose_name='Especificação complementar')),
                ('unidade_medida', models.CharField(max_length=20, verbose_name='Unidade de medida')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={'ordering': ['familia', 'nome'], 'verbose_name': 'Item do Catálogo', 'verbose_name_plural': 'Itens do Catálogo'},
        ),
    ]
