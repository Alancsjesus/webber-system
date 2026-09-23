"""
Indicadores de tempo sobre o Painel de Tramitação (D1 do roadmap — Data Mart
de Tramitação). Reaproveita `estagio.listar_itens_painel()`, que já resolve
"onde está" cada processo e desde quando (`data_entrada_fase`) — não exige
nenhum dado novo, só agrega o que o Painel Gerencial (set/2026, sinal-driven)
já calcula.

Escopo v1: tempo de permanência na ETAPA/FASE ATUAL (quanto tempo o processo
já está parado onde está agora) — não o tempo histórico total gasto em cada
etapa ao longo de todo o ciclo de vida (isso exigiria consolidar os
Historico* de DFD/ETP/TR/Procedimento numa linha do tempo única por processo;
registrado como extensão futura, não implementada aqui).
"""
from datetime import date

from core.models import ParametroSistema

from .estagio import listar_itens_painel


def _limiar_dias(chave, default):
    try:
        return int(ParametroSistema.get(chave, str(default)))
    except (TypeError, ValueError):
        return default


def _dias_atencao():
    return _limiar_dias('tramitacao_dias_atencao', 15)


def _dias_critico():
    return _limiar_dias('tramitacao_dias_critico', 30)


def _classificar(dias, atencao, critico):
    if dias is None:
        return None
    if dias >= critico:
        return 'critico'
    if dias >= atencao:
        return 'atencao'
    return 'normal'


def _media(valores):
    return round(sum(valores) / len(valores), 1) if valores else None


def _filtrar_itens(itens, request):
    """Filtros do painel de indicadores (D2 — Solução 3 do diagnóstico CLIC:
    período/unidade/etapa). ?setor= e ?etapa= são exatos; ?data_inicio=/
    ?data_fim= restringem por data_entrada_fase (formato YYYY-MM-DD)."""
    setor = request.query_params.get('setor')
    etapa = request.query_params.get('etapa')
    data_inicio = request.query_params.get('data_inicio')
    data_fim = request.query_params.get('data_fim')

    if setor:
        itens = [i for i in itens if i['setor'] == setor]
    if etapa:
        alvo = None if etapa == 'manual' else etapa
        itens = [i for i in itens if i['etapa_atual'] == alvo]
    if data_inicio:
        try:
            di = date.fromisoformat(data_inicio)
            itens = [i for i in itens if i['data_entrada_fase'] and i['data_entrada_fase'] >= di]
        except ValueError:
            pass
    if data_fim:
        try:
            df = date.fromisoformat(data_fim)
            itens = [i for i in itens if i['data_entrada_fase'] and i['data_entrada_fase'] <= df]
        except ValueError:
            pass
    return itens


def calcular_indicadores(request):
    hoje = date.today()
    atencao, critico = _dias_atencao(), _dias_critico()
    itens = _filtrar_itens(listar_itens_painel(request), request)

    for item in itens:
        if item['data_entrada_fase']:
            item['dias_na_fase'] = (hoje - item['data_entrada_fase']).days
        else:
            item['dias_na_fase'] = None
        item['classificacao'] = _classificar(item['dias_na_fase'], atencao, critico)

    com_dias = [i for i in itens if i['dias_na_fase'] is not None]

    por_setor = {}
    por_etapa = {}
    for i in itens:
        g_setor = por_setor.setdefault(i['setor'], {'setor': i['setor'], 'total': 0, 'criticos': 0, 'atencao': 0, '_dias': []})
        g_setor['total'] += 1
        if i['classificacao'] == 'critico':
            g_setor['criticos'] += 1
        elif i['classificacao'] == 'atencao':
            g_setor['atencao'] += 1
        if i['dias_na_fase'] is not None:
            g_setor['_dias'].append(i['dias_na_fase'])

        etapa = i['etapa_atual'] or 'Manual (sem DFD)'
        g_etapa = por_etapa.setdefault(etapa, {'etapa': etapa, 'total': 0, 'criticos': 0, '_dias': []})
        g_etapa['total'] += 1
        if i['classificacao'] == 'critico':
            g_etapa['criticos'] += 1
        if i['dias_na_fase'] is not None:
            g_etapa['_dias'].append(i['dias_na_fase'])

    grupos_setor = []
    for g in por_setor.values():
        dias = g.pop('_dias')
        g['tempo_medio'] = _media(dias)
        grupos_setor.append(g)
    grupos_setor.sort(key=lambda g: -(g['tempo_medio'] or 0))

    grupos_etapa = []
    for g in por_etapa.values():
        dias = g.pop('_dias')
        g['tempo_medio'] = _media(dias)
        grupos_etapa.append(g)
    grupos_etapa.sort(key=lambda g: -(g['tempo_medio'] or 0))

    etapa_maior_tempo = grupos_etapa[0]['etapa'] if grupos_etapa and grupos_etapa[0]['tempo_medio'] else None

    top_criticos = sorted(com_dias, key=lambda i: -i['dias_na_fase'])[:10]

    from core.cronograma_contratacoes import (
        estatisticas_duracao_por_modalidade, estatisticas_duracao_por_tipo_objeto,
        estatisticas_impacto_tramitacao_externa,
    )
    duracao_por_modalidade = estatisticas_duracao_por_modalidade(request.org_id)
    duracao_por_tipo_objeto = estatisticas_duracao_por_tipo_objeto(request.org_id)
    impacto_tramitacao_externa = estatisticas_impacto_tramitacao_externa(request.org_id)

    return {
        'total_processos': len(itens),
        'processos_criticos': sum(1 for i in itens if i['classificacao'] == 'critico'),
        'processos_atencao': sum(1 for i in itens if i['classificacao'] == 'atencao'),
        'tempo_medio_geral': _media([i['dias_na_fase'] for i in com_dias]),
        'etapa_maior_tempo_medio': etapa_maior_tempo,
        'limiar_dias_atencao': atencao,
        'limiar_dias_critico': critico,
        'por_setor': grupos_setor,
        'por_etapa': grupos_etapa,
        'duracao_por_modalidade': duracao_por_modalidade,
        'duracao_por_tipo_objeto': duracao_por_tipo_objeto,
        'impacto_tramitacao_externa': impacto_tramitacao_externa,
        'top_criticos': [
            {
                'numero_sei': i['numero_sei'],
                'objeto': i['objeto'],
                'setor': i['setor'],
                'fase_atual': i['fase_atual'],
                'dias_na_fase': i['dias_na_fase'],
                'etapa_atual': i['etapa_atual'],
                'etapa_registro_id': i['etapa_registro_id'],
            }
            for i in top_criticos
        ],
    }
