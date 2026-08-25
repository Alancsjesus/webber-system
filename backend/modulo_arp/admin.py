from django.contrib import admin

from .models import Ata, ItemAta, HistoricoAta


class ItemAtaInline(admin.TabularInline):
    model = ItemAta
    extra = 0


@admin.register(Ata)
class AtaAdmin(admin.ModelAdmin):
    list_display = ['numero_ata', 'tipo_origem', 'status', 'org_id', 'data_vigencia_fim']
    list_filter = ['tipo_origem', 'status', 'org_id']
    search_fields = ['numero_ata', 'objeto', 'orgao_gerenciador_nome']
    ordering = ['-data_assinatura']
    inlines = [ItemAtaInline]


@admin.register(HistoricoAta)
class HistoricoAtaAdmin(admin.ModelAdmin):
    list_display = ['ata', 'status_anterior', 'status_novo', 'usuario', 'criado_em']
    list_filter = ['status_novo']
    ordering = ['-criado_em']
