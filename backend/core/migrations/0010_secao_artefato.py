from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_area_atuacao'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecaoArtefato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('DFD', 'DFD — Documento de Formalização da Demanda'), ('ETP', 'ETP — Estudo Técnico Preliminar'), ('TR', 'TR — Minuta do Termo de Referência')], max_length=3, verbose_name='Tipo de artefato')),
                ('codigo', models.CharField(max_length=60, verbose_name='Código (chave técnica)')),
                ('titulo', models.CharField(max_length=200, verbose_name='Título da seção')),
                ('descricao', models.TextField(blank=True, default='', verbose_name='Orientação de preenchimento')),
                ('ordem', models.PositiveIntegerField(default=0, verbose_name='Ordem de exibição')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('obrigatorio', models.BooleanField(default=False, verbose_name='Preenchimento obrigatório')),
                ('aplica_modalidades', models.JSONField(default=list, help_text='Lista vazia = todas as modalidades', verbose_name='Aplica para modalidades')),
            ],
            options={'ordering': ['tipo', 'ordem'], 'verbose_name': 'Seção de Artefato', 'verbose_name_plural': 'Seções de Artefatos'},
        ),
        migrations.AlterUniqueTogether(
            name='secaoartefato',
            unique_together={('tipo', 'codigo')},
        ),
    ]
