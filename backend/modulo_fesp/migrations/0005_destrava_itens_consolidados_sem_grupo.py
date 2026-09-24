"""
Itens do Plano de Aplicação com status "consolidado" mas sem grupo e sem
necessidade ficavam presos (não geram necessidade individual nem entram em
nova consolidação). Volta-os para "pendente".
"""
from django.db import migrations


def destravar(apps, schema_editor):
    Item = apps.get_model('modulo_fesp', 'ItemPlanoAplicacao')
    Item.objects.filter(
        status='consolidado', grupo_consolidacao__isnull=True, necessidade_gerada__isnull=True,
    ).update(status='pendente')


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_fesp', '0004_alter_planoaplicacao_ementa'),
    ]

    operations = [
        migrations.RunPython(destravar, migrations.RunPython.noop),
    ]
