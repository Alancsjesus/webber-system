"""
Exporta o banco atual (normalmente o SQLite local, já populado pelos seeds e
pelas cadeias E2E de scripts/e2e/cadeia.py) como a carga de demonstração que
o `carregar_demo` instala em produção.

O SQLite não barra valor acima do max_length nem fora das choices; o Postgres
barra o primeiro. Por isso a exportação normaliza os valores legados conhecidos
(CORRECOES) e valida o resto — se sobrar algo inválido, aborta sem gravar.

Uso:
    python manage.py exportar_demo            # grava core/fixtures/demo_webber.json.gz
"""
import gzip
import io
import json
import re
from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import models

ARQUIVO = Path(__file__).resolve().parents[2] / 'fixtures' / 'demo_webber.json.gz'

EXCLUIR = ['contenttypes', 'auth.permission', 'admin.logentry', 'sessions']

# Valores gravados antes das choices atuais existirem → valor equivalente de hoje.
CORRECOES = {
    ('modulo_tr.tr', 'instrumento_inicio'): {
        'nota_empenho': 'afm',     # NE substitui o contrato (art. 95) — compras
        'ordem_servico': 'aps',
    },
    ('modulo_tr.tr', 'tipo_prazo_vigencia'): {'meses': 'continuo'},
    ('modulo_planejamento.necessidadeplanejamento', 'prioridade'): {
        'alta': 'Alta', 'media': 'Média', 'baixa': 'Baixa',
    },
    ('modulo_etp.etp', 'tipo_objeto'): {
        'material': 'bens', 'servico_continuo': 'servicos', 'servico': 'servicos',
    },
    ('modulo_etp.etp', 'tipo_parcelamento'): {
        'parcelado': 'lotes', 'nao_parcelado': 'lote_unico',
    },
}


def _fundamento(valor, choices):
    """'art. 75, II — ...' → 'art75_ii' (fundamentos de dispensa/inexigibilidade em texto livre)."""
    m = re.match(r'\s*art\.?\s*(\d+)\s*,\s*([ivxlc]+)\b', valor, re.I)
    codigo = f'art{m.group(1)}_{m.group(2).lower()}' if m else None
    return codigo if codigo in choices else 'outro'


class Command(BaseCommand):
    help = 'Exporta o banco atual como carga de demonstração (core/fixtures/demo_webber.json.gz)'

    def handle(self, *args, **options):
        buf = io.StringIO()
        call_command('dumpdata', '--natural-foreign', *[f'--exclude={e}' for e in EXCLUIR], stdout=buf)
        # a versão instalada é estado do ambiente de destino, não dado da carga
        objetos = [o for o in json.loads(buf.getvalue())
                   if not (o['model'] == 'core.parametrosistema' and o['fields'].get('chave') == 'carga_demo_versao')]

        corrigidos, erros = 0, []
        for obj in objetos:
            model = apps.get_model(obj['model'])
            for f in model._meta.concrete_fields:
                if not isinstance(f, models.CharField) or f.name not in obj['fields']:
                    continue
                valor = obj['fields'][f.name]
                if not valor:
                    continue
                choices = {c[0] for c in f.flatchoices}
                novo = valor
                if (obj['model'], f.name) in CORRECOES:
                    novo = CORRECOES[(obj['model'], f.name)].get(valor, valor)
                elif choices and valor not in choices and f.name.startswith('fundamento_'):
                    novo = _fundamento(valor, choices)
                if novo != valor:
                    obj['fields'][f.name] = novo
                    corrigidos += 1
                    self.stdout.write(f'  ~ {obj["model"]}#{obj["pk"]}.{f.name}: {valor!r} → {novo!r}')
                if choices and novo not in choices:
                    erros.append(f'{obj["model"]}#{obj["pk"]}.{f.name}: {novo!r} fora das choices')
                if f.max_length and len(novo) > f.max_length:
                    erros.append(f'{obj["model"]}#{obj["pk"]}.{f.name}: {len(novo)} > {f.max_length} caracteres')

        if erros:
            raise CommandError('Valores inválidos para o Postgres (corrija ou inclua em CORRECOES):\n  '
                               + '\n  '.join(erros))

        ARQUIVO.parent.mkdir(exist_ok=True)
        # mtime=0: mesmo conteúdo → mesmo arquivo (a versão da carga é o hash dele)
        with open(ARQUIVO, 'wb') as bruto, gzip.GzipFile(filename='', mode='wb', fileobj=bruto, mtime=0) as gz:
            gz.write(json.dumps(objetos, ensure_ascii=False).encode('utf-8'))
        self.stdout.write(self.style.SUCCESS(
            f'{len(objetos)} objetos exportados ({corrigidos} valores normalizados) → {ARQUIVO}'))
