import django.db.models.deletion
from django.db import migrations, models


def popular_siglas(apps, schema_editor):
    """Gera siglas a partir das iniciais do nome do órgão."""
    Orgao = apps.get_model('core', 'Orgao')
    usadas = set()
    for orgao in Orgao.objects.all().order_by('id'):
        palavras = orgao.nome.split()
        candidata = ''.join(w[0].upper() for w in palavras if w)[:20]
        sigla = candidata
        sufixo = 1
        while sigla in usadas:
            sigla = f'{candidata[:18]}{sufixo}'
            sufixo += 1
        orgao.sigla = sigla
        orgao.save(update_fields=['sigla'])
        usadas.add(sigla)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_org_tipo_hierarquia_papeis'),
    ]

    operations = [
        # 1. Renomeia Organization → Orgao (renomeia tabela e atualiza FK refs)
        migrations.RenameModel('Organization', 'Orgao'),

        # 2. Remove campos do modelo antigo
        migrations.RemoveField(model_name='orgao', name='tipo'),
        migrations.RemoveField(model_name='orgao', name='vinculada_a'),
        migrations.RemoveField(model_name='orgao', name='cnpj'),

        # 3. Adiciona sigla (nullable inicialmente)
        migrations.AddField(
            model_name='orgao',
            name='sigla',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),

        # 4. Popula siglas
        migrations.RunPython(popular_siglas, migrations.RunPython.noop),

        # 5. Torna sigla obrigatória e única
        migrations.AlterField(
            model_name='orgao',
            name='sigla',
            field=models.CharField(max_length=20, unique=True),
        ),

        # 6. Adiciona hierarquia pai/filho
        migrations.AddField(
            model_name='orgao',
            name='parent',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orgaos_filhos',
                to='core.orgao',
            ),
        ),

        # 7. Cria UnidadeOrganizacional
        migrations.CreateModel(
            name='UnidadeOrganizacional',
            fields=[
                ('id',    models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome',  models.CharField(max_length=200)),
                ('sigla', models.CharField(max_length=30)),
                ('tipo',  models.CharField(
                    max_length=20,
                    choices=[
                        ('demandante',  'Unidade Demandante'),
                        ('licitante',   'Unidade Licitante'),
                        ('contratante', 'Unidade Contratante'),
                    ],
                )),
                ('ativa', models.BooleanField(default=True)),
                ('orgao', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='unidades',
                    to='core.orgao',
                )),
            ],
            options={
                'verbose_name': 'Unidade Organizacional',
                'verbose_name_plural': 'Unidades Organizacionais',
                'ordering': ['orgao', 'sigla'],
                'unique_together': {('orgao', 'sigla', 'tipo')},
            },
        ),

        # 8. Adiciona unidade ao UserProfile
        migrations.AddField(
            model_name='userprofile',
            name='unidade',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='usuarios',
                to='core.unidadeorganizacional',
            ),
        ),
    ]
