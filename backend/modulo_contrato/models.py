from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
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
    GARANTIA_TIPO_CHOICES = [
        ('caucao_dinheiro', 'Caução em Dinheiro'),
        ('caucao_titulos',  'Caução em Títulos da Dívida Pública'),
        ('seguro_garantia', 'Seguro-Garantia'),
        ('fianca_bancaria', 'Fiança Bancária'),
    ]

    numero               = models.CharField(max_length=30, unique=True, editable=False, verbose_name='Número do contrato')
    exercicio            = models.IntegerField(verbose_name='Exercício fiscal')
    orgao_executor       = models.ForeignKey('core.Orgao', on_delete=models.PROTECT, related_name='contratos', verbose_name='Órgão executor')
    objeto               = models.TextField(verbose_name='Objeto do contrato')
    tipo_origem          = models.CharField(max_length=20, choices=TIPO_ORIGEM_CHOICES, verbose_name='Origem do contrato')
    fornecedor           = models.ForeignKey('modulo_fornecedor.Fornecedor', null=True, blank=True, on_delete=models.PROTECT, related_name='contratos', verbose_name='Fornecedor contratado')
    dfd                  = models.ForeignKey('modulo_demanda.DFD', null=True, blank=True, on_delete=models.SET_NULL, related_name='contratos', verbose_name='DFD de origem')
    lotes                = models.ManyToManyField('modulo_tr.LoteTR', blank=True, related_name='contratos', verbose_name='Lotes de origem')
    numero_processo_sei  = models.CharField(max_length=50, blank=True, default='', verbose_name='Número do processo SEI do contrato')
    valor_contrato       = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor do contrato (R$)')
    data_assinatura      = models.DateField(null=True, blank=True, verbose_name='Data de assinatura')
    data_vigencia_inicio = models.DateField(null=True, blank=True, verbose_name='Início da vigência')
    data_vigencia_fim    = models.DateField(null=True, blank=True, verbose_name='Fim da vigência')
    status               = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Vigente')
    fiscal_contrato      = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='contratos_fiscal', verbose_name='Fiscal do contrato')
    gestor_contrato      = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='contratos_gestor', verbose_name='Gestor do contrato')
    ordenador            = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='contratos_ordenador', verbose_name='Ordenador de despesa')
    observacoes          = models.TextField(blank=True, default='')

    # Garantia contratual (Lei 14.133/2021, art. 96-98)
    garantia_exigida               = models.BooleanField(default=False, verbose_name='Garantia exigida')
    garantia_tipo                  = models.CharField(max_length=20, choices=GARANTIA_TIPO_CHOICES, blank=True, default='', verbose_name='Tipo de garantia')
    garantia_percentual            = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Percentual de garantia (%)')
    garantia_apolice               = models.CharField(max_length=100, blank=True, default='', verbose_name='Nº da apólice / título')
    garantia_vigencia_inicio       = models.DateField(null=True, blank=True, verbose_name='Início da vigência da garantia')
    garantia_vigencia_fim          = models.DateField(null=True, blank=True, verbose_name='Fim da vigência da garantia')
    garantia_justificativa_acima_5 = models.TextField(blank=True, default='', verbose_name='Justificativa para percentual acima de 5%')

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


class CronogramaEntrega(BaseModel):
    STATUS_CHOICES = [
        ('pendente',  'Pendente'),
        ('entregue',  'Entregue'),
        ('atrasado',  'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]
    contrato       = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='cronograma')
    numero         = models.CharField(max_length=40, editable=False, verbose_name='Número do item')
    descricao      = models.TextField(verbose_name='Etapa / item a entregar')
    quantidade     = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    unidade_medida = models.CharField(max_length=20, blank=True, default='')
    data_prevista  = models.DateField(verbose_name='Data prevista de entrega')
    data_realizada = models.DateField(null=True, blank=True, verbose_name='Data de entrega realizada')
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    observacoes    = models.TextField(blank=True, default='')

    class Meta(BaseModel.Meta):
        ordering = ['data_prevista']
        verbose_name = 'Cronograma de Entrega'
        verbose_name_plural = 'Cronograma de Entregas'

    def __str__(self):
        return f'{self.numero} — {self.descricao[:60]}'

    @property
    def is_atrasado(self):
        return self.status == 'pendente' and self.data_prevista < timezone.localdate()


class Medicao(BaseModel):
    STATUS_CHOICES = [
        ('pendente',  'Pendente'),
        ('aprovada',  'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]
    contrato              = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='medicoes')
    numero                = models.CharField(max_length=40, editable=False, verbose_name='Número da medição')
    competencia_inicio    = models.DateField(verbose_name='Início do período medido')
    competencia_fim       = models.DateField(verbose_name='Fim do período medido')
    data_medicao          = models.DateField(verbose_name='Data da medição')
    percentual_executado  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Percentual executado (%)')
    valor_medido          = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor medido (R$)')
    fiscal_responsavel    = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='medicoes_fiscal')
    status                = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    parecer_fiscal        = models.TextField(blank=True, default='')
    data_aprovacao        = models.DateField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        ordering = ['competencia_inicio']
        verbose_name = 'Medição'
        verbose_name_plural = 'Medições'

    def __str__(self):
        return f'{self.numero} ({self.get_status_display()})'


class Pagamento(BaseModel):
    STATUS_CHOICES = [
        ('pendente',  'Pendente'),
        ('pago',      'Pago'),
        ('atrasado',  'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]
    contrato           = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='pagamentos')
    medicao            = models.ForeignKey(Medicao, null=True, blank=True, on_delete=models.SET_NULL, related_name='pagamentos', verbose_name='Medição vinculada')
    numero             = models.CharField(max_length=40, editable=False, verbose_name='Número do pagamento')
    numero_empenho     = models.CharField(max_length=50, blank=True, default='', verbose_name='Nº da nota de empenho')
    numero_nota_fiscal = models.CharField(max_length=50, blank=True, default='', verbose_name='Nº da nota fiscal')
    valor_pago         = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor (R$)')
    data_vencimento    = models.DateField(null=True, blank=True)
    data_pagamento     = models.DateField(null=True, blank=True, verbose_name='Data de efetivação do pagamento')
    status              = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    observacoes         = models.TextField(blank=True, default='')

    class Meta(BaseModel.Meta):
        ordering = ['-data_vencimento']
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'

    def __str__(self):
        return f'{self.numero} — {self.get_status_display()}'


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


@receiver(pre_save, sender=CronogramaEntrega)
def gerar_numero_cronograma(sender, instance, **kwargs):
    if instance.numero:
        return
    seq = instance.contrato.cronograma.count() + 1
    instance.numero = f'{instance.contrato.numero}-CRG-{seq:03d}'


@receiver(pre_save, sender=Medicao)
def gerar_numero_medicao(sender, instance, **kwargs):
    if instance.numero:
        return
    seq = instance.contrato.medicoes.count() + 1
    instance.numero = f'{instance.contrato.numero}-MED-{seq:03d}'


@receiver(pre_save, sender=Pagamento)
def gerar_numero_pagamento(sender, instance, **kwargs):
    if instance.numero:
        return
    seq = instance.contrato.pagamentos.count() + 1
    instance.numero = f'{instance.contrato.numero}-PAG-{seq:03d}'
