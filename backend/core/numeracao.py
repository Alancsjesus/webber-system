"""
Numeração sequencial de documentos (PE-CLIC-001/2026, SSP-003/2026-MED-002...).

Os geradores partiam de `count() + 1`, que repete um número já usado assim que
um registro do meio da série é excluído (ex.: 3 procedimentos, exclui o 1º →
o próximo sai "003" de novo). Aqui o sequencial avança até um número livre.
"""


def numero_livre(model, formato, seq, campo='numero'):
    """Primeiro `formato(n)`, n >= seq, que ainda não existe em `model.campo`."""
    while model.objects.filter(**{campo: formato(seq)}).exists():
        seq += 1
    return formato(seq)
