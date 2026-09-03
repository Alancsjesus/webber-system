"""
Helper compartilhado por DFD/ETP/TR/Procedimento para marcar onde um processo está
tramitando fisicamente agora (`mesa_atual`, GenericForeignKey para UnidadeOrganizacional
ou Orgao) — distinto das FKs fixas de responsabilidade (unidade_demandante/licitante/
gestora), que dizem quem é dono da etapa, não onde ela está circulando neste momento.
"""
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError

from core.models import Orgao, UnidadeOrganizacional

MODELOS_MESA = {
    'unidade': UnidadeOrganizacional,
    'orgao': Orgao,
}


def aplicar_mesa_atual(instance, tipo, obj_id, data, usuario=None):
    """
    Resolve `tipo` ('unidade'|'orgao') + `obj_id` contra um mapa fechado de models —
    nunca aceita ContentType cru do cliente — e grava mesa_atual/data_mesa_atual em
    `instance`. `instance` precisa ter os campos mesa_atual_content_type/object_id/
    data_mesa_atual (DFD, ETP, TR, Procedimento).
    """
    model = MODELOS_MESA.get(tipo)
    if model is None:
        raise ValidationError({'tipo': 'Deve ser "unidade" ou "orgao".'})
    try:
        obj = model.objects.get(pk=obj_id)
    except model.DoesNotExist:
        raise ValidationError({'id': f'{tipo} não encontrado(a).'})

    instance.mesa_atual_content_type = ContentType.objects.get_for_model(model)
    instance.mesa_atual_object_id = obj.pk
    instance.data_mesa_atual = data
    if usuario is not None and hasattr(instance, 'updated_by'):
        instance.updated_by = usuario
    instance.save()
    return obj


def mesa_atual_label(instance):
    """Rótulo legível da mesa_atual de `instance`, ou None se não preenchida."""
    obj = getattr(instance, 'mesa_atual', None)
    if obj is None:
        return None
    if isinstance(obj, UnidadeOrganizacional):
        return f'{obj.sigla} — {obj.nome}'
    if isinstance(obj, Orgao):
        return obj.sigla
    return str(obj)
