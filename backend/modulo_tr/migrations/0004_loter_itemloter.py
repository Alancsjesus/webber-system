import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('modulo_demanda', '0001_initial'),
        ('modulo_tr', '0003_tr_remove_prazo_execucao'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Criar LoteTR sem o FK auto-referencial
        migrations.CreateModel(
            name='LoteTR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('numero', models.CharField(editable=False, max_length=20, verbose_name='Número do lote')),
                ('descricao', models.CharField(blank=True, default='', max_length=200, verbose_name='Descrição do lote')),
                ('modalidade', models.CharField(
                    choices=[('ampla', 'Ampla Concorrência'), ('cota_me_epp', 'Reserva de Cota ME/EPP'), ('exclusiva_me_epp', 'Exclusivo ME/EPP')],
                    default='ampla', max_length=20, verbose_name='Modalidade de participação')),
                ('percentual_cota', models.PositiveIntegerField(default=25, verbose_name='Percentual da cota (%)')),
                ('ordem', models.PositiveIntegerField(default=0, verbose_name='Ordem de exibição')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Observações')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lotetr_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lotetr_updated', to=settings.AUTH_USER_MODEL)),
                ('org_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lotes_tr', to='core.orgao')),
                ('tr', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lotes', to='modulo_tr.tr')),
            ],
            options={'ordering': ['tr', 'ordem', 'numero'], 'abstract': False,
                     'verbose_name': 'Lote do TR', 'verbose_name_plural': 'Lotes do TR'},
        ),
        # 2. Adicionar FK auto-referencial depois que a tabela existe
        migrations.AddField(
            model_name='lotetr',
            name='lote_origem',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lotes_cota',
                to='modulo_tr.lotetr',
                verbose_name='Lote de origem (para cotas)',
            ),
        ),
        # 3. Criar ItemLoteTR
        migrations.CreateModel(
            name='ItemLoteTR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=4, max_digits=15, verbose_name='Quantidade no lote')),
                ('item_dfd', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lotes_tr', to='modulo_demanda.itemdfd')),
                ('lote', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='modulo_tr.lotetr')),
            ],
            options={'verbose_name': 'Item do Lote TR', 'verbose_name_plural': 'Itens dos Lotes TR'},
        ),
        migrations.AlterUniqueTogether(
            name='itemlotetr',
            unique_together={('lote', 'item_dfd')},
        ),
    ]
