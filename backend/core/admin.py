from django.contrib import admin
from .models import Orgao, UnidadeOrganizacional, UserProfile, AuditLog


@admin.register(Orgao)
class OrgaoAdmin(admin.ModelAdmin):
    list_display  = ('sigla', 'nome', 'parent', 'ativa', 'criada_em')
    list_filter   = ('ativa', 'parent')
    search_fields = ('nome', 'sigla')
    readonly_fields = ('criada_em',)


@admin.register(UnidadeOrganizacional)
class UnidadeOrganizacionalAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'orgao', 'tipo', 'ativa')
    list_filter   = ('tipo', 'ativa', 'orgao')
    search_fields = ('nome', 'sigla', 'orgao__sigla')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'org_id', 'unidade', 'papel')
    list_filter   = ('papel', 'org_id')
    search_fields = ('user__username',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('org_id', 'modelo', 'acao', 'usuario', 'criado_em')
    list_filter   = ('modelo', 'acao', 'criado_em', 'org_id')
    search_fields = ('modelo', 'objeto_id')
    readonly_fields = ('org_id', 'modelo', 'objeto_id', 'acao', 'usuario',
                       'antes_json', 'depois_json', 'criado_em')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
