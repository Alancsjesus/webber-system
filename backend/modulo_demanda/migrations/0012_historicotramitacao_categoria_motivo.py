from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('modulo_demanda', '0011_itemdfd_catalogo')]
    operations = [migrations.AddField(
        model_name='historicotramitacao', name='categoria_motivo',
        field=models.CharField(blank=True, choices=[
            ('documentacao_incompleta', 'Documentação incompleta'),
            ('valor_incorreto', 'Valor estimado incorreto'),
            ('areas_inconsistentes', 'Áreas de aplicação inconsistentes'),
            ('especificacao_inadequada', 'Especificação inadequada'),
            ('sem_vinculo_orcamentario', 'Sem vinculação orçamentária'),
            ('outro', 'Outro'),
        ], default='', max_length=40, verbose_name='Categoria do motivo'),
    )]
