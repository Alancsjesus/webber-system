"""
Serviços de consolidação de itens do Plano de Aplicação e geração automática
de Necessidades de Planejamento a partir de grupos consolidados.

Reaproveita deliberadamente a ponte já existente entre órgão pai/filho em
NecessidadePlanejamento (tipo_execucao/org_gestor/orgao_executor/aceite_pai)
em vez de inventar criação cross-tenant de DFD — ver plano de implementação.
"""
from decimal import Decimal
from itertools import groupby

from django.db import transaction


def chave_agrupamento(item):
    """
    Chave usada para sugerir consolidação entre itens de unidades/órgãos
    diferentes: prefere a família SIMPAS (quando o item está vinculado ao
    catálogo interno); cai para os dois primeiros segmentos do Cód. SENASP
    (ex: "MAT.14.006.0002" -> "MAT.14") quando não há vínculo de catálogo.
    """
    if item.item_catalogo_id and item.item_catalogo.familia:
        return item.item_catalogo.familia
    if item.codigo_senasp:
        partes = item.codigo_senasp.split('.')
        return '.'.join(partes[:2]) if len(partes) >= 2 else item.codigo_senasp
    return ''


@transaction.atomic
def gerar_necessidades_de_grupo(grupo, request):
    """
    Cria uma NecessidadePlanejamento por org_beneficiaria presente no grupo
    de consolidação, populada a partir dos itens daquele órgão. A partir daí
    o fluxo já existente (NecessidadeViewSet.iniciar_dfd) assume o controle
    — nenhuma alteração é feita nesse endpoint.
    """
    from modulo_planejamento.models import NecessidadePlanejamento, HistoricoNecessidade
    from .models import ItemPlanoAplicacao

    itens = list(
        grupo.itens
        .filter(status__in=('pendente', 'consolidado'))
        .select_related('org_beneficiaria', 'unidade_beneficiaria')
        .order_by('org_beneficiaria_id')
    )
    if not itens:
        return []

    plano = grupo.plano
    necessidades_criadas = []

    for _, grupo_itens_iter in groupby(itens, key=lambda i: i.org_beneficiaria_id):
        grupo_itens = list(grupo_itens_iter)
        org_beneficiaria = grupo_itens[0].org_beneficiaria
        valor_total = sum((i.valor_total_estimado for i in grupo_itens), Decimal('0'))
        e_externa = org_beneficiaria.id != plano.org_id_id

        unidades_distintas = {i.unidade_beneficiaria_id for i in grupo_itens}
        unidade_unica = grupo_itens[0].unidade_beneficiaria if len(unidades_distintas) == 1 else None

        nec = NecessidadePlanejamento.objects.create(
            titulo=f'{grupo.titulo} — {org_beneficiaria.sigla}',
            descricao=(
                grupo.descricao
                or f'Necessidade consolidada a partir do Plano de Aplicação {plano.numero} '
                   f'(grupo "{grupo.titulo}").'
            ),
            valor_estimado=valor_total,
            departamento_solicitante=unidade_unica.nome if unidade_unica else org_beneficiaria.nome,
            exercicio_fiscal=plano.exercicio_fiscal,
            org_id=org_beneficiaria,
            unidade_demandante=unidade_unica,
            tipo_execucao='externa' if e_externa else 'interna',
            aceite_pai='aceita' if e_externa else None,
            org_gestor=plano.org_id if e_externa else None,
            orgao_executor=plano.org_id if e_externa else org_beneficiaria,
            origem_plano_aplicacao_fesp=plano,
            status='Aprovada',
            created_by=request.user, updated_by=request.user,
        )
        HistoricoNecessidade.objects.create(
            necessidade=nec, status_anterior='', status_novo='Aprovada', usuario=request.user,
            motivo=(
                f'Gerada automaticamente a partir do grupo de consolidação "{grupo.titulo}" '
                f'do Plano de Aplicação {plano.numero}.'
            ),
        )
        ItemPlanoAplicacao.objects.filter(pk__in=[i.pk for i in grupo_itens]).update(
            necessidade_gerada=nec, status='necessidade_gerada',
        )
        necessidades_criadas.append(nec)

    grupo.status = 'processado'
    grupo.save(update_fields=['status'])
    return necessidades_criadas


@transaction.atomic
def gerar_necessidade_individual(item, request):
    """
    Para um item sem par de consolidação (não bate com nenhuma família/
    código de outro item): cria um GrupoConsolidacaoItem de 1 item e chama
    gerar_necessidades_de_grupo, evitando ter dois caminhos de código.
    """
    from .models import GrupoConsolidacaoItem

    grupo = GrupoConsolidacaoItem.objects.create(
        org_id=item.org_id, created_by=request.user, updated_by=request.user,
        plano=item.meta_especifica.plano,
        chave_agrupamento=chave_agrupamento(item),
        titulo=item.bem_servico,
        descricao=item.descricao,
    )
    item.grupo_consolidacao = grupo
    item.status = 'consolidado'
    item.save(update_fields=['grupo_consolidacao', 'status'])

    resultado = gerar_necessidades_de_grupo(grupo, request)
    return resultado[0] if resultado else None
