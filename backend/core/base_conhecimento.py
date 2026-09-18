"""
Base de conhecimento estruturada (D3 — Solução 6 do diagnóstico CLIC):
"quais processos semelhantes a este já foram analisados" e "quantos retornos
esse tipo de processo já teve". Usa o vínculo já existente entre ItemDFD e o
catálogo (item_catalogo_id) para achar outros DFDs que compraram/tentaram
comprar os mesmos itens — não é busca semântica/NLP, é o mesmo dado
estruturado que o catálogo SIMPAS já garante, sem exigir campo novo.

Escopo v1: similaridade por item de catálogo compartilhado, dentro do
mesmo órgão. Cross-org fica para uma extensão futura, se fizer sentido de
negócio (comparar como outro órgão resolveu a mesma família de compra).
"""
from core.views_rastreabilidade import _rel


def _total_devolucoes(dfd):
    """Soma devoluções em toda a cadeia DFD→ETP→TR desse processo."""
    total = dfd.historico.filter(status_novo='Devolvida').count()
    etp = _rel(dfd, 'etp')
    if etp:
        total += etp.historico.filter(status_novo='Devolvido').count()
        tr = _rel(etp, 'tr')
        if tr:
            total += tr.historico.filter(status_novo='Devolvido').count()
    return total


def _etapa_atual_label(dfd):
    from modulo_tramitacao.estagio import estagio_atual_dfd
    estagio = estagio_atual_dfd(dfd)
    return estagio[0] if estagio else 'Concluído (execução)'


def buscar_similares(dfd, org_id):
    from modulo_demanda.models import DFD, ItemDFD

    itens_ref = list(
        ItemDFD.objects.filter(dfd=dfd, item_catalogo__isnull=False)
        .values('item_catalogo_id', 'item_catalogo__nome', 'item_catalogo__familia')
        .distinct()
    )
    catalogo_ids = [i['item_catalogo_id'] for i in itens_ref]

    referencia = {'id': dfd.id, 'numero_sei': dfd.numero_sei, 'objeto': dfd.descricao}

    if not catalogo_ids:
        return {'dfd_referencia': referencia, 'itens_compartilhados': [], 'similares': []}

    candidatos = (
        DFD.objects.filter(org_id=org_id, itens__item_catalogo_id__in=catalogo_ids)
        .exclude(pk=dfd.pk)
        .distinct()
        .select_related('etp__tr')
    )

    similares = []
    for c in candidatos:
        itens_comum = (
            ItemDFD.objects.filter(dfd=c, item_catalogo_id__in=catalogo_ids)
            .values('item_catalogo_id').distinct().count()
        )
        similares.append({
            'dfd_id': c.id,
            'numero_sei': c.numero_sei,
            'objeto': c.descricao,
            'status': c.status,
            'etapa_atual': _etapa_atual_label(c),
            'itens_em_comum': itens_comum,
            'total_devolucoes': _total_devolucoes(c),
            'criado_em': c.created_at.date().isoformat() if c.created_at else None,
        })

    similares.sort(key=lambda s: (-s['itens_em_comum'], -s['total_devolucoes']))

    return {
        'dfd_referencia': referencia,
        'itens_compartilhados': [
            {
                'item_catalogo_id': i['item_catalogo_id'],
                'nome': i['item_catalogo__nome'],
                'familia': i['item_catalogo__familia'],
            }
            for i in itens_ref
        ],
        'similares': similares,
    }
