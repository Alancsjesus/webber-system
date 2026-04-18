from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Orgao(models.Model):
    """Órgão ou secretaria — suporta hierarquia pai/filho."""
    nome   = models.CharField(max_length=255)
    sigla  = models.CharField(max_length=20, unique=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='orgaos_filhos',
    )
    ativa     = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Órgão'
        verbose_name_plural = 'Órgãos'

    def __str__(self):
        return self.sigla


# Backward compatibility alias — mantém imports existentes funcionando
Organization = Orgao


class UnidadeOrganizacional(models.Model):
    """Unidade funcional dentro de um órgão: demandante, licitante, contratante ou planejamento."""
    TIPO_CHOICES = [
        ('demandante',   'Unidade Demandante'),
        ('licitante',    'Unidade Licitante'),
        ('contratante',  'Unidade Contratante'),
        ('planejamento', 'Unidade de Planejamento'),
    ]
    orgao = models.ForeignKey(Orgao, on_delete=models.CASCADE, related_name='unidades')
    nome  = models.CharField(max_length=200)
    sigla = models.CharField(max_length=30)
    tipo  = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ['orgao', 'sigla']
        unique_together = [('orgao', 'sigla', 'tipo')]
        verbose_name = 'Unidade Organizacional'
        verbose_name_plural = 'Unidades Organizacionais'

    def __str__(self):
        return f'{self.orgao.sigla}/{self.sigla}'


class UserProfile(models.Model):
    """Perfil de usuário com papel, órgão e unidade organizacional."""
    PAPEL_CHOICES = [
        ('admin',               'Administrador'),
        ('analista',            'Analista de Contratações'),
        ('gestor_planejamento', 'Gestor de Planejamento'),
        ('gestor_contrato',     'Gestor de Contrato'),
        ('fiscal_contrato',     'Fiscal de Contrato'),
        ('ordenador',           'Ordenador de Despesas'),
        ('solicitante',         'Solicitante'),
        ('responsavel_tecnico', 'Responsável Técnico'),
    ]

    user    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    org_id  = models.ForeignKey(Orgao, on_delete=models.SET_NULL, null=True, blank=True)
    unidade = models.ForeignKey(
        UnidadeOrganizacional, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='usuarios',
    )
    papel   = models.CharField(max_length=30, choices=PAPEL_CHOICES, default='solicitante')

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuário'

    def __str__(self):
        return f"{self.user.username} ({self.papel})"


@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class BaseModel(models.Model):
    """Abstract base model with multi-tenant support."""
    org_id     = models.ForeignKey(Orgao, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['org_id', '-created_at']),
        ]


class AuditLog(models.Model):
    """Immutable audit trail"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('status_changed', 'Status Changed'),
    ]

    org_id      = models.ForeignKey(Orgao, on_delete=models.CASCADE)
    modelo      = models.CharField(max_length=100)
    objeto_id   = models.IntegerField()
    acao        = models.CharField(max_length=50, choices=ACTION_CHOICES)
    usuario     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    antes_json  = models.JSONField(null=True, blank=True)
    depois_json = models.JSONField(null=True, blank=True)
    criado_em   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['org_id', '-criado_em']),
            models.Index(fields=['modelo', 'objeto_id']),
        ]
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'

    def __str__(self):
        return f"{self.modelo} - {self.acao} - {self.criado_em}"
