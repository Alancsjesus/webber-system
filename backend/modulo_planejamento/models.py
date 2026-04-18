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


class ItemPlanoOrcamentario(models.Model):
    """Classificação da origem de cada necessidade em um plano orçamentário."""
    ORIGEM_CHOICES = [
        ('propria',     'Demanda Própria'),
        ('orgao_filho', 'Demanda de Órgão Filho'),
    ]
    plano       = models.ForeignKey(
        'PlanoOrcamentario', on_delete=models.CASCADE, related_name='itens',
    )
    necessidade = models.ForeignKey(
        NecessidadePlanejamento, on_delete=models.CASCADE, related_name='itens_plano',
    )
    origem      = models.CharField(max_length=15, choices=ORIGEM_CHOICES, default='propria')

    class Meta:
        unique_together = [('plano', 'necessidade')]
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
    criado_em        = models.DateTimeField(auto_now_add=True)
    atualizado_em    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-exercicio_fiscal', 'orgao__sigla']
        unique_together = [('orgao', 'exercicio_fiscal')]
        verbose_name = 'Plano Orçamentário'
        verbose_name_plural = 'Planos Orçamentários'

    def __str__(self):
        return f"Plano {self.exercicio_fiscal} — {self.orgao.sigla}"
