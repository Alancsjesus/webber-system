"""
Estimativa de valor do TR como consolidação do Mapa de Preços aprovado
(Lei 14.133, art. 23; Decreto Estadual 22.886/2024): cada item dos lotes é
precificado pelo item correspondente do Mapa aprovado do DFD, e a estimativa
do TR é a soma dos lotes — não um número digitado.
"""
from decimal import Decimal


def mapa_aprovado(dfd):
    """Mapa de Preços aprovado mais recente do DFD (ou None)."""
    if dfd is None:
        return None
    from modulo_mapa_precos.models import MapaComparativoPrecos
    return (MapaComparativoPrecos.objects
            .filter(dfd=dfd, status='Aprovado').order_by('-created_at').first())


def item_do_mapa(item_dfd, mapa):
    """
    Item do Mapa que corresponde ao ItemDFD: 1) código SIMPAS do catálogo;
    2) descrição (primeiros 20 caracteres); 3) posição, quando DFD e Mapa têm
    o mesmo número de itens.
    """
    if item_dfd is None or mapa is None:
        return None
    itens = list(mapa.itens.order_by('ordem', 'id'))
    simpas = item_dfd.item_catalogo.codigo_simpas if item_dfd.item_catalogo_id else ''
    if simpas:
        achado = next((i for i in itens if i.codigo_simpas == simpas), None)
        if achado:
            return achado
    if item_dfd.objeto:
        trecho = item_dfd.objeto[:20].lower()
        achado = next((i for i in itens if trecho in (i.descricao or '').lower()), None)
        if achado:
            return achado
    dfd_itens = list(item_dfd.dfd.itens.order_by('id'))
    if len(dfd_itens) == len(itens) and item_dfd in dfd_itens:
        return itens[dfd_itens.index(item_dfd)]
    return None


def preco_referencia(item_dfd, mapa=None):
    """(valor_unitario, origem, item_mapa) — Mapa aprovado se houver, senão estimativa do DFD."""
    if item_dfd is None:
        return None, 'dfd', None
    mapa = mapa if mapa is not None else mapa_aprovado(item_dfd.dfd)
    item_mapa = item_do_mapa(item_dfd, mapa)
    if item_mapa is not None and item_mapa.valor_unitario_calculado:
        return item_mapa.valor_unitario_calculado, 'mapa', item_mapa
    return item_dfd.valor_unitario_estimado, 'dfd', None


def atualizar_precos(tr):
    """
    Reprecifica os itens dos lotes pelo Mapa aprovado atual e grava a
    estimativa consolidada no TR. Chamado ao aprovar o Mapa e ao submeter o TR.
    """
    from .models import ItemLoteTR
    mapa = mapa_aprovado(tr.etp.dfd)
    for item in ItemLoteTR.objects.filter(lote__tr=tr).select_related('item_dfd__item_catalogo', 'item_dfd__dfd'):
        valor, origem, _ = preco_referencia(item.item_dfd, mapa)
        if (item.valor_unitario_ref, item.preco_origem) != (valor, origem):
            item.valor_unitario_ref, item.preco_origem = valor, origem
            item.save(update_fields=['valor_unitario_ref', 'preco_origem'])
    recalcular_estimativa(tr)


def recalcular_estimativa(tr):
    """estimativa_valor do TR = soma dos lotes (sem as cotas ME/EPP, que são recorte do lote de origem)."""
    from .models import TR, ItemLoteTR
    total = sum(
        (i.valor_total for i in ItemLoteTR.objects.filter(lote__tr=tr)
         .exclude(lote__modalidade='cota_me_epp').select_related('item_dfd')),
        Decimal('0'),
    ).quantize(Decimal('0.01'))
    TR.objects.filter(pk=tr.pk).update(estimativa_valor=total)
    tr.estimativa_valor = total
    return total


def consolidar(tr):
    """
    Quadro da estimativa: lotes → itens com códigos, quantidade, unidade,
    valor unitário, total e origem do preço; total geral e pendências.
    """
    mapa = mapa_aprovado(tr.etp.dfd)
    lotes, total, sem_mapa = [], Decimal('0'), 0
    for lote in tr.lotes.all():
        linhas, subtotal = [], Decimal('0')
        for item in lote.itens.all():
            idfd = item.item_dfd
            cat = idfd.item_catalogo if idfd is not None else None
            item_mapa = item_do_mapa(idfd, mapa) if item.preco_origem == 'mapa' else None
            if item.preco_origem != 'mapa':
                sem_mapa += 1
            valor_total = item.valor_total.quantize(Decimal('0.01'))
            subtotal += valor_total
            linhas.append({
                'item_lote_id': item.id,
                'descricao': idfd.objeto if idfd else '—',
                'codigo_simpas': (cat.codigo_simpas if cat else '') or (item_mapa.codigo_simpas if item_mapa else ''),
                'codigo_interno': cat.codigo_interno if cat else '',
                'unidade': idfd.unidade_medida if idfd else '',
                'quantidade': f'{item.quantidade.normalize():f}',
                'valor_unitario': str(item.valor_unitario_efetivo),
                'valor_total': str(valor_total),
                'origem': item.preco_origem,
                'metodo': item_mapa.get_metodo_aplicado_display() if item_mapa and item_mapa.metodo_aplicado else '',
            })
        eh_cota = lote.modalidade == 'cota_me_epp'
        if not eh_cota:
            total += subtotal
        lotes.append({
            'id': lote.id, 'numero': lote.numero, 'descricao': lote.descricao,
            'modalidade': lote.get_modalidade_display(), 'cota': eh_cota,
            'itens': linhas, 'subtotal': str(subtotal),
        })
    return {
        'mapa': ({'id': mapa.id, 'metodo': mapa.get_metodo_calculo_display(),
                  'data_aprovacao': mapa.data_aprovacao.isoformat() if mapa.data_aprovacao else None}
                 if mapa else None),
        'lotes': lotes,
        'total': str(total.quantize(Decimal('0.01'))),
        'itens_sem_mapa': sem_mapa,
    }
