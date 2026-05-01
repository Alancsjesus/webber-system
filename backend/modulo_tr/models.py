from decimal import Decimal
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

    TIPO_PRAZO_CHOICES = [
        ('escopo',      'Por Escopo — Aquisição/entrega única (AFM, Art. 105)'),
        ('continuo',    'Contínuo — Serviço continuado (até 5 anos prorrogável, Art. 106/107)'),
        ('emergencial', 'Emergencial — Contratação direta emergência (até 1 ano, Art. 75, VIII)'),
        ('direta_108',  'Contratação Direta Art. 108 — Obras/serviços especiais (até 10 anos)'),
    ]
    INSTRUMENTO_CHOICES = [
        ('contrato', 'Assinatura do Contrato'),
        ('afm',      'AFM — Autorização de Fornecimento de Material'),
        ('aps',      'APS — Autorização de Prestação de Serviços'),
    ]

    tipo_prazo_vigencia  = models.CharField(max_length=20, choices=TIPO_PRAZO_CHOICES, blank=True, default='', verbose_name='Tipo de prazo de vigência')
    prazo_meses          = models.PositiveIntegerField(null=True, blank=True, verbose_name='Prazo em meses')
    instrumento_inicio   = models.CharField(max_length=10, choices=INSTRUMENTO_CHOICES, blank=True, default='', verbose_name='Instrumento de início da vigência')
    prazo_observacao     = models.TextField(blank=True, default='', verbose_name='Redação do prazo de vigência')

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


class LoteTR(BaseModel):
    """
    Lote de licitação dentro de um TR.
    Cada lote tem um único vencedor (adjudicação global por lote).
    Lotes de cota (25% ME/EPP) são gerados a partir de lotes de ampla concorrência.
    """
    MODALIDADE_CHOICES = [
        ('ampla',            'Ampla Concorrência'),
        ('cota_me_epp',      'Reserva de Cota ME/EPP'),
        ('exclusiva_me_epp', 'Exclusivo ME/EPP'),
    ]

    tr              = models.ForeignKey(TR, on_delete=models.CASCADE, related_name='lotes')
    numero          = models.CharField(max_length=20, editable=False, verbose_name='Número do lote')
    descricao       = models.CharField(max_length=200, blank=True, default='', verbose_name='Descrição do lote')
    modalidade      = models.CharField(max_length=20, choices=MODALIDADE_CHOICES, default='ampla', verbose_name='Modalidade de participação')
    percentual_cota = models.PositiveIntegerField(default=25, verbose_name='Percentual da cota (%)')
    lote_origem     = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='lotes_cota', verbose_name='Lote de origem (para cotas)')
    ordem           = models.PositiveIntegerField(default=0, verbose_name='Ordem de exibição')
    observacoes     = models.TextField(blank=True, default='', verbose_name='Observações')

    class Meta(BaseModel.Meta):
        ordering = ['tr', 'ordem', 'numero']
        verbose_name = 'Lote do TR'
        verbose_name_plural = 'Lotes do TR'

    def __str__(self):
        return f'{self.numero} ({self.get_modalidade_display()}) — TR {self.tr_id}'

    def save(self, *args, **kwargs):
        if not self.numero:
            seq = LoteTR.objects.filter(tr=self.tr).count() + 1
            if self.modalidade == 'cota_me_epp':
                sufixo = '-Cota'
            elif self.modalidade == 'exclusiva_me_epp':
                sufixo = '-Excl'
            else:
                sufixo = ''
            self.numero = f'Lote {seq:02d}{sufixo}'
        if not self.ordem:
            self.ordem = LoteTR.objects.filter(tr=self.tr).count() + 1
        super().save(*args, **kwargs)

    @property
    def valor_total(self):
        total = Decimal('0')
        for item in self.itens.select_related('item_dfd'):
            if item.item_dfd:
                total += item.quantidade * item.item_dfd.valor_unitario_estimado
        return total


class ItemLoteTR(models.Model):
    """Item vinculado a um lote do TR com quantidade específica (pode diferir do ItemDFD original)."""
    lote      = models.ForeignKey(LoteTR, on_delete=models.CASCADE, related_name='itens')
    item_dfd  = models.ForeignKey('modulo_demanda.ItemDFD', on_delete=models.SET_NULL, null=True, related_name='lotes_tr')
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, verbose_name='Quantidade no lote')

    class Meta:
        unique_together = [('lote', 'item_dfd')]
        verbose_name = 'Item do Lote TR'
        verbose_name_plural = 'Itens dos Lotes TR'

    def __str__(self):
        obj = self.item_dfd.objeto if self.item_dfd else '—'
        return f'{self.lote.numero} · {obj} ({self.quantidade})'

    @property
    def valor_total(self):
        if self.item_dfd:
            return self.quantidade * self.item_dfd.valor_unitario_estimado
        return Decimal('0')


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
