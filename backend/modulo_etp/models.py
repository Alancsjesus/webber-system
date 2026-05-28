from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class ETP(BaseModel):
    """
    Estudo Técnico Preliminar — criado a partir de um DFD aprovado.
    Referência normativa: IN SEGES 58/2022 (Lei 14.133/2021).
    Fluxo: Rascunho → Submetido → Em Análise → Aprovado | Devolvido
    """
    STATUS_CHOICES = [
        ('Rascunho',   'Rascunho'),
        ('Submetido',  'Submetido'),
        ('Em Análise', 'Em Análise'),
        ('Devolvido',  'Devolvido'),
        ('Aprovado',   'Aprovado'),
        ('Cancelado',  'Cancelado'),
        ('Dispensado', 'Dispensado (ETP não obrigatório)'),
    ]

    TRANSICOES_PERMITIDAS = {
        'Rascunho':   ['Submetido'],
        'Submetido':  ['Em Análise'],
        'Em Análise': ['Aprovado', 'Devolvido'],
        'Devolvido':  ['Submetido'],
        'Aprovado':   ['Cancelado'],
        'Cancelado':  [],
        'Dispensado': ['Cancelado'],
    }

    dfd = models.OneToOneField(
        'modulo_demanda.DFD',
        on_delete=models.CASCADE,
        related_name='etp',
        verbose_name='DFD de origem',
    )

    numero_sei = models.CharField(
        max_length=50, unique=True,
        verbose_name='Número SEI do ETP',
    )

    necessidade_contratacao = models.TextField(verbose_name='Necessidade da contratação')
    requisitos_contratacao  = models.TextField(blank=True, default='', verbose_name='Requisitos da contratação')
    levantamento_mercado    = models.TextField(blank=True, default='', verbose_name='Levantamento de mercado')
    estimativa_valor        = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Estimativa de valor (R$)',
    )
    descricao_solucao       = models.TextField(blank=True, default='', verbose_name='Descrição da solução escolhida')
    justificativa_solucao   = models.TextField(blank=True, default='', verbose_name='Justificativa da solução')
    riscos                  = models.TextField(blank=True, default='', verbose_name='Mapa de riscos')
    sustentabilidade        = models.TextField(blank=True, default='', verbose_name='Critérios de sustentabilidade')

    # ── Tipo de objeto (Lei 14.133/2021) ─────────────────────────────────────
    TIPO_OBJETO_CHOICES = [
        ('bens',                 'Bens'),
        ('servicos',             'Serviços Comuns'),
        ('servicos_engenharia',  'Serviços de Engenharia'),
        ('obras',                'Obras'),
    ]
    tipo_objeto = models.CharField(
        max_length=25, choices=TIPO_OBJETO_CHOICES, blank=True, default='',
        verbose_name='Tipo de objeto',
    )

    # ── Parcelamento e adjudicação (Lei 14.133/2021, Art. 40, V) ──────────────
    PARCELAMENTO_CHOICES = [
        ('lote_unico', 'Lote único — contratação global'),
        ('lotes',      'Dividido em lotes — adjudicação por lote'),
        ('por_item',   'Por item — adjudicação individualizada'),
    ]
    tipo_parcelamento          = models.CharField(max_length=20, choices=PARCELAMENTO_CHOICES, blank=True, default='', verbose_name='Tipo de parcelamento')
    parcelamento_justificativa = models.TextField(blank=True, default='', verbose_name='Justificativa do parcelamento (Art. 40, V)')

    # ── Reserva de cota ME/EPP (LC 123/2006, Art. 48, III) ────────────────────
    reserva_cota_me_epp        = models.BooleanField(default=False, verbose_name='Reserva de cota 25% para ME/EPP')
    reserva_cota_justificativa = models.TextField(blank=True, default='', verbose_name='Justificativa da não-reserva de cota')
    licitacao_exclusiva_me_epp = models.BooleanField(default=False, verbose_name='Licitação exclusiva ME/EPP (até R$80.000)')

    # ── Campos obrigatórios do Checklist ETP — SSP-BA (C0) ───────────────────
    # Todos opcionais no banco; obrigatoriedade controlada pelo ChecklistEngine.

    posicionamento_conclusivo = models.TextField(
        blank=True, default='',
        verbose_name='Posicionamento conclusivo',
        help_text='OBRIGATÓRIO — Adequação da contratação ao interesse público (Lei 14.133, art. 18, §1º, XIII).',
    )
    classificacao_sensivel = models.BooleanField(
        null=True, blank=True,
        verbose_name='ETP sensível/sigiloso?',
        help_text='OBRIGATÓRIO — Avaliação justificada (Decreto 22.598/2024, art. 8º).',
    )
    classificacao_sensivel_justificativa = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa de classificação sigilosa',
    )
    alinhamento_planesp = models.TextField(
        blank=True, default='',
        verbose_name='Alinhamento ao PLANESP',
        help_text='Objetivo Estratégico do PLANESP ou PCA atendido (específico SSP-BA).',
    )
    contratacoes_correlatas = models.TextField(
        blank=True, default='',
        verbose_name='Contratações correlatas ou interdependentes',
        help_text='Outras contratações em andamento ou planejadas que interagem com esta (art. 18, §1º, XI).',
    )
    impacto_ambiental = models.TextField(
        blank=True, default='',
        verbose_name='Impactos ambientais e medidas mitigadoras',
        help_text='Incluir logística reversa, baixo consumo de energia etc. (art. 18, §1º, XII).',
    )
    providencias_pre_contrato = models.TextField(
        blank=True, default='',
        verbose_name='Providências antes da celebração',
        help_text='Capacitação, adequações físicas, etc. necessárias antes da contratação (art. 18, §1º, X).',
    )
    compra_vs_locacao = models.TextField(
        blank=True, default='',
        verbose_name='Análise compra vs. locação',
        help_text='Para bens: custos e benefícios de cada opção (art. 44 + Decreto 22.598/2024, art. 6º, V, c).',
    )

    status           = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Rascunho')
    motivo_devolucao = models.TextField(blank=True, null=True, verbose_name='Motivo da devolução')
    dispensa_motivo  = models.TextField(blank=True, null=True, verbose_name='Motivo da dispensa de ETP')
    observacoes      = models.TextField(blank=True, default='', verbose_name='Observações')

    class Meta(BaseModel.Meta):
        ordering = ['-created_at']
        verbose_name = 'Estudo Técnico Preliminar'
        verbose_name_plural = 'Estudos Técnicos Preliminares'
        indexes = BaseModel.Meta.indexes + [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"ETP {self.numero_sei} (DFD {self.dfd.numero_sei}) — {self.status}"


MOTIVOS_DEVOLUCAO_ETP = [
    ('alternativas_insuficientes',  'Alternativas insuficientes'),
    ('estimativa_sem_referencia',   'Estimativa de valor sem referência'),
    ('requisitos_incompletos',      'Requisitos técnicos incompletos'),
    ('fontes_inadequadas',          'Fontes de pesquisa inadequadas'),
    ('outro',                       'Outro'),
]


class HistoricoETP(models.Model):
    """Registro imutável de cada transição de status do ETP."""
    etp              = models.ForeignKey(ETP, on_delete=models.CASCADE, related_name='historico')
    status_anterior  = models.CharField(max_length=15)
    status_novo      = models.CharField(max_length=15)
    usuario          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo           = models.TextField(blank=True, null=True)
    categoria_motivo = models.CharField(max_length=40, choices=MOTIVOS_DEVOLUCAO_ETP, blank=True, default='', verbose_name='Categoria do motivo')
    criado_em        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico do ETP'
        verbose_name_plural = 'Históricos do ETP'

    def __str__(self):
        return f"ETP {self.etp_id}: {self.status_anterior} → {self.status_novo}"


class HistoricoNumeroSEI(models.Model):
    """Rastreia cada alteração do número SEI do ETP."""
    etp             = models.ForeignKey(ETP, on_delete=models.CASCADE, related_name='historico_numero_sei')
    numero_anterior = models.CharField(max_length=50)
    numero_novo     = models.CharField(max_length=50)
    usuario         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo          = models.TextField(blank=True, default='')
    criado_em       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico de Número SEI'
        verbose_name_plural = 'Históricos de Número SEI'

    def __str__(self):
        return f"ETP {self.etp_id}: {self.numero_anterior} → {self.numero_novo}"
