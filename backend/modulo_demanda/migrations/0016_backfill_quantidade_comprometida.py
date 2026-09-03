from decimal import Decimal
from django.db import migrations, models


def backfill(apps, schema_editor):
    """
    Recalcula ItemDFD.quantidade_comprometida para itens criados antes deste
    campo existir. Sem isso, itens já comprometidos em TRs/lotes anteriores
    ficariam marcados como 'disponivel', permitindo comprometê-los de novo
    em outro lote (a duplicação que este campo existe para evitar).
    Reproduz a mesma regra do sinal em modulo_tr.models: exclui lotes de
    Reserva de Cota ME/EPP do somatório (são recorte do lote de origem).
    """
    ItemDFD = apps.get_model('modulo_demanda', 'ItemDFD')
    ItemLoteTR = apps.get_model('modulo_tr', 'ItemLoteTR')

    somas = (
        ItemLoteTR.objects
        .exclude(lote__modalidade='cota_me_epp')
        .exclude(item_dfd__isnull=True)
        .values('item_dfd')
        .annotate(total=models.Sum('quantidade'))
    )
    totais_por_item = {row['item_dfd']: row['total'] or Decimal('0') for row in somas}

    for item_id, total in totais_por_item.items():
        ItemDFD.objects.filter(pk=item_id).update(quantidade_comprometida=total)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_demanda', '0015_itemdfd_quantidade_comprometida'),
        ('modulo_tr', '0011_tr_req_vistoria_justificativa_obrigatoriedade'),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
