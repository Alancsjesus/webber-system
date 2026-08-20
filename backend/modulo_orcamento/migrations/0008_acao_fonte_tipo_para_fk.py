from django.db import migrations, models
import django.db.models.deletion


def backfill_tipo_fk(apps, schema_editor):
    AcaoOrcamentaria = apps.get_model('modulo_orcamento', 'AcaoOrcamentaria')
    FonteRecurso = apps.get_model('modulo_orcamento', 'FonteRecurso')
    TipoAcaoOrcamentaria = apps.get_model('modulo_orcamento', 'TipoAcaoOrcamentaria')
    TipoFonteRecurso = apps.get_model('modulo_orcamento', 'TipoFonteRecurso')

    for acao in AcaoOrcamentaria.objects.all():
        tipo, _ = TipoAcaoOrcamentaria.objects.get_or_create(descricao=acao.tipo)
        acao.tipo_novo_id = tipo.id
        acao.save(update_fields=['tipo_novo'])

    for fonte in FonteRecurso.objects.all():
        tipo, _ = TipoFonteRecurso.objects.get_or_create(descricao=fonte.tipo)
        fonte.tipo_novo_id = tipo.id
        fonte.save(update_fields=['tipo_novo'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_orcamento', '0007_tipo_acao_fonte_catalogos'),
    ]

    operations = [
        # 1) Cria colunas FK novas, ao lado das antigas CharField 'tipo'.
        migrations.AddField(
            model_name='acaoorcamentaria',
            name='tipo_novo',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='acoes', to='modulo_orcamento.tipoacaoorcamentaria',
                verbose_name='Tipo',
            ),
        ),
        migrations.AddField(
            model_name='fonterecurso',
            name='tipo_novo',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='fontes', to='modulo_orcamento.tipofonterecurso',
                verbose_name='Tipo',
            ),
        ),
        # 2) Preenche as novas colunas a partir do texto das antigas.
        migrations.RunPython(backfill_tipo_fk, noop),
        # 3) Remove as colunas antigas e promove as novas ao nome 'tipo'.
        migrations.RemoveField(model_name='acaoorcamentaria', name='tipo'),
        migrations.RemoveField(model_name='fonterecurso', name='tipo'),
        migrations.RenameField(model_name='acaoorcamentaria', old_name='tipo_novo', new_name='tipo'),
        migrations.RenameField(model_name='fonterecurso', old_name='tipo_novo', new_name='tipo'),
        # 4) Torna a FK obrigatória, já com todos os registros preenchidos.
        migrations.AlterField(
            model_name='acaoorcamentaria',
            name='tipo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='acoes', to='modulo_orcamento.tipoacaoorcamentaria',
                verbose_name='Tipo',
            ),
        ),
        migrations.AlterField(
            model_name='fonterecurso',
            name='tipo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='fontes', to='modulo_orcamento.tipofonterecurso',
                verbose_name='Tipo',
            ),
        ),
    ]
