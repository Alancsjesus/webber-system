from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_parametro_norma_vigencia'),
    ]

    operations = [
        migrations.CreateModel(
            name='AreaAtuacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=50, unique=True, verbose_name='Código')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('ativa', models.BooleanField(default=True, verbose_name='Ativa')),
            ],
            options={
                'verbose_name': 'Área de Atuação',
                'verbose_name_plural': 'Áreas de Atuação',
                'ordering': ['nome'],
            },
        ),
    ]
