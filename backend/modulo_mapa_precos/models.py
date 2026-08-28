"""
Mapa Comparativo de Preços — Decreto Estadual 22.886/2024.
Implementa os 5 parâmetros de pesquisa, validação de outliers (±30%),
consulta ao histórico WEBBER e escolha de método estatístico.
"""
import statistics
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


# ── Choices ────────────────────────────────────────────────────────────────────

TIPO_FONTE_CHOICES = [
    ('I',    'Parâmetro I — SIMPAS / Comprasnet.BA / banco de preços em saúde'),
    ('II',   'Parâmetro II — Contratações similares (Administração Pública)'),
    ('III',  'Parâmetro III — Mídia especializada / sítios eletrônicos'),
    ('IV',   'Parâmetro IV — Base de notas fiscais eletrônicas'),
    ('V',    'Parâmetro V — Pesquisa direta com fornecedores (≥ 3 fornecedores)'),
    ('HIST', 'Histórico WEBBER — Aquisições anteriores do sistema'),
]
# IV = NF-e | V = Pesquisa direta — alinhado ao Decreto Estadual 22.886/2024, Art. 5º

METODO_CALCULO_CHOICES = [
    ('media',        'Média aritmética dos preços válidos'),
    ('mediana',      'Mediana de todos os preços coletados'),
    ('menor_valido', 'Menor preço válido'),
]

STATUS_MAPA_CHOICES = [
    ('Rascunho',   'Rascunho'),
    ('Submetido',  'Submetido para aprovação'),
    ('Em Análise', 'Em análise pela Unidade Licitante'),
    ('Aprovado',   'Aprovado'),
    ('Devolvido',  'Devolvido para correção'),
    ('Cancelado',  'Cancelado'),
]

TRANSICOES_MAPA = {
    'Rascunho':   ['Submetido', 'Cancelado'],
    'Submetido':  ['Em Análise', 'Rascunho', 'Cancelado'],
    'Em Análise': ['Aprovado', 'Devolvido', 'Cancelado'],
    'Devolvido':  ['Submetido', 'Cancelado'],
    'Aprovado':   ['Cancelado'],
    'Cancelado':  [],
}

# Mapeamento tipo_fonte → chave do parâmetro de prazo (meses)
PRAZO_PARAM_KEYS = {
    'I':    'prazo_validade_parametro_i_meses',
    'II':   'prazo_validade_parametro_ii_meses',
    'III':  'prazo_validade_parametro_iii_meses',
    'IV':   'prazo_validade_parametro_iv_meses',
    'V':    'prazo_validade_parametro_v_meses',
    'HIST': None,  # Histórico interno — sem prazo de vencimento
}

MOTIVO_EXCLUSAO_CHOICES = [
    ('excessivo',   'Valor excessivamente elevado (acima de +30% da mediana)'),
    ('inexequivel', 'Valor inexequível (abaixo de -30% da mediana)'),
    ('inconsistente', 'Valor inconsistente (especificação diferente)'),
    ('desatualizado', 'Cotação desatualizada (prazo vencido)'),
    ('manual',      'Excluído manualmente pelo responsável'),
]


class MapaComparativoPrecos(BaseModel):
    """
    Mapa Comparativo de Preços conforme Decreto Estadual 22.886/2024.
    Vinculado a um DFD ou criado de forma autônoma para subsidiar pesquisa.
    """
    dfd = models.ForeignKey(
        'modulo_demanda.DFD',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mapas_preco',
        verbose_name='DFD vinculado',
    )
    objeto = models.TextField(verbose_name='Objeto da pesquisa de preços')
    exercicio_fiscal = models.IntegerField(verbose_name='Exercício fiscal')
    status = models.CharField(
        max_length=15, choices=STATUS_MAPA_CHOICES,
        default='Rascunho', verbose_name='Status',
    )
    metodo_calculo = models.CharField(
        max_length=15, choices=METODO_CALCULO_CHOICES,
        default='media', verbose_name='Método de cálculo',
    )
    valor_estimado_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='Valor estimado total (R$)',
    )
    responsavel = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mapas_responsavel',
        verbose_name='Responsável pela pesquisa',
    )
    aprovador = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mapas_aprovados',
        verbose_name='Aprovador (Unidade Licitante)',
    )
    data_aprovacao = models.DateField(null=True, blank=True, verbose_name='Data de aprovação')
    motivo_devolucao = models.TextField(
        blank=True, default='', verbose_name='Motivo da devolução',
    )
    justificativa_metodologia = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa da metodologia adotada',
        help_text='Art. 3º, inc. VI — Descrever a metodologia e por que foi adotada.',
    )
    parametros_combinados_justificativa = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa pela não combinação de parâmetros',
        help_text='Art. 5º, §1º — Preencher quando não foi possível combinar múltiplos parâmetros.',
    )
    observacoes = models.TextField(blank=True, default='', verbose_name='Observações')

    class Meta(BaseModel.Meta):
        ordering = ['-exercicio_fiscal', '-created_at']
        verbose_name = 'Mapa Comparativo de Preços'
        verbose_name_plural = 'Mapas Comparativos de Preços'

    def __str__(self):
        return f'Mapa {self.pk} — {self.objeto[:50]} ({self.exercicio_fiscal})'

    def validar_prazo_cotacoes(self):
        """
        Verifica e invalida automaticamente preços cuja data_referencia
        está fora do prazo definido nos Parâmetros do Sistema.
        Retorna lista de preços invalidados.
        """
        from core.models import ParametroSistema
        from datetime import date, timedelta

        invalidados = []
        hoje = date.today()

        for item in self.itens.all():
            for preco in item.precos.all():
                chave = PRAZO_PARAM_KEYS.get(preco.fonte.tipo)
                if not chave:
                    continue  # HIST não tem prazo
                prazo_meses = int(ParametroSistema.get(chave, 12))
                limite = hoje - timedelta(days=prazo_meses * 30)
                if preco.data_referencia < limite:
                    if preco.valido:
                        preco.valido = False
                        preco.motivo_exclusao = 'desatualizado'
                        preco.sugestao_exclusao = (
                            f'Data {preco.data_referencia.strftime("%d/%m/%Y")} '
                            f'excede o prazo de {prazo_meses} meses '
                            f'({preco.fonte.get_tipo_display()}) — '
                            f'parâmetro {chave}'
                        )
                        preco.save(update_fields=['valido', 'motivo_exclusao', 'sugestao_exclusao'])
                        invalidados.append(preco)
        return invalidados

    def recalcular_total(self):
        total = sum(
            item.valor_unitario_calculado * item.quantidade
            for item in self.itens.all()
            if item.valor_unitario_calculado
        )
        self.valor_estimado_total = total
        self.save(update_fields=['valor_estimado_total'])


MOTIVOS_DEVOLUCAO_MAPA = [
    ('fontes_inadequadas',       'Fontes de pesquisa inadequadas'),
    ('cotacoes_fora_prazo',      'Cotações fora do prazo'),
    ('qtd_insuficiente',         'Número insuficiente de cotações'),
    ('metodo_inadequado',        'Método de cálculo inadequado'),
    ('outro',                    'Outro'),
]


class HistoricoMapa(models.Model):
    """Trilha imutável de transições de status do Mapa."""
    mapa             = models.ForeignKey(MapaComparativoPrecos, on_delete=models.CASCADE, related_name='historico')
    status_anterior  = models.CharField(max_length=15)
    status_novo      = models.CharField(max_length=15)
    usuario          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo           = models.TextField(blank=True, null=True)
    categoria_motivo = models.CharField(max_length=40, choices=MOTIVOS_DEVOLUCAO_MAPA, blank=True, default='', verbose_name='Categoria do motivo')
    criado_em        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico do Mapa'


class FonteConsultada(models.Model):
    """
    Fonte de pesquisa utilizada no mapa (Art. 3º, inciso III, Decreto 22.886/2024).
    Cada fonte deve ser documentada com origem, referência e data de consulta.
    """
    mapa = models.ForeignKey(
        MapaComparativoPrecos, on_delete=models.CASCADE, related_name='fontes',
    )
    tipo = models.CharField(
        max_length=5, choices=TIPO_FONTE_CHOICES, verbose_name='Parâmetro (Art. 5º)',
    )
    descricao = models.CharField(
        max_length=255, verbose_name='Descrição da fonte',
        help_text='Ex: Portal SIMPAS, Pregão PMMG 001/2025, Portal PNCP',
    )
    referencia = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name='Referência documental',
        help_text='Número SEI, URL, número do certame, CNPJ do fornecedor',
    )
    data_consulta = models.DateField(verbose_name='Data da consulta')
    documento_sei = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name='Nº documento SEI (se houver)',
    )
    infrutífera = models.BooleanField(
        default=False,
        verbose_name='Consulta infrutífera',
        help_text='Marque se o fornecedor/fonte não respondeu ou não tinha o item',
    )
    justificativa_infrutífera = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa da consulta infrutífera',
    )
    # P1 — Parâmetro V: justificativa da escolha dos fornecedores
    justificativa_escolha_fornecedores = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa da escolha dos fornecedores',
        help_text='Art. 3º, inc. VII — Obrigatório para Parâmetro V (pesquisa direta). Indicar critério de seleção.',
    )

    class Meta:
        ordering = ['tipo', 'data_consulta']
        verbose_name = 'Fonte Consultada'
        verbose_name_plural = 'Fontes Consultadas'

    def __str__(self):
        return f'[{self.tipo}] {self.descricao}'


class ItemMapa(models.Model):
    """
    Item individual do mapa de preços.
    Cada item tem seu próprio conjunto de preços coletados e valor calculado.
    """
    mapa = models.ForeignKey(
        MapaComparativoPrecos, on_delete=models.CASCADE, related_name='itens',
    )
    ordem = models.PositiveSmallIntegerField(default=1, verbose_name='Ordem')
    descricao = models.CharField(max_length=500, verbose_name='Descrição do item')
    codigo_simpas = models.CharField(
        max_length=50, blank=True, default='', verbose_name='Código SIMPAS',
    )
    unidade_medida = models.CharField(max_length=20, verbose_name='Unidade de medida')
    quantidade = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name='Quantidade',
    )
    valor_unitario_calculado = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor unitário calculado (R$)',
    )
    valor_total_calculado = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor total calculado (R$)',
    )
    metodo_aplicado = models.CharField(
        max_length=15, choices=METODO_CALCULO_CHOICES, blank=True, default='',
        verbose_name='Método aplicado a este item',
    )
    qtd_precos_validos = models.PositiveSmallIntegerField(
        default=0, verbose_name='Nº de preços válidos utilizados',
    )
    justificativa_item = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa (quando < 3 preços ou método excepcional)',
    )
    alerta = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name='Alerta de validação',
    )

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Item do Mapa'
        verbose_name_plural = 'Itens do Mapa'

    def __str__(self):
        return f'{self.ordem}. {self.descricao[:60]}'

    def calcular(self, metodo=None):
        """
        Calcula o valor unitário do item conforme o método escolhido.
        Aplica detecção de outliers (±30% da mediana) antes de calcular.
        Retorna dict com resultado e diagnóstico.
        """
        metodo = metodo or self.mapa.metodo_calculo
        precos_qs = self.precos.filter(valido=True)
        valores = [float(p.valor_unitario) for p in precos_qs]

        if not valores:
            self.valor_unitario_calculado = None
            self.valor_total_calculado    = None
            self.qtd_precos_validos       = 0
            self.alerta = 'Nenhum preço válido coletado para este item.'
            self.save()
            return {'ok': False, 'alerta': self.alerta}

        # Detectar e sinalizar outliers (apenas para informação — usuário decide)
        alertas = []
        if len(valores) >= 2:
            mediana = statistics.median(valores)
            limite_sup = mediana * 1.30
            limite_inf = mediana * 0.70
            for p in precos_qs:
                v = float(p.valor_unitario)
                if v > limite_sup:
                    p.sugestao_exclusao = f'Acima de +30% da mediana (R$ {mediana:.2f})'
                    p.save(update_fields=['sugestao_exclusao'])
                elif v < limite_inf:
                    p.sugestao_exclusao = f'Abaixo de -30% da mediana (R$ {mediana:.2f})'
                    p.save(update_fields=['sugestao_exclusao'])
                else:
                    if p.sugestao_exclusao:
                        p.sugestao_exclusao = ''
                        p.save(update_fields=['sugestao_exclusao'])

        # Calcular com método escolhido
        if metodo == 'media':
            resultado = sum(valores) / len(valores)
        elif metodo == 'mediana':
            resultado = statistics.median(valores)
        else:  # menor_valido
            resultado = min(valores)

        # Alertas de conformidade com o Decreto
        if len(valores) < 3:
            alertas.append(
                f'Atenção: apenas {len(valores)} preço(s) válido(s). '
                'O Decreto 22.886/2024 recomenda mínimo de 3. Justificativa obrigatória (§5, Art. 8º).'
            )

        self.valor_unitario_calculado = Decimal(str(round(resultado, 2)))
        self.valor_total_calculado    = self.valor_unitario_calculado * self.quantidade
        self.qtd_precos_validos       = len(valores)
        self.metodo_aplicado          = metodo
        self.alerta                   = ' | '.join(alertas)
        self.save()
        return {'ok': True, 'valor': float(self.valor_unitario_calculado), 'alertas': alertas}


class PrecoColetado(models.Model):
    """
    Preço individual coletado para um item do mapa.
    Rastreia origem, validade e motivo de exclusão.
    Conforme Art. 3º, inciso IV, Decreto 22.886/2024.
    """
    item = models.ForeignKey(
        ItemMapa, on_delete=models.CASCADE, related_name='precos',
    )
    fonte = models.ForeignKey(
        FonteConsultada, on_delete=models.PROTECT, related_name='precos',
    )
    fornecedor = models.ForeignKey(
        'modulo_fornecedor.Fornecedor', null=True, blank=True,
        on_delete=models.PROTECT, related_name='precos_coletados',
        verbose_name='Fornecedor',
    )
    valor_unitario = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Valor unitário (R$)',
    )
    # Identificação da origem (orgão, empresa, certame) — mantido como histórico/fallback
    origem_orgao_empresa = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name='Órgão / Empresa de origem',
        help_text='Ex: PMMG, Pregão 001/2025, CNPJ 12.345.678/0001-00',
    )
    numero_certame = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='Número do certame / processo',
    )
    data_referencia = models.DateField(
        verbose_name='Data de referência do preço',
    )
    # Validação
    valido = models.BooleanField(
        default=True, verbose_name='Válido para cálculo',
    )
    motivo_exclusao = models.CharField(
        max_length=20, choices=MOTIVO_EXCLUSAO_CHOICES,
        blank=True, default='', verbose_name='Motivo da exclusão',
    )
    sugestao_exclusao = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name='Sugestão automática de exclusão (sistema)',
    )
    justificativa_exclusao = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa detalhada da exclusão',
    )
    observacao = models.TextField(
        blank=True, default='', verbose_name='Observação',
    )
    arquivo = models.FileField(
        upload_to='cotacoes/', null=True, blank=True,
        verbose_name='Documento comprobatório (PDF/imagem)',
    )

    class Meta:
        ordering = ['item', 'valor_unitario']
        verbose_name = 'Preço Coletado'
        verbose_name_plural = 'Preços Coletados'

    def __str__(self):
        status = '✓' if self.valido else '✗'
        return f'{status} R$ {self.valor_unitario} [{self.fonte.tipo}] {self.origem_orgao_empresa}'


class SolicitacaoCotacao(models.Model):
    """
    Disparo formal de solicitação de cotação — Parâmetro V. Um único disparo é
    enviado por e-mail a TODOS os fornecedores cadastrados numa família SIMPAS
    (ver FornecedorFamilia); as respostas individuais de cada fornecedor são
    registradas em RespostaCotacao, uma por fornecedor que respondeu.
    Decreto Estadual 22.886/2024, Art. 5º, IV c/c Art. 7º, IV.
    """
    mapa = models.ForeignKey(
        MapaComparativoPrecos, on_delete=models.CASCADE,
        related_name='solicitacoes_cotacao',
        verbose_name='Mapa de preços',
    )
    fonte = models.ForeignKey(
        FonteConsultada, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='solicitacoes',
        verbose_name='Fonte (Parâmetro V)',
        help_text='Vincular à FonteConsultada de tipo V criada para este disparo.',
    )

    familia_simpas = models.CharField(
        max_length=15, verbose_name='Família SIMPAS',
        help_text='Família de itens cujos fornecedores cadastrados (modulo_fornecedor.FornecedorFamilia) recebem o disparo.',
    )

    # Rastreamento do envio
    data_envio = models.DateField(verbose_name='Data de envio da solicitação')
    prazo_resposta = models.DateField(verbose_name='Prazo para resposta')
    encerrada = models.BooleanField(default=False, verbose_name='Disparo encerrado')

    # Documentação comprobatória — Art. 7º, IV
    email_enviado_pdf = models.FileField(
        upload_to='cotacoes/solicitacoes/', null=True, blank=True,
        verbose_name='PDF do e-mail enviado',
        help_text='Decreto 22.886/2024, Art. 7º, IV — obrigatório para comprovação.',
    )
    observacoes = models.TextField(blank=True, default='', verbose_name='Observações')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['mapa', '-data_envio']
        verbose_name = 'Solicitação de Cotação'
        verbose_name_plural = 'Solicitações de Cotação'

    def __str__(self):
        return f'{self.familia_simpas} — {self.data_envio}'


class RespostaCotacao(models.Model):
    """Resposta de um fornecedor específico a um disparo de SolicitacaoCotacao."""
    solicitacao = models.ForeignKey(
        SolicitacaoCotacao, on_delete=models.CASCADE,
        related_name='respostas', verbose_name='Solicitação de cotação',
    )
    fornecedor = models.ForeignKey(
        'modulo_fornecedor.Fornecedor', on_delete=models.PROTECT,
        related_name='respostas_cotacao', verbose_name='Fornecedor',
    )
    recusou = models.BooleanField(default=False, verbose_name='Fornecedor recusou')
    valor_respondido = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Valor unitário respondido (R$)',
    )
    resposta_pdf = models.FileField(
        upload_to='cotacoes/respostas/', null=True, blank=True,
        verbose_name='PDF da proposta/cotação recebida',
    )
    data_resposta = models.DateField(verbose_name='Data da resposta')
    escolhida = models.BooleanField(
        default=False, verbose_name='Usar como referência de preço',
    )
    justificativa_escolha = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa da escolha deste fornecedor',
        help_text='Art. 3º, inc. VII — Por que esta resposta foi adotada como referência.',
    )
    observacoes = models.TextField(blank=True, default='', verbose_name='Observações')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_resposta']
        verbose_name = 'Resposta de Cotação'
        verbose_name_plural = 'Respostas de Cotação'

    def __str__(self):
        return f'{self.fornecedor.nome_razao_social} — {self.solicitacao}'

    def __str__(self):
        return f'{self.fornecedor_nome} — {self.get_status_display()} ({self.data_envio})'
