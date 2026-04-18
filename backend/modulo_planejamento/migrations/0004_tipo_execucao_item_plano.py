# Generated manually — fix M2M through table migration

import django.db.models.deletion
from django.db import migrations, models


def migrar_m2m_para_through(apps, schema_editor):
    """Migra linhas existentes da tabela M2M automática para ItemPlanoOrcamentario."""
    PlanoOrcamentario = apps.get_model('modulo_planejamento', 'PlanoOrcamentario')
    ItemPlanoOrcamentario = apps.get_model('modulo_planejamento', 'ItemPlanoOrcamentario')
    db_alias = schema_editor.connection.alias

    # Lê a tabela M2M antiga diretamente via SQL (a tabela ainda existe neste ponto)
    from django.db import connections
    conn = connections[db_alias]
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                'SELECT planoorcamentario_id, necessidadeplanejamento_id '
                'FROM modulo_planejamento_planoorcamentario_necessidades'
            )
            rows = cursor.fetchall()
        except Exception:
            rows = []

    for plano_id, nec_id in rows:
        try:
            plano = PlanoOrcamentario.objects.using(db_alias).get(pk=plano_id)
            nec   = apps.get_model('modulo_planejamento', 'NecessidadePlanejamento').objects.using(db_alias).get(pk=nec_id)
            origem = 'orgao_filho' if nec.org_id_id != plano.orgao_id else 'propria'
            ItemPlanoOrcamentario.objects.using(db_alias).get_or_create(
                plano=plano, necessidade=nec, defaults={'origem': origem}
            )
        except Exception:
            pass


def desfazer_migracao_m2m(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_planejamento', '0003_necessidade_org_gestor'),
    ]

    operations = [
        # 1. Adicionar tipo_execucao
        migrations.AddField(
            model_name='necessidadeplanejamento',
            name='tipo_execucao',
            field=models.CharField(
                choices=[('interna', 'Execução Interna'), ('externa', 'Execução Externa (Órgão Pai)')],
                default='interna', max_length=10, verbose_name='Tipo de execução',
            ),
        ),
        # 2. Criar a tabela through
        migrations.CreateModel(
            name='ItemPlanoOrcamentario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origem', models.CharField(
                    choices=[('propria', 'Demanda Própria'), ('orgao_filho', 'Demanda de Órgão Filho')],
                    default='propria', max_length=15,
                )),
                ('necessidade', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='itens_plano',
                    to='modulo_planejamento.necessidadeplanejamento',
                )),
                ('plano', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='itens',
                    to='modulo_planejamento.planoorcamentario',
                )),
            ],
            options={
                'verbose_name': 'Item do Plano Orçamentário',
                'verbose_name_plural': 'Itens do Plano Orçamentário',
                'unique_together': {('plano', 'necessidade')},
            },
        ),
        # 3. Migrar dados antes de remover a tabela antiga
        migrations.RunPython(migrar_m2m_para_through, desfazer_migracao_m2m),
        # 4. Remover M2M antiga (dropa a tabela auto-gerada)
        migrations.RemoveField(
            model_name='planoorcamentario',
            name='necessidades',
        ),
        # 5. Adicionar M2M nova com through explícito (sem criar nova tabela)
        migrations.AddField(
            model_name='planoorcamentario',
            name='necessidades',
            field=models.ManyToManyField(
                blank=True,
                related_name='planos',
                through='modulo_planejamento.ItemPlanoOrcamentario',
                to='modulo_planejamento.necessidadeplanejamento',
                verbose_name='Necessidades vinculadas',
            ),
        ),
    ]
