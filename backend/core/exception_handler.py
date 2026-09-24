"""
Converte ValidationError do Django (levantada por `full_clean()` dentro de
`Model.save()`, ex.: DFD) em HTTP 400 — sem isso ela escapava como 500 em
qualquer action que cria/salva o modelo direto via ORM.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(exc.message_dict if hasattr(exc, 'error_dict') else {'detail': exc.messages})
    return drf_exception_handler(exc, context)
