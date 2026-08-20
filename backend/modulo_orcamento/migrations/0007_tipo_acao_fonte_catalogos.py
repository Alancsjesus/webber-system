from django.db import migrations, models


TIPOS_ACAO_SEED = [
    'Obra / Equipamento',
    'Funcionamento / Operação',
    'Capacitação',
    'Equipamento',
    'Publicidade',
    'Estudo / Projeto Obra',
    'Outras Atividades',
    'Serviço',
    'Outros Projetos',
    'Outras Operações Especiais',
    'Reserva de Contingência',
]

TIPOS_FONTE_SEED = [
    'Tesouro',
    'FESP',
    'FUNEBOM',
]


def seed_tipos(apps, schema_editor):
    TipoAcaoOrcamentaria = apps.get_model('modulo_orcamento', 'TipoAcaoOrcamentaria')
    TipoFonteRecurso = apps.get_model('modulo_orcamento', 'TipoFonteRecurso')
    for descricao in TIPOS_ACAO_SEED:
        TipoAcaoOrcamentaria.objects.get_or_create(descricao=descricao)
    for descricao in TIPOS_FONTE_SEED:
        TipoFonteRecurso.objects.get_or_create(descricao=descricao)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_orcamento', '0006_remove_indicacaoorcamentaria_unique_indicacao_numero_por_org_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoAcaoOrcamentaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=100, unique=True, verbose_name='Descrição')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Tipo de Ação Orçamentária',
                'verbose_name_plural': 'Tipos de Ação Orçamentária',
                'ordering': ['descricao'],
            },
        ),
        migrations.CreateModel(
            name='TipoFonteRecurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=100, unique=True, verbose_name='Descrição')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Tipo de Fonte de Recurso',
                'verbose_name_plural': 'Tipos de Fonte de Recurso',
                'ordering': ['descricao'],
            },
        ),
        migrations.RunPython(seed_tipos, noop),
    ]
