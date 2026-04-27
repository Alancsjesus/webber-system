from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_mapa_precos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapacomparativoprecos',
            name='status',
            field=models.CharField(
                choices=[
                    ('Rascunho', 'Rascunho'),
                    ('Submetido', 'Submetido para aprovação'),
                    ('Em Análise', 'Em análise pela Unidade Licitante'),
                    ('Aprovado', 'Aprovado'),
                    ('Devolvido', 'Devolvido para correção'),
                    ('Cancelado', 'Cancelado'),
                ],
                default='Rascunho', max_length=15, verbose_name='Status',
            ),
        ),
        migrations.AddField(
            model_name='mapacomparativoprecos',
            name='aprovador',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='mapas_aprovados',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Aprovador (Unidade Licitante)',
            ),
        ),
        migrations.AddField(
            model_name='mapacomparativoprecos',
            name='data_aprovacao',
            field=models.DateField(blank=True, null=True, verbose_name='Data de aprovação'),
        ),
        migrations.AddField(
            model_name='mapacomparativoprecos',
            name='motivo_devolucao',
            field=models.TextField(blank=True, default='', verbose_name='Motivo da devolução'),
        ),
        migrations.CreateModel(
            name='HistoricoMapa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('status_anterior', models.CharField(max_length=15)),
                ('status_novo', models.CharField(max_length=15)),
                ('motivo', models.TextField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('mapa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historico', to='modulo_mapa_precos.mapacomparativoprecos')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Histórico do Mapa', 'ordering': ['-criado_em']},
        ),
    ]
