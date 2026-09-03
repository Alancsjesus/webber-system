from django.contrib import admin

from .models import ProcessoTramitacao, HistoricoTramitacaoProcesso


@admin.register(ProcessoTramitacao)
class ProcessoTramitacaoAdmin(admin.ModelAdmin):
    list_display = ['numero_sei', 'setor_atual', 'fase_atual', 'data_entrada_fase', 'ativo', 'org_id']
    list_filter = ['setor_atual', 'ativo', 'org_id']
    search_fields = ['numero_sei', 'objeto']
    ordering = ['setor_atual', '-data_entrada_fase']


@admin.register(HistoricoTramitacaoProcesso)
class HistoricoTramitacaoProcessoAdmin(admin.ModelAdmin):
    list_display = ['processo', 'setor_anterior', 'setor_novo', 'usuario', 'criado_em']
    list_filter = ['setor_novo']
    ordering = ['-criado_em']
