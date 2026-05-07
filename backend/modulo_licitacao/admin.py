from django.contrib import admin
from .models import Procedimento, HistoricoProcedimento, TramitacaoExterna, ResultadoLote

@admin.register(Procedimento)
class ProcedimentoAdmin(admin.ModelAdmin):
    list_display  = ('numero', 'modalidade', 'status', 'exercicio', 'valor_estimado', 'org_id')
    list_filter   = ('modalidade', 'status', 'exercicio')
    search_fields = ('numero', 'objeto')

admin.site.register(TramitacaoExterna)
admin.site.register(ResultadoLote)
