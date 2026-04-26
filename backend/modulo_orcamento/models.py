from django.db import models
from core.models import BaseModel


TIPO_ACAO_CHOICES = [
    ('Obra / Equipamento', 'Obra / Equipamento'),
    ('Funcionamento / Operação', 'Funcionamento / Operação'),
    ('Capacitação', 'Capacitação'),
    ('Equipamento', 'Equipamento'),
    ('Publicidade', 'Publicidade'),
    ('Estudo / Projeto Obra', 'Estudo / Projeto Obra'),
    ('Outras Atividades', 'Outras Atividades'),
    ('Serviço', 'Serviço'),
    ('Outros Projetos', 'Outros Projetos'),
    ('Outras Operações Especiais', 'Outras Operações Especiais'),
    ('Reserva de Contingência', 'Reserva de Contingência'),
]

TIPO_FONTE_CHOICES = [
    ('Tesouro', 'Tesouro'),
    ('FESP', 'FESP'),
    ('FUNEBOM', 'FUNEBOM'),
]

STATUS_DOTACAO_CHOICES = [
    ('Proposta', 'Proposta'),
    ('Em Análise', 'Em Análise'),
    ('Aprovada', 'Aprovada'),
    ('Em Execução', 'Em Execução'),
    ('Concluída', 'Concluída'),
    ('Cancelada', 'Cancelada'),
]


class AcaoOrcamentaria(BaseModel):
    """
    Ação orçamentária da organização. Codes differ per org/fund,
    so this is scoped per org_id.
    """
    codigo = models.CharField(max_length=20, verbose_name='Código')
    nome = models.CharField(max_length=255, verbose_name='Nome')
    tipo = models.CharField(
        max_length=50, choices=TIPO_ACAO_CHOICES, verbose_name='Tipo'
    )
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    ativa = models.BooleanField(default=True, verbose_name='Ativa')

    class Meta(BaseModel.Meta):
        unique_together = ['org_id', 'codigo']
        ordering = ['codigo']
        verbose_name = 'Ação Orçamentária'
        verbose_name_plural = 'Ações Orçamentárias'

    def __str__(self):
        return f'{self.codigo} — {self.nome}'


class ElementoDespesa(models.Model):
    """
    Standardized expense elements (Lei 14.133/2021).
    Global — not org-scoped. Pre-populated via management command.
    """
    codigo = models.IntegerField(unique=True, verbose_name='Código')
    descricao = models.CharField(max_length=255, verbose_name='Descrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Elemento de Despesa'
        verbose_name_plural = 'Elementos de Despesa'

    def __str__(self):
        return f'{self.codigo} — {self.descricao}'


class FonteRecurso(BaseModel):
    """
    Funding sources. Org-scoped because each org may use
    specific funds (FESP, FUNEBOM are org-specific).
    """
    codigo = models.IntegerField(verbose_name='Código')
    nome = models.CharField(max_length=100, verbose_name='Nome')
    tipo = models.CharField(
        max_length=20, choices=TIPO_FONTE_CHOICES, verbose_name='Tipo'
    )
    exercicio_anterior = models.BooleanField(
        default=False,
        verbose_name='Exercício anterior',
        help_text='Códigos 300, 342, 359 referem-se a exercícios anteriores'
    )

    class Meta(BaseModel.Meta):
        unique_together = ['org_id', 'codigo']
        ordering = ['codigo']
        verbose_name = 'Fonte de Recurso'
        verbose_name_plural = 'Fontes de Recurso'

    def __str__(self):
        return f'{self.codigo} — {self.nome}'


class DotacaoOrcamentaria(BaseModel):
    """
    Budget allocation (dotação). Core model of the budget planning module.
    Links to AcaoOrcamentaria, ElementoDespesa, FonteRecurso and
    optionally to demand planning needs (NecessidadePlanejamento).
    """
    exercicio_fiscal = models.IntegerField(verbose_name='Exercício fiscal')
    acao = models.ForeignKey(
        AcaoOrcamentaria,
        on_delete=models.PROTECT,
        related_name='dotacoes',
        verbose_name='Ação orçamentária',
    )
    elemento_despesa = models.ForeignKey(
        ElementoDespesa,
        on_delete=models.PROTECT,
        related_name='dotacoes',
        verbose_name='Elemento de despesa',
    )
    fonte_recurso = models.ForeignKey(
        FonteRecurso,
        on_delete=models.PROTECT,
        related_name='dotacoes',
        verbose_name='Fonte de recurso',
    )
    valor_dotado = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Valor dotado (R$)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_DOTACAO_CHOICES,
        default='Proposta',
        verbose_name='Status',
    )
    eixo = models.CharField(
        max_length=255, blank=True, default='', verbose_name='Eixo estratégico'
    )
    objetivo_estrategico = models.CharField(
        max_length=255, blank=True, default='', verbose_name='Objetivo estratégico'
    )
    observacoes = models.TextField(blank=True, default='', verbose_name='Observações')

    necessidades = models.ManyToManyField(
        'modulo_planejamento.NecessidadePlanejamento',
        blank=True,
        related_name='dotacoes',
        verbose_name='Necessidades vinculadas',
    )

    class Meta(BaseModel.Meta):
        ordering = ['-exercicio_fiscal', 'acao__codigo']
        verbose_name = 'Dotação Orçamentária'
        verbose_name_plural = 'Dotações Orçamentárias'
        indexes = [
            models.Index(fields=['exercicio_fiscal']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (
            f'Dotação {self.exercicio_fiscal} — '
            f'{self.acao.codigo} / {self.elemento_despesa.codigo} / '
            f'{self.fonte_recurso.codigo}'
        )
