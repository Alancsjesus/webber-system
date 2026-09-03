from django.contrib.auth.models import User
from django.db import models

from core.models import BaseModel


class ProcessoTramitacao(BaseModel):
    """
    Painel gerencial de tramitação: "em qual setor/mesa está cada processo
    SEI agora". Independente do fluxo estruturado do Webber (DFD/ETP/TR/
    Procedimento/Contrato) — existe mesmo antes de haver DFD (fase inicial
    "demandante"), com vínculo opcional ao DFD quando ele passar a existir.

    setor_atual é a lista fixa usada para agrupar o painel/relatório;
    fase_atual é texto curto livre (o frontend sugere valores comuns via
    datalist, mas não é um enum fechado no backend — a rotina real observada
    inclui frases como "Retornou para demandante - ajustes").
    """
    SETOR_CHOICES = [
        ('casa_civil', 'Casa Civil'),
        ('ccc',        'CCC'),
        ('cfcr',       'CFCR'),
        ('clic',       'CLIC'),
        ('demandante',  'Demandante'),
        ('pge',        'PGE'),
        ('saeb_coe',   'SAEB/COE'),
        ('saeb_dm',    'SAEB/DM'),
        ('sefaz',      'SEFAZ'),
        ('ssp_gab',    'SSP/GAB'),
    ]

    numero_sei = models.CharField(max_length=50, verbose_name='Processo SEI')
    objeto = models.TextField(verbose_name='Objeto')
    fontes_recurso = models.ManyToManyField(
        'modulo_orcamento.FonteRecurso', blank=True, related_name='processos_tramitacao',
        verbose_name='Fontes de recurso',
    )
    setor_atual = models.CharField(max_length=20, choices=SETOR_CHOICES, verbose_name='Setor atual')
    fase_atual = models.CharField(max_length=120, blank=True, default='', verbose_name='Fase')
    data_entrada_fase = models.DateField(verbose_name='Data de entrada na fase')
    dfd = models.ForeignKey(
        'modulo_demanda.DFD', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tramitacoes', verbose_name='DFD vinculado',
        help_text='Preenchido quando o DFD correspondente já existir no sistema.',
    )
    ativo = models.BooleanField(
        default=True, verbose_name='Ativo',
        help_text='Desmarcar para tirar da visão gerencial sem apagar o histórico (processo concluído/arquivado).',
    )
    observacoes = models.TextField(blank=True, default='')

    class Meta(BaseModel.Meta):
        ordering = ['setor_atual', '-data_entrada_fase']
        verbose_name = 'Processo em Tramitação'
        verbose_name_plural = 'Processos em Tramitação'

    def __str__(self):
        return f'{self.numero_sei} ({self.get_setor_atual_display()})'


class HistoricoTramitacaoProcesso(models.Model):
    """Registro imutável de cada mudança de setor/fase de um ProcessoTramitacao."""
    processo = models.ForeignKey(ProcessoTramitacao, on_delete=models.CASCADE, related_name='historico')
    setor_anterior = models.CharField(max_length=20, blank=True, default='')
    fase_anterior = models.CharField(max_length=120, blank=True, default='')
    setor_novo = models.CharField(max_length=20)
    fase_nova = models.CharField(max_length=120, blank=True, default='')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    motivo = models.TextField(blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Histórico de Tramitação'
        verbose_name_plural = 'Históricos de Tramitação'

    def __str__(self):
        return f'Processo {self.processo_id}: {self.setor_anterior} → {self.setor_novo}'
