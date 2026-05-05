import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('modulo_tr', '0006_historicotr_categoria_motivo'),
    ]

    operations = [
        # Fix pre-existing org_id inconsistency on LoteTR
        # (migration 0004 created it as null=True SET_NULL; BaseModel requires CASCADE non-null)
        migrations.RunSQL(
            sql="UPDATE modulo_tr_lotetr SET org_id_id = (SELECT id FROM core_orgao LIMIT 1) WHERE org_id_id IS NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='lotetr',
            name='org_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lotes_tr', to='core.orgao'),
        ),
        # New field: justificativa_agrupamento
        migrations.AddField(
            model_name='lotetr',
            name='justificativa_agrupamento',
            field=models.TextField(blank=True, default='', verbose_name='Justificativa do agrupamento de itens'),
        ),
    ]
