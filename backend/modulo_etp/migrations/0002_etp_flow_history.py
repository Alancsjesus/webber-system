import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_etp', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Add motivo_devolucao to ETP
        migrations.AddField(
            model_name='etp',
            name='motivo_devolucao',
            field=models.TextField(blank=True, null=True, verbose_name='Motivo da devolução'),
        ),
        # 2. Update status choices (data-only; max_length stays 15)
        migrations.AlterField(
            model_name='etp',
            name='status',
            field=models.CharField(
                choices=[
                    ('Rascunho',   'Rascunho'),
                    ('Submetido',  'Submetido'),
                    ('Em Análise', 'Em Análise'),
                    ('Devolvido',  'Devolvido'),
                    ('Aprovado',   'Aprovado'),
                    ('Cancelado',  'Cancelado'),
                ],
                default='Rascunho',
                max_length=15,
            ),
        ),
        # 3. HistoricoETP
        migrations.CreateModel(
            name='HistoricoETP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_anterior', models.CharField(max_length=15)),
                ('status_novo',     models.CharField(max_length=15)),
                ('motivo',          models.TextField(blank=True, null=True)),
                ('criado_em',       models.DateTimeField(auto_now_add=True)),
                ('etp', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historico',
                    to='modulo_etp.etp',
                )),
                ('usuario', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Histórico do ETP',
                'verbose_name_plural': 'Históricos do ETP',
                'ordering': ['-criado_em'],
            },
        ),
        # 4. HistoricoNumeroSEI
        migrations.CreateModel(
            name='HistoricoNumeroSEI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_anterior', models.CharField(max_length=50)),
                ('numero_novo',     models.CharField(max_length=50)),
                ('motivo',          models.TextField(blank=True, default='')),
                ('criado_em',       models.DateTimeField(auto_now_add=True)),
                ('etp', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historico_numero_sei',
                    to='modulo_etp.etp',
                )),
                ('usuario', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Histórico de Número SEI',
                'verbose_name_plural': 'Históricos de Número SEI',
                'ordering': ['-criado_em'],
            },
        ),
    ]
