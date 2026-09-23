from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMultiTenant


class ProcessosSimilaresView(APIView):
    """
    GET /api/base-conhecimento/similares/?dfd=<id> | ?etp=<id> | ?tr=<id>
    Dado um DFD, ETP ou TR de referência, retorna outros DFDs do mesmo órgão
    que compartilham ao menos um item do catálogo (mesma "família" de compra),
    com a etapa atual e o total de devoluções (DFD+ETP+TR) de cada um —
    resposta direta a "quais processos semelhantes a este já foram
    analisados" e "quantas vezes esse tipo de processo já retornou".

    ETP e TR resolvem para o DFD de origem (etp.dfd / tr.etp.dfd) e reaproveitam
    a mesma busca — a similaridade é sobre os itens do catálogo, que vivem no
    DFD, não sobre em qual peça do processo o usuário está olhando agora.
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_demanda.models import DFD
        from modulo_etp.models import ETP
        from modulo_tr.models import TR
        from core.base_conhecimento import buscar_similares

        dfd_id = request.query_params.get('dfd')
        etp_id = request.query_params.get('etp')
        tr_id  = request.query_params.get('tr')

        if dfd_id:
            dfd = DFD.objects.filter(pk=dfd_id, org_id=request.org_id).first()
            if not dfd:
                raise NotFound('DFD não encontrado.')
        elif etp_id:
            etp = ETP.objects.filter(pk=etp_id, org_id=request.org_id).select_related('dfd').first()
            if not etp:
                raise NotFound('ETP não encontrado.')
            dfd = etp.dfd
        elif tr_id:
            tr = TR.objects.filter(pk=tr_id, org_id=request.org_id).select_related('etp__dfd').first()
            if not tr:
                raise NotFound('TR não encontrado.')
            dfd = tr.etp.dfd if tr.etp else None
        else:
            return Response({'detail': 'Informe um dos parâmetros: "dfd", "etp" ou "tr".'}, status=400)

        if not dfd:
            return Response({'detail': 'Não foi possível localizar o DFD de origem.'}, status=404)

        return Response(buscar_similares(dfd, request.org_id))
