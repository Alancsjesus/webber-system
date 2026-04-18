import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_planejamento', '0001_initial'),
        ('core', '0005_orgao_unidade_organizacional'),
    ]

    operations = [
        # Vincula unidade demandante à necessidade
        migrations.AddField(
            model_name='necessidadeplanejamento',
            name='unidade_demandante',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='necessidades',
                to='core.unidadeorganizacional',
                verbose_name='Unidade demandante',
            ),
        ),

        # Órgão que irá executar a necessidade
        migrations.AddField(
            model_name='necessidadeplanejamento',
            name='orgao_executor',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='necessidades_a_executar',
                to='core.orgao',
                verbose_name='Órgão executor',
            ),
        ),

        # Plano Orçamentário
        migrations.CreateModel(
            name='PlanoOrcamentario',
            fields=[
                ('id',               models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('exercicio_fiscal', models.IntegerField(verbose_name='Exercício fiscal')),
                ('descricao',        models.CharField(blank=True, max_length=200, verbose_name='Descrição')),
                ('dotacao_total',    models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True, verbose_name='Dotação total (R$)')),
                ('criado_em',        models.DateTimeField(auto_now_add=True)),
                ('atualizado_em',    models.DateTimeField(auto_now=True)),
                ('orgao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='planos_orcamentarios',
                    to='core.orgao',
                    verbose_name='Órgão',
                )),
                ('necessidades', models.ManyToManyField(
                    blank=True,
                    related_name='planos',
                    to='modulo_planejamento.necessidadeplanejamento',
                    verbose_name='Necessidades vinculadas',
                )),
            ],
            options={
                'verbose_name': 'Plano Orçamentário',
                'verbose_name_plural': 'Planos Orçamentários',
                'ordering': ['-exercicio_fiscal', 'orgao__sigla'],
                'unique_together': {('orgao', 'exercicio_fiscal')},
            },
        ),
    ]
