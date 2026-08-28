import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_fornecedor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FornecedorFamilia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('familia_simpas', models.CharField(max_length=15, verbose_name='Família SIMPAS')),
                ('fornecedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='familias', to='modulo_fornecedor.fornecedor')),
            ],
            options={
                'verbose_name': 'Família do Fornecedor',
                'verbose_name_plural': 'Famílias do Fornecedor',
                'ordering': ['familia_simpas'],
                'unique_together': {('fornecedor', 'familia_simpas')},
            },
        ),
    ]
