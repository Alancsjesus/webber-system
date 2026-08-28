from django.contrib.auth.models import User
from django.db import models
from core.models import BaseModel


class Ata(BaseModel):
    """
    Ata de Registro de Preços (Lei 14.133/2021, Art. 82-86).

    tipo_origem reflete os 3 papéis possíveis deste órgão em relação à ata
    (Art. 82-86, especialmente Art. 86 §1º-4º sobre carona/adesão):
      - gerenciador:  este órgão conduziu a licitação e gerencia a ata.
      - participante: aderiu desde a formação — consta do edital/pesquisa
        de preços original, com cota própria dentro do próprio instrumento.
      - carona:       adere depois de a ata já estar vigente, sem ter
        participado da formação — sujeita aos limites de adesão do Art. 86.
    "Gerenciador" é sempre deste órgão; "participante" e "carona" são
    sempre de uma ata gerenciada por outro órgão/ente.

    Escopo v1: cadastro + confronto de itens pendentes de contratação contra
    itens de atas vigentes. Não gera Contrato automaticamente — o Saque de
    ARP continua sendo registrado manualmente em Contrato.tipo_origem
    ('saque_arp'/'adesao_arp'), sem vínculo de FK ainda. O ato formal de
    adesão (solicitação + anuência do gerenciador) também não é rastreado
    ainda — só o cadastro da própria ata, com seus itens e saldo.
    """
    TIPO_ORIGEM_CHOICES = [
        ('gerenciador',  'Gerenciador'),
        ('participante', 'Participante'),
        ('carona',       'Carona (não-participante)'),
    ]
    TIPOS_ORIGEM_EXTERNA = ('participante', 'carona')
    STATUS_CHOICES = [
        ('rascunho',  'Rascunho'),
        ('vigente',   'Vigente'),
        ('encerrada', 'Encerrada'),
        ('cancelada', 'Cancelada'),
    ]
    TRANSICOES_PERMITIDAS = {
        'rascunho':  ['vigente', 'cancelada'],
        'vigente':   ['encerrada', 'cancelada'],
        'encerrada': [],
        'cancelada': [],
    }

    tipo_origem = models.CharField(
        max_length=15, choices=TIPO_ORIGEM_CHOICES, verbose_name='Tipo de origem',
    )
    numero_ata = models.CharField(max_length=50, verbose_name='Número da ata')
    procedimento = models.ForeignKey(
        'modulo_licitacao.Procedimento', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='atas',
        verbose_name='Procedimento de origem',
        help_text='Preenchido apenas quando tipo_origem="gerenciador".',
    )

    # Só fazem sentido quando tipo_origem é 'participante' ou 'carona' —
    # ata gerenciada por outro órgão/ente (mesmo estado ou outro ente federativo).
    numero_pncp = models.CharField(max_length=50, blank=True, default='', verbose_name='Número no PNCP')
    orgao_gerenciador_nome = models.CharField(max_length=255, blank=True, default='', verbose_name='Órgão gerenciador')
    orgao_gerenciador_cnpj = models.CharField(max_length=18, blank=True, default='', verbose_name='CNPJ do órgão gerenciador')
    orgao_gerenciador_uf = models.CharField(max_length=2, blank=True, default='', verbose_name='UF do órgão gerenciador')
    instrumento_preparatorio = models.FileField(
        upload_to='arp/instrumentos_preparatorios/', null=True, blank=True,
        verbose_name='Instrumento preparatório',
        help_text='ETP ou documento equivalente que fundamentou a adesão — exigido para ata participante/carona (Nota Recomendatória Atricon-IRB-CNPTC-AUDICON nº 01/2025).',
    )

    objeto = models.TextField(verbose_name='Objeto')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='rascunho')
    data_assinatura = models.DateField(null=True, blank=True, verbose_name='Data de assinatura')
    data_vigencia_inicio = models.DateField(null=True, blank=True, verbose_name='Início da vigência')
    data_vigencia_fim = models.DateField(null=True, blank=True, verbose_name='Fim da vigência')
    observacoes = models.TextField(blank=True, default='')

    class Meta(BaseModel.Meta):
        ordering = ['-data_assinatura', '-created_at']
        verbose_name = 'Ata de Registro de Preços'
        verbose_name_plural = 'Atas de Registro de Preços'

    def __str__(self):
        return f'Ata {self.numero_ata} ({self.get_tipo_origem_display()})'


class ItemAta(models.Model):
    """
    Item registrado numa Ata — quantidade e valor unitário registrados, com
    saldo derivado de quantidade_registrada - quantidade_consumida.
    quantidade_consumida não é decrementada nesta entrega (nenhum fluxo de
    Saque ainda existe); o campo já está preparado para isso.
    """
    ata = models.ForeignKey(Ata, on_delete=models.CASCADE, related_name='itens')
    item_catalogo = models.ForeignKey(
        'core.ItemCatalogo', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='itens_ata',
        verbose_name='Item do catálogo',
    )
    objeto = models.CharField(max_length=255, verbose_name='Objeto / Descrição')
    unidade_medida = models.CharField(max_length=20, verbose_name='Unidade de medida')
    fornecedor = models.ForeignKey(
        'modulo_fornecedor.Fornecedor', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='itens_ata',
    )
    quantidade_registrada = models.DecimalField(max_digits=15, decimal_places=4, verbose_name='Quantidade registrada')
    valor_unitario_registrado = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Valor unitário registrado (R$)')
    quantidade_consumida = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name='Quantidade já consumida')
    observacoes = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Item da Ata'
        verbose_name_plural = 'Itens da Ata'

    def __str__(self):
        return f'{self.objeto} ({self.ata.numero_ata})'

    @property
    def saldo_disponivel(self):
        return self.quantidade_registrada - self.quantidade_consumida


class HistoricoAta(models.Model):
    """Registro imutável de cada transição de status da Ata."""
    ata = models.ForeignKey(Ata, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=10, blank=True, default='')
    status_novo = models.CharField(max_length=10)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    motivo = models.TextField(blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'Ata {self.ata_id}: {self.status_anterior} → {self.status_novo}'
