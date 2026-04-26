from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Orgao


class WebberTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT customizado com orgao_id, unidade_id, tipo_unidade e papel."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        profile = getattr(user, 'profile', None)

        # orgao_id via perfil ou fallback para primeiro órgão ativo
        orgao_id = getattr(profile, 'org_id_id', None)
        if not orgao_id:
            orgao = Orgao.objects.filter(ativa=True).first()
            if orgao:
                orgao_id = orgao.id

        token['org_id']   = str(orgao_id) if orgao_id else None
        token['orgao_id'] = str(orgao_id) if orgao_id else None

        # nomes do órgão para exibição no frontend
        orgao_obj = None
        if orgao_id:
            try:
                orgao_obj = Orgao.objects.get(id=orgao_id)
            except Orgao.DoesNotExist:
                pass
        token['orgao_sigla'] = orgao_obj.sigla if orgao_obj else None
        token['orgao_nome']  = orgao_obj.nome  if orgao_obj else None

        # unidade
        unidade = getattr(profile, 'unidade', None) if profile else None
        token['unidade_id']   = str(unidade.id)   if unidade else None
        token['tipo_unidade'] = unidade.tipo       if unidade else None
        token['unidade_sigla']= unidade.sigla      if unidade else None
        token['unidade_nome'] = unidade.nome       if unidade else None

        # papel
        if profile:
            token['papel'] = profile.papel
        elif user.is_superuser:
            token['papel'] = 'admin'
        else:
            token['papel'] = 'solicitante'

        return token


class WebberTokenObtainPairView(TokenObtainPairView):
    serializer_class = WebberTokenObtainPairSerializer
