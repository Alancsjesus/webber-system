from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMultiTenant


class ProcessosSimilaresView(APIView):
    """
    GET /api/base-conhecimento/similares/?dfd=<id>
    Dado um DFD de referência, retorna outros DFDs do mesmo órgão que
    compartilham ao menos um item do catálogo (mesma "família" de compra),
    com a etapa atual e o total de devoluções (DFD+ETP+TR) de cada um —
    resposta direta a "quais processos semelhantes a este já foram
    analisados" e "quantas vezes esse tipo de processo já retornou".
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_demanda.models import DFD
        from core.base_conhecimento import buscar_similares

        dfd_id = request.query_params.get('dfd')
        if not dfd_id:
            return Response({'detail': 'Parâmetro "dfd" é obrigatório.'}, status=400)

        dfd = DFD.objects.filter(pk=dfd_id, org_id=request.org_id).first()
        if not dfd:
            raise NotFound('DFD não encontrado.')

        return Response(buscar_similares(dfd, request.org_id))
