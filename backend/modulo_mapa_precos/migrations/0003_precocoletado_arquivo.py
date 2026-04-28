from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_mapa_precos', '0002_workflow_aprovacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='precocoletado',
            name='arquivo',
            field=models.FileField(
                blank=True, null=True,
                upload_to='cotacoes/',
                verbose_name='Documento comprobatório (PDF/imagem)',
            ),
        ),
    ]
