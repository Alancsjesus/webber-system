import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
from .models import AuditLog, BaseModel


def serialize_model(instance):
    """Convert model instance to a JSON-safe dict (all values serializable)."""
    data = {}
    for field in instance._meta.get_fields():
        if field.many_to_one or field.one_to_one:
            value = getattr(instance, field.name + '_id', None)
        else:
            value = getattr(instance, field.name, None)

        if value is None:
            continue
        try:
            # Serializa e de-serializa para garantir que tudo é nativo Python
            data[field.name] = json.loads(json.dumps(value, cls=DjangoJSONEncoder))
        except (TypeError, ValueError):
            data[field.name] = str(value)

    return data


@receiver(post_save)
def capture_audit_log_on_save(sender, instance, created, **kwargs):
    """Capture AuditLog on model save"""
    if not issubclass(sender, BaseModel) or sender == BaseModel:
        return
    
    if not hasattr(instance, 'org_id_id') or not instance.org_id_id:
        return
    
    action = 'created' if created else 'updated'
    model_name = sender.__name__
    
    depois_json = serialize_model(instance)
    
    AuditLog.objects.create(
        org_id_id=instance.org_id_id,
        modelo=model_name,
        objeto_id=instance.id,
        acao=action,
        usuario=instance.updated_by or instance.created_by,
        depois_json=depois_json,
    )


@receiver(post_delete)
def capture_audit_log_on_delete(sender, instance, **kwargs):
    """Capture AuditLog on model delete"""
    if not issubclass(sender, BaseModel) or sender == BaseModel:
        return
    
    if not hasattr(instance, 'org_id_id') or not instance.org_id_id:
        return
    
    model_name = sender.__name__
    antes_json = serialize_model(instance)
    
    AuditLog.objects.create(
        org_id_id=instance.org_id_id,
        modelo=model_name,
        objeto_id=instance.id,
        acao='deleted',
        usuario_id=None,
        antes_json=antes_json,
    )