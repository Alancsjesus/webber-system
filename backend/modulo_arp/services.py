"""Lógica de negócio do módulo ARP reaproveitada fora do ViewSet — extraída de
AtaViewSet.confronto (a action original permanece, agora só chamando isto) para
que o Cronograma de Início Sugerido (core/cronograma_contratacoes.py) possa
descobrir Atas vigentes com saldo sem duplicar a query."""
from .models import ItemAta


def atas_vigentes_com_saldo_por_catalogo(org_id):
    """{item_catalogo_id: [ItemAta, ...]} — só Atas vigentes e com saldo > 0."""
    itens_ata_vigentes = (
        ItemAta.objects
        .filter(ata__org_id=org_id, ata__status='vigente', item_catalogo__isnull=False)
        .select_related('ata', 'item_catalogo', 'fornecedor')
    )
    por_catalogo = {}
    for item_ata in itens_ata_vigentes:
        if item_ata.saldo_disponivel <= 0:
            continue
        por_catalogo.setdefault(item_ata.item_catalogo_id, []).append(item_ata)
    return por_catalogo
