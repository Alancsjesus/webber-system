"""
Pesquisa de preços unitários na API pública de Dados Abertos do Compras.gov.br
(módulo "pesquisa-preco", sucessor do Painel de Preços).
Especificação: https://dadosabertos.compras.gov.br/v3/api-docs

Segurança — o que sai do WEBBER nesta integração:
  * só o código público de catálogo (CATMAT/CATSER), o período e, se informada, a UF;
  * nenhuma descrição de item, órgão, usuário, valor ou documento interno é enviada;
  * consulta feita direto do backend ao host oficial (sem intermediário/MCP de
    terceiros), com HTTPS e certificado verificado, host fixo e resposta limitada.
"""
import json
import logging
import ssl
import statistics
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.cache import cache

from core.models import ParametroSistema

logger = logging.getLogger(__name__)

COMPRASGOV_BASE = 'https://dadosabertos.compras.gov.br'
ROTA_PRECO = {
    'material': '/modulo-pesquisa-preco/1_consultarMaterial',
    'servico':  '/modulo-pesquisa-preco/3_consultarServico',
}
# Itens de Atas de Registro de Preços (espelho do PNCP, inclui estados e municípios)
ROTA_ARP_ITEM = '/modulo-arp/2_consultarARPItem'
ROTA_CATALOGO = {
    'material': ('/modulo-material/4_consultarItemMaterial', 'codigoItem'),
    'servico':  ('/modulo-servico/6_consultarItemServico', 'codigoServico'),
}
UFS = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA',
    'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
}
TAMANHO_PAGINA = 500        # máximo aceito pela API
MAX_PAGINAS = 4             # teto de 2.000 registros por consulta
MAX_BYTES_RESPOSTA = 20 * 1024 * 1024
CACHE_TTL = 15 * 60
# Decreto Estadual 22.886/2024 — mesmo critério de ±30% da mediana usado em ItemMapa.calcular
FAIXA_OUTLIER = 0.30


class ErroComprasGov(Exception):
    """Falha de consulta com mensagem já pronta para o usuário."""


def validar_codigo(codigo) -> str:
    c = str(codigo or '').strip()
    if not c.isdigit() or len(c) > 9:
        raise ErroComprasGov('Informe o código CATMAT/CATSER (somente números, até 9 dígitos).')
    return c


def validar_tipo(tipo) -> str:
    if tipo not in ROTA_PRECO:
        raise ErroComprasGov('Tipo deve ser "material" (CATMAT) ou "servico" (CATSER).')
    return tipo


def validar_uf(uf) -> str:
    uf = str(uf or '').strip().upper()
    if uf and uf not in UFS:
        raise ErroComprasGov('UF inválida.')
    return uf


def prazo_meses_parametro_ii() -> int:
    try:
        return max(1, int(ParametroSistema.get('prazo_validade_parametro_ii_meses', 12)))
    except (TypeError, ValueError):
        return 12


def _timeout() -> int:
    try:
        return int(ParametroSistema.get('pncp_timeout_segundos', '20'))
    except (TypeError, ValueError):
        return 20


def _get_json(rota: str, params: dict) -> dict:
    # A rota vem sempre das constantes acima; o host nunca é composto com entrada do usuário.
    url = f'{COMPRASGOV_BASE}{rota}?{urllib.parse.urlencode(params)}'
    req = urllib.request.Request(url, headers={
        'Accept': 'application/json',
        'User-Agent': 'WEBBER-System/1.0 (pesquisa de precos)',
    })
    try:
        with urllib.request.urlopen(req, timeout=_timeout(), context=ssl.create_default_context()) as resp:
            corpo = resp.read(MAX_BYTES_RESPOSTA + 1)
    except urllib.error.HTTPError as e:
        logger.warning('Compras.gov.br HTTP %s em %s', e.code, rota)
        if e.code == 400:
            raise ErroComprasGov('A API do Compras.gov.br recusou os parâmetros da consulta.')
        raise ErroComprasGov(f'A API do Compras.gov.br respondeu com erro {e.code}. Tente novamente mais tarde.')
    except (urllib.error.URLError, TimeoutError, ssl.SSLError) as e:
        logger.warning('Compras.gov.br indisponível em %s: %s', rota, e)
        raise ErroComprasGov('Não foi possível conectar à API do Compras.gov.br (indisponível ou sem resposta).')
    if len(corpo) > MAX_BYTES_RESPOSTA:
        raise ErroComprasGov('Resposta da API do Compras.gov.br excedeu o tamanho permitido.')
    try:
        return json.loads(corpo.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ErroComprasGov('Resposta inválida da API do Compras.gov.br.')


def consultar_catalogo(tipo: str, codigo: str) -> dict | None:
    """Confere se o código existe no catálogo e devolve o nome oficial do item."""
    tipo, codigo = validar_tipo(tipo), validar_codigo(codigo)
    chave = f'comprasgov:cat:{tipo}:{codigo}'
    achado = cache.get(chave)
    if achado is not None:
        return achado or None
    rota, campo = ROTA_CATALOGO[tipo]
    dados = _get_json(rota, {'pagina': 1, campo: codigo})
    itens = dados.get('resultado') or []
    item = itens[0] if itens else None
    if item is None:
        achado = {}
    elif tipo == 'material':
        achado = {
            'codigo': codigo,
            'nome': str(item.get('descricaoItem') or '')[:500],
            'pdm': str(item.get('nomePdm') or '')[:255],
            'classe': str(item.get('nomeClasse') or '')[:255],
            'ativo': bool(item.get('statusItem', True)),
        }
    else:
        achado = {
            'codigo': codigo,
            'nome': str(item.get('nomeServico') or '')[:500],
            'pdm': '',
            'classe': str(item.get('nomeGrupo') or '')[:255],
            'ativo': bool(item.get('statusServico', True)),
        }
    cache.set(chave, achado, CACHE_TTL)
    return achado or None


def _dec(val) -> Decimal | None:
    try:
        d = Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return d if d.is_finite() else None


def _data(val) -> date | None:
    try:
        return date.fromisoformat(str(val)[:10])
    except (TypeError, ValueError):
        return None


def _txt(val, limite=255) -> str:
    return str(val or '').strip()[:limite]


def _normalizar(reg: dict, tipo: str) -> dict | None:
    preco = _dec(reg.get('precoUnitario'))
    if preco is None or preco <= 0:
        return None
    data_ref = _data(reg.get('dataResultado')) or _data(reg.get('dataCompra'))
    if tipo == 'material':
        unidade = _txt(reg.get('siglaUnidadeFornecimento') or reg.get('siglaUnidadeMedida'), 30)
        unidade_nome = _txt(reg.get('nomeUnidadeFornecimento') or reg.get('nomeUnidadeMedida'), 60)
    else:
        unidade = _txt(reg.get('siglaUnidadeMedida'), 30)
        unidade_nome = _txt(reg.get('nomeUnidadeMedida'), 60)
    id_item = _txt(reg.get('idCompraItem'), 40) or f"{_txt(reg.get('idCompra'), 30)}-{_txt(reg.get('numeroItemCompra'), 8)}"
    return {
        'id': id_item,
        'origem': 'compra',
        'chave_compra': _chave_compra(reg.get('idCompra'), reg.get('numeroItemCompra')),
        'id_compra': _txt(reg.get('idCompra'), 30),
        'numero_item': _txt(reg.get('numeroItemCompra'), 8),
        'preco_unitario': str(preco),
        'quantidade': str(_dec(reg.get('quantidade')) or ''),
        'unidade': unidade,
        'unidade_nome': unidade_nome,
        'descricao': _txt(reg.get('descricaoDetalhadaItem') or reg.get('descricaoItem'), 500),
        'marca': _txt(reg.get('marca'), 120),
        'fornecedor': _txt(reg.get('nomeFornecedor'), 255),
        'fornecedor_ni': _txt(reg.get('niFornecedor'), 20),
        'orgao': _txt(reg.get('nomeOrgao'), 255),
        'uasg': _txt(reg.get('codigoUasg'), 10),
        'uasg_nome': _txt(reg.get('nomeUasg'), 255),
        'municipio': _txt(reg.get('municipio'), 80),
        'uf': _txt(reg.get('estado'), 2),
        'esfera': _txt(reg.get('esfera'), 2),
        'forma': _txt(reg.get('forma'), 20),
        'data_referencia': data_ref.isoformat() if data_ref else '',
    }


def _chave_compra(id_compra, numero_item) -> str:
    try:
        return f'{_txt(id_compra, 30)}#{int(str(numero_item))}'
    except (TypeError, ValueError):
        return ''


def _normalizar_arp(reg: dict) -> dict | None:
    if reg.get('itemExcluido'):
        return None
    preco = _dec(reg.get('valorUnitario'))
    if preco is None or preco <= 0:
        return None
    ata = _txt(reg.get('numeroControlePncpAta'), 60)
    data_ref = _data(reg.get('dataAssinatura')) or _data(reg.get('dataVigenciaInicial'))
    return {
        'id': f"ARP-{ata or _txt(reg.get('idCompra'), 30)}-{_txt(reg.get('numeroItem'), 8)}"[:100],
        'origem': 'ata',
        'chave_compra': _chave_compra(reg.get('idCompra'), reg.get('numeroItem')),
        'id_compra': _txt(reg.get('idCompra'), 30),
        'numero_item': _txt(reg.get('numeroItem'), 8),
        'preco_unitario': str(preco),
        'quantidade': str(_dec(reg.get('quantidadeHomologadaVencedor')) or ''),
        'unidade': '',  # a API de ARP não informa a unidade de fornecimento
        'unidade_nome': '',
        'descricao': _txt(reg.get('descricaoItem'), 500),
        'marca': '',
        'fornecedor': _txt(reg.get('nomeRazaoSocialFornecedor'), 255),
        'fornecedor_ni': _txt(reg.get('niFornecedor'), 20),
        'orgao': _txt(reg.get('nomeUnidadeGerenciadora'), 255),
        'uasg': _txt(reg.get('codigoUnidadeGerenciadora'), 10),
        'uasg_nome': _txt(reg.get('nomeUnidadeGerenciadora'), 255),
        'municipio': '',
        'uf': '',
        'esfera': '',
        'forma': f"Ata RP {_txt(reg.get('numeroAtaRegistroPreco'), 20)}".strip(),
        'ata_pncp': ata,
        'vigencia_fim': _txt(reg.get('dataVigenciaFinal'), 10),
        'data_referencia': data_ref.isoformat() if data_ref else '',
    }


def _consultar_arp(tipo: str, codigo: str, inicio: date, fim: date) -> tuple[list, int]:
    params = {
        'tamanhoPagina': TAMANHO_PAGINA,
        'codigoItem': codigo,
        'tipoItem': 'Material' if tipo == 'material' else 'Serviço',
        'dataVigenciaInicialMin': inicio.isoformat(),
        'dataVigenciaInicialMax': fim.isoformat(),
    }
    brutos, total = [], 0
    for pagina in range(1, MAX_PAGINAS + 1):
        dados = _get_json(ROTA_ARP_ITEM, {**params, 'pagina': pagina})
        total = int(dados.get('totalRegistros') or 0)
        brutos.extend(dados.get('resultado') or [])
        if not dados.get('paginasRestantes'):
            break
    return brutos, total


def consultar_precos(tipo: str, codigo: str, uf: str = '', meses: int | None = None) -> dict:
    """
    Busca preços homologados do item no período de validade do Parâmetro II
    (ParametroSistema.prazo_validade_parametro_ii_meses) e devolve registros
    normalizados + estatística. Resultado em cache por 15 min para que a
    importação revalide os mesmos dados sem nova chamada externa.
    """
    tipo, codigo, uf = validar_tipo(tipo), validar_codigo(codigo), validar_uf(uf)
    meses = min(max(int(meses or prazo_meses_parametro_ii()), 1), 24)
    hoje = date.today()
    inicio = hoje - timedelta(days=meses * 30)
    chave = f'comprasgov:preco:{tipo}:{codigo}:{uf}:{inicio.isoformat()}'
    em_cache = cache.get(chave)
    if em_cache is not None:
        return em_cache

    params = {
        'tamanhoPagina': TAMANHO_PAGINA,
        'dataCompraInicio': inicio.isoformat(),
        'dataCompraFim': hoje.isoformat(),
    }
    if tipo == 'material':
        params.update({'tipo': 'codigoItemCatalogo', 'codigo': codigo})
    else:
        params['codigoItemCatalogo'] = codigo
    if uf:
        params['estado'] = uf

    brutos, total_api = [], 0
    for pagina in range(1, MAX_PAGINAS + 1):
        dados = _get_json(ROTA_PRECO[tipo], {**params, 'pagina': pagina})
        total_api = int(dados.get('totalRegistros') or 0)
        brutos.extend(dados.get('resultado') or [])
        if not dados.get('paginasRestantes'):
            break

    registros, vistos = [], set()
    for reg in brutos:
        n = _normalizar(reg, tipo)
        if n and n['id'] not in vistos:
            vistos.add(n['id'])
            registros.append(n)

    # Atas de RP: sem CNPJ, por código de catálogo. A API de ARP não traz UF, então
    # com filtro de UF elas ficam de fora (não há como garantir a localidade).
    avisos = []
    total_arp = 0
    if uf:
        avisos.append('Atas de RP não entram quando há filtro de UF (a API de atas não informa a UF).')
    else:
        try:
            brutos_arp, total_arp = _consultar_arp(tipo, codigo, inicio, hoje)
        except ErroComprasGov as e:
            brutos_arp = []
            avisos.append(f'Atas de RP não consultadas: {e}')
        compras = {r['chave_compra'] for r in registros if r['chave_compra']}
        for reg in brutos_arp:
            n = _normalizar_arp(reg)
            # mesmo item de compra já veio como preço homologado → não conta duas vezes
            if n and n['id'] not in vistos and n['chave_compra'] not in compras:
                vistos.add(n['id'])
                registros.append(n)
    registros.sort(key=lambda r: r['data_referencia'], reverse=True)

    resultado = {
        'tipo': tipo,
        'codigo': codigo,
        'uf': uf,
        'periodo_inicio': inicio.isoformat(),
        'periodo_fim': hoje.isoformat(),
        'meses': meses,
        'total_api': total_api + total_arp,
        'truncado': total_api > len(brutos) or total_arp > MAX_PAGINAS * TAMANHO_PAGINA,
        'avisos': avisos,
        'registros': registros,
    }
    cache.set(chave, resultado, CACHE_TTL)
    return resultado


def estatistica(valores: list[float]) -> dict:
    """Resumo da amostra + faixa de aceitação (±30% da mediana, Decreto 22.886/2024)."""
    if not valores:
        return {'n': 0}
    mediana = statistics.median(valores)
    media = statistics.fmean(valores)
    desvio = statistics.stdev(valores) if len(valores) > 1 else 0.0
    return {
        'n': len(valores),
        'minimo': round(min(valores), 4),
        'maximo': round(max(valores), 4),
        'media': round(media, 4),
        'mediana': round(mediana, 4),
        'desvio_padrao': round(desvio, 4),
        'coef_variacao_pct': round(desvio / media * 100, 1) if media else 0.0,
        'limite_inferior': round(mediana * (1 - FAIXA_OUTLIER), 4),
        'limite_superior': round(mediana * (1 + FAIXA_OUTLIER), 4),
    }


def classificar(registros: list[dict], unidade_item: str = '') -> dict:
    """
    Marca cada registro como inexequível/excessivo/ok e se a unidade diverge do item.
    A estatística usa só os registros na mesma unidade do item (quando há algum) —
    misturar "caixa" com "unidade" distorceria a mediana.
    """
    un = (unidade_item or '').strip().upper()
    for r in registros:
        r['unidade_diverge'] = bool(un and r['unidade'] and r['unidade'].upper() != un)
    base = [r for r in registros if not r['unidade_diverge']] or registros
    est = estatistica([float(r['preco_unitario']) for r in base])
    est['qtd_mesma_unidade'] = sum(1 for r in registros if not r['unidade_diverge'])
    for r in registros:
        v = float(r['preco_unitario'])
        if est['n'] >= 3 and v < est['limite_inferior']:
            r['situacao'] = 'inexequivel'
        elif est['n'] >= 3 and v > est['limite_superior']:
            r['situacao'] = 'excessivo'
        else:
            r['situacao'] = 'ok'
    return est


def valor_2_casas(preco: str) -> Decimal:
    return Decimal(preco).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
