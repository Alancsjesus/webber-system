from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMultiTenant


class CronogramaContratacoesView(APIView):
    """
    GET /api/indicadores/cronograma-contratacoes/?exercicio=2026

    Cronograma de início sugerido para os itens pendentes do Plano de Compras:
    para cada item consolidado, compara o prazo da necessidade com a duração
    real que cada modalidade aplicável já levou neste órgão, e agrupa por
    trimestre a data em que o procedimento precisaria começar. Ver
    core/cronograma_contratacoes.py para a lógica e os princípios (sugestão
    de direcionamento, nunca decisão automática de modalidade).
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from core.cronograma_contratacoes import montar_cronograma

        exercicio = request.query_params.get('exercicio')
        try:
            exercicio = int(exercicio) if exercicio else None
        except ValueError:
            exercicio = None

        return Response(montar_cronograma(request.org_id, exercicio))
