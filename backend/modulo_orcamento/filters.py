import django_filters
from .models import AcaoOrcamentaria, FonteRecurso, SubFonteRecurso, DotacaoOrcamentaria


class AcaoOrcamentariaFilter(django_filters.FilterSet):
    tipo = django_filters.NumberFilter(field_name='tipo_id')
    ativa = django_filters.BooleanFilter(field_name='ativa')

    class Meta:
        model = AcaoOrcamentaria
        fields = ['tipo', 'ativa']


class FonteRecursoFilter(django_filters.FilterSet):
    tipo = django_filters.NumberFilter(field_name='tipo_id')
    exercicio_anterior = django_filters.BooleanFilter(field_name='exercicio_anterior')

    class Meta:
        model = FonteRecurso
        fields = ['tipo', 'exercicio_anterior']


class SubFonteRecursoFilter(django_filters.FilterSet):
    fonte_recurso = django_filters.NumberFilter(field_name='fonte_recurso__id')
    ativa = django_filters.BooleanFilter(field_name='ativa')

    class Meta:
        model = SubFonteRecurso
        fields = ['fonte_recurso', 'ativa']


class DotacaoOrcamentariaFilter(django_filters.FilterSet):
    exercicio_fiscal = django_filters.NumberFilter(field_name='exercicio_fiscal')
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    acao = django_filters.NumberFilter(field_name='acao__id')
    acao_codigo = django_filters.CharFilter(field_name='acao__codigo', lookup_expr='exact')
    elemento_despesa = django_filters.NumberFilter(field_name='elemento_despesa__id')
    elemento_codigo = django_filters.NumberFilter(field_name='elemento_despesa__codigo')
    fonte_recurso = django_filters.NumberFilter(field_name='fonte_recurso__id')
    fonte_tipo = django_filters.CharFilter(field_name='fonte_recurso__tipo__descricao', lookup_expr='exact')

    class Meta:
        model = DotacaoOrcamentaria
        fields = ['exercicio_fiscal', 'status']
