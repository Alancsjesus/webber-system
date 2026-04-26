from django.http import HttpRequest
from django.core.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Orgao


class TenantMiddleware:
    """Extrai orgao_id, unidade_id, tipo_unidade e papel do token JWT."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        orgao_id     = None
        unidade_id   = None
        tipo_unidade = None
        papel        = None

        if request.META.get('HTTP_AUTHORIZATION', '').startswith('Bearer '):
            try:
                auth = JWTAuthentication()
                validated = auth.authenticate(request)
                if validated:
                    user, token = validated
                    orgao_id     = token.get('orgao_id') or token.get('org_id')
                    unidade_id   = token.get('unidade_id')
                    tipo_unidade = token.get('tipo_unidade')
                    papel        = token.get('papel', 'solicitante')
            except Exception:
                pass

        # Fallback to header
        if not orgao_id:
            orgao_id = request.META.get('HTTP_X_ORG_ID')

        if orgao_id:
            try:
                orgao = Orgao.objects.get(id=orgao_id, ativa=True)
                request.orgao_id = orgao.id
                request.orgao    = orgao
            except Orgao.DoesNotExist:
                raise PermissionDenied("Invalid or inactive organization")
        else:
            request.orgao_id = None
            request.orgao    = None

        # Retrocompatibilidade — código existente usa request.org_id
        request.org_id       = request.orgao_id
        request.unidade_id   = unidade_id
        request.tipo_unidade = tipo_unidade
        request.papel        = papel

        response = self.get_response(request)
        return response
