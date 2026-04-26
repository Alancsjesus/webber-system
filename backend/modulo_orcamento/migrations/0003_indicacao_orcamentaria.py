from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_orcamento', '0002_natureza_despesa_pipeline_valores'),
        ('modulo_demanda', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IndicacaoOrcamentaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('numero', models.CharField(max_length=20, verbose_name='Número')),
                ('exercicio_fiscal', models.IntegerField(verbose_name='Exercício fiscal')),
                ('valor_total', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Valor total indicado (R$)')),
                ('status', models.CharField(choices=[('Rascunho', 'Rascunho'), ('Submetida', 'Submetida'), ('Aprovada', 'Aprovada (DOD emitida)'), ('Cancelada', 'Cancelada')], default='Rascunho', max_length=15, verbose_name='Status')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Observações')),
                ('data_aprovacao', models.DateField(blank=True, null=True, verbose_name='Data de aprovação')),
                ('motivo_cancelamento', models.TextField(blank=True, default='', verbose_name='Motivo do cancelamento')),
                ('org_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.orgao')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='indicacaoorcamentaria_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='indicacaoorcamentaria_updated', to=settings.AUTH_USER_MODEL)),
                ('dfd', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='indicacoes', to='modulo_demanda.dfd', verbose_name='DFD vinculado')),
                ('necessidade', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='indicacoes', to='modulo_planejamento.necessidadeplanejamento', verbose_name='Necessidade vinculada')),
                ('ordenador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='indicacoes_ordenadas', to=settings.AUTH_USER_MODEL, verbose_name='Ordenador de despesa')),
            ],
            options={
                'verbose_name': 'Indicação Orçamentária',
                'verbose_name_plural': 'Indicações Orçamentárias',
                'ordering': ['-exercicio_fiscal', '-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='indicacaoorcamentaria',
            constraint=models.UniqueConstraint(fields=['org_id', 'numero'], name='unique_indicacao_numero_por_org'),
        ),
        migrations.AddIndex(
            model_name='indicacaoorcamentaria',
            index=models.Index(fields=['org_id', '-created_at'], name='indicacao_org_created_idx'),
        ),
        migrations.CreateModel(
            name='IndicacaoDotacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('valor_indicado', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Valor indicado (R$)')),
                ('indicacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='modulo_orcamento.indicacaoorcamentaria')),
                ('dotacao', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='itens_indicacao', to='modulo_orcamento.dotacaoorcamentaria')),
            ],
            options={
                'verbose_name': 'Item de Indicação',
                'verbose_name_plural': 'Itens de Indicação',
            },
        ),
        migrations.AlterUniqueTogether(
            name='indicacaodotacao',
            unique_together={('indicacao', 'dotacao')},
        ),
        migrations.CreateModel(
            name='HistoricoIndicacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('status_anterior', models.CharField(max_length=15)),
                ('status_novo', models.CharField(max_length=15)),
                ('motivo', models.TextField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('indicacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historico', to='modulo_orcamento.indicacaoorcamentaria')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Histórico de Indicação',
                'ordering': ['-criado_em'],
            },
        ),
    ]
