from datetime import date as date_type
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsMultiTenant
from .models import PNCPImportacao, PNCPRegistro
from .serializers import PNCPImportacaoSerializer, PNCPRegistroSerializer


def _parse_date(s: str) -> date_type | None:
    if not s:
        return None
    try:
        y, m, d = s.split('-')
        return date_type(int(y), int(m), int(d))
    except Exception:
        return None


class PNCPImportacaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Histórico de importações PNCP do órgão.
    A criação e execução acontecem via action no MapaViewSet.
    """
    serializer_class   = PNCPImportacaoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get_queryset(self):
        return PNCPImportacao.objects.filter(
            org_id=self.request.org_id
        ).prefetch_related('registros').order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='confirmar')
    def confirmar(self, request, pk=None):
        """
        Efetiva a importação dos registros selecionados para o Mapa.
        Body: { ids: [1, 2, 3] }
        """
        from .services import ImportadorPNCP

        importacao = self.get_object()
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'Selecione ao menos um registro.'}, status=400)

        resultado = ImportadorPNCP().executar(importacao, ids)
        return Response(resultado)
