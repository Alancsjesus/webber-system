import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_fornecedor', '0001_initial'),
        ('modulo_mapa_precos', '0007_precocoletado_fornecedor_and_more'),
    ]

    operations = [
        migrations.RemoveField(model_name='solicitacaocotacao', name='fornecedor'),
        migrations.RemoveField(model_name='solicitacaocotacao', name='fornecedor_nome'),
        migrations.RemoveField(model_name='solicitacaocotacao', name='fornecedor_cnpj'),
        migrations.RemoveField(model_name='solicitacaocotacao', name='fornecedor_email'),
        migrations.RemoveField(model_name='solicitacaocotacao', name='respondeu'),
        migrations.RemoveField(model_name='solicitacaocotacao', name='valor_respondido'),
        migrations.RemoveField(model_name='solicitacaocotacao', name='resposta_pdf'),
        migrations.RemoveField(model_name='solicitacaocotacao', name='justificativa_escolha'),
        migrations.RemoveField(model_name='solicitacaocotacao', name='status'),
        migrations.AddField(
            model_name='solicitacaocotacao',
            name='familia_simpas',
            field=models.CharField(default='', max_length=15, verbose_name='Família SIMPAS',
                                    help_text='Família de itens cujos fornecedores cadastrados (modulo_fornecedor.FornecedorFamilia) recebem o disparo.'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='solicitacaocotacao',
            name='encerrada',
            field=models.BooleanField(default=False, verbose_name='Disparo encerrado'),
        ),
        migrations.AlterModelOptions(
            name='solicitacaocotacao',
            options={'ordering': ['mapa', '-data_envio'], 'verbose_name': 'Solicitação de Cotação', 'verbose_name_plural': 'Solicitações de Cotação'},
        ),
        migrations.CreateModel(
            name='RespostaCotacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recusou', models.BooleanField(default=False, verbose_name='Fornecedor recusou')),
                ('valor_respondido', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor unitário respondido (R$)')),
                ('resposta_pdf', models.FileField(blank=True, null=True, upload_to='cotacoes/respostas/', verbose_name='PDF da proposta/cotação recebida')),
                ('data_resposta', models.DateField(verbose_name='Data da resposta')),
                ('escolhida', models.BooleanField(default=False, verbose_name='Usar como referência de preço')),
                ('justificativa_escolha', models.TextField(blank=True, default='', help_text='Art. 3º, inc. VII — Por que esta resposta foi adotada como referência.', verbose_name='Justificativa da escolha deste fornecedor')),
                ('observacoes', models.TextField(blank=True, default='', verbose_name='Observações')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('fornecedor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='respostas_cotacao', to='modulo_fornecedor.fornecedor', verbose_name='Fornecedor')),
                ('solicitacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respostas', to='modulo_mapa_precos.solicitacaocotacao', verbose_name='Solicitação de cotação')),
            ],
            options={
                'verbose_name': 'Resposta de Cotação',
                'verbose_name_plural': 'Respostas de Cotação',
                'ordering': ['-data_resposta'],
            },
        ),
    ]
