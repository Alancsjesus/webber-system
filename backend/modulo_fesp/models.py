from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from core.models import BaseModel


class InstrumentoFinanceiro(BaseModel):
    """
    Instrumento jurídico concreto que dá origem a recursos extraordinários
    geridos pelo órgão (um FESP específico, uma emenda parlamentar, um
    convênio, um contrato de repasse, uma transferência fundo a fundo ou
    um financiamento). É o registro do "de onde vem o dinheiro"; o
    PlanoAplicacao é o "para onde vai".
    """
    TIPO_CHOICES = [
        ('fesp',                        'FESP — Fundo Estadual de Segurança Pública'),
        ('emenda_parlamentar',          'Emenda Parlamentar'),
        ('convenio',                    'Convênio'),
        ('contrato_repasse',            'Contrato de Repasse'),
        ('transferencia_fundo_a_fundo', 'Transferência Fundo a Fundo'),
        ('financiamento',               'Financiamento'),
    ]
    STATUS_CHOICES = [
        ('rascunho',  'Rascunho'),
        ('vigente',   'Vigente'),
        ('encerrado', 'Encerrado'),
        ('cancelado', 'Cancelado'),
    ]
    TRANSICOES_PERMITIDAS = {
        'rascunho':  ['vigente', 'cancelado'],
        'vigente':   ['encerrado', 'cancelado'],
        'encerrado': [],
        'cancelado': [],
    }

    tipo_instrumento = models.CharField(
        max_length=30, choices=TIPO_CHOICES, verbose_name='Tipo de instrumento',
    )
    numero_instrumento = models.CharField(
        max_length=100, verbose_name='Número do instrumento (externo)',
        help_text='Ex: nº do convênio no SICONV, nº da emenda no SIOP, exercício do FESP.',
    )
    objeto = models.TextField(verbose_name='Objeto')
    orgao_concedente_nome = models.CharField(
        max_length=255, blank=True, default='', verbose_name='Órgão/ente concedente',
        help_text='Ex: União, Ministério da Justiça e Segurança Pública, Bancada Federal BA.',
    )
    fonte_recurso = models.ForeignKey(
        'modulo_orcamento.FonteRecurso', null=True, blank=True,
        on_delete=models.PROTECT, related_name='instrumentos_financeiros',
        verbose_name='Fonte de recurso (Orçamento)',
        help_text='Vínculo opcional com a Fonte de Recurso formal do módulo de Orçamento, '
                   'usado quando a execução via Indicação/Dotação começar.',
    )
    valor_total_pactuado = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Valor total pactuado (R$)',
    )
    valor_contrapartida = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='Valor de contrapartida (R$)',
    )
    data_assinatura = models.DateField(null=True, blank=True, verbose_name='Data de assinatura')
    vigencia_inicio = models.DateField(null=True, blank=True, verbose_name='Início da vigência')
    vigencia_fim = models.DateField(null=True, blank=True, verbose_name='Fim da vigência')
    numero_processo_sei = models.CharField(
        max_length=50, blank=True, default='', verbose_name='Nº processo SEI',
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='rascunho', verbose_name='Status',
    )
    dados_especificos = models.JSONField(
        default=dict, blank=True, verbose_name='Dados específicos do tipo',
        help_text='Campos livres conforme o tipo de instrumento — ex: '
                   '{"parlamentar_autor": "..."} para emenda; '
                   '{"banco": "...", "agencia": "...", "conta_especifica": "..."} para '
                   'convênio/repasse/fundo a fundo; '
                   '{"agente_financeiro": "...", "numero_contrato_financiamento": "..."} '
                   'para financiamento.',
    )
    observacoes = models.TextField(blank=True, default='', verbose_name='Observações')

    class Meta(BaseModel.Meta):
        unique_together = [['org_id', 'tipo_instrumento', 'numero_instrumento']]
        ordering = ['-data_assinatura', '-created_at']
        verbose_name = 'Instrumento Financeiro'
        verbose_name_plural = 'Instrumentos Financeiros'

    def __str__(self):
        return f'{self.get_tipo_instrumento_display()} {self.numero_instrumento}'


class HistoricoInstrumentoFinanceiro(models.Model):
    """Registro imutável de cada transição de status do Instrumento Financeiro."""
    instrumento = models.ForeignKey(
        InstrumentoFinanceiro, on_delete=models.CASCADE, related_name='historico',
    )
    status_anterior = models.CharField(max_length=15, blank=True, default='')
    status_novo = models.CharField(max_length=15)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    motivo = models.TextField(blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'Instrumento {self.instrumento_id}: {self.status_anterior} → {self.status_novo}'


class ComposicaoConselhoGestor(BaseModel):
    """
    Membro do Conselho Gestor do FESP (Lei 14.169/2019, arts. 7º-12).
    É uma atribuição adicional com mandato/portaria — não substitui o
    papel de acesso operacional que o usuário já tem no sistema
    (ex: ordenador, gestor_planejamento).
    """
    CARGO_CHOICES = [
        ('presidente',                 'Presidente (Secretário de Segurança Pública)'),
        ('assessor_planejamento',      'Assessor de Planejamento'),
        ('diretor_geral',              'Diretor-Geral'),
        ('representante_casa_civil',   'Representante da Casa Civil'),
        ('representante_fazenda',      'Representante da Secretaria da Fazenda'),
        ('representante_planejamento', 'Representante da Secretaria de Planejamento'),
        ('membro_convidado',           'Membro Convidado'),
    ]

    usuario = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='composicoes_conselho_fesp', verbose_name='Usuário',
    )
    cargo = models.CharField(max_length=30, choices=CARGO_CHOICES, verbose_name='Cargo no Conselho')
    orgao_representado = models.ForeignKey(
        'core.Orgao', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+', verbose_name='Órgão representado (tenant Webber)',
    )
    nome_orgao_externo = models.CharField(
        max_length=150, blank=True, default='', verbose_name='Órgão/ente externo',
        help_text='Preencher quando o órgão representado não é um tenant Webber '
                   '(ex: Casa Civil, SEFAZ).',
    )
    portaria_nomeacao = models.CharField(max_length=100, blank=True, default='', verbose_name='Portaria de nomeação')
    data_inicio_mandato = models.DateField(verbose_name='Início do mandato')
    data_fim_mandato = models.DateField(null=True, blank=True, verbose_name='Fim do mandato')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta(BaseModel.Meta):
        ordering = ['cargo']
        verbose_name = 'Membro do Conselho Gestor (FESP)'
        verbose_name_plural = 'Membros do Conselho Gestor (FESP)'

    def __str__(self):
        nome = self.usuario.get_full_name() or self.usuario.username if self.usuario else '(vago)'
        return f'{self.get_cargo_display()} — {nome}'


class PlanoAplicacao(BaseModel):
    """
    Plano de Aplicação anual — agregador aprovado pelo Conselho Gestor e
    homologado por ato do Chefe do Poder Executivo (Lei 14.169/2019, art. 12).
    """
    STATUS_CHOICES = [
        ('elaboracao',         'Em Elaboração'),
        ('submetido_conselho', 'Submetido ao Conselho Gestor'),
        ('devolvido',          'Devolvido para Ajustes'),
        ('aprovado_conselho',  'Aprovado pelo Conselho Gestor'),
        ('homologado',         'Homologado (Ato do Chefe do Executivo)'),
        ('aprovado',           'Aprovado'),
        ('publicado',          'Publicado'),
        ('encerrado',          'Encerrado'),
        ('cancelado',          'Cancelado'),
    ]
    # Naturezas cujo rito legal exige Conselho Gestor + homologação por ato do
    # Chefe do Executivo (Lei 14.169/2019, arts. 7º-12). As demais naturezas
    # (emenda, convênio, repasse, fundo a fundo, financiamento) usam o rito
    # simples — cada uma tem sua própria prestação de contas externa ao Webber.
    NATUREZAS_RITO_CONSELHO = {'fesp'}
    TRANSICOES_FESP = {
        'elaboracao':         ['submetido_conselho', 'cancelado'],
        'submetido_conselho': ['aprovado_conselho', 'devolvido'],
        'devolvido':          ['elaboracao'],
        'aprovado_conselho':  ['homologado', 'devolvido'],
        'homologado':         ['publicado'],
        'publicado':          ['encerrado'],
        'encerrado':          [],
        'cancelado':          [],
    }
    TRANSICOES_SIMPLES = {
        'elaboracao': ['aprovado', 'cancelado'],
        'aprovado':   ['publicado'],
        'publicado':  ['encerrado'],
        'encerrado':  [],
        'cancelado':  [],
    }
    PREFIXO_NUMERO = {
        'fesp':                        'PLANFESP',
        'emenda_parlamentar':          'PLANEMEN',
        'convenio':                    'PLANCONV',
        'contrato_repasse':            'PLANREPA',
        'transferencia_fundo_a_fundo': 'PLANFAF',
        'financiamento':               'PLANFIN',
    }

    numero = models.CharField(max_length=40, blank=True, editable=False, verbose_name='Número')
    natureza = models.CharField(
        max_length=30, choices=InstrumentoFinanceiro.TIPO_CHOICES, default='fesp',
        verbose_name='Natureza do recurso',
        help_text='Define o rito de aprovação do plano (Conselho Gestor + homologação, exclusivo '
                   'do FESP, ou aprovação direta para as demais naturezas) e quais Instrumentos '
                   'Financeiros podem ser vinculados aos itens deste plano.',
    )
    exercicio_fiscal = models.IntegerField(verbose_name='Exercício fiscal')
    ementa = models.CharField(max_length=255, verbose_name='Ementa')
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='elaboracao', verbose_name='Status',
    )

    # ── Vedações legais (Lei 14.169/2019, art. 4º, §1º) — atestação humana. ──
    # O sistema exige que a pergunta tenha sido respondida antes da submissão
    # ao Conselho; não arbitra automaticamente se a resposta está correta —
    # ver CLAUDE.md / plano de implementação para a justificativa.
    declaracao_nao_pessoal = models.BooleanField(
        null=True, blank=True,
        verbose_name='Declara que nenhum item se destina a folha de pessoal/encargos',
    )
    declaracao_nao_unidade_administrativa = models.BooleanField(
        null=True, blank=True,
        verbose_name='Declara que nenhum item beneficia unidade puramente administrativa',
    )
    declaracao_sem_contingenciamento = models.BooleanField(
        null=True, blank=True,
        verbose_name='Declara ciência de que os recursos não estão sujeitos a contingenciamento',
    )

    # ── Conselho Gestor ──
    reuniao_aprovacao = models.ForeignKey(
        'ReuniaoConselhoGestor', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+', verbose_name='Reunião de aprovação',
    )
    motivo_devolucao_conselho = models.TextField(blank=True, default='', verbose_name='Motivo da devolução')

    # ── Ato de homologação (Chefe do Poder Executivo) ──
    numero_ato = models.CharField(max_length=50, blank=True, default='', verbose_name='Nº do ato de homologação')
    data_ato = models.DateField(null=True, blank=True, verbose_name='Data do ato')
    numero_processo_sei_ato = models.CharField(
        max_length=50, blank=True, default='', verbose_name='Nº processo SEI do ato',
    )

    # ── Contatos formais (exigidos em exportações/prestação de contas) ──
    responsavel_gestao_nome = models.CharField(max_length=150, blank=True, default='', verbose_name='Responsável pela gestão do fundo — nome')
    responsavel_gestao_email = models.EmailField(blank=True, default='', verbose_name='Responsável pela gestão do fundo — e-mail')
    responsavel_gestao_cargo = models.CharField(max_length=150, blank=True, default='', verbose_name='Responsável pela gestão do fundo — cargo')
    responsavel_gestao_telefone = models.CharField(max_length=20, blank=True, default='', verbose_name='Responsável pela gestão do fundo — telefone')
    responsavel_elaboracao_nome = models.CharField(max_length=150, blank=True, default='', verbose_name='Responsável pela elaboração — nome')
    responsavel_elaboracao_email = models.EmailField(blank=True, default='', verbose_name='Responsável pela elaboração — e-mail')
    responsavel_elaboracao_cargo = models.CharField(max_length=150, blank=True, default='', verbose_name='Responsável pela elaboração — cargo')
    responsavel_elaboracao_telefone = models.CharField(max_length=20, blank=True, default='', verbose_name='Responsável pela elaboração — telefone')

    # ── Narrativa do plano (diagnóstico, meta geral, justificativa) ──
    diagnostico = models.TextField(blank=True, default='', verbose_name='Diagnóstico')
    meta_geral = models.TextField(blank=True, default='', verbose_name='Meta geral')
    justificativa = models.TextField(blank=True, default='', verbose_name='Justificativa')

    # ── Indicador geral de resultado (mesma forma do indicador de cada Meta Específica) ──
    indicador_geral_descricao = models.TextField(blank=True, default='', verbose_name='Indicador geral — descrição')
    indicador_geral_formula = models.TextField(blank=True, default='', verbose_name='Indicador geral — fórmula')
    indicador_geral_valor_referencia = models.CharField(max_length=50, blank=True, default='', verbose_name='Indicador geral — valor de referência')
    indicador_geral_periodo_referencia = models.CharField(max_length=50, blank=True, default='', verbose_name='Indicador geral — período de referência')
    indicador_geral_fonte = models.CharField(max_length=255, blank=True, default='', verbose_name='Indicador geral — fonte')

    # ── Decomposição financeira (Lei 14.169/2019, art. 3º — origem dos recursos) ──
    # "Planejado" é o quanto de cada origem já foi alocado a Metas Específicas/itens;
    # os demais são o teto disponível daquela origem no exercício.
    valor_originario_investimento = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor originário — Investimento (R$)')
    valor_originario_custeio = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor originário — Custeio (R$)')
    valor_suplementar_investimento = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor suplementar — Investimento (R$)')
    valor_suplementar_custeio = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor suplementar — Custeio (R$)')
    valor_rendimento_investimento = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor rendimento — Investimento (R$)')
    valor_rendimento_custeio = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor rendimento — Custeio (R$)')
    valor_planejado_investimento = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, editable=False, verbose_name='Valor planejado — Investimento (R$)',
    )
    valor_planejado_custeio = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, editable=False, verbose_name='Valor planejado — Custeio (R$)',
    )

    class Meta(BaseModel.Meta):
        unique_together = [['org_id', 'exercicio_fiscal', 'natureza']]
        ordering = ['-exercicio_fiscal']
        verbose_name = 'Plano de Aplicação'
        verbose_name_plural = 'Planos de Aplicação'

    def __str__(self):
        return f'{self.numero or "(sem número)"} — {self.ementa} ({self.exercicio_fiscal})'

    @property
    def usa_rito_conselho(self):
        return self.natureza in self.NATUREZAS_RITO_CONSELHO

    @property
    def transicoes_permitidas(self):
        return self.TRANSICOES_FESP if self.usa_rito_conselho else self.TRANSICOES_SIMPLES


class HistoricoPlanoAplicacao(models.Model):
    """Registro imutável de cada transição de status do Plano de Aplicação."""
    plano = models.ForeignKey(PlanoAplicacao, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=20, blank=True, default='')
    status_novo = models.CharField(max_length=20)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    motivo = models.TextField(blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'Plano {self.plano_id}: {self.status_anterior} → {self.status_novo}'


class MetaEspecifica(BaseModel):
    """
    Meta Específica de um Plano de Aplicação — agrupa itens em torno de um
    objetivo e indicador próprios (ex: "reduzir feminicídios no interior"),
    espelhando a estrutura usada nos planos de aplicação do FESP.
    """
    STATUS_CHOICES = [
        ('planejada',    'Planejada'),
        ('em_execucao',  'Em Execução'),
        ('concluida',    'Concluída'),
        ('cancelada',    'Cancelada'),
    ]
    PERIODICIDADE_CHOICES = [
        ('mensal',      'Mensal'),
        ('trimestral',  'Trimestral'),
        ('semestral',   'Semestral'),
        ('anual',       'Anual'),
    ]

    plano = models.ForeignKey(PlanoAplicacao, on_delete=models.CASCADE, related_name='metas_especificas')
    numero = models.PositiveIntegerField(null=True, blank=True, editable=False, verbose_name='Número')
    titulo = models.CharField(max_length=255, verbose_name='Título')
    descricao_meta = models.TextField(blank=True, default='', verbose_name='Descrição da meta')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='planejada', verbose_name='Status')

    descricao_indicador = models.TextField(blank=True, default='', verbose_name='Descrição do indicador')
    formula_indicador = models.TextField(blank=True, default='', verbose_name='Fórmula do indicador')
    valor_referencia = models.CharField(max_length=50, blank=True, default='', verbose_name='Valor de referência')
    periodo_referencia = models.CharField(max_length=50, blank=True, default='', verbose_name='Período de referência')
    fonte_indicador = models.CharField(max_length=255, blank=True, default='', verbose_name='Fonte do indicador')
    periodicidade = models.CharField(max_length=15, choices=PERIODICIDADE_CHOICES, blank=True, default='', verbose_name='Periodicidade')

    carteira_politicas_mjsp = models.CharField(max_length=255, blank=True, default='', verbose_name='Carteira de Políticas do MJSP')
    meta_pnsp = models.CharField(max_length=255, blank=True, default='', verbose_name='Meta do PNSP')
    meta_pesp = models.CharField(max_length=255, blank=True, default='', verbose_name='Meta do PESP')

    valor_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, editable=False, verbose_name='Valor total (R$)',
        help_text='Soma dos itens vinculados a esta Meta Específica (calculado a partir da Fase 2).',
    )

    class Meta(BaseModel.Meta):
        unique_together = [['plano', 'numero']]
        ordering = ['numero']
        verbose_name = 'Meta Específica'
        verbose_name_plural = 'Metas Específicas'

    def __str__(self):
        return f'ME {self.numero} — {self.titulo}'


@receiver(pre_save, sender=MetaEspecifica)
def gerar_numero_meta_especifica(sender, instance, **kwargs):
    if instance.numero:
        return
    instance.numero = (
        MetaEspecifica.objects.filter(plano=instance.plano).exclude(pk=instance.pk).count() + 1
    )


class GrupoConsolidacaoItem(BaseModel):
    """
    Agrupamento de ItemPlanoAplicacao considerados a mesma demanda entre
    unidades/órgãos diferentes (ex: PMBA e CBMBA pedindo o mesmo tipo de
    item). Criado na Fase 3 (consolidação); o modelo já existe aqui porque
    ItemPlanoAplicacao referencia-o.
    """
    STATUS_CHOICES = [
        ('confirmado', 'Confirmado'),
        ('processado', 'Necessidades Geradas'),
        ('descartado', 'Descartado'),
    ]
    plano = models.ForeignKey(PlanoAplicacao, on_delete=models.CASCADE, related_name='grupos_consolidacao')
    chave_agrupamento = models.CharField(
        max_length=50, blank=True, default='', verbose_name='Chave de agrupamento',
        help_text='Código usado para sugerir o agrupamento (família SIMPAS ou prefixo do Cód. SENASP).',
    )
    titulo = models.CharField(max_length=255, verbose_name='Título')
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='confirmado', verbose_name='Status')

    class Meta(BaseModel.Meta):
        ordering = ['-created_at']
        verbose_name = 'Grupo de Consolidação de Itens'
        verbose_name_plural = 'Grupos de Consolidação de Itens'

    def __str__(self):
        return self.titulo


class ItemPlanoAplicacao(BaseModel):
    """
    Item de uma Meta Específica — a linha orçamentária concreta (bem,
    serviço ou capacitação), no mesmo formato usado nos planos de
    aplicação do FESP: Bem/Serviço, Cód. SENASP, Natureza (ND),
    Instituição/Destinação beneficiária e base legal do inciso da Lei
    14.169/2019 que ampara o item.
    """
    NATUREZA_CHOICES = [
        ('custeio',      'Custeio'),
        ('investimento', 'Investimento'),
    ]
    STATUS_CHOICES = [
        ('pendente',            'Pendente'),
        ('consolidado',         'Consolidado'),
        ('necessidade_gerada',  'Necessidade Gerada'),
        ('cancelado',           'Cancelado'),
    ]

    meta_especifica = models.ForeignKey(
        MetaEspecifica, on_delete=models.CASCADE, related_name='itens', verbose_name='Meta Específica',
    )
    instrumento = models.ForeignKey(
        InstrumentoFinanceiro, on_delete=models.PROTECT, related_name='itens_plano', verbose_name='Instrumento financeiro',
    )

    org_beneficiaria = models.ForeignKey(
        'core.Orgao', on_delete=models.PROTECT, related_name='itens_plano_fesp_beneficiados',
        verbose_name='Instituição beneficiária',
        help_text='Força/órgão que se beneficia do item (ex: Polícia Militar, Polícia Civil). '
                   'É apenas um dado de coluna — a linha inteira pertence ao tenant do órgão gestor do fundo.',
    )
    unidade_beneficiaria = models.ForeignKey(
        'core.UnidadeOrganizacional', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='itens_plano_fesp', verbose_name='Unidade beneficiária (estruturada)',
    )
    destinacao = models.CharField(
        max_length=500, blank=True, default='', verbose_name='Destinação',
        help_text='Texto livre — unidade(s)/departamento(s) específicos beneficiados '
                   '(ex: várias DEAMs listadas), conforme registrado no plano oficial.',
    )

    item_catalogo = models.ForeignKey(
        'core.ItemCatalogo', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='itens_plano_fesp', verbose_name='Item do catálogo (SIMPAS)',
        help_text='Vínculo opcional ao catálogo interno do Webber, usado para sugestão de '
                   'agrupamento por família SIMPAS.',
    )
    codigo_senasp = models.CharField(
        max_length=30, blank=True, default='', verbose_name='Código SENASP',
        help_text='Código do catálogo federal (SENASP), quando aplicável (ex: MAT.14.006.0002).',
    )
    bem_servico = models.CharField(max_length=255, verbose_name='Bem/Serviço')
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    base_legal = models.CharField(
        max_length=255, blank=True, default='', verbose_name='Base legal',
        help_text='Dispositivo legal/normativo que ampara o item (ex: "Lei 14.169/2019, Art. 7º, I, b)").',
    )
    natureza = models.CharField(max_length=15, choices=NATUREZA_CHOICES, verbose_name='Natureza (ND)')

    unidade_medida = models.CharField(max_length=50, verbose_name='Unidade de medida')
    quantidade = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Quantidade planejada')
    valor_unitario_estimado = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor unitário estimado (R$)')
    valor_total_estimado = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, editable=False, verbose_name='Valor total estimado (R$)',
    )

    aprovado = models.BooleanField(
        null=True, blank=True, verbose_name='Aprovado',
        help_text='Atestação humana de aprovação do item dentro do plano — mesmo espírito das '
                   'declarações de vedação do Plano: o sistema registra a decisão, não a arbitra.',
    )

    grupo_consolidacao = models.ForeignKey(
        GrupoConsolidacaoItem, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='itens', verbose_name='Grupo de consolidação',
    )
    necessidade_gerada = models.ForeignKey(
        'modulo_planejamento.NecessidadePlanejamento', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='itens_plano_aplicacao_fesp', verbose_name='Necessidade gerada',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name='Status')
    observacoes = models.TextField(blank=True, default='', verbose_name='Observações')

    def save(self, *args, **kwargs):
        self.valor_total_estimado = self.quantidade * self.valor_unitario_estimado
        super().save(*args, **kwargs)

    class Meta(BaseModel.Meta):
        ordering = ['created_at']
        verbose_name = 'Item do Plano de Aplicação'
        verbose_name_plural = 'Itens do Plano de Aplicação'
        indexes = [
            models.Index(fields=['org_id', '-created_at']),
            models.Index(fields=['meta_especifica', 'status']),
            models.Index(fields=['org_beneficiaria']),
        ]

    def __str__(self):
        return f'{self.bem_servico} — {self.org_beneficiaria.sigla if self.org_beneficiaria_id else "?"}'


def _recalcular_totais(meta_especifica_id):
    if not meta_especifica_id:
        return
    from django.db.models import Sum
    meta = MetaEspecifica.objects.filter(pk=meta_especifica_id).first()
    if not meta:
        return
    total = meta.itens.exclude(status='cancelado').aggregate(s=Sum('valor_total_estimado'))['s'] or 0
    meta.valor_total = total
    meta.save(update_fields=['valor_total'])

    plano = meta.plano
    investimento = 0
    custeio = 0
    for m in plano.metas_especificas.all():
        for item in m.itens.exclude(status='cancelado').only('valor_total_estimado', 'natureza'):
            if item.natureza == 'investimento':
                investimento += item.valor_total_estimado
            else:
                custeio += item.valor_total_estimado
    plano.valor_planejado_investimento = investimento
    plano.valor_planejado_custeio = custeio
    plano.save(update_fields=['valor_planejado_investimento', 'valor_planejado_custeio'])


@receiver(post_save, sender=ItemPlanoAplicacao)
def _item_plano_aplicacao_post_save(sender, instance, **kwargs):
    _recalcular_totais(instance.meta_especifica_id)


@receiver(post_delete, sender=ItemPlanoAplicacao)
def _item_plano_aplicacao_post_delete(sender, instance, **kwargs):
    _recalcular_totais(instance.meta_especifica_id)


class ReuniaoConselhoGestor(BaseModel):
    """Ata de reunião do Conselho Gestor do FESP referente a um Plano de Aplicação."""
    TIPO_CHOICES = [('ordinaria', 'Ordinária'), ('extraordinaria', 'Extraordinária')]

    plano = models.ForeignKey(PlanoAplicacao, on_delete=models.CASCADE, related_name='reunioes')
    numero_ata = models.CharField(max_length=50, verbose_name='Número da ata')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='ordinaria', verbose_name='Tipo')
    data_reuniao = models.DateField(verbose_name='Data da reunião')
    quorum_atingido = models.BooleanField(default=True, verbose_name='Quórum atingido')
    deliberacao = models.TextField(blank=True, default='', verbose_name='Deliberação')
    presentes = models.ManyToManyField(
        ComposicaoConselhoGestor, blank=True, related_name='reunioes', verbose_name='Membros presentes',
    )

    class Meta(BaseModel.Meta):
        ordering = ['-data_reuniao']
        verbose_name = 'Reunião do Conselho Gestor'
        verbose_name_plural = 'Reuniões do Conselho Gestor'

    def __str__(self):
        return f'Ata {self.numero_ata} — {self.data_reuniao} ({self.get_tipo_display()})'


@receiver(pre_save, sender=PlanoAplicacao)
def gerar_numero_plano_aplicacao(sender, instance, **kwargs):
    if instance.numero:
        return
    sigla = instance.org_id.sigla if instance.org_id_id else 'ORG'
    prefixo = PlanoAplicacao.PREFIXO_NUMERO.get(instance.natureza, 'PLAN')
    seq = (
        PlanoAplicacao.objects
        .filter(org_id=instance.org_id, exercicio_fiscal=instance.exercicio_fiscal, natureza=instance.natureza)
        .exclude(pk=instance.pk)
        .count() + 1
    )
    instance.numero = f'{prefixo}-{sigla}-{seq:03d}/{instance.exercicio_fiscal}'
