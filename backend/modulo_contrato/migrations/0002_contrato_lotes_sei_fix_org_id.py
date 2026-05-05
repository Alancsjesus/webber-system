import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('modulo_contrato', '0001_initial'),
        ('modulo_tr', '0006_historicotr_categoria_motivo'),
    ]

    operations = [
        # Fix pre-existing org_id inconsistency on Apostila and Aditivo
        # (migration 0001 set them as nullable SET_NULL; BaseModel requires CASCADE non-null)
        migrations.RunSQL(
            sql="UPDATE modulo_contrato_apostila SET org_id_id = (SELECT id FROM core_orgao LIMIT 1) WHERE org_id_id IS NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="UPDATE modulo_contrato_aditivo SET org_id_id = (SELECT id FROM core_orgao LIMIT 1) WHERE org_id_id IS NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='apostila',
            name='org_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='apostilas_org', to='core.orgao'),
        ),
        migrations.AlterField(
            model_name='aditivo',
            name='org_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aditivos_org', to='core.orgao'),
        ),
        # Also fix Contrato.org_id for consistency
        migrations.RunSQL(
            sql="UPDATE modulo_contrato_contrato SET org_id_id = (SELECT id FROM core_orgao LIMIT 1) WHERE org_id_id IS NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='contrato',
            name='org_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contratos_org', to='core.orgao'),
        ),
        # New fields
        migrations.AddField(
            model_name='contrato',
            name='numero_processo_sei',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Número do processo SEI do contrato'),
        ),
        migrations.AddField(
            model_name='contrato',
            name='lotes',
            field=models.ManyToManyField(blank=True, related_name='contratos', to='modulo_tr.lotetr', verbose_name='Lotes de origem'),
        ),
    ]
