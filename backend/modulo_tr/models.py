from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class TR(BaseModel):
    """
    Termo de Referência — criado a partir de um ETP aprovado.
    Referência normativa: Lei 14.133/2021 Art. 6º, XXIII.
    Fluxo: Rascunho → Submetido → Em Análise → Aprovado | Devolvido
    """
    STATUS_CHOICES = [
        ('Rascunho',   'Rascunho'),
        ('Submetido',  'Submetido'),
        ('Em Análise', 'Em Análise'),
        ('Devolvido',  'Devolvido'),
        ('Aprovado',   'Aprovado'),
        ('Cancelado',  'Cancelado'),
    ]

    TRANSICOES_PERMITIDAS = {
        'Rascunho':   ['Submetido'],
        'Submetido':  ['Em Análise'],
        'Em Análise': ['Aprovado', 'Devolvido'],
        'Devolvido':  ['Submetido'],
        'Aprovado':   ['Cancelado'],
        'Cancelado':  [],
    }

    etp = models.OneToOneField(
        'modulo_etp.ETP',
        on_delete=models.CASCADE,
        related_name='tr',
        verbose_name='ETP de origem',
    )

    numero_sei = models.CharField(
        max_length=50, unique=True,
        verbose_name='Número SEI do TR',
    )

    objeto_contratacao        = models.TextField(verbose_name='Objeto da contratação')
    justificativa             = models.TextField(blank=True, default='', verbose_name='Justificativa da contratação')
    requisitos_contratacao    = models.TextField(blank=True, default='', verbose_name='Requisitos da contratação')
    obrigacoes_contratada     = models.TextField(blank=True, default='', verbose_name='Obrigações da contratada')
    obrigacoes_contratante    = models.TextField(blank=True, default='', verbose_name='Obrigações da contratante')
    criterios_selecao         = models.TextField(blank=True, default='', verbose_name='Critérios de seleção do fornecedor')
    criterios_medicao         = models.TextField(blank=True, default='', verbose_name='Critérios de medição e pagamento')
    prazo_execucao            = models.CharField(max_length=200, blank=True, default='', verbose_name='Prazo de execução')
    local_entrega             = models.TextField(blank=True, default='', verbose_name='Local de entrega')
    garantia_contrato         = models.TextField(blank=True, default='', verbose_name='Garantia contratual')
    estimativa_valor          = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Estimativa de valor (R$)',
    )

    status           = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Rascunho')
    motivo_devolucao = models.TextField(blank=True, null=True, verbose_name='Motivo da devolução')
    observacoes      = models.TextField(blank=True, default='', verbose_name='Observações')

    class Meta(BaseModel.Meta):
        ordering = ['-created_at']
        verbose_name = 'Termo de Referência'
        verbose_name_plural = 'Termos de Referência'
        indexes = BaseModel.Meta.indexes + [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"TR {self.numero_sei} (ETP {self.etp.numero_sei}) — {self.status}"


class HistoricoTR(models.Model):
    """Registro imutável de cada transição de status do TR."""
    tr              = models.ForeignKey(TR, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=15)
    status_novo     = models.CharField(max_length=15)
    usuario         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo          = models.TextField(blank=True, null=True)
    criado_em       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico do TR'
        verbose_name_plural = 'Históricos do TR'

    def __str__(self):
        return f"TR {self.tr_id}: {self.status_anterior} → {self.status_novo}"
