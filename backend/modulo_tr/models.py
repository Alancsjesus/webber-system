from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel, MesaAtualMixin


class TR(MesaAtualMixin, BaseModel):
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

    # ── Tipo de objeto (herdado do ETP, editável no TR) ───────────────────────
    TIPO_OBJETO_CHOICES = [
        ('bens',                'Bens — Aquisição de materiais/equipamentos'),
        ('servicos',            'Serviços Comuns'),
        ('servicos_engenharia', 'Serviços de Engenharia'),
        ('hibrido',             'Híbrido — Bens e Serviços no mesmo certame'),
        ('obras',               'Obras'),
    ]
    tipo_objeto = models.CharField(
        max_length=25, choices=TIPO_OBJETO_CHOICES, blank=True, default='',
        verbose_name='Tipo de objeto',
    )

    # ── Flags gerais (Seção 1) ────────────────────────────────────────────────
    contratacao_delegada      = models.BooleanField(default=False, verbose_name='Contratação delegada')
    sistema_registro_precos   = models.BooleanField(default=False, verbose_name='Sistema de Registro de Preços (ARP)')

    # ── Requisitos da contratação — parametrizáveis (Seção 4) ─────────────────

    # 4.1 Sustentabilidade
    req_sustentabilidade          = models.BooleanField(default=False, verbose_name='Exige critérios de sustentabilidade')
    req_sustentabilidade_criterios= models.TextField(blank=True, default='', verbose_name='Critérios de sustentabilidade')

    # 4.2 Indicação de marca
    req_indicacao_marca           = models.BooleanField(default=False, verbose_name='Indica marca/modelo')
    req_indicacao_marca_justific  = models.TextField(blank=True, default='', verbose_name='Justificativa da indicação de marca')

    # 4.3 Exame de adequação (amostras / prova de conceito)
    REQ_EXAME_CHOICES = [
        ('nenhum',     'Não será exigido exame de adequação'),
        ('amostra',    'Amostra'),
        ('conformidade','Exame de conformidade'),
        ('prova_conceito','Prova de conceito'),
        ('certificacao','Certificação CONMETRO'),
        ('teste',      'Teste específico'),
    ]
    req_exame_adequacao   = models.CharField(max_length=20, choices=REQ_EXAME_CHOICES, default='nenhum', verbose_name='Exame de adequação do objeto')
    req_exame_descricao   = models.TextField(blank=True, default='', verbose_name='Descrição/critérios do exame')

    # 4.4 Vistoria prévia
    REQ_VISTORIA_CHOICES = [
        ('nao',        'Não será exigida vistoria prévia'),
        ('obrigatoria','Vistoria obrigatória com agendamento'),
        ('facultativa','Vistoria facultativa (declaração em substituição)'),
    ]
    req_vistoria         = models.CharField(max_length=15, choices=REQ_VISTORIA_CHOICES, default='nao', verbose_name='Vistoria prévia')
    req_vistoria_detalhes= models.TextField(blank=True, default='', verbose_name='Detalhes da vistoria (endereço, horário)')
    req_vistoria_justificativa_obrigatoriedade = models.TextField(
        blank=True, default='', verbose_name='Justificativa técnica da obrigatoriedade da vistoria',
        help_text='Obrigatório quando a vistoria é "obrigatória" — TCU só admite vistoria obrigatória quando a Administração '
                   'demonstra que o conhecimento presencial das condições locais é imprescindível e não pode ser suprido por '
                   'outros meios (Súmula 272/2012 e Acórdão 138/2024, ambos do TCU).',
    )

    # 4.5 Subcontratação
    REQ_SUBCONTR_CHOICES = [
        ('nao',     'Não será admitida subcontratação'),
        ('parcial', 'Subcontratação parcial permitida'),
    ]
    req_subcontratacao           = models.CharField(max_length=10, choices=REQ_SUBCONTR_CHOICES, default='nao', verbose_name='Subcontratação')
    req_subcontratacao_descricao = models.TextField(blank=True, default='', verbose_name='Parcelas permitidas para subcontratação')
    req_subcontratacao_mep       = models.BooleanField(default=False, verbose_name='Obrigatório subcontratar ME/EPP (art. 48, II, LC 123/2006)')

    # 4.6 Garantia da contratação
    req_garantia_proposta        = models.BooleanField(default=False, verbose_name='Exige garantia de proposta (art. 58)')
    req_garantia_contratacao     = models.BooleanField(default=False, verbose_name='Exige garantia da contratação (art. 96)')
    req_garantia_percentual      = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Percentual da garantia (%)')
    REQ_GARANTIA_MOD_CHOICES = [
        ('','Qualquer modalidade do art. 96, §1º'),
        ('caucao_dinheiro','Caução em dinheiro'),
        ('titulos','Títulos da dívida pública'),
        ('seguro_garantia','Seguro-garantia'),
        ('fianca_bancaria','Fiança bancária'),
    ]
    req_garantia_modalidade      = models.CharField(max_length=20, choices=REQ_GARANTIA_MOD_CHOICES, blank=True, default='', verbose_name='Modalidade de garantia')

    # ── Habilitação (Seção 8) ─────────────────────────────────────────────────
    HAB_FISCAL_ESFERA_CHOICES = [
        ('estadual', 'Estadual/Distrital'),
        ('municipal','Municipal/Distrital'),
        ('ambos',    'Estadual e Municipal'),
    ]
    hab_fiscal_esfera = models.CharField(max_length=10, choices=HAB_FISCAL_ESFERA_CHOICES, default='estadual', verbose_name='Esfera de habilitação fiscal')

    # ── Campos EXCLUSIVOS DE BENS ─────────────────────────────────────────────
    bens_nao_luxo              = models.BooleanField(default=True, verbose_name='Objeto não se enquadra como bem de luxo (art. 20)')
    bens_reserva_cota          = models.BooleanField(default=False, verbose_name='Reserva de cota para ME/EPP (art. 48, III, LC 123/2006)')
    bens_reserva_cota_percentual= models.PositiveIntegerField(default=25, verbose_name='Percentual da cota ME/EPP (%)')
    bens_carta_solidariedade   = models.BooleanField(default=False, verbose_name='Exige carta de solidariedade do fabricante (para revendedores)')
    bens_validade_pereciveis   = models.TextField(blank=True, default='', verbose_name='Validade mínima dos produtos perecíveis')
    bens_garantia_tecnica_prazo= models.PositiveIntegerField(null=True, blank=True, verbose_name='Prazo de garantia técnica (meses)')
    bens_garantia_tecnica_det  = models.TextField(blank=True, default='', verbose_name='Detalhes da garantia técnica e assistência')

    # ── Campos EXCLUSIVOS DE SERVIÇOS ─────────────────────────────────────────
    serv_transicao_contratual  = models.BooleanField(default=False, verbose_name='Exige transição contratual com transferência de conhecimento')
    serv_transicao_descricao   = models.TextField(blank=True, default='', verbose_name='Descrição da transição contratual')
    serv_regime_execucao       = models.TextField(blank=True, default='', verbose_name='Regime de execução (cronograma, horário, forma)')
    serv_materiais             = models.TextField(blank=True, default='', verbose_name='Materiais e equipamentos a disponibilizar')
    serv_qualificacao_tecnica  = models.TextField(blank=True, default='', verbose_name='Qualificação técnica exigida (atestados, conselho profissional)')
    serv_parcelas_relevancia   = models.TextField(blank=True, default='', verbose_name='Parcelas de maior relevância ou valor significativo')

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

    # ── Campos do Checklist TR — SSP-BA (C0) ─────────────────────────────────
    # Todos opcionais no banco; obrigatoriedade controlada pelo ChecklistEngine.

    # Seção 4.7 — Consórcio
    permite_consorcio = models.BooleanField(
        null=True, blank=True,
        verbose_name='Permite participação de consórcios?',
        help_text='Lei 14.133, art. 15. Regra: admitir. Vedação requer justificativa.',
    )
    permite_consorcio_justificativa = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa para vedação de consórcios',
    )

    # Seção 8.2 — Qualificação Jurídica
    qualificacao_juridica = models.TextField(
        blank=True, default='',
        verbose_name='Qualificação jurídica exigida',
        help_text='Descrever exigências ou informar "Não exigida" com justificativa (art. 62, I).',
    )
    qualificacao_juridica_suprimida = models.BooleanField(
        null=True, blank=True,
        verbose_name='Qualificação jurídica suprimida?',
    )
    qualificacao_juridica_suprimida_justificativa = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa da supressão da qualificação jurídica',
    )

    # Seção 8.4 — Qualificação Econômico-Financeira
    qualificacao_economica = models.TextField(
        blank=True, default='',
        verbose_name='Qualificação econômico-financeira exigida',
        help_text='Descrever ou justificar dispensa (art. 62, IV + IN SAEB 010/2024).',
    )
    qualificacao_economica_dispensada = models.BooleanField(
        null=True, blank=True,
        verbose_name='Qualificação econômico-financeira dispensada?',
        help_text='IN SAEB 010/2024: pode dispensar para entrega imediata ou baixo valor.',
    )

    # Seção 8.2 — Degrau de lances (art. 57)
    degrau_lances = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Degrau mínimo entre lances (R$)',
        help_text='Preferir R$ 0,01 (art. 57). Checklist SSP-BA, item 8.2.',
    )

    # Seção 9.1 — Adequação orçamentária
    adequacao_orcamentaria = models.TextField(
        blank=True, default='',
        verbose_name='Adequação orçamentária',
        help_text='Lei 14.133, art. 6º, XXIII, j. Texto padrão: "As despesas correrão à conta de recursos da Dotação Orçamentária a ser emitida pela Diretoria Geral/SSP."',
    )

    # Seção 7.1 — Prazos de recebimento e pagamento (IN SEGES/ME 77/2022)
    prazo_recebimento_provisorio_dias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Prazo de recebimento provisório (dias úteis)',
        help_text='Sugerido: 5 dias úteis.',
    )
    prazo_recebimento_definitivo_dias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Prazo de recebimento definitivo (dias úteis)',
        help_text='Sugerido: 5 dias úteis.',
    )
    prazo_liquidacao_dias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Prazo de liquidação (dias úteis)',
        help_text='Sugerido: 10 dias úteis (IN SEGES/ME 77/2022).',
    )
    prazo_pagamento_dias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Prazo de pagamento (dias úteis)',
        help_text='Sugerido: 10 dias úteis (IN SEGES/ME 77/2022).',
    )

    # Seção 6.1 — Prazo de providência de irregularidade
    prazo_providencia_irregularidade_dias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Prazo para providência de irregularidade (dias úteis)',
        help_text='Sugerido: 5 dias úteis. Checklist SSP-BA, item 6.1.',
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
    justificativa_agrupamento = models.TextField(blank=True, default='', verbose_name='Justificativa do agrupamento de itens')
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
    """
    Item vinculado a um lote do TR.
    O preço de referência prioriza o Mapa de Preços aprovado vinculado ao DFD;
    se não houver mapa, usa a estimativa do ItemDFD.
    """
    PRECO_ORIGEM_CHOICES = [
        ('mapa', 'Mapa de Preços'),
        ('dfd',  'Estimativa DFD'),
    ]

    lote               = models.ForeignKey(LoteTR, on_delete=models.CASCADE, related_name='itens')
    item_dfd           = models.ForeignKey('modulo_demanda.ItemDFD', on_delete=models.SET_NULL, null=True, related_name='lotes_tr')
    quantidade         = models.DecimalField(max_digits=15, decimal_places=4, verbose_name='Quantidade no lote')
    valor_unitario_ref = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Preço unitário de referência (R$)')
    preco_origem       = models.CharField(max_length=5, choices=PRECO_ORIGEM_CHOICES, default='dfd', verbose_name='Origem do preço')

    class Meta:
        unique_together = [('lote', 'item_dfd')]
        verbose_name = 'Item do Lote TR'
        verbose_name_plural = 'Itens dos Lotes TR'

    def __str__(self):
        obj = self.item_dfd.objeto if self.item_dfd else '—'
        return f'{self.lote.numero} · {obj} ({self.quantidade})'

    @property
    def valor_unitario_efetivo(self):
        """Preço a usar: mapa se disponível, senão estimativa do DFD."""
        if self.valor_unitario_ref:
            return self.valor_unitario_ref
        if self.item_dfd:
            return self.item_dfd.valor_unitario_estimado
        return Decimal('0')

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario_efetivo


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver([post_save, post_delete], sender=ItemLoteTR)
def atualizar_quantidade_comprometida_item_dfd(sender, instance, **kwargs):
    """
    Recalcula ItemDFD.quantidade_comprometida sempre que um ItemLoteTR é
    criado, alterado ou removido. Lotes de Reserva de Cota ME/EPP são
    excluídos do somatório: são um recorte do lote de origem (ver
    LoteTR.gerar_cota), não uma demanda adicional — contá-los duplicaria o
    comprometimento do mesmo item.
    """
    item_dfd = instance.item_dfd
    if item_dfd is None:
        return
    from modulo_demanda.models import ItemDFD
    total = item_dfd.lotes_tr.exclude(lote__modalidade='cota_me_epp').aggregate(
        total=models.Sum('quantidade')
    )['total'] or Decimal('0')
    ItemDFD.objects.filter(pk=item_dfd.pk).update(quantidade_comprometida=total)


MOTIVOS_DEVOLUCAO_TR = [
    ('objeto_mal_definido',          'Objeto mal definido'),
    ('criterios_habilitacao_excess', 'Critérios de habilitação excessivos'),
    ('obrigacoes_desequilibradas',   'Obrigações desequilibradas'),
    ('prazo_irreal',                 'Prazo irreal'),
    ('outro',                        'Outro'),
]


class HistoricoTR(models.Model):
    """Registro imutável de cada transição de status do TR."""
    tr               = models.ForeignKey(TR, on_delete=models.CASCADE, related_name='historico')
    status_anterior  = models.CharField(max_length=15)
    status_novo      = models.CharField(max_length=15)
    usuario          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo           = models.TextField(blank=True, null=True)
    categoria_motivo = models.CharField(max_length=40, choices=MOTIVOS_DEVOLUCAO_TR, blank=True, default='', verbose_name='Categoria do motivo')
    criado_em        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico do TR'
        verbose_name_plural = 'Históricos do TR'

    def __str__(self):
        return f"TR {self.tr_id}: {self.status_anterior} → {self.status_novo}"
