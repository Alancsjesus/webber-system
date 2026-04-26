from django.contrib import admin
from .models import DFD


@admin.register(DFD)
class DFDAdmin(admin.ModelAdmin):
    list_display = ('numero_sei', 'descricao_short', 'valor_estimado', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'area_aplicacao', 'created_at', 'org_id')
    search_fields = ('numero_sei', 'descricao')
    readonly_fields = ('org_id', 'created_by', 'updated_by', 'created_at', 'updated_at')
    fieldsets = (
        ('Informações Principais', {
            'fields': ('numero_sei', 'descricao', 'org_id')
        }),
        ('Dados Financeiros e Prazo', {
            'fields': ('valor_estimado', 'prazo_necessidade')
        }),
        ('Classificação', {
            'fields': ('area_aplicacao', 'status')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def descricao_short(self, obj):
        return obj.descricao[:50] + "..." if len(obj.descricao) > 50 else obj.descricao
    descricao_short.short_description = 'Descrição'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é criação
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)