from django.contrib import admin
from .models import AcaoOrcamentaria, ElementoDespesa, FonteRecurso, DotacaoOrcamentaria


@admin.register(AcaoOrcamentaria)
class AcaoOrcamentariaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'tipo', 'ativa', 'org_id']
    list_filter = ['tipo', 'ativa', 'org_id']
    search_fields = ['codigo', 'nome']
    ordering = ['org_id', 'codigo']


@admin.register(ElementoDespesa)
class ElementoDespesaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'ativo']
    list_filter = ['ativo']
    search_fields = ['codigo', 'descricao']
    ordering = ['codigo']


@admin.register(FonteRecurso)
class FonteRecursoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'tipo', 'exercicio_anterior', 'org_id']
    list_filter = ['tipo', 'exercicio_anterior', 'org_id']
    search_fields = ['codigo', 'nome']
    ordering = ['org_id', 'codigo']


@admin.register(DotacaoOrcamentaria)
class DotacaoOrcamentariaAdmin(admin.ModelAdmin):
    list_display = ['exercicio_fiscal', 'acao', 'elemento_despesa', 'fonte_recurso', 'valor_dotado', 'status', 'org_id']
    list_filter = ['exercicio_fiscal', 'status', 'org_id']
    search_fields = ['acao__codigo', 'acao__nome', 'eixo', 'objetivo_estrategico']
    ordering = ['-exercicio_fiscal', 'acao__codigo']
    filter_horizontal = ['necessidades']
