"""
Saque de Ata de Registro de Preços: contratação a partir de Ata vigente.

Não tem TR/ETP/Mapa próprios — essas peças foram produzidas na formação da
Ata (o TR do procedimento de SRP é a minuta). Exige DFD aprovado com DOD (é
no saque que o orçamento é comprometido) e saldo na Ata para cada item.
"""
from collections import defaultdict
from decimal import Decimal


class SaqueInvalido(Exception):
    pass


def itens_do_saque(dfd, ata):
    """
    Casa cada item do DFD com o item da Ata (pelo item de catálogo) e confere
    saldo. Retorna [(item_dfd, item_ata, quantidade)]; levanta SaqueInvalido
    com a lista de problemas.
    """
    problemas, pares = [], []
    itens_ata = list(ata.itens.select_related('item_catalogo', 'fornecedor'))
    for item in dfd.itens.select_related('item_catalogo'):
        if not item.item_catalogo_id:
            problemas.append(f'"{item.objeto}" não está vinculado ao catálogo — não há como localizá-lo na Ata.')
            continue
        item_ata = next((i for i in itens_ata if i.item_catalogo_id == item.item_catalogo_id), None)
        if item_ata is None:
            problemas.append(f'"{item.objeto}" não está registrado na Ata {ata.numero_ata}.')
        elif item_ata.saldo_disponivel < item.quantidade:
            problemas.append(f'"{item.objeto}": saldo na Ata {item_ata.saldo_disponivel.normalize():f} '
                             f'< quantidade pedida {item.quantidade.normalize():f}.')
        elif item_ata.fornecedor_id is None:
            problemas.append(f'"{item.objeto}": item da Ata sem fornecedor registrado.')
        else:
            pares.append((item, item_ata, item.quantidade))
    if problemas:
        raise SaqueInvalido(problemas)
    if not pares:
        raise SaqueInvalido(['O DFD não tem itens.'])
    return pares


def validar_ata(ata, hoje):
    if ata.status != 'vigente':
        raise SaqueInvalido([f'A Ata {ata.numero_ata} não está vigente (status: {ata.get_status_display()}).'])
    if ata.data_vigencia_fim and ata.data_vigencia_fim < hoje:
        raise SaqueInvalido([f'A vigência da Ata {ata.numero_ata} terminou em {ata.data_vigencia_fim:%d/%m/%Y}.'])


def por_fornecedor(pares):
    """Agrupa os itens por fornecedor registrado: {fornecedor: [(item_dfd, item_ata, qtd)]}."""
    grupos = defaultdict(list)
    for par in pares:
        grupos[par[1].fornecedor].append(par)
    return grupos


def valor(pares):
    return sum((qtd * item_ata.valor_unitario_registrado for _, item_ata, qtd in pares), Decimal('0')).quantize(Decimal('0.01'))


def consumir_saldo(pares):
    from django.db.models import F
    from modulo_arp.models import ItemAta
    for _, item_ata, qtd in pares:
        ItemAta.objects.filter(pk=item_ata.pk).update(quantidade_consumida=F('quantidade_consumida') + qtd)
