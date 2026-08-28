from django.db import models
from core.models import BaseModel


class NecessidadePlanejamento(BaseModel):
    """
    Necessidade de contratação identificada no planejamento.
    Nasce em uma unidade demandante e pode ser direcionada ao órgão pai
    (centralização) ou executada pelo próprio órgão filho.
    """

    STATUS_CHOICES = [
        ('Identificada', 'Identificada'),
        ('Em Análise',   'Em Análise'),
        ('Aprovada',     'Aprovada'),
        ('DFD Criado',   'DFD Criado'),
        ('Cancelada',    'Cancelada'),
    ]

    PRIORIDADE_CHOICES = [
        ('Alta',  'Alta'),
        ('Média', 'Média'),
        ('Baixa', 'Baixa'),
    ]

    AREA_CHOICES = [
        ('TI',        'Tecnologia da Informação'),
        ('Formação',  'Formação'),
        ('Ops',       'Operações'),
        ('Rede',      'Rede'),
        ('Frota',     'Frota'),
        ('Derivados', 'Derivados'),
    ]

    titulo                   = models.CharField(max_length=255, verbose_name='Título')
    descricao                = models.TextField(verbose_name='Descrição')
    area_aplicacao           = models.JSONField(default=list, verbose_name='Áreas de aplicação')
    valor_estimado           = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor estimado (R$)')
    departamento_solicitante = models.CharField(max_length=255, verbose_name='Departamento solicitante')
    exercicio_fiscal         = models.IntegerField(verbose_name='Exercício fiscal')
    prioridade               = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='Média', verbose_name='Prioridade')
    status                   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Identificada', verbose_name='Status')
    prazo_desejado           = models.DateField(null=True, blank=True, verbose_name='Prazo desejado')
    observacoes              = models.TextField(blank=True, default='', verbose_name='Observações')

    TIPO_EXECUCAO_CHOICES = [
        ('interna', 'Execução Interna'),
        ('externa', 'Execução Externa (Órgão Pai)'),
    ]
    tipo_execucao = models.CharField(
        max_length=10,
        choices=TIPO_EXECUCAO_CHOICES,
        default='interna',
        verbose_name='Tipo de execução',
    )

    ACEITE_PAI_CHOICES = [
        ('pendente', 'Aguardando aceite do órgão pai'),
        ('aceita',   'Aceita pelo órgão pai'),
        ('recusada', 'Recusada pelo órgão pai'),
    ]
    aceite_pai = models.CharField(
        max_length=10,
        choices=ACEITE_PAI_CHOICES,
        null=True, blank=True,
        verbose_name='Aceite pelo órgão pai',
        help_text='Preenchido automaticamente para execuções externas',
    )

    # Órgão que atualmente controla esta necessidade para fins de métricas.
    # None = ainda pertence ao org de origem; preenchido quando o órgão
    # executor inicia análise (aceita a necessidade em seu fluxo).
    org_gestor = models.ForeignKey(
        'core.Orgao', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='necessidades_gerenciadas',
        verbose_name='Órgão gestor',
    )

    # Unidade e órgão de origem
    unidade_demandante = models.ForeignKey(
        'core.UnidadeOrganizacional',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='necessidades',
        verbose_name='Unidade demandante',
    )

    # Órgão que irá executar (pode ser o órgão pai centralizador ou o próprio órgão filho)
    orgao_executor = models.ForeignKey(
        'core.Orgao',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='necessidades_a_executar',
        verbose_name='Órgão executor',
    )

    # Referência ao DFD gerado
    dfd = models.OneToOneField(
        'modulo_demanda.DFD',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='necessidade_origem',
        verbose_name='DFD gerado',
    )

    ata_origem = models.ForeignKey(
        'modulo_arp.Ata', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='necessidades_saque',
        verbose_name='Ata de Registro de Preços (saque)',
        help_text='Preencher quando a necessidade for atendida por saque de Ata gerenciada por esta Secretaria.',
    )

    # Origem: quando a necessidade nasce da consolidação de itens de um
    # Plano de Aplicação FESP/Emendas/Financiamentos (ver modulo_fesp).
    origem_plano_aplicacao_fesp = models.ForeignKey(
        'modulo_fesp.PlanoAplicacao',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='necessidades_geradas',
        verbose_name='Origem: Plano de Aplicação (FESP/Emendas/Financiamentos)',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Necessidade de Planejamento'
        verbose_name_plural = 'Necessidades de Planejamento'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['exercicio_fiscal']),
            models.Index(fields=['prioridade']),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.exercicio_fiscal}) — {self.status}"


class HistoricoNecessidade(models.Model):
    """Registro imutável de cada transição de status da Necessidade."""
    necessidade     = models.ForeignKey(
        NecessidadePlanejamento, on_delete=models.CASCADE, related_name='historico',
    )
    status_anterior = models.CharField(max_length=30, blank=True, default='')
    status_novo     = models.CharField(max_length=30)
    usuario         = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, related_name='+',
    )
    motivo          = models.TextField(blank=True, default='')
    criado_em       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f"Necessidade {self.necessidade_id}: {self.status_anterior} → {self.status_novo}"


class ItemPlanoOrcamentario(models.Model):
    """Classificação da origem de cada necessidade em um plano orçamentário."""
    ORIGEM_CHOICES = [
        ('propria',     'Demanda Própria'),
        ('orgao_filho', 'Demanda de Órgão Filho'),
    ]
    CATEGORIA_ORCA_CHOICES = [
        ('custeio',      'Custeio'),
        ('investimento', 'Investimento'),
    ]

    plano       = models.ForeignKey(
        'PlanoOrcamentario', on_delete=models.CASCADE, related_name='itens',
    )
    necessidade = models.ForeignKey(
        NecessidadePlanejamento, on_delete=models.CASCADE, related_name='itens_plano',
    )
    origem      = models.CharField(max_length=15, choices=ORIGEM_CHOICES, default='propria')

    # ── Campos específicos do PCA (IN SEGES 65/2021) ──────────────────────────
    categoria_orcamentaria = models.CharField(
        max_length=15, choices=CATEGORIA_ORCA_CHOICES, blank=True, default='',
        verbose_name='Categoria orçamentária',
    )
    programa_acao = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='Programa/Ação',
        help_text='Ex: 1234/0001',
    )
    data_estimada_inicio = models.DateField(
        null=True, blank=True,
        verbose_name='Data estimada de início',
    )
    vinculacao_pgi = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='OE — Objetivo Estratégico',
        help_text='Referência ao objetivo estratégico institucional vinculado a esta contratação',
    )
    numero_sequencial_pca = models.PositiveIntegerField(
        null=True, blank=True, editable=False,
        verbose_name='Sequencial no PCA',
    )

    class Meta:
        unique_together = [('plano', 'necessidade')]
        ordering = ['numero_sequencial_pca', 'id']
        verbose_name = 'Item do Plano Orçamentário'
        verbose_name_plural = 'Itens do Plano Orçamentário'

    def __str__(self):
        return f"{self.plano} ← {self.necessidade.titulo} [{self.origem}]"


class PlanoOrcamentario(models.Model):
    """
    Plano orçamentário de um órgão por exercício fiscal.
    Agrega as necessidades aprovadas que serão executadas por esse órgão.
    """
    orgao            = models.ForeignKey(
        'core.Orgao', on_delete=models.CASCADE,
        related_name='planos_orcamentarios',
        verbose_name='Órgão',
    )
    exercicio_fiscal = models.IntegerField(verbose_name='Exercício fiscal')
    descricao        = models.CharField(max_length=200, blank=True, verbose_name='Descrição')
    dotacao_total    = models.DecimalField(
        max_digits=18, decimal_places=2,
        null=True, blank=True,
        verbose_name='Dotação total (R$)',
    )
    necessidades     = models.ManyToManyField(
        NecessidadePlanejamento,
        through='ItemPlanoOrcamentario',
        blank=True,
        related_name='planos',
        verbose_name='Necessidades vinculadas',
    )
    status_pca = models.CharField(
        max_length=15,
        choices=[('rascunho', 'Rascunho'), ('publicado', 'Publicado')],
        default='rascunho',
        verbose_name='Status do PCA',
    )
    criado_em        = models.DateTimeField(auto_now_add=True)
    atualizado_em    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-exercicio_fiscal', 'orgao__sigla']
        unique_together = [('orgao', 'exercicio_fiscal')]
        verbose_name = 'Plano Orçamentário'
        verbose_name_plural = 'Planos Orçamentários'

    @property
    def org_id_id(self):
        return self.orgao_id

    def __str__(self):
        return f"Plano {self.exercicio_fiscal} — {self.orgao.sigla}"
