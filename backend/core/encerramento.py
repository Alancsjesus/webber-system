"""
Encerramento sem prosseguimento de peças de instrução (ETP, TR, Mapa de Preços).

Uma peça que não vai virar contratação — demanda desistida, necessidade
superada, sem orçamento, ou aproveitada em outra contratação — precisa sair do
fluxo com registro do motivo. Senão ela fica "em rascunho/devolvida" para
sempre e infla o tempo de construção das peças e o tempo parado da demanda.

Não há coluna própria: o encerramento é uma transição de status como as demais,
e a data, o motivo e a categoria ficam no histórico da peça (criado_em, motivo,
categoria_motivo) — é de lá que os indicadores de tempo leem.
"""

STATUS_ENCERRADO = 'Encerrado'

MOTIVOS_ENCERRAMENTO = [
    ('enc_desistencia', 'Demanda desistida pela unidade demandante'),
    ('enc_perda_objeto', 'Perda de objeto — necessidade superada'),
    ('enc_sem_orcamento', 'Sem disponibilidade orçamentária no exercício'),
    ('enc_substituida', 'Substituída por outra contratação'),
    ('enc_aproveitada', 'Aproveitada em outra contratação (adesão a ARP, outro processo)'),
    ('enc_outro', 'Outro'),
]
_ROTULOS = dict(MOTIVOS_ENCERRAMENTO)

# Procedimento nesses status já não usa a peça — pode encerrar.
_PROC_INATIVOS = ('Revogado', 'Anulado', 'Deserto', 'Fracassado')
# Peças sucessoras nesses status não prendem a antecessora.
_PECA_INATIVA = ('Cancelado', STATUS_ENCERRADO)


def validar_pedido(dados):
    """(categoria, motivo_completo) a partir do corpo da requisição, ou ValueError."""
    categoria = (dados.get('categoria') or '').strip()
    motivo = (dados.get('motivo') or '').strip()
    referencia = (dados.get('referencia') or '').strip()
    if categoria not in _ROTULOS:
        raise ValueError('Informe a categoria do encerramento.')
    if not motivo:
        raise ValueError('Descreva o motivo do encerramento.')
    if categoria in ('enc_aproveitada', 'enc_substituida') and not referencia:
        raise ValueError('Informe o processo SEI ou a contratação em que a peça foi aproveitada/substituída.')
    texto = f'{_ROTULOS[categoria]}: {motivo}'
    if referencia:
        texto += f' (referência: {referencia})'
    return categoria, texto


def impedimento_etp(etp):
    tr = getattr(etp, 'tr', None)
    if tr is not None and tr.status not in _PECA_INATIVA:
        return f'O ETP é base do TR {tr.numero_sei} ({tr.status}) — encerre o TR antes.'
    return None


def impedimento_tr(tr):
    ativos = [p for p in tr.procedimentos.all() if p.status not in _PROC_INATIVOS]
    if ativos:
        p = ativos[0]
        return f'O TR está em uso no procedimento {p.numero} ({p.status}).'
    return None


def impedimento_mapa(mapa):
    if mapa.dfd_id is None:
        return None
    from modulo_licitacao.models import Procedimento
    ativo = Procedimento.objects.filter(dfd_id=mapa.dfd_id).exclude(status__in=_PROC_INATIVOS).first()
    if ativo:
        return f'O Mapa fundamenta o procedimento {ativo.numero} ({ativo.status}).'
    return None

# Quem pode encerrar: quem elabora (solicitante/responsável técnico), analisa ou planeja.
PAPEIS_ENCERRAR = ('admin', 'analista', 'gestor_planejamento', 'solicitante', 'responsavel_tecnico')
