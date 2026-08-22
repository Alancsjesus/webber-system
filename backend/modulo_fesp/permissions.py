from rest_framework import permissions
from .models import ComposicaoConselhoGestor


class IsMembroConselhoFesp(permissions.BasePermission):
    """Usuário precisa compor o Conselho Gestor do FESP ativo na organização corrente."""

    def has_permission(self, request, view):
        papel = getattr(request, 'papel', None)
        if papel == 'admin':
            return True
        org_id = getattr(request, 'org_id', None)
        if not org_id or not request.user or not request.user.is_authenticated:
            return False
        return ComposicaoConselhoGestor.objects.filter(
            usuario=request.user, org_id=org_id, ativo=True,
        ).exists()
