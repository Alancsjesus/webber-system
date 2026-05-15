from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class PNCPImportacao(BaseModel):
    """
    Registro de uma importação de dados do PNCP.
    Vinculada a um MapaComparativoPrecos como destino dos preços importados.
    """
    STATUS_CHOICES = [
        ('pendente',     'Pendente'),
        ('em_andamento', 'Em andamento'),
        ('concluida',    'Concluída'),
        ('erro',         'Erro'),
    ]

    mapa = models.ForeignKey(
        'modulo_mapa_precos.MapaComparativoPrecos',
        on_delete=models.CASCADE,
        related_name='importacoes_pncp',
        verbose_name='Mapa de destino',
    )
    cnpj_orgao_referencia = models.CharField(
        max_length=18, blank=True, default='',
        verbose_name='CNPJ do órgão de referência',
        help_text='CNPJ do órgão cujas contratações serão consultadas. Deixe em branco para busca ampla.',
    )
    uf = models.CharField(
        max_length=2, default='BA',
        verbose_name='UF para busca',
    )
    termo_busca = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Termo de busca',
        help_text='Palavra-chave para filtrar o objeto das contratações',
    )
    periodo_inicio = models.DateField(verbose_name='Período — início')
    periodo_fim    = models.DateField(verbose_name='Período — fim')
    tipo_fonte     = models.CharField(
        max_length=10, default='II',
        verbose_name='Parâmetro de pesquisa',
        help_text='Parâmetro do Decreto 22.886/2024 que será atribuído aos preços importados',
    )

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    total_consultados  = models.IntegerField(default=0)
    total_importados   = models.IntegerField(default=0)
    erro_mensagem      = models.TextField(blank=True, default='')
    log               = models.JSONField(default=list)

    class Meta(BaseModel.Meta):
        ordering = ['-created_at']
        verbose_name = 'Importação PNCP'
        verbose_name_plural = 'Importações PNCP'

    def __str__(self):
        return f'Importação PNCP #{self.pk} — {self.status}'


class PNCPRegistro(models.Model):
    """
    Um registro individual retornado pela API do PNCP.
    Armazenado para permitir seleção antes da importação definitiva ao Mapa.
    """
    importacao     = models.ForeignKey(PNCPImportacao, on_delete=models.CASCADE, related_name='registros')
    numero_pncp    = models.CharField(max_length=150, verbose_name='Número/ID PNCP')
    objeto         = models.TextField(verbose_name='Objeto da contratação')
    valor_global   = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quantidade     = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    unidade_medida = models.CharField(max_length=30, blank=True, default='')
    orgao_nome     = models.CharField(max_length=255, blank=True, default='')
    orgao_cnpj     = models.CharField(max_length=18,  blank=True, default='')
    uf             = models.CharField(max_length=2,   blank=True, default='')
    data_referencia = models.DateField(null=True, blank=True)
    numero_certame  = models.CharField(max_length=100, blank=True, default='')
    modalidade      = models.CharField(max_length=100, blank=True, default='')
    tipo_registro   = models.CharField(
        max_length=15, default='contrato',
        choices=[('contrato', 'Contrato'), ('ata', 'Ata de Registro de Preços')],
    )
    # FK para o PrecoColetado criado após importação
    preco_coletado = models.OneToOneField(
        'modulo_mapa_precos.PrecoColetado',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pncp_registro',
    )
    importado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-data_referencia']
        verbose_name = 'Registro PNCP'
        verbose_name_plural = 'Registros PNCP'

    def __str__(self):
        return f'{self.numero_pncp} — {self.objeto[:50]}'
