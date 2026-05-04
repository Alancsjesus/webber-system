from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('modulo_mapa_precos', '0003_precocoletado_arquivo')]
    operations = [migrations.AddField(
        model_name='historicomapa', name='categoria_motivo',
        field=models.CharField(blank=True, choices=[
            ('fontes_inadequadas', 'Fontes de pesquisa inadequadas'),
            ('cotacoes_fora_prazo', 'Cotações fora do prazo'),
            ('qtd_insuficiente', 'Número insuficiente de cotações'),
            ('metodo_inadequado', 'Método de cálculo inadequado'),
            ('outro', 'Outro'),
        ], default='', max_length=40, verbose_name='Categoria do motivo'),
    )]
