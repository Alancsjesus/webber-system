import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('modulo_demanda', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contrato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('numero', models.CharField(editable=False, max_length=30, unique=True, verbose_name='Número do contrato')),
                ('exercicio', models.IntegerField(verbose_name='Exercício fiscal')),
                ('objeto', models.TextField(verbose_name='Objeto do contrato')),
                ('tipo_origem', models.CharField(choices=[('licitacao', 'Licitação'), ('dispensa', 'Dispensa de Licitação'), ('inexigibilidade', 'Inexigibilidade'), ('saque_arp', 'Saque de ATA de Registro de Preços'), ('adesao_arp', 'Adesão a ATA de Registro de Preços')], max_length=20, verbose_name='Origem do contrato')),
                ('valor_contrato', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Valor do contrato (R$)')),
                ('data_assinatura', models.DateField(blank=True, null=True, verbose_name='Data de assinatura')),
                ('data_vigencia_inicio', models.DateField(blank=True, null=True, verbose_name='Início da vigência')),
                ('data_vigencia_fim', models.DateField(blank=True, null=True, verbose_name='Fim da vigência')),
                ('status', models.CharField(choices=[('Vigente', 'Vigente'), ('Encerrado', 'Encerrado'), ('Suspenso', 'Suspenso'), ('Rescindido', 'Rescindido')], default='Vigente', max_length=15)),
                ('observacoes', models.TextField(blank=True, default='')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
                ('org_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratos_org', to='core.orgao')),
                ('orgao_executor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='contratos', to='core.orgao', verbose_name='Órgão executor')),
                ('dfd', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratos', to='modulo_demanda.dfd', verbose_name='DFD de origem')),
                ('fiscal_contrato', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratos_fiscal', to=settings.AUTH_USER_MODEL, verbose_name='Fiscal do contrato')),
                ('gestor_contrato', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratos_gestor', to=settings.AUTH_USER_MODEL, verbose_name='Gestor do contrato')),
                ('ordenador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratos_ordenador', to=settings.AUTH_USER_MODEL, verbose_name='Ordenador de despesa')),
            ],
            options={'ordering': ['-exercicio', 'numero'], 'abstract': False},
        ),
        migrations.CreateModel(
            name='Apostila',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('numero', models.CharField(editable=False, max_length=40, verbose_name='Número da apostila')),
                ('objeto', models.TextField(verbose_name='Objeto da apostila')),
                ('data', models.DateField(verbose_name='Data da apostila')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
                ('org_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='apostilas_org', to='core.orgao')),
                ('contrato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='apostilas', to='modulo_contrato.contrato')),
            ],
            options={'ordering': ['data'], 'abstract': False},
        ),
        migrations.CreateModel(
            name='Aditivo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('numero', models.CharField(editable=False, max_length=40, verbose_name='Número do aditivo')),
                ('tipo', models.CharField(choices=[('prazo', 'Prorrogação de Prazo'), ('valor', 'Acréscimo/Redução de Valor'), ('objeto', 'Alteração de Objeto'), ('rescisao', 'Rescisão')], max_length=10, verbose_name='Tipo de aditivo')),
                ('valor_acrescimo', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor acrescido/reduzido (R$)')),
                ('nova_vigencia', models.DateField(blank=True, null=True, verbose_name='Nova data de vigência')),
                ('objeto', models.TextField(verbose_name='Objeto do aditivo')),
                ('data', models.DateField(verbose_name='Data do aditivo')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
                ('org_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='aditivos_org', to='core.orgao')),
                ('contrato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aditivos', to='modulo_contrato.contrato')),
            ],
            options={'ordering': ['data'], 'abstract': False},
        ),
    ]
