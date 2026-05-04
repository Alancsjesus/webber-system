from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('modulo_etp', '0005_etp_remove_adjudicacao_por_item')]
    operations = [migrations.AddField(
        model_name='historicoetp', name='categoria_motivo',
        field=models.CharField(blank=True, choices=[
            ('alternativas_insuficientes', 'Alternativas insuficientes'),
            ('estimativa_sem_referencia', 'Estimativa de valor sem referência'),
            ('requisitos_incompletos', 'Requisitos técnicos incompletos'),
            ('fontes_inadequadas', 'Fontes de pesquisa inadequadas'),
            ('outro', 'Outro'),
        ], default='', max_length=40, verbose_name='Categoria do motivo'),
    )]
