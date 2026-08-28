from django.contrib.auth.models import User
from django.db import models


TIPO_PESSOA_CHOICES = [
    ('PJ', 'Pessoa Jurídica'),
    ('PF', 'Pessoa Física'),
]

PORTE_CHOICES = [
    ('MEI', 'MEI'),
    ('ME', 'Microempresa'),
    ('EPP', 'Empresa de Pequeno Porte'),
    ('DEMAIS', 'Demais'),
]


class Fornecedor(models.Model):
    """
    Cadastro de fornecedores (pessoa física ou jurídica). Global — não escopado
    por org_id, pois um CNPJ/CPF é uma entidade única que pode se relacionar
    com múltiplos órgãos. A chave de correlação é o campo `documento`.
    """
    tipo_pessoa = models.CharField(
        max_length=2, choices=TIPO_PESSOA_CHOICES, verbose_name='Tipo de pessoa',
    )
    documento = models.CharField(
        max_length=18, unique=True, verbose_name='CNPJ/CPF',
    )
    nome_razao_social = models.CharField(max_length=255, verbose_name='Nome / Razão social')
    nome_fantasia = models.CharField(max_length=255, blank=True, default='', verbose_name='Nome fantasia')
    porte_empresa = models.CharField(
        max_length=10, choices=PORTE_CHOICES, blank=True, default='', verbose_name='Porte',
    )
    email = models.EmailField(blank=True, default='')
    telefone = models.CharField(max_length=20, blank=True, default='')
    municipio = models.CharField(max_length=100, blank=True, default='')
    uf = models.CharField(max_length=2, blank=True, default='')
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name='fornecedores_criados',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome_razao_social']
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'

    def __str__(self):
        return f'{self.documento} — {self.nome_razao_social}'


class FornecedorFamilia(models.Model):
    """
    Vínculo de um fornecedor a uma família SIMPAS (código derivado dos dois
    primeiros segmentos de core.ItemCatalogo.codigo_simpas — não existe
    catálogo fixo de famílias, por isso é um CharField livre, não uma FK).
    Usado para disparar Solicitação de Cotação (Parâmetro V) a todos os
    fornecedores de uma família de uma vez.
    """
    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.CASCADE, related_name='familias',
    )
    familia_simpas = models.CharField(max_length=15, verbose_name='Família SIMPAS')

    class Meta:
        unique_together = ('fornecedor', 'familia_simpas')
        ordering = ['familia_simpas']
        verbose_name = 'Família do Fornecedor'
        verbose_name_plural = 'Famílias do Fornecedor'

    def __str__(self):
        return f'{self.fornecedor.nome_razao_social} — {self.familia_simpas}'
