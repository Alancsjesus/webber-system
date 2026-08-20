from django.contrib import admin

from .models import Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['documento', 'nome_razao_social', 'tipo_pessoa', 'porte_empresa', 'ativo']
    list_filter = ['tipo_pessoa', 'porte_empresa', 'ativo', 'uf']
    search_fields = ['documento', 'nome_razao_social', 'nome_fantasia']
    ordering = ['nome_razao_social']
