"""
Helpers de agregação/indicadores do Plano de Aplicação FESP — compartilhados
entre o painel de execução (indicadores/execucao/) e o relatório de itens
(relatorio-itens/). Mantidos num módulo próprio para não inflar views.py.
"""
from django.db.models import Exists, OuterRef

from modulo_contrato.models import Contrato

from .models import ItemPlanoAplicacao


def anotar_execucao(queryset):
    """Anota cada ItemPlanoAplicacao com `executado` (bool).

    "Executado" = o DFD gerado pela necessidade do item já tem pelo menos um
    Contrato vinculado. Não navega toda a cadeia de rastreabilidade (ETP/TR/
    Procedimento) — só o elo final (Contrato) importa para essa decisão.
    """
    contrato_sub = Contrato.objects.filter(dfd_id=OuterRef('necessidade_gerada__dfd_id'))
    return queryset.annotate(executado=Exists(contrato_sub))


def itens_plano_aplicacao_queryset(org_id):
    """Queryset base de ItemPlanoAplicacao com select_related e anotação de
    execução prontos para agregação/relatório."""
    qs = ItemPlanoAplicacao.objects.filter(org_id=org_id).select_related(
        'meta_especifica',
        'meta_especifica__plano',
        'meta_especifica__plano__org_id',
        'org_beneficiaria',
        'unidade_beneficiaria',
        'necessidade_gerada',
        'necessidade_gerada__dfd',
    )
    return anotar_execucao(qs)
