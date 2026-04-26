from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_orcamento', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NaturezaDespesa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=6, unique=True, verbose_name='Código')),
                ('descricao', models.CharField(max_length=255, verbose_name='Descrição')),
                ('ativa', models.BooleanField(default=True, verbose_name='Ativa')),
                ('elemento_despesa', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='naturezas',
                    to='modulo_orcamento.elementodespesa',
                    verbose_name='Elemento de despesa',
                )),
            ],
            options={
                'verbose_name': 'Natureza de Despesa',
                'verbose_name_plural': 'Naturezas de Despesa',
                'ordering': ['codigo'],
            },
        ),
        migrations.AddField(
            model_name='dotacaoorcamentaria',
            name='natureza_despesa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='dotacoes',
                to='modulo_orcamento.naturezadespesa',
                verbose_name='Natureza de despesa',
            ),
        ),
        migrations.AddField(
            model_name='dotacaoorcamentaria',
            name='valor_indicado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Valor indicado (R$)'),
        ),
        migrations.AddField(
            model_name='dotacaoorcamentaria',
            name='valor_descentralizado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Valor descentralizado (R$)'),
        ),
        migrations.AddField(
            model_name='dotacaoorcamentaria',
            name='valor_concedido',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Valor concedido (R$)'),
        ),
    ]
