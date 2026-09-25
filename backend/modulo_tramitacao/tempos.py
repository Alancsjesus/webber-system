"""
Tempos de instrução por ano — compara, por exemplo, se em 2025 a construção
das peças e a instrução dos procedimentos levava mais ou menos que em 2026.

Fonte: a data de criação de cada registro e o histórico de status (criado_em
de cada transição). Definições:

Peças (DFD, ETP, TR, Mapa de Preços) — tempo de construção:
    criação → primeira aprovação. O ano do corte é o da aprovação.
    Peças encerradas/canceladas/rejeitadas não entram na mediana de construção
    (não foram concluídas): são contadas à parte, com o tempo até o
    encerramento. Peças ainda em andamento aparecem só como estoque atual
    (quantidade e idade), porque ainda não têm duração.

Procedimento:
    fase preparatória — criação do DFD → aprovação do procedimento para
                        publicação/contratação (art. 17, I e art. 18);
    fase externa      — publicação do edital → homologação (licitações);
    ciclo total       — criação do DFD → assinatura do contrato.

Mediana (e não média) é o número principal: um único processo atípico não
desloca a comparação entre anos.
"""
from collections import defaultdict
from datetime import date, datetime
from statistics import median

APROVADO = {'DFD': 'Aprovada', 'ETP': 'Aprovado', 'TR': 'Aprovado', 'Mapa': 'Aprovado'}
ENCERRAMENTO = {'Encerrado', 'Cancelado', 'Rejeitada'}
DEVOLUCAO = {'Devolvido', 'Devolvida'}


def _dias(inicio, fim):
    if isinstance(inicio, datetime):
        inicio = inicio.date()
    if isinstance(fim, datetime):
        fim = fim.date()
    return max(0, (fim - inicio).days)


def _resumo(valores):
    if not valores:
        return {'n': 0, 'mediana': None, 'media': None}
    return {'n': len(valores), 'mediana': round(median(valores), 1), 'media': round(sum(valores) / len(valores), 1)}


def _metricas_peca(chave, rotulo, registros, hist_de):
    """registros: iteráveis com created_at/status; hist_de(r) → histórico em ordem cronológica."""
    concl = defaultdict(list)
    encerr = defaultdict(list)
    devol = defaultdict(list)
    andamento = []
    hoje = date.today()
    for r in registros:
        hist = hist_de(r)
        aprov = next((h.criado_em for h in hist if h.status_novo == APROVADO[chave]), None)
        if aprov is None and r.status == APROVADO[chave]:
            aprov = r.updated_at  # dado antigo aprovado sem trilha: melhor aproximação disponível
        if aprov:
            concl[aprov.year].append(_dias(r.created_at, aprov))
            devol[aprov.year].append(sum(1 for h in hist if h.status_novo in DEVOLUCAO and h.criado_em <= aprov))
            continue
        fim = next((h for h in hist if h.status_novo in ENCERRAMENTO), None)
        if fim or r.status in ENCERRAMENTO:
            quando = fim.criado_em if fim else r.updated_at
            encerr[quando.year].append(_dias(r.created_at, quando))
        elif r.status not in ('Dispensado',):
            andamento.append(_dias(r.created_at, hoje))
    anos = set(concl) | set(encerr)
    return {
        'chave': chave, 'rotulo': rotulo, 'grupo': 'peca',
        'definicao': 'Da criação até a primeira aprovação.',
        'por_ano': {
            ano: {
                **_resumo(concl[ano]),
                'devolucoes_media': round(sum(devol[ano]) / len(devol[ano]), 1) if devol[ano] else None,
                'encerradas': len(encerr[ano]),
                'encerradas_mediana': round(median(encerr[ano]), 1) if encerr[ano] else None,
            } for ano in sorted(anos)
        },
        'em_andamento': {'n': len(andamento), 'idade_mediana': round(median(andamento), 1) if andamento else None},
    }


def _metrica_simples(chave, rotulo, definicao, pares):
    """pares: (data_inicio, data_fim) já resolvidos; ano do corte = ano do fim."""
    por_ano = defaultdict(list)
    for inicio, fim in pares:
        if inicio and fim:
            por_ano[fim.year].append(_dias(inicio, fim))
    return {'chave': chave, 'rotulo': rotulo, 'grupo': 'procedimento', 'definicao': definicao,
            'por_ano': {ano: _resumo(v) for ano, v in sorted(por_ano.items())}}


def calcular_tempos_por_ano(org_id):
    from modulo_contrato.models import Contrato
    from modulo_demanda.models import DFD
    from modulo_etp.models import ETP
    from modulo_licitacao.models import Procedimento
    from modulo_mapa_precos.models import MapaComparativoPrecos
    from modulo_tr.models import TR

    def cron(qs):
        return sorted(qs, key=lambda h: h.criado_em)

    metricas = [
        _metricas_peca('DFD', 'DFD', DFD.objects.filter(org_id=org_id).prefetch_related('historico'),
                       lambda r: cron(r.historico.all())),
        _metricas_peca('ETP', 'ETP', ETP.objects.filter(org_id=org_id).prefetch_related('historico'),
                       lambda r: cron(r.historico.all())),
        _metricas_peca('TR', 'Termo de Referência', TR.objects.filter(org_id=org_id).prefetch_related('historico'),
                       lambda r: cron(r.historico.all())),
        _metricas_peca('Mapa', 'Mapa de Preços',
                       MapaComparativoPrecos.objects.filter(org_id=org_id).prefetch_related('historico'),
                       lambda r: cron(r.historico.all())),
    ]

    procs = list(Procedimento.objects.filter(org_id=org_id).select_related('dfd').prefetch_related('historico'))
    prep, externa, ciclo = [], [], []
    for p in procs:
        hist = cron(p.historico.all())
        inicio = p.dfd.created_at if p.dfd_id else p.created_at
        aprov = next((h.criado_em for h in hist if h.status_novo == 'Aprovado'), None)
        publ = next((h.criado_em for h in hist if h.status_novo == 'Publicado'), None)
        homol = next((h.criado_em for h in hist if h.status_novo == 'Homologado'), None)
        prep.append((inicio, aprov))
        if p.eh_licitacao:
            externa.append((publ, homol))
    for c in Contrato.objects.filter(org_id=org_id, data_assinatura__isnull=False).select_related('dfd'):
        if c.dfd_id:
            ciclo.append((c.dfd.created_at.date(), c.data_assinatura))

    metricas += [
        _metrica_simples('proc_preparatoria', 'Fase preparatória',
                         'Da criação do DFD à aprovação do procedimento para publicação/contratação.', prep),
        _metrica_simples('proc_externa', 'Fase externa (licitações)',
                         'Da publicação do edital à homologação.', externa),
        _metrica_simples('ciclo_total', 'Ciclo total',
                         'Da criação do DFD à assinatura do contrato.', ciclo),
    ]
    anos = sorted({a for m in metricas for a in m['por_ano']})
    return {'anos': anos, 'metricas': metricas}
