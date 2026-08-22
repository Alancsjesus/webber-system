from django.contrib import admin
from .models import (
    InstrumentoFinanceiro, ComposicaoConselhoGestor, PlanoAplicacao, ReuniaoConselhoGestor,
    MetaEspecifica, GrupoConsolidacaoItem, ItemPlanoAplicacao,
)


@admin.register(InstrumentoFinanceiro)
class InstrumentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ['numero_instrumento', 'tipo_instrumento', 'status', 'valor_total_pactuado', 'org_id']
    list_filter = ['tipo_instrumento', 'status', 'org_id']
    search_fields = ['numero_instrumento', 'objeto', 'orgao_concedente_nome']
    ordering = ['-data_assinatura']


@admin.register(ComposicaoConselhoGestor)
class ComposicaoConselhoGestorAdmin(admin.ModelAdmin):
    list_display = ['cargo', 'usuario', 'ativo', 'data_inicio_mandato', 'data_fim_mandato', 'org_id']
    list_filter = ['cargo', 'ativo', 'org_id']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name']
    ordering = ['cargo']


@admin.register(PlanoAplicacao)
class PlanoAplicacaoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'ementa', 'exercicio_fiscal', 'status', 'valor_planejado_investimento', 'valor_planejado_custeio', 'org_id']
    list_filter = ['status', 'exercicio_fiscal', 'org_id']
    search_fields = ['numero', 'ementa']
    ordering = ['-exercicio_fiscal']


@admin.register(MetaEspecifica)
class MetaEspecificaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'titulo', 'plano', 'status', 'valor_total', 'org_id']
    list_filter = ['status', 'org_id']
    search_fields = ['titulo', 'descricao_meta']
    ordering = ['plano', 'numero']


@admin.register(GrupoConsolidacaoItem)
class GrupoConsolidacaoItemAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'plano', 'chave_agrupamento', 'status', 'org_id']
    list_filter = ['status', 'org_id']
    search_fields = ['titulo', 'chave_agrupamento']
    ordering = ['-created_at']


@admin.register(ItemPlanoAplicacao)
class ItemPlanoAplicacaoAdmin(admin.ModelAdmin):
    list_display = [
        'bem_servico', 'meta_especifica', 'org_beneficiaria', 'natureza',
        'valor_total_estimado', 'aprovado', 'status', 'org_id',
    ]
    list_filter = ['natureza', 'status', 'aprovado', 'org_id']
    search_fields = ['bem_servico', 'descricao', 'codigo_senasp']
    ordering = ['meta_especifica', 'created_at']


@admin.register(ReuniaoConselhoGestor)
class ReuniaoConselhoGestorAdmin(admin.ModelAdmin):
    list_display = ['numero_ata', 'plano', 'tipo', 'data_reuniao', 'quorum_atingido', 'org_id']
    list_filter = ['tipo', 'quorum_atingido', 'org_id']
    search_fields = ['numero_ata']
    ordering = ['-data_reuniao']
