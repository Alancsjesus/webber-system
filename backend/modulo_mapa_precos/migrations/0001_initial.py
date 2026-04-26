from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('modulo_demanda', '0001_initial'),
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MapaComparativoPrecos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('objeto', models.TextField(verbose_name='Objeto da pesquisa de preços')),
                ('exercicio_fiscal', models.IntegerField(verbose_name='Exercício fiscal')),
                ('status', models.CharField(choices=[('Rascunho', 'Rascunho'), ('Finalizado', 'Finalizado'), ('Cancelado', 'Cancelado')], default='Rascunho', max_length=15, verbose_name='Status')),
                ('metodo_calculo', models.CharField(choices=[('media', 'Média aritmética dos preços válidos'), ('mediana', 'Mediana de todos os preços coletados'), ('menor_valido', 'Menor preço válido')], default='media', max_length=15, verbose_name='Método de cálculo')),
                ('valor_estimado_total', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Valor estimado total (R$)')),
                ('justificativa_metodologia', models.TextField(blank=True, default='', verbose_name='Justificativa da metodologia adotada')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Observações')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mapacomparativoprecos_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mapacomparativoprecos_updated', to=settings.AUTH_USER_MODEL)),
                ('dfd', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mapas_preco', to='modulo_demanda.dfd', verbose_name='DFD vinculado')),
                ('org_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.orgao')),
                ('responsavel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mapas_responsavel', to=settings.AUTH_USER_MODEL, verbose_name='Responsável pela pesquisa')),
            ],
            options={'verbose_name': 'Mapa Comparativo de Preços', 'verbose_name_plural': 'Mapas Comparativos de Preços', 'ordering': ['-exercicio_fiscal', '-created_at'], 'abstract': False},
        ),
        migrations.AddIndex(model_name='mapacomparativoprecos', index=models.Index(fields=['org_id', '-created_at'], name='mapa_org_created_idx')),
        migrations.CreateModel(
            name='FonteConsultada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[('I', 'Parâmetro I — SIMPAS / Comprasnet.BA / banco de preços em saúde'), ('II', 'Parâmetro II — Contratações similares (Administração Pública)'), ('III', 'Parâmetro III — Mídia especializada / sítios eletrônicos'), ('IV', 'Parâmetro IV — Pesquisa direta com fornecedores'), ('V', 'Parâmetro V — Base de notas fiscais eletrônicas'), ('HIST', 'Histórico WEBBER — Aquisições anteriores do sistema')], max_length=5, verbose_name='Parâmetro (Art. 5º)')),
                ('descricao', models.CharField(max_length=255, verbose_name='Descrição da fonte')),
                ('referencia', models.CharField(blank=True, default='', max_length=255, verbose_name='Referência documental')),
                ('data_consulta', models.DateField(verbose_name='Data da consulta')),
                ('documento_sei', models.CharField(blank=True, default='', max_length=50, verbose_name='Nº documento SEI (se houver)')),
                ('infrutífera', models.BooleanField(default=False, verbose_name='Consulta infrutífera')),
                ('justificativa_infrutífera', models.TextField(blank=True, default='', verbose_name='Justificativa da consulta infrutífera')),
                ('mapa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fontes', to='modulo_mapa_precos.mapacomparativoprecos')),
            ],
            options={'verbose_name': 'Fonte Consultada', 'verbose_name_plural': 'Fontes Consultadas', 'ordering': ['tipo', 'data_consulta']},
        ),
        migrations.CreateModel(
            name='ItemMapa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('ordem', models.PositiveSmallIntegerField(default=1, verbose_name='Ordem')),
                ('descricao', models.CharField(max_length=500, verbose_name='Descrição do item')),
                ('codigo_simpas', models.CharField(blank=True, default='', max_length=50, verbose_name='Código SIMPAS')),
                ('unidade_medida', models.CharField(max_length=20, verbose_name='Unidade de medida')),
                ('quantidade', models.DecimalField(decimal_places=3, max_digits=12, verbose_name='Quantidade')),
                ('valor_unitario_calculado', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor unitário calculado (R$)')),
                ('valor_total_calculado', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor total calculado (R$)')),
                ('metodo_aplicado', models.CharField(blank=True, choices=[('media', 'Média aritmética'), ('mediana', 'Mediana'), ('menor_valido', 'Menor valor válido')], default='', max_length=15, verbose_name='Método aplicado a este item')),
                ('qtd_precos_validos', models.PositiveSmallIntegerField(default=0, verbose_name='Nº de preços válidos utilizados')),
                ('justificativa_item', models.TextField(blank=True, default='', verbose_name='Justificativa')),
                ('alerta', models.CharField(blank=True, default='', max_length=255, verbose_name='Alerta de validação')),
                ('mapa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='modulo_mapa_precos.mapacomparativoprecos')),
            ],
            options={'verbose_name': 'Item do Mapa', 'verbose_name_plural': 'Itens do Mapa', 'ordering': ['ordem']},
        ),
        migrations.CreateModel(
            name='PrecoColetado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('valor_unitario', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Valor unitário (R$)')),
                ('origem_orgao_empresa', models.CharField(blank=True, default='', max_length=255, verbose_name='Órgão / Empresa de origem')),
                ('numero_certame', models.CharField(blank=True, default='', max_length=100, verbose_name='Número do certame / processo')),
                ('data_referencia', models.DateField(verbose_name='Data de referência do preço')),
                ('valido', models.BooleanField(default=True, verbose_name='Válido para cálculo')),
                ('motivo_exclusao', models.CharField(blank=True, choices=[('excessivo', 'Valor excessivamente elevado (acima de +30% da mediana)'), ('inexequivel', 'Valor inexequível (abaixo de -30% da mediana)'), ('inconsistente', 'Valor inconsistente (especificação diferente)'), ('desatualizado', 'Cotação desatualizada (prazo vencido)'), ('manual', 'Excluído manualmente pelo responsável')], default='', max_length=20, verbose_name='Motivo da exclusão')),
                ('sugestao_exclusao', models.CharField(blank=True, default='', max_length=255, verbose_name='Sugestão automática de exclusão (sistema)')),
                ('justificativa_exclusao', models.TextField(blank=True, default='', verbose_name='Justificativa detalhada da exclusão')),
                ('observacao', models.TextField(blank=True, default='', verbose_name='Observação')),
                ('fonte', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='precos', to='modulo_mapa_precos.fonteconsultada')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='precos', to='modulo_mapa_precos.itemmapa')),
            ],
            options={'verbose_name': 'Preço Coletado', 'verbose_name_plural': 'Preços Coletados', 'ordering': ['item', 'valor_unitario']},
        ),
    ]
