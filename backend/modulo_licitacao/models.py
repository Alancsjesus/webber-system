"""
Módulo de Licitação e Contratações Diretas — Lei 14.133/2021.

Cobre:
- Procedimento (licitação, dispensa, inexigibilidade)
- TramitacaoExterna (PGE, SAEB, Casa Civil, SEFAZ…)
- ResultadoLote (empresa vencedora, valor final, desconto)
- Limites de dispensa por família SIMPAS/exercício
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from core.models import BaseModel


# ── Constantes legais (Lei 14.133/2021) ────────────────────────────────────

MODALIDADE_CHOICES = [
    ('pregao_eletronico',    'Pregão Eletrônico'),
    ('concorrencia',         'Concorrência'),
    ('dispensa_eletronica',  'Dispensa Eletrônica (por Valor — Art. 75 I/II)'),
    ('dispensa_tradicional', 'Dispensa Tradicional'),
    ('inexigibilidade',      'Inexigibilidade'),
]

PREFIXO_MODALIDADE = {
    'pregao_eletronico':    'PE',
    'concorrencia':         'CC',
    'dispensa_eletronica':  'DE',
    'dispensa_tradicional': 'DT',
    'inexigibilidade':      'INEX',
}

# Prazo mínimo legal entre publicação e abertura (dias úteis)
PRAZO_LEGAL_DIAS_UTEIS = {
    'pregao_eletronico':    8,   # Lei 14.133, art. 55, II
    'concorrencia':         25,  # Lei 14.133, art. 55, I
    'dispensa_eletronica':  3,   # Lei 14.133, art. 75, §3°
    'dispensa_tradicional': 0,
    'inexigibilidade':      0,
}

# Tetos de dispensa por exercício (atualizados pelo Decreto 11.871/2023)
TETO_DISPENSA_BENS_SERVICOS  = Decimal('57277.08')
TETO_DISPENSA_OBRAS          = Decimal('114554.16')

STATUS_CHOICES = [
    ('Em Instrução',          'Em Instrução'),
    ('Aguardando Aprovação',  'Aguardando Aprovação interna'),
    ('Aprovado',              'Aprovado para publicação/envio'),
    ('Publicado',             'Publicado (edital no ar)'),
    ('Em Sessão',             'Em Sessão Pública'),
    ('Homologado',            'Homologado'),
    ('Contratado',            'Contratado'),
    ('Deserto',               'Deserto (sem propostas)'),
    ('Fracassado',            'Fracassado (propostas recusadas)'),
    ('Revogado',              'Revogado'),
    ('Anulado',               'Anulado'),
]

TRANSICOES_PERMITIDAS = {
    'Em Instrução':         ['Aguardando Aprovação', 'Anulado'],
    'Aguardando Aprovação': ['Aprovado', 'Em Instrução'],
    'Aprovado':             ['Publicado', 'Contratado', 'Em Instrução'],  # Contratado para dispensas diretas
    'Publicado':            ['Em Sessão', 'Revogado', 'Anulado'],
    'Em Sessão':            ['Homologado', 'Deserto', 'Fracassado', 'Revogado'],
    'Homologado':           ['Contratado', 'Anulado'],
    'Contratado':           [],
    'Deserto':              ['Em Instrução', 'Anulado'],
    'Fracassado':           ['Em Instrução', 'Anulado'],
    'Revogado':             [],
    'Anulado':              [],
}

FUNDAMENTO_DISPENSA_CHOICES = [
    ('art75_i',   'Art. 75, I — Bens e serviços (até R$ 57.277,08)'),
    ('art75_ii',  'Art. 75, II — Obras e serviços de eng. (até R$ 114.554,16)'),
    ('art75_iii', 'Art. 75, III — Licitação deserta'),
    ('art75_iv',  'Art. 75, IV — Licitação fracassada'),
    ('art75_v',   'Art. 75, V — Emergência/calamidade'),
    ('art75_vi',  'Art. 75, VI — Empresa pública/sociedade de economia mista'),
    ('art75_xi',  'Art. 75, XI — Associações/cooperativas (preço menor)'),
    ('outro',     'Outro fundamento legal'),
]

FUNDAMENTO_INEXIGIBILIDADE_CHOICES = [
    ('art74_i',  'Art. 74, I — Fornecedor exclusivo'),
    ('art74_ii', 'Art. 74, II — Serviço técnico especializado de natureza singular'),
    ('art74_iii','Art. 74, III — Contratação de profissional do setor artístico'),
    ('art74_iv', 'Art. 74, IV — Credenciamento'),
    ('art74_v',  'Art. 74, V — Aquisição de obras de arte ou produto artístico'),
    ('outro',    'Outro fundamento legal'),
]

ORGAO_EXTERNO_CHOICES = [
    ('PGE',       'PGE — Procuradoria Geral do Estado'),
    ('SAEB',      'SAEB — Secretaria de Administração do Estado'),
    ('CasaCivil', 'Casa Civil'),
    ('SEFAZ',     'SEFAZ — Secretaria da Fazenda do Estado'),
    ('TCM',       'TCM — Tribunal de Contas dos Municípios'),
    ('TCE',       'TCE — Tribunal de Contas do Estado'),
    ('CGE',       'CGE — Controladoria Geral do Estado'),
    ('outro',     'Outro órgão'),
]

TIPO_TRAMITACAO_CHOICES = [
    ('aprovacao_juridica',  'Aprovação jurídica'),
    ('aprovacao_tecnica',   'Aprovação técnica'),
    ('consulta',            'Consulta/parecer'),
    ('anuencia',            'Anuência prévia'),
    ('registro',            'Registro/publicação'),
    ('outro',               'Outro'),
]


# ── Models ──────────────────────────────────────────────────────────────────

class Procedimento(BaseModel):
    """
    Procedimento licitatório ou contratação direta vinculado a um DFD/TR.
    Núcleo do Módulo de Licitação — conecta o planejamento (TR) ao Contrato.
    """
    numero   = models.CharField(max_length=30, unique=True, editable=False,
                                verbose_name='Número do procedimento')
    exercicio = models.IntegerField(verbose_name='Exercício fiscal')
    modalidade = models.CharField(max_length=25, choices=MODALIDADE_CHOICES,
                                  verbose_name='Modalidade')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES,
                              default='Em Instrução', verbose_name='Status')

    # Unidade gestora responsável pelo procedimento — define a sigla no número
    unidade_gestora = models.ForeignKey(
        'core.UnidadeOrganizacional',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='procedimentos_gestora',
        verbose_name='Unidade gestora',
    )

    # Vínculo com o planejamento
    dfd = models.ForeignKey(
        'modulo_demanda.DFD', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='procedimentos',
        verbose_name='DFD de origem',
    )
    tr = models.ForeignKey(
        'modulo_tr.TR', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='procedimentos',
        verbose_name='TR de origem',
    )

    # Objeto e valores
    objeto        = models.TextField(verbose_name='Objeto do procedimento')
    valor_estimado = models.DecimalField(max_digits=15, decimal_places=2,
                                         null=True, blank=True,
                                         verbose_name='Valor estimado (R$)')

    # Fundamento legal (dispensas e inexigibilidades)
    fundamento_dispensa       = models.CharField(max_length=20,
        choices=FUNDAMENTO_DISPENSA_CHOICES, blank=True, default='',
        verbose_name='Fundamento (dispensa)')
    fundamento_inexigibilidade = models.CharField(max_length=20,
        choices=FUNDAMENTO_INEXIGIBILIDADE_CHOICES, blank=True, default='',
        verbose_name='Fundamento (inexigibilidade)')
    justificativa             = models.TextField(blank=True, default='',
        verbose_name='Justificativa da contratação direta')

    # Processo SEI
    numero_sei    = models.CharField(max_length=50, blank=True, default='',
                                     verbose_name='Número do processo SEI')

    # Datas do procedimento
    data_publicacao  = models.DateField(null=True, blank=True,
                                        verbose_name='Data de publicação do edital')
    data_abertura    = models.DateField(null=True, blank=True,
                                        verbose_name='Data de abertura das propostas')
    data_homologacao = models.DateField(null=True, blank=True,
                                        verbose_name='Data de homologação')

    # Prazos legais calculados automaticamente
    prazo_minimo_dias_uteis = models.PositiveIntegerField(
        default=0, editable=False,
        verbose_name='Prazo mínimo legal (dias úteis)')
    alerta_prazo = models.CharField(max_length=255, blank=True, default='',
                                    verbose_name='Alerta de prazo legal')
    alerta_teto_dispensa = models.CharField(max_length=255, blank=True, default='',
                                            verbose_name='Alerta de teto de dispensa')

    # Controle de dispensa (acumulador)
    valor_acumulado_dispensa = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, editable=False,
        verbose_name='Valor acumulado de dispensas (família/exercício)')

    motivo_revogacao = models.TextField(blank=True, default='',
                                        verbose_name='Motivo da revogação/anulação')
    observacoes = models.TextField(blank=True, default='')

    class Meta(BaseModel.Meta):
        ordering = ['-exercicio', '-created_at']
        verbose_name = 'Procedimento'
        verbose_name_plural = 'Procedimentos'

    def __str__(self):
        return f'{self.numero} — {self.get_modalidade_display()}'

    @property
    def eh_licitacao(self):
        return self.modalidade in ('pregao_eletronico', 'concorrencia')

    @property
    def eh_dispensa(self):
        return self.modalidade in ('dispensa_eletronica', 'dispensa_tradicional')

    @property
    def eh_inexigibilidade(self):
        return self.modalidade == 'inexigibilidade'

    @property
    def transicoes_disponiveis(self):
        return TRANSICOES_PERMITIDAS.get(self.status, [])

    def calcular_prazo_legal(self):
        """Retorna o prazo mínimo legal em dias úteis."""
        return PRAZO_LEGAL_DIAS_UTEIS.get(self.modalidade, 0)

    @staticmethod
    def familias_simpas(dfd=None, tr=None):
        """
        Famílias SIMPAS envolvidas num procedimento — via itens dos lotes do TR
        quando houver, senão diretamente dos itens do DFD (caso mais comum em
        dispensas por valor, que costumam dispensar TR/ETP).
        """
        familias = set()
        if tr is not None:
            for lote in tr.lotes.prefetch_related('itens__item_dfd__item_catalogo'):
                for item in lote.itens.all():
                    if item.item_dfd and item.item_dfd.item_catalogo:
                        fam = item.item_dfd.item_catalogo.familia
                        if fam:
                            familias.add(fam)
        if not familias and dfd is not None:
            for item in dfd.itens.select_related('item_catalogo'):
                if item.item_catalogo and item.item_catalogo.familia:
                    familias.add(item.item_catalogo.familia)
        return familias

    @staticmethod
    def calcular_teto_dispensa(org_id, exercicio, modalidade, dfd, tr, valor_estimado, excluir_pk=None):
        """
        Calcula o acumulado de dispensas que compartilham ao menos uma família
        SIMPAS com este procedimento, no mesmo exercício/órgão, e retorna
        (alerta, acumulado_sem_atual, teto, familias) — alerta vazio quando
        dentro do limite.
        """
        if modalidade not in ('dispensa_eletronica', 'dispensa_tradicional'):
            return '', Decimal('0'), Decimal('0'), set()

        familias = Procedimento.familias_simpas(dfd=dfd, tr=tr)
        if not familias:
            return '', Decimal('0'), Decimal('0'), set()

        tipo = getattr(tr.etp, 'tipo_objeto', '') if tr is not None and tr.etp_id else ''
        teto = TETO_DISPENSA_OBRAS if tipo in ('obras', 'servicos_engenharia') else TETO_DISPENSA_BENS_SERVICOS

        outros = Procedimento.objects.filter(
            org_id=org_id,
            exercicio=exercicio,
            modalidade__in=['dispensa_eletronica', 'dispensa_tradicional'],
            status__in=['Aprovado', 'Contratado', 'Homologado'],
        ).exclude(pk=excluir_pk or 0).select_related('tr__etp', 'dfd')

        acumulado = Decimal('0')
        for p in outros:
            p_familias = Procedimento.familias_simpas(dfd=p.dfd, tr=p.tr)
            if familias & p_familias and p.valor_estimado:
                acumulado += p.valor_estimado

        valor_atual = valor_estimado or Decimal('0')
        total_com_atual = acumulado + valor_atual

        alerta = ''
        pct = (total_com_atual / teto * 100) if teto else 0
        if total_com_atual > teto:
            alerta = (
                f'ATENÇÃO: Teto de dispensa EXCEDIDO para a(s) família(s) {", ".join(sorted(familias))}. '
                f'Acumulado R$ {total_com_atual:,.2f} > Limite R$ {teto:,.2f} (Art. 75 Lei 14.133).'
            )
        elif pct >= 80:
            restante = teto - acumulado
            alerta = (
                f'Alerta: {pct:.0f}% do teto de dispensa utilizado para a(s) família(s) {", ".join(sorted(familias))}. '
                f'Saldo restante: R$ {restante:,.2f}.'
            )
        return alerta, acumulado, teto, familias

    def verificar_teto_dispensa(self):
        """Versão de instância (procedimento já persistido) de calcular_teto_dispensa."""
        if not self.eh_dispensa:
            return '', Decimal('0')
        alerta, acumulado, teto, familias = Procedimento.calcular_teto_dispensa(
            org_id=self.org_id_id, exercicio=self.exercicio, modalidade=self.modalidade,
            dfd=self.dfd, tr=self.tr, valor_estimado=self.valor_estimado, excluir_pk=self.pk,
        )

        return alerta, acumulado


class HistoricoProcedimento(models.Model):
    """Registro imutável de cada transição de status do procedimento."""
    procedimento   = models.ForeignKey(Procedimento, on_delete=models.CASCADE,
                                       related_name='historico')
    status_anterior = models.CharField(max_length=25)
    status_novo     = models.CharField(max_length=25)
    usuario         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo          = models.TextField(blank=True, default='')
    criado_em       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.procedimento.numero}: {self.status_anterior} → {self.status_novo}'


class TramitacaoExterna(models.Model):
    """
    Registro de envio/retorno do processo a órgãos externos
    (PGE, SAEB, Casa Civil, SEFAZ…).
    """
    procedimento    = models.ForeignKey(Procedimento, on_delete=models.CASCADE,
                                        related_name='tramitacoes')
    orgao_externo   = models.CharField(max_length=20, choices=ORGAO_EXTERNO_CHOICES,
                                       verbose_name='Órgão externo')
    orgao_descricao = models.CharField(max_length=100, blank=True, default='',
                                       verbose_name='Descrição (quando "outro")')
    tipo            = models.CharField(max_length=25, choices=TIPO_TRAMITACAO_CHOICES,
                                       verbose_name='Tipo de tramitação')
    numero_sei      = models.CharField(max_length=50, blank=True, default='',
                                       verbose_name='Nº SEI da tramitação')
    data_envio      = models.DateField(verbose_name='Data de envio')
    prazo_esperado  = models.DateField(null=True, blank=True,
                                       verbose_name='Prazo esperado de retorno')
    data_retorno    = models.DateField(null=True, blank=True,
                                       verbose_name='Data de retorno efetivo')
    observacoes     = models.TextField(blank=True, default='')
    registrado_por  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                        related_name='tramitacoes_registradas')
    criado_em       = models.DateTimeField(auto_now_add=True)
    atualizado_em   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_envio']
        verbose_name = 'Tramitação Externa'
        verbose_name_plural = 'Tramitações Externas'

    def __str__(self):
        return f'{self.get_orgao_externo_display()} — {self.data_envio}'

    @property
    def status(self):
        from datetime import date
        if self.data_retorno:
            return 'Retornado'
        if self.prazo_esperado and date.today() > self.prazo_esperado:
            return 'Atrasado'
        return 'Pendente'

    @property
    def orgao_label(self):
        if self.orgao_externo == 'outro':
            return self.orgao_descricao or 'Outro'
        return self.get_orgao_externo_display()


class ResultadoLote(models.Model):
    """
    Resultado de cada lote após sessão de licitação ou despacho de dispensa.
    Homologado = empresa vencedora + valor final → habilita criação de Contrato.
    """
    RESULTADO_CHOICES = [
        ('homologado', 'Homologado'),
        ('deserto',    'Deserto (sem propostas)'),
        ('fracassado', 'Fracassado (propostas recusadas)'),
        ('cancelado',  'Cancelado'),
    ]

    procedimento      = models.ForeignKey(Procedimento, on_delete=models.CASCADE,
                                          related_name='resultados')
    lote              = models.ForeignKey('modulo_tr.LoteTR', null=True, blank=True,
                                          on_delete=models.SET_NULL,
                                          related_name='resultados_licitacao',
                                          verbose_name='Lote do TR')
    descricao_lote    = models.CharField(max_length=200, blank=True, default='',
                                         verbose_name='Descrição do lote')
    resultado         = models.CharField(max_length=15, choices=RESULTADO_CHOICES,
                                         verbose_name='Resultado')
    fornecedor        = models.ForeignKey('modulo_fornecedor.Fornecedor', null=True, blank=True,
                                          on_delete=models.PROTECT,
                                          related_name='resultados_licitacao',
                                          verbose_name='Fornecedor vencedor')
    empresa_vencedora = models.CharField(max_length=200, blank=True, default='',
                                         verbose_name='Empresa vencedora (histórico)')
    cnpj_vencedor     = models.CharField(max_length=20, blank=True, default='',
                                         verbose_name='CNPJ do vencedor')
    valor_estimado    = models.DecimalField(max_digits=15, decimal_places=2,
                                            null=True, blank=True,
                                            verbose_name='Valor estimado (R$)')
    valor_final       = models.DecimalField(max_digits=15, decimal_places=2,
                                            null=True, blank=True,
                                            verbose_name='Valor final adjudicado (R$)')
    contrato_gerado   = models.ForeignKey('modulo_contrato.Contrato', null=True, blank=True,
                                          on_delete=models.SET_NULL,
                                          related_name='resultado_licitacao',
                                          verbose_name='Contrato gerado')
    observacoes       = models.TextField(blank=True, default='')
    criado_em         = models.DateTimeField(auto_now_add=True)
    atualizado_em     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['procedimento', 'descricao_lote']
        verbose_name = 'Resultado de Lote'
        verbose_name_plural = 'Resultados de Lotes'

    def __str__(self):
        return f'{self.descricao_lote or self.lote} — {self.get_resultado_display()}'

    @property
    def percentual_desconto(self):
        if self.valor_estimado and self.valor_final and self.valor_estimado > 0:
            return round((1 - self.valor_final / self.valor_estimado) * 100, 2)
        return None


# ── Numeração automática ─────────────────────────────────────────────────────

@receiver(pre_save, sender=Procedimento)
def gerar_numero_procedimento(sender, instance, **kwargs):
    if instance.numero:
        return
    prefixo   = PREFIXO_MODALIDADE.get(instance.modalidade, 'PR')
    exercicio = instance.exercicio or 2026
    org       = instance.org_id

    # Sigla da unidade gestora quando informada; caso contrário usa o órgão
    if instance.unidade_gestora_id:
        sigla = instance.unidade_gestora.sigla
    elif org:
        sigla = org.sigla
    else:
        sigla = 'ORG'

    ultimo = (
        Procedimento.objects
        .filter(org_id=org, exercicio=exercicio, modalidade=instance.modalidade)
        .exclude(pk=instance.pk if instance.pk else 0)
        .count()
    )
    seq = ultimo + 1
    instance.numero = f'{prefixo}-{sigla}-{seq:03d}/{exercicio}'
    instance.prazo_minimo_dias_uteis = PRAZO_LEGAL_DIAS_UTEIS.get(instance.modalidade, 0)
