import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_orcamento', '0003_indicacao_orcamentaria'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DescentralizacaoOrcamentaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('numero_npo', models.CharField(max_length=50, verbose_name='Número da NPO (sistema financeiro)')),
                ('data_emissao', models.DateField(verbose_name='Data de emissão')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Valor descentralizado (R$)')),
                ('cancelada', models.BooleanField(default=False, verbose_name='Cancelada')),
                ('data_cancelamento', models.DateField(blank=True, null=True, verbose_name='Data do cancelamento')),
                ('motivo_cancelamento', models.TextField(blank=True, default='', verbose_name='Motivo do cancelamento')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Observações')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('indicacao_dotacao', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='descentralizacoes', to='modulo_orcamento.indicacaodotacao', verbose_name='Item de indicação (dotação)')),
                ('registrada_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='npos_registradas', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-data_emissao', '-criado_em'], 'verbose_name': 'Descentralização Orçamentária (NPO)', 'verbose_name_plural': 'Descentralizações Orçamentárias (NPO)'},
        ),
        migrations.CreateModel(
            name='ConcessaoOrcamentaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('numero_doc', models.CharField(max_length=50, verbose_name='Número do documento (sistema financeiro)')),
                ('data_emissao', models.DateField(verbose_name='Data de emissão')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Valor concedido (R$)')),
                ('cancelada', models.BooleanField(default=False, verbose_name='Cancelada')),
                ('data_cancelamento', models.DateField(blank=True, null=True, verbose_name='Data do cancelamento')),
                ('motivo_cancelamento', models.TextField(blank=True, default='', verbose_name='Motivo do cancelamento')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Observações')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('indicacao_dotacao', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='concessoes', to='modulo_orcamento.indicacaodotacao', verbose_name='Item de indicação (dotação)')),
                ('registrada_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='concessoes_registradas', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-data_emissao', '-criado_em'], 'verbose_name': 'Concessão Orçamentária', 'verbose_name_plural': 'Concessões Orçamentárias'},
        ),
    ]
