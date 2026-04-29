from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_tr', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tr',
            name='tipo_prazo_vigencia',
            field=models.CharField(
                blank=True, default='', max_length=20,
                choices=[
                    ('escopo',      'Por Escopo — Aquisição/entrega única (AFM, Art. 105)'),
                    ('continuo',    'Contínuo — Serviço continuado (até 5 anos prorrogável, Art. 106/107)'),
                    ('emergencial', 'Emergencial — Contratação direta emergência (até 1 ano, Art. 75, VIII)'),
                    ('direta_108',  'Contratação Direta Art. 108 — Obras/serviços especiais (até 10 anos)'),
                ],
                verbose_name='Tipo de prazo de vigência',
            ),
        ),
        migrations.AddField(
            model_name='tr',
            name='prazo_meses',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Prazo em meses'),
        ),
        migrations.AddField(
            model_name='tr',
            name='instrumento_inicio',
            field=models.CharField(
                blank=True, default='', max_length=10,
                choices=[
                    ('contrato', 'Assinatura do Contrato'),
                    ('afm',      'AFM — Autorização de Fornecimento de Material'),
                    ('aps',      'APS — Autorização de Prestação de Serviços'),
                ],
                verbose_name='Instrumento de início da vigência',
            ),
        ),
        migrations.AddField(
            model_name='tr',
            name='prazo_observacao',
            field=models.TextField(blank=True, default='', verbose_name='Redação do prazo de vigência'),
        ),
    ]
