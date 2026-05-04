from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('modulo_tr', '0005_itemlotetr_preco_referencia')]
    operations = [migrations.AddField(
        model_name='historicotr', name='categoria_motivo',
        field=models.CharField(blank=True, choices=[
            ('objeto_mal_definido', 'Objeto mal definido'),
            ('criterios_habilitacao_excess', 'Critérios de habilitação excessivos'),
            ('obrigacoes_desequilibradas', 'Obrigações desequilibradas'),
            ('prazo_irreal', 'Prazo irreal'),
            ('outro', 'Outro'),
        ], default='', max_length=40, verbose_name='Categoria do motivo'),
    )]
