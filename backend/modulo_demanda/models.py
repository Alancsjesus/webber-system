from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from core.models import BaseModel


class DFD(BaseModel):
    """
    Documento Formalização Demanda
    Entry point for any new initiative under Lei 14.133/2021
    """
    
    STATUS_CHOICES = [
        ('Rascunho',    'Rascunho'),
        ('Submetida',   'Submetida'),
        ('Em Análise',  'Em Análise'),
        ('Devolvida',   'Devolvida'),
        ('Aprovada',    'Aprovada'),
        ('Rejeitada',   'Rejeitada'),
    ]

    TRANSICOES_PERMITIDAS = {
        'Rascunho':   ['Submetida'],
        'Submetida':  ['Em Análise'],
        'Em Análise': ['Aprovada', 'Devolvida'],
        'Devolvida':  ['Submetida'],
        'Aprovada':   ['Rejeitada'],
        'Rejeitada':  [],
    }
    
    MODALIDADE_CHOICES = [
        ('licitacao',           'Licitação'),
        ('dispensa_valor',      'Dispensa por Valor'),
        ('dispensa_emergencia', 'Dispensa por Emergência'),
        ('inexigibilidade',     'Inexigibilidade'),
        ('arp_saque',           'Saque de ATA de Registro de Preços'),
    ]

    AREA_CHOICES = [
        ('TI', 'Tecnologia da Informação'),
        ('Formação', 'Formação e Capacitação'),
        ('Ops', 'Operações'),
        ('Rede', 'Rede Física'),
        ('Frota', 'Frota'),
        ('Derivados', 'Derivados'),
    ]
    
    numero_sei = models.CharField(
        max_length=50, 
        unique=True,
        help_text="SEI reference number"
    )
    descricao = models.TextField(help_text="Detailed description of the demand")
    valor_estimado = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Estimated value in BRL"
    )
    area_aplicacao = models.JSONField(
        default=list,
        help_text="Application areas: ['TI', 'Formação', 'Operação e Funcionamento', 'Rede', 'Frota', 'Derivados']"
    )
    prazo_necessidade = models.DateField(help_text="Required deadline")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Rascunho'
    )
    modalidade_aquisicao = models.CharField(
        max_length=25, choices=MODALIDADE_CHOICES,
        default='licitacao', verbose_name='Modalidade de aquisição',
    )
    observacoes                    = models.TextField(blank=True, null=True)
    local_entrega                  = models.TextField(blank=True, default='', verbose_name='Local de entrega')
    motivo_devolucao               = models.TextField(blank=True, null=True)
    justificativa_sem_planejamento = models.TextField(
        blank=True, null=True,
        help_text="Obrigatório quando não houver necessidade de planejamento vinculada"
    )

    # Órgão que atualmente controla este DFD para fins de métricas.
    # None = ainda pertence ao org de origem; preenchido quando o órgão
    # licitante inicia a análise (iniciar_analise).
    org_gestor = models.ForeignKey(
        'core.Orgao', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='dfds_gerenciados',
    )

    # Órgão de compras — referência permanente para painéis e relatórios.
    # Populado em iniciar_analise junto com org_gestor; não muda após isso.
    orgao_compras = models.ForeignKey(
        'core.Orgao', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='dfds_compras',
        verbose_name='Órgão de compras',
    )

    # Unidades responsáveis por etapa do processo
    unidade_demandante  = models.ForeignKey(
        'core.UnidadeOrganizacional', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='dfds_demandados',
    )
    unidade_licitante   = models.ForeignKey(
        'core.UnidadeOrganizacional', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='dfds_licitados',
    )
    unidade_contratante = models.ForeignKey(
        'core.UnidadeOrganizacional', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='dfds_contratados',
    )

    # Responsáveis pelo contrato
    fiscal_contrato = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='dfds_como_fiscal', verbose_name='Fiscal do contrato',
    )
    fiscal_suplente = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='dfds_como_fiscal_suplente', verbose_name='Fiscal suplente',
    )
    gestor_contrato = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='dfds_como_gestor', verbose_name='Gestor do contrato',
    )
    gestor_suplente = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='dfds_como_gestor_suplente', verbose_name='Gestor suplente',
    )

    class Meta(BaseModel.Meta):
        ordering = ['-created_at']
        verbose_name = 'Documento Formalização Demanda'
        verbose_name_plural = 'Documentos Formalização Demanda'
    
    def __str__(self):
        return f"DFD {self.numero_sei} - {self.status}"
    
    def clean(self):
        """Validate model fields"""
        super().clean()
        
        # Validate area_aplicacao is not empty
        if not self.area_aplicacao or len(self.area_aplicacao) == 0:
            raise ValidationError({'area_aplicacao': 'Pelo menos uma área de aplicação é obrigatória'})
        
        # Validate all areas are valid choices
        valid_areas = [choice[0] for choice in self.AREA_CHOICES]
        for area in self.area_aplicacao:
            if area not in valid_areas:
                raise ValidationError({'area_aplicacao': f'Área inválida: {area}'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ItemDFD(BaseModel):
    """Item individual de uma demanda — objeto, quantidade e valor estimado."""
    dfd = models.ForeignKey(DFD, on_delete=models.CASCADE, related_name='itens')
    item_catalogo = models.ForeignKey(
        'core.ItemCatalogo', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='itens_dfd',
        verbose_name='Item do catálogo',
    )
    objeto = models.CharField(max_length=500)
    justificativa = models.CharField(max_length=500, default='')
    unidade_medida = models.CharField(max_length=50)
    quantidade = models.DecimalField(max_digits=15, decimal_places=4)
    valor_unitario_estimado = models.DecimalField(max_digits=15, decimal_places=2)
    valor_total_estimado = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    observacao = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        ordering = ['created_at']
        verbose_name = 'Item do DFD'
        verbose_name_plural = 'Itens do DFD'

    def save(self, *args, **kwargs):
        self.valor_total_estimado = self.quantidade * self.valor_unitario_estimado
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.objeto} ({self.quantidade} {self.unidade_medida})"


class NumeroProcesso(BaseModel):
    """Número de processo SEI vinculado a um DFD por etapa."""
    ETAPA_CHOICES = [
        ('dfd',       'DFD'),
        ('etp',       'ETP'),
        ('tr',        'Termo de Referência'),
        ('licitacao', 'Licitação'),
        ('contrato',  'Contrato'),
    ]
    dfd = models.ForeignKey(DFD, on_delete=models.CASCADE, related_name='processos')
    numero = models.CharField(max_length=50)
    etapa = models.CharField(max_length=20, choices=ETAPA_CHOICES)
    descricao = models.TextField(blank=True)
    data_abertura = models.DateField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        ordering = ['etapa', 'created_at']
        verbose_name = 'Número de Processo'
        verbose_name_plural = 'Números de Processo'

    def __str__(self):
        return f"{self.numero} ({self.get_etapa_display()})"


class HistoricoTramitacao(models.Model):
    """Registro imutável de cada transição de status do DFD"""
    dfd            = models.ForeignKey(DFD, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=20)
    status_novo     = models.CharField(max_length=20)
    usuario        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo         = models.TextField(blank=True, null=True)
    criado_em      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico de Tramitação'
        verbose_name_plural = 'Históricos de Tramitação'

    def __str__(self):
        return f"DFD {self.dfd_id}: {self.status_anterior} → {self.status_novo}"


@receiver([post_save, post_delete], sender='modulo_demanda.ItemDFD')
def atualizar_valor_estimado_dfd(sender, instance, **kwargs):
    """Recalcula valor_estimado do DFD sempre que um item é salvo ou removido."""
    dfd = instance.dfd
    total = dfd.itens.aggregate(total=Sum('valor_total_estimado'))['total'] or 0
    DFD.objects.filter(pk=dfd.pk).update(valor_estimado=total)