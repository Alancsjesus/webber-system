from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

PAPEIS_ANALISTA     = ('analista', 'gestor_planejamento', 'gestor_contrato',
                       'fiscal_contrato', 'ordenador', 'admin')
PAPEIS_SOLICITANTE  = ('solicitante', 'responsavel_tecnico', 'admin')
PAPEIS_PLANEJAMENTO = ('gestor_planejamento', 'admin')


class IsMultiTenant(permissions.BasePermission):
    """Garante que o usuário acesse apenas dados do seu órgão ou de objetos que seu órgão gerencia."""

    def has_permission(self, request, view):
        if not request.org_id:
            raise PermissionDenied("Organization context not found")
        return True

    def has_object_permission(self, request, view, obj):
        oid = request.org_id
        # Origem
        if obj.org_id_id == oid:
            return True
        # Órgão que tomou controle (após iniciar_analise / aprovação)
        if getattr(obj, 'org_gestor_id', None) and obj.org_gestor_id == oid:
            return True
        # Órgão executor da necessidade (antes de aceitar)
        if getattr(obj, 'orgao_executor_id', None) and obj.orgao_executor_id == oid:
            return True
        # Órgão das unidades licitante/contratante do DFD
        for attr in ('unidade_licitante', 'unidade_contratante'):
            unidade = getattr(obj, attr, None)
            if unidade and unidade.orgao_id == oid:
                return True
        return False


class IsAnalista(permissions.BasePermission):
    """Analistas, gestores, fiscais, ordenadores e admins."""

    def has_permission(self, request, view):
        return getattr(request, 'papel', None) in PAPEIS_ANALISTA


class IsSolicitante(permissions.BasePermission):
    """Solicitantes, responsáveis técnicos e admins."""

    def has_permission(self, request, view):
        return getattr(request, 'papel', None) in PAPEIS_SOLICITANTE


class IsUnidadeDemandante(permissions.BasePermission):
    """Usuários lotados em unidade demandante."""

    def has_permission(self, request, view):
        return getattr(request, 'tipo_unidade', None) == 'demandante' or request.papel == 'admin'


class IsUnidadeLicitante(permissions.BasePermission):
    """Usuários lotados em unidade licitante."""

    def has_permission(self, request, view):
        return getattr(request, 'tipo_unidade', None) == 'licitante' or request.papel == 'admin'


class IsUnidadeContratante(permissions.BasePermission):
    """Usuários lotados em unidade contratante."""

    def has_permission(self, request, view):
        return getattr(request, 'tipo_unidade', None) == 'contratante' or request.papel == 'admin'


class IsUnidadePlanejamento(permissions.BasePermission):
    """Usuários lotados em unidade de planejamento ou com papel gestor_planejamento."""

    def has_permission(self, request, view):
        return (
            getattr(request, 'tipo_unidade', None) == 'planejamento'
            or getattr(request, 'papel', None) in PAPEIS_PLANEJAMENTO
        )


# Aliases para compatibilidade
IsDemandante    = IsSolicitante
IsCentralizadora = IsUnidadeLicitante
IsDemandanteOrg  = IsUnidadeDemandante
