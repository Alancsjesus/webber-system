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
    ('IV',   'Parâmetro IV — Pesquisa direta com fornecedores'),
    ('V',    'Parâmetro V — Base de notas fiscais eletrônicas'),
    ('HIST', 'Histórico WEBBER — Aquisições anteriores do sistema'),
]

METODO_CALCULO_CHOICES = [
    ('media',        'Média aritmética dos preços válidos'),
    ('mediana',      'Mediana de todos os preços coletados'),
    ('menor_valido', 'Menor preço válido'),
]

STATUS_MAPA_CHOICES = [
    ('Rascunho',   'Rascunho'),
    ('Finalizado', 'Finalizado'),
    ('Cancelado',  'Cancelado'),
]

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
    justificativa_metodologia = models.TextField(
        blank=True, default='',
        verbose_name='Justificativa da metodologia adotada',
    )
    observacoes = models.TextField(blank=True, default='', verbose_name='Observações')

    class Meta(BaseModel.Meta):
        ordering = ['-exercicio_fiscal', '-created_at']
        verbose_name = 'Mapa Comparativo de Preços'
        verbose_name_plural = 'Mapas Comparativos de Preços'

    def __str__(self):
        return f'Mapa {self.pk} — {self.objeto[:50]} ({self.exercicio_fiscal})'

    def recalcular_total(self):
        total = sum(
            item.valor_unitario_calculado * item.quantidade
            for item in self.itens.all()
            if item.valor_unitario_calculado
        )
        self.valor_estimado_total = total
        self.save(update_fields=['valor_estimado_total'])


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
    valor_unitario = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Valor unitário (R$)',
    )
    # Identificação da origem (orgão, empresa, certame)
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

    class Meta:
        ordering = ['item', 'valor_unitario']
        verbose_name = 'Preço Coletado'
        verbose_name_plural = 'Preços Coletados'

    def __str__(self):
        status = '✓' if self.valido else '✗'
        return f'{status} R$ {self.valor_unitario} [{self.fonte.tipo}] {self.origem_orgao_empresa}'
