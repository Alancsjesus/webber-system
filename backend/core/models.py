from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Orgao(models.Model):
    """Órgão ou secretaria — suporta hierarquia pai/filho."""
    nome   = models.CharField(max_length=255)
    sigla  = models.CharField(max_length=20, unique=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='orgaos_filhos',
    )
    ativa     = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Órgão'
        verbose_name_plural = 'Órgãos'

    def __str__(self):
        return self.sigla


# Backward compatibility alias — mantém imports existentes funcionando
Organization = Orgao


class UnidadeOrganizacional(models.Model):
    """Unidade funcional dentro de um órgão: demandante, licitante, contratante ou planejamento."""
    TIPO_CHOICES = [
        ('demandante',   'Unidade Demandante'),
        ('licitante',    'Unidade Licitante'),
        ('contratante',  'Unidade Contratante'),
        ('planejamento', 'Unidade de Planejamento'),
    ]
    orgao = models.ForeignKey(Orgao, on_delete=models.CASCADE, related_name='unidades')
    nome  = models.CharField(max_length=200)
    sigla = models.CharField(max_length=30)
    tipo  = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ['orgao', 'sigla']
        unique_together = [('orgao', 'sigla', 'tipo')]
        verbose_name = 'Unidade Organizacional'
        verbose_name_plural = 'Unidades Organizacionais'

    def __str__(self):
        return f'{self.orgao.sigla}/{self.sigla}'


class UserProfile(models.Model):
    """Perfil de usuário com papel, órgão e unidade organizacional."""
    PAPEL_CHOICES = [
        ('admin',               'Administrador'),
        ('analista',            'Analista de Contratações'),
        ('gestor_planejamento', 'Gestor de Planejamento'),
        ('gestor_contrato',     'Gestor de Contrato'),
        ('fiscal_contrato',     'Fiscal de Contrato'),
        ('ordenador',           'Ordenador de Despesas'),
        ('solicitante',         'Solicitante'),
        ('responsavel_tecnico', 'Responsável Técnico'),
        ('auditor',             'Auditor / Controle Interno'),
    ]

    user    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    org_id  = models.ForeignKey(Orgao, on_delete=models.SET_NULL, null=True, blank=True)
    unidade = models.ForeignKey(
        UnidadeOrganizacional, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='usuarios',
    )
    papel   = models.CharField(max_length=30, choices=PAPEL_CHOICES, default='solicitante')

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuário'

    def __str__(self):
        return f"{self.user.username} ({self.papel})"


@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class BaseModel(models.Model):
    """Abstract base model with multi-tenant support."""
    org_id     = models.ForeignKey(Orgao, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['org_id', '-created_at']),
        ]


class ParametroSistema(models.Model):
    """Parâmetros de configuração globais do sistema — editáveis por admin/licitante/planejamento."""
    chave          = models.CharField(max_length=100, unique=True)
    valor          = models.CharField(max_length=500)
    descricao      = models.CharField(max_length=500, blank=True)
    norma_base     = models.CharField(
        max_length=500, blank=True, default='',
        verbose_name='Norma / Legislação base',
        help_text='Ex: Decreto Estadual 22.886/2024, Art. 5º, II',
    )
    data_vigencia  = models.DateField(
        null=True, blank=True,
        verbose_name='Data de vigência da norma',
    )
    atualizado_em  = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['chave']
        verbose_name = 'Parâmetro do Sistema'
        verbose_name_plural = 'Parâmetros do Sistema'

    def __str__(self):
        return f'{self.chave} = {self.valor}'

    @classmethod
    def get(cls, chave, default=None):
        try:
            return cls.objects.get(chave=chave).valor
        except cls.DoesNotExist:
            return default


class AreaAtuacao(models.Model):
    """
    Áreas de atuação configuráveis — substituem o AREA_CHOICES hardcoded.
    Global, não org-scoped (todas as orgs compartilham as mesmas áreas).
    """
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    nome   = models.CharField(max_length=100, verbose_name='Nome')
    ativa  = models.BooleanField(default=True, verbose_name='Ativa')

    class Meta:
        ordering = ['nome']
        verbose_name = 'Área de Atuação'
        verbose_name_plural = 'Áreas de Atuação'

    def __str__(self):
        return f'{self.codigo} — {self.nome}'


class CategoriaItem(models.Model):
    """
    Árvore hierárquica de categorias para itens do catálogo.
    Exemplo: FROTA > VEÍCULOS LEVES > PICKUP
    Nós raiz têm pai=None. Profundidade livre, tipicamente 2-3 níveis.
    Global (não org-scoped), gerenciado pelo admin.
    """
    nome   = models.CharField(max_length=150, verbose_name='Nome da categoria')
    codigo = models.CharField(max_length=30, blank=True, default='', verbose_name='Código (opcional)')
    pai    = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='filhos',
        verbose_name='Categoria pai',
    )

    class Meta:
        ordering = ['nome']
        verbose_name = 'Categoria de Item'
        verbose_name_plural = 'Categorias de Itens'

    def __str__(self):
        return self.caminho_completo

    @property
    def caminho_completo(self) -> str:
        partes = []
        atual = self
        while atual:
            partes.append(atual.nome)
            atual = atual.pai
        return ' > '.join(reversed(partes))

    @property
    def nivel(self) -> int:
        n, atual = 0, self
        while atual.pai_id:
            n += 1
            atual = atual.pai
        return n


class ItemCatalogo(models.Model):
    """
    Catálogo de itens com código interno WEBBER e código SIMPAS.
    A família é derivada automaticamente dos dois primeiros segmentos do SIMPAS.
    Formato SIMPAS: 42.40.20.00016900-5  →  família: 42.40
    """
    CLASSIFICACAO_CHOICES = [
        ('consumo',    'Material de Consumo'),
        ('permanente', 'Material Permanente'),
        ('servico',    'Serviço'),
        ('',           'Não classificado'),
    ]

    codigo_interno = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Código interno')
    codigo_simpas  = models.CharField(max_length=40, blank=True, default='', verbose_name='Código SIMPAS')
    familia        = models.CharField(max_length=15, blank=True, default='', verbose_name='Família SIMPAS', db_index=True)
    categoria      = models.ForeignKey(
        CategoriaItem, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='itens',
        verbose_name='Categoria',
    )
    nome           = models.CharField(max_length=300, verbose_name='Descrição do item')
    descricao      = models.TextField(blank=True, default='', verbose_name='Especificação complementar')
    unidade_medida = models.CharField(max_length=20, verbose_name='Unidade de medida')
    ativo          = models.BooleanField(default=True, verbose_name='Ativo')

    # Campos originados do SIMPAS
    item_sustentavel      = models.BooleanField(default=False, verbose_name='Item sustentável', db_index=True)
    item_luxo             = models.BooleanField(default=False, verbose_name='Item de luxo', db_index=True)
    classificacao_tipo    = models.CharField(
        max_length=15, blank=True, default='',
        choices=CLASSIFICACAO_CHOICES,
        verbose_name='Classificação', db_index=True,
    )
    valor_referencia      = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name='Valor de referência SIMPAS (R$)',
    )
    data_referencia       = models.DateField(
        null=True, blank=True,
        verbose_name='Data do valor de referência',
    )
    num_licitacao_ref     = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='Nº licitação de referência',
    )

    class Meta:
        ordering = ['familia', 'nome']
        verbose_name = 'Item do Catálogo'
        verbose_name_plural = 'Itens do Catálogo'

    def __str__(self):
        return f'{self.codigo_interno} — {self.nome}'

    @staticmethod
    def extrair_familia(codigo_simpas: str) -> str:
        """Extrai a família dos dois primeiros segmentos do código SIMPAS."""
        if not codigo_simpas:
            return ''
        partes = codigo_simpas.strip().split('.')
        if len(partes) >= 2:
            return f'{partes[0]}.{partes[1]}'
        return ''

    def save(self, *args, **kwargs):
        # Deriva família do SIMPAS
        if self.codigo_simpas:
            self.familia = self.extrair_familia(self.codigo_simpas)
        # Gera código interno sequencial
        if not self.codigo_interno:
            ultimo = ItemCatalogo.objects.count() + 1
            self.codigo_interno = f'WBR-{ultimo:05d}'
        super().save(*args, **kwargs)


class SecaoArtefato(models.Model):
    """
    Seções configuráveis dos artefatos documentais (DFD, ETP, TR).
    Permite ao admin personalizar estrutura, ordem e aplicabilidade por modalidade.
    Global — não org-scoped (compartilhado entre todos os órgãos).
    """
    TIPO_CHOICES = [
        ('DFD', 'DFD — Documento de Formalização da Demanda'),
        ('ETP', 'ETP — Estudo Técnico Preliminar'),
        ('TR',  'TR — Minuta do Termo de Referência'),
    ]
    MODALIDADE_CHOICES = [
        ('todas',              'Todas as modalidades'),
        ('licitacao',          'Licitação'),
        ('dispensa_valor',     'Dispensa por Valor'),
        ('dispensa_emergencia','Dispensa por Emergência'),
        ('inexigibilidade',    'Inexigibilidade'),
        ('arp_saque',          'Saque de ARP'),
    ]

    tipo               = models.CharField(max_length=3, choices=TIPO_CHOICES, verbose_name='Tipo de artefato')
    codigo             = models.CharField(max_length=60, verbose_name='Código (chave técnica)')
    titulo             = models.CharField(max_length=200, verbose_name='Título da seção')
    descricao          = models.TextField(blank=True, default='', verbose_name='Orientação de preenchimento')
    ordem              = models.PositiveIntegerField(default=0, verbose_name='Ordem de exibição')
    ativo              = models.BooleanField(default=True, verbose_name='Ativo')
    obrigatorio        = models.BooleanField(default=False, verbose_name='Preenchimento obrigatório')
    aplica_modalidades = models.JSONField(default=list, verbose_name='Aplica para modalidades',
                                          help_text='Lista vazia = todas as modalidades')
    aplica_tipo_objeto = models.JSONField(default=list, verbose_name='Aplica para tipo de objeto',
                                          help_text='Ex: ["bens","hibrido"]. Lista vazia = todos os tipos')

    class Meta:
        unique_together = [('tipo', 'codigo')]
        ordering        = ['tipo', 'ordem']
        verbose_name = 'Seção de Artefato'
        verbose_name_plural = 'Seções de Artefatos'

    def __str__(self):
        return f'[{self.tipo}] {self.titulo}'


class AuditLog(models.Model):
    """Trilha de auditoria imutável — registra criação, exclusão, alterações de valor e SEI, logins."""
    ACTION_CHOICES = [
        ('created',       'Criado'),
        ('deleted',       'Excluído'),
        ('value_changed', 'Valor alterado'),
        ('sei_changed',   'Nº SEI vinculado/alterado'),
        ('login',         'Login no sistema'),
        ('updated',       'Atualizado'),
    ]

    org_id       = models.ForeignKey(Orgao, on_delete=models.CASCADE, null=True, blank=True)
    modelo       = models.CharField(max_length=100, db_index=True)
    objeto_id    = models.IntegerField(null=True, blank=True)
    objeto_repr  = models.CharField(max_length=300, blank=True, default='')
    acao         = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    descricao    = models.CharField(max_length=500, blank=True, default='')
    usuario      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    antes_json   = models.JSONField(null=True, blank=True)
    depois_json  = models.JSONField(null=True, blank=True)
    criado_em    = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['org_id', '-criado_em']),
            models.Index(fields=['modelo', 'objeto_id']),
        ]
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'

    def __str__(self):
        return f"{self.modelo} - {self.acao} - {self.criado_em}"


# ── Notificações Internas ──────────────────────────────────────────────────────

class NotificacaoInterna(models.Model):
    """
    Notificação interna para um usuário do sistema.
    Criada automaticamente via signals quando documentos mudam de status.
    """
    TIPO_CHOICES = [
        ('aprovacao',          'Documento aprovado'),
        ('devolucao',          'Documento devolvido'),
        ('pendente_aprovacao', 'Aguardando sua aprovação'),
        ('alerta',             'Alerta do sistema'),
    ]

    destinatario  = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='notificacoes', verbose_name='Destinatário',
    )
    tipo          = models.CharField(max_length=25, choices=TIPO_CHOICES)
    titulo        = models.CharField(max_length=200)
    mensagem      = models.TextField(blank=True, default='')
    url_destino   = models.CharField(max_length=200, blank=True, default='',
                                     help_text='Rota frontend para navegação direta')
    lida          = models.BooleanField(default=False)
    criado_em     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Notificação Interna'
        verbose_name_plural = 'Notificações Internas'
        indexes = [
            models.Index(fields=['destinatario', 'lida', '-criado_em']),
        ]

    def __str__(self):
        return f'[{self.tipo}] {self.titulo} → {self.destinatario.username}'
