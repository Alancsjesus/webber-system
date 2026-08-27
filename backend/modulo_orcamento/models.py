from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


# Valores originais de TIPO_ACAO_CHOICES/TIPO_FONTE_CHOICES, mantidos aqui só como
# referência histórica da migração 0007 (seed de TipoAcaoOrcamentaria/TipoFonteRecurso).
# Os tipos hoje são parametrizáveis via TipoAcaoOrcamentaria/TipoFonteRecurso (ver abaixo).

STATUS_DOTACAO_CHOICES = [
    ('Proposta', 'Proposta'),
    ('Em Análise', 'Em Análise'),
    ('Aprovada', 'Aprovada'),
    ('Em Execução', 'Em Execução'),
    ('Concluída', 'Concluída'),
    ('Cancelada', 'Cancelada'),
]


class TipoAcaoOrcamentaria(models.Model):
    """
    Catálogo parametrizável de tipos de Ação Orçamentária (classificação PPA:
    Obra/Equipamento, Serviço, Capacitação etc.). Global — não escopado por
    org_id, mesmo padrão de ElementoDespesa. Editável em Configurações →
    Orçamento → Tipos de Ação, sem exigir alteração de código.
    """
    descricao = models.CharField(max_length=100, unique=True, verbose_name='Descrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        ordering = ['descricao']
        verbose_name = 'Tipo de Ação Orçamentária'
        verbose_name_plural = 'Tipos de Ação Orçamentária'

    def __str__(self):
        return self.descricao


class TipoFonteRecurso(models.Model):
    """
    Catálogo parametrizável de tipos de Fonte de Recurso (Tesouro, FESP,
    FUNEBOM etc.). Global — não escopado por org_id, mesmo padrão de
    ElementoDespesa. Editável em Configurações → Orçamento → Tipos de Fonte.
    """
    descricao = models.CharField(max_length=100, unique=True, verbose_name='Descrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        ordering = ['descricao']
        verbose_name = 'Tipo de Fonte de Recurso'
        verbose_name_plural = 'Tipos de Fonte de Recurso'

    def __str__(self):
        return self.descricao


class AcaoOrcamentaria(BaseModel):
    """
    Ação orçamentária da organização. Codes differ per org/fund,
    so this is scoped per org_id.
    """
    codigo = models.CharField(max_length=20, verbose_name='Código')
    nome = models.CharField(max_length=255, verbose_name='Nome')
    tipo = models.ForeignKey(
        TipoAcaoOrcamentaria, on_delete=models.PROTECT,
        related_name='acoes', verbose_name='Tipo',
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
    Elementos de despesa (dois dígitos: 30, 39, 52...).
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
        return f'{self.codigo:02d} — {self.descricao}'


class NaturezaDespesa(models.Model):
    """
    Natureza de despesa no formato 3.3.90.30 (ex: 339030, 339039, 449052).
    Global — not org-scoped, padronizada pela classificação orçamentária.
    """
    codigo = models.CharField(max_length=6, unique=True, verbose_name='Código')
    descricao = models.CharField(max_length=255, verbose_name='Descrição')
    elemento_despesa = models.ForeignKey(
        ElementoDespesa,
        on_delete=models.PROTECT,
        related_name='naturezas',
        verbose_name='Elemento de despesa',
    )
    ativa = models.BooleanField(default=True, verbose_name='Ativa')

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Natureza de Despesa'
        verbose_name_plural = 'Naturezas de Despesa'

    @property
    def formato(self):
        c = str(self.codigo).zfill(6)
        return f'{c[0]}.{c[1]}.{c[2:4]}.{c[4:6]}'

    def __str__(self):
        return f'{self.formato} — {self.descricao}'


class FonteRecurso(BaseModel):
    """
    Funding sources. Org-scoped because each org may use
    specific funds (FESP, FUNEBOM are org-specific).
    """
    codigo = models.IntegerField(verbose_name='Código')
    nome = models.CharField(max_length=100, verbose_name='Nome')
    tipo = models.ForeignKey(
        TipoFonteRecurso, on_delete=models.PROTECT,
        related_name='fontes', verbose_name='Tipo',
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


class SubFonteRecurso(BaseModel):
    """
    Subfonte de uma Fonte de Recurso — mesmo padrão de hierarquia usado entre
    NaturezaDespesa e ElementoDespesa (FK simples, org-scoped).
    """
    fonte_recurso = models.ForeignKey(
        FonteRecurso, on_delete=models.PROTECT,
        related_name='subfontes', verbose_name='Fonte de recurso',
    )
    codigo = models.CharField(max_length=20, verbose_name='Código')
    nome = models.CharField(max_length=100, verbose_name='Nome')
    ativa = models.BooleanField(default=True, verbose_name='Ativa')

    class Meta(BaseModel.Meta):
        unique_together = ['org_id', 'fonte_recurso', 'codigo']
        ordering = ['fonte_recurso__codigo', 'codigo']
        verbose_name = 'Subfonte de Recurso'
        verbose_name_plural = 'Subfontes de Recurso'

    def __str__(self):
        return f'{self.fonte_recurso.codigo}.{self.codigo} — {self.nome}'


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
    natureza_despesa = models.ForeignKey(
        NaturezaDespesa,
        on_delete=models.PROTECT,
        related_name='dotacoes',
        null=True, blank=True,
        verbose_name='Natureza de despesa',
    )
    fonte_recurso = models.ForeignKey(
        FonteRecurso,
        on_delete=models.PROTECT,
        related_name='dotacoes',
        verbose_name='Fonte de recurso',
    )
    subfonte_recurso = models.ForeignKey(
        SubFonteRecurso,
        on_delete=models.PROTECT,
        related_name='dotacoes',
        null=True, blank=True,
        verbose_name='Subfonte de recurso',
    )
    valor_dotado = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Valor dotado (R$)'
    )
    valor_indicado = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='Valor indicado (R$)',
    )
    valor_descentralizado = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='Valor descentralizado (R$)',
    )
    valor_concedido = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='Valor concedido (R$)',
    )
    valor_empenhado = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='Valor empenhado (R$)',
    )
    valor_liquidado = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='Valor liquidado (R$)',
    )
    valor_pago = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='Valor pago (R$)',
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


# ── Indicação Orçamentária / DOD ───────────────────────────────────────────────

class IndicacaoOrcamentaria(BaseModel):
    """
    Indicação orçamentária que formaliza a alocação de recursos de uma ou mais
    dotações para uma demanda (DFD ou Necessidade). Quando aprovada pelo
    Ordenador de Despesa, gera a DOD — Declaração do Ordenador de Despesa.
    """
    STATUS_CHOICES = [
        ('Rascunho',  'Rascunho'),
        ('Submetida', 'Submetida'),
        ('Aprovada',  'Aprovada (DOD emitida)'),
        ('Cancelada', 'Cancelada'),
    ]

    TRANSICOES_PERMITIDAS = {
        'Rascunho':  ['Submetida'],
        'Submetida': ['Aprovada', 'Cancelada'],
        'Aprovada':  ['Cancelada'],
        'Cancelada': [],
    }

    numero           = models.CharField(max_length=20, verbose_name='Número')
    exercicio_fiscal = models.IntegerField(verbose_name='Exercício fiscal')
    numero_sei = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name='Processo SEI',
        help_text='Processo SEI da própria indicação/DOD (distinto do SEI do DFD vinculado).',
    )
    dfd              = models.ForeignKey(
        'modulo_demanda.DFD',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='indicacoes',
        verbose_name='DFD vinculado',
    )
    necessidade = models.ForeignKey(
        'modulo_planejamento.NecessidadePlanejamento',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='indicacoes',
        verbose_name='Necessidade vinculada',
    )
    valor_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='Valor total indicado (R$)',
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='Rascunho',
        verbose_name='Status',
    )
    observacoes     = models.TextField(blank=True, default='', verbose_name='Observações')
    ordenador       = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='indicacoes_ordenadas',
        verbose_name='Ordenador de despesa',
    )
    data_aprovacao  = models.DateField(null=True, blank=True, verbose_name='Data de aprovação')
    motivo_cancelamento = models.TextField(
        blank=True, default='', verbose_name='Motivo do cancelamento',
    )
    dotacoes = models.ManyToManyField(
        DotacaoOrcamentaria,
        through='IndicacaoDotacao',
        blank=True,
        related_name='indicacoes',
        verbose_name='Dotações indicadas',
    )

    class Meta(BaseModel.Meta):
        ordering = ['-exercicio_fiscal', '-created_at']
        unique_together = [['org_id', 'numero']]
        verbose_name = 'Indicação Orçamentária'
        verbose_name_plural = 'Indicações Orçamentárias'

    def __str__(self):
        return f'{self.numero} — {self.status} ({self.exercicio_fiscal})'


class IndicacaoDotacao(models.Model):
    """Vínculo entre Indicação e Dotação com o valor indicado para cada dotação."""
    indicacao      = models.ForeignKey(
        IndicacaoOrcamentaria, on_delete=models.CASCADE, related_name='itens',
    )
    dotacao        = models.ForeignKey(
        DotacaoOrcamentaria, on_delete=models.PROTECT, related_name='itens_indicacao',
    )
    valor_indicado = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Valor indicado (R$)',
    )
    em_diligencia = models.BooleanField(
        default=False, verbose_name='Em diligência',
        help_text='Pendência administrativa antes de confirmar o valor indicado.',
    )

    class Meta:
        unique_together = [['indicacao', 'dotacao']]
        verbose_name = 'Item de Indicação'
        verbose_name_plural = 'Itens de Indicação'

    def __str__(self):
        return f'{self.indicacao.numero} ← {self.dotacao} = R$ {self.valor_indicado}'


class ItemIndicacaoDotacao(models.Model):
    """
    Rateio: quanto de uma linha Indicação+Dotação é destinado a cada Item do
    DFD. N:N real — uma dotação pode financiar vários itens, e um item pode
    ser financiado por várias dotações/indicações diferentes.
    """
    indicacao_dotacao = models.ForeignKey(
        IndicacaoDotacao, on_delete=models.CASCADE, related_name='itens_detalhados',
    )
    item_dfd = models.ForeignKey(
        'modulo_demanda.ItemDFD', on_delete=models.CASCADE, related_name='rateios_indicacao',
    )
    valor = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor rateado (R$)')

    class Meta:
        unique_together = [['indicacao_dotacao', 'item_dfd']]
        verbose_name = 'Item de Indicação (rateio)'
        verbose_name_plural = 'Itens de Indicação (rateio)'

    def __str__(self):
        return f'{self.indicacao_dotacao} → {self.item_dfd.objeto} = R$ {self.valor}'


class DescentralizacaoOrcamentaria(models.Model):
    """
    NPO — Nota de Programação Orçamentária.
    Registra cada descentralização de recursos de uma dotação indicada.
    Uma NPO por dotação; múltiplas NPOs podem acumular no mesmo indicação_dotacao.
    Ao salvar: dotacao.valor_descentralizado += valor
    Ao cancelar: dotacao.valor_descentralizado -= valor
    Restrição de cancelamento: descentralizado - valor >= concedido
    """
    from decimal import Decimal

    indicacao_dotacao = models.ForeignKey(
        IndicacaoDotacao, on_delete=models.PROTECT,
        related_name='descentralizacoes',
        verbose_name='Item de indicação (dotação)',
    )
    numero_npo        = models.CharField(max_length=50, verbose_name='Número da NPO (sistema financeiro)')
    numero_ne         = models.CharField(max_length=50, blank=True, default='', verbose_name='Número da NE (FIPLAN)')
    data_emissao      = models.DateField(verbose_name='Data de emissão')
    valor             = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor descentralizado (R$)')
    cancelada         = models.BooleanField(default=False, verbose_name='Cancelada')
    data_cancelamento = models.DateField(null=True, blank=True, verbose_name='Data do cancelamento')
    motivo_cancelamento = models.TextField(blank=True, default='', verbose_name='Motivo do cancelamento')
    observacoes       = models.TextField(blank=True, default='', verbose_name='Observações')
    registrada_por    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='npos_registradas')
    criado_em         = models.DateTimeField(auto_now_add=True)
    atualizado_em     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_emissao', '-criado_em']
        verbose_name = 'Descentralização Orçamentária (NPO)'
        verbose_name_plural = 'Descentralizações Orçamentárias (NPO)'

    def __str__(self):
        status = '[CANCELADA] ' if self.cancelada else ''
        return f'{status}NPO {self.numero_npo} — R$ {self.valor} ({self.data_emissao})'


class ConcessaoOrcamentaria(models.Model):
    """
    Concessão orçamentária — documento externo que formaliza a execução
    dos recursos descentralizados.
    Ao salvar: dotacao.valor_concedido += valor
    Ao cancelar: dotacao.valor_concedido -= valor
    Restrição: valor_concedido <= valor_descentralizado
    """
    indicacao_dotacao = models.ForeignKey(
        IndicacaoDotacao, on_delete=models.PROTECT,
        related_name='concessoes',
        verbose_name='Item de indicação (dotação)',
    )
    numero_doc        = models.CharField(max_length=50, verbose_name='Número do documento (sistema financeiro)')
    data_emissao      = models.DateField(verbose_name='Data de emissão')
    valor             = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor concedido (R$)')
    cancelada         = models.BooleanField(default=False, verbose_name='Cancelada')
    data_cancelamento = models.DateField(null=True, blank=True, verbose_name='Data do cancelamento')
    motivo_cancelamento = models.TextField(blank=True, default='', verbose_name='Motivo do cancelamento')
    observacoes       = models.TextField(blank=True, default='', verbose_name='Observações')
    registrada_por    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='concessoes_registradas')
    criado_em         = models.DateTimeField(auto_now_add=True)
    atualizado_em     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_emissao', '-criado_em']
        verbose_name = 'Concessão Orçamentária'
        verbose_name_plural = 'Concessões Orçamentárias'

    def __str__(self):
        status = '[CANCELADA] ' if self.cancelada else ''
        return f'{status}Concessão {self.numero_doc} — R$ {self.valor} ({self.data_emissao})'


class EmpenhoOrcamentario(models.Model):
    """
    Empenho — 1º estágio da despesa pública (Lei 4.320/64, art. 58-61).
    Independente da cadeia NPO/Concessão (mecanismo de descentralização
    FIPLAN/BA); limitado pelo valor indicado da própria linha.
    Ao salvar: dotacao.valor_empenhado += valor
    Ao cancelar: dotacao.valor_empenhado -= valor
    Restrição de cancelamento: empenhado - valor >= liquidado
    """
    indicacao_dotacao = models.ForeignKey(
        IndicacaoDotacao, on_delete=models.PROTECT,
        related_name='empenhos',
        verbose_name='Item de indicação (dotação)',
    )
    numero_doc        = models.CharField(max_length=50, verbose_name='Número da Nota de Empenho')
    data_emissao      = models.DateField(verbose_name='Data de emissão')
    valor             = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor empenhado (R$)')
    cancelada         = models.BooleanField(default=False, verbose_name='Cancelada')
    data_cancelamento = models.DateField(null=True, blank=True, verbose_name='Data do cancelamento')
    motivo_cancelamento = models.TextField(blank=True, default='', verbose_name='Motivo do cancelamento')
    observacoes       = models.TextField(blank=True, default='', verbose_name='Observações')
    registrada_por    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='empenhos_registrados')
    criado_em         = models.DateTimeField(auto_now_add=True)
    atualizado_em     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_emissao', '-criado_em']
        verbose_name = 'Empenho Orçamentário'
        verbose_name_plural = 'Empenhos Orçamentários'

    def __str__(self):
        status = '[CANCELADA] ' if self.cancelada else ''
        return f'{status}Empenho {self.numero_doc} — R$ {self.valor} ({self.data_emissao})'


class LiquidacaoOrcamentaria(models.Model):
    """
    Liquidação — 2º estágio da despesa pública (Lei 4.320/64, art. 62-63).
    Ao salvar: dotacao.valor_liquidado += valor
    Ao cancelar: dotacao.valor_liquidado -= valor
    Restrição de cancelamento: liquidado - valor >= pago
    """
    indicacao_dotacao = models.ForeignKey(
        IndicacaoDotacao, on_delete=models.PROTECT,
        related_name='liquidacoes',
        verbose_name='Item de indicação (dotação)',
    )
    numero_doc        = models.CharField(max_length=50, verbose_name='Número do documento de liquidação')
    data_emissao      = models.DateField(verbose_name='Data de emissão')
    valor             = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor liquidado (R$)')
    cancelada         = models.BooleanField(default=False, verbose_name='Cancelada')
    data_cancelamento = models.DateField(null=True, blank=True, verbose_name='Data do cancelamento')
    motivo_cancelamento = models.TextField(blank=True, default='', verbose_name='Motivo do cancelamento')
    observacoes       = models.TextField(blank=True, default='', verbose_name='Observações')
    registrada_por    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='liquidacoes_registradas')
    criado_em         = models.DateTimeField(auto_now_add=True)
    atualizado_em     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_emissao', '-criado_em']
        verbose_name = 'Liquidação Orçamentária'
        verbose_name_plural = 'Liquidações Orçamentárias'

    def __str__(self):
        status = '[CANCELADA] ' if self.cancelada else ''
        return f'{status}Liquidação {self.numero_doc} — R$ {self.valor} ({self.data_emissao})'


class PagamentoOrcamentario(models.Model):
    """
    Pagamento — 3º estágio da despesa pública (Lei 4.320/64, art. 64).
    Ao salvar: dotacao.valor_pago += valor
    Ao cancelar: dotacao.valor_pago -= valor
    """
    indicacao_dotacao = models.ForeignKey(
        IndicacaoDotacao, on_delete=models.PROTECT,
        related_name='pagamentos',
        verbose_name='Item de indicação (dotação)',
    )
    numero_doc        = models.CharField(max_length=50, verbose_name='Número do documento de pagamento')
    data_emissao      = models.DateField(verbose_name='Data de emissão')
    valor             = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor pago (R$)')
    cancelada         = models.BooleanField(default=False, verbose_name='Cancelada')
    data_cancelamento = models.DateField(null=True, blank=True, verbose_name='Data do cancelamento')
    motivo_cancelamento = models.TextField(blank=True, default='', verbose_name='Motivo do cancelamento')
    observacoes       = models.TextField(blank=True, default='', verbose_name='Observações')
    registrada_por    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pagamentos_registrados')
    criado_em         = models.DateTimeField(auto_now_add=True)
    atualizado_em     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_emissao', '-criado_em']
        verbose_name = 'Pagamento Orçamentário'
        verbose_name_plural = 'Pagamentos Orçamentários'

    def __str__(self):
        status = '[CANCELADA] ' if self.cancelada else ''
        return f'{status}Pagamento {self.numero_doc} — R$ {self.valor} ({self.data_emissao})'


class HistoricoIndicacao(models.Model):
    """Trilha imutável de transições de status da Indicação Orçamentária."""
    indicacao       = models.ForeignKey(
        IndicacaoOrcamentaria, on_delete=models.CASCADE, related_name='historico',
    )
    status_anterior = models.CharField(max_length=15)
    status_novo     = models.CharField(max_length=15)
    usuario         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo          = models.TextField(blank=True, null=True)
    criado_em       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico de Indicação'
