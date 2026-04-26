from django.contrib import admin
from .models import NecessidadePlanejamento


@admin.register(NecessidadePlanejamento)
class NecessidadeAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'status', 'prioridade', 'exercicio_fiscal', 'valor_estimado', 'created_at']
    list_filter = ['status', 'prioridade', 'exercicio_fiscal']
    search_fields = ['titulo', 'descricao', 'departamento_solicitante']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
