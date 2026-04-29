from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from core.models import BaseModel


class Contrato(BaseModel):
    TIPO_ORIGEM_CHOICES = [
        ('licitacao',       'Licitação'),
        ('dispensa',        'Dispensa de Licitação'),
        ('inexigibilidade', 'Inexigibilidade'),
        ('saque_arp',       'Saque de ATA de Registro de Preços'),
        ('adesao_arp',      'Adesão a ATA de Registro de Preços'),
    ]
    STATUS_CHOICES = [
        ('Vigente',    'Vigente'),
        ('Encerrado',  'Encerrado'),
        ('Suspenso',   'Suspenso'),
        ('Rescindido', 'Rescindido'),
    ]

    numero               = models.CharField(max_length=30, unique=True, editable=False, verbose_name='Número do contrato')
    exercicio            = models.IntegerField(verbose_name='Exercício fiscal')
    orgao_executor       = models.ForeignKey('core.Orgao', on_delete=models.PROTECT, related_name='contratos', verbose_name='Órgão executor')
    objeto               = models.TextField(verbose_name='Objeto do contrato')
    tipo_origem          = models.CharField(max_length=20, choices=TIPO_ORIGEM_CHOICES, verbose_name='Origem do contrato')
    dfd                  = models.ForeignKey('modulo_demanda.DFD', null=True, blank=True, on_delete=models.SET_NULL, related_name='contratos', verbose_name='DFD de origem')
    valor_contrato       = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor do contrato (R$)')
    data_assinatura      = models.DateField(null=True, blank=True, verbose_name='Data de assinatura')
    data_vigencia_inicio = models.DateField(null=True, blank=True, verbose_name='Início da vigência')
    data_vigencia_fim    = models.DateField(null=True, blank=True, verbose_name='Fim da vigência')
    status               = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Vigente')
    fiscal_contrato      = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='contratos_fiscal', verbose_name='Fiscal do contrato')
    gestor_contrato      = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='contratos_gestor', verbose_name='Gestor do contrato')
    ordenador            = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='contratos_ordenador', verbose_name='Ordenador de despesa')
    observacoes          = models.TextField(blank=True, default='')

    class Meta(BaseModel.Meta):
        ordering = ['-exercicio', 'numero']
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'

    def __str__(self):
        return f'{self.numero} — {self.objeto[:60]}'


class Apostila(BaseModel):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='apostilas')
    numero   = models.CharField(max_length=40, editable=False, verbose_name='Número da apostila')
    objeto   = models.TextField(verbose_name='Objeto da apostila')
    data     = models.DateField(verbose_name='Data da apostila')

    class Meta(BaseModel.Meta):
        ordering = ['data']
        verbose_name = 'Apostila'
        verbose_name_plural = 'Apostilas'

    def __str__(self):
        return f'Apostila {self.numero}'


class Aditivo(BaseModel):
    TIPO_CHOICES = [
        ('prazo',    'Prorrogação de Prazo'),
        ('valor',    'Acréscimo/Redução de Valor'),
        ('objeto',   'Alteração de Objeto'),
        ('rescisao', 'Rescisão'),
    ]
    contrato        = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='aditivos')
    numero          = models.CharField(max_length=40, editable=False, verbose_name='Número do aditivo')
    tipo            = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo de aditivo')
    valor_acrescimo = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Valor acrescido/reduzido (R$)')
    nova_vigencia   = models.DateField(null=True, blank=True, verbose_name='Nova data de vigência')
    objeto          = models.TextField(verbose_name='Objeto do aditivo')
    data            = models.DateField(verbose_name='Data do aditivo')

    class Meta(BaseModel.Meta):
        ordering = ['data']
        verbose_name = 'Aditivo'
        verbose_name_plural = 'Aditivos'

    def __str__(self):
        return f'Aditivo {self.numero} ({self.get_tipo_display()})'


# ── Numeração automática ───────────────────────────────────────────────────────

@receiver(pre_save, sender=Contrato)
def gerar_numero_contrato(sender, instance, **kwargs):
    if instance.numero:
        return
    orgao = instance.orgao_executor
    sigla = orgao.sigla if orgao else 'ORG'
    exercicio = instance.exercicio or 2026
    ultimo = (
        Contrato.objects.filter(orgao_executor=orgao, exercicio=exercicio)
        .exclude(pk=instance.pk)
        .count()
    )
    seq = ultimo + 1
    instance.numero = f'{sigla}-{seq:03d}/{exercicio}'


@receiver(pre_save, sender=Apostila)
def gerar_numero_apostila(sender, instance, **kwargs):
    if instance.numero:
        return
    seq = instance.contrato.apostilas.count() + 1
    instance.numero = f'{instance.contrato.numero}-APO-{seq:03d}'


@receiver(pre_save, sender=Aditivo)
def gerar_numero_aditivo(sender, instance, **kwargs):
    if instance.numero:
        return
    seq = instance.contrato.aditivos.count() + 1
    instance.numero = f'{instance.contrato.numero}-ADT-{seq:03d}'
