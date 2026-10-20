"""
Serviços de integração com a API pública do PNCP.
Documentação: https://pncp.gov.br/api/consulta/swagger-ui/index.html
"""
import logging
from datetime import date
from decimal import Decimal, InvalidOperation

import urllib.request
import urllib.parse
import urllib.error
import json
import ssl

from core.models import ParametroSistema

logger = logging.getLogger(__name__)

PNCP_BASE = 'https://pncp.gov.br/api/consulta/v1'


def _get_timeout():
    try:
        return int(ParametroSistema.get('pncp_timeout_segundos', '20'))
    except (ValueError, TypeError):
        return 20


def _ssl_ctx():
    # Certificado e hostname verificados: desligar a verificação permitiria que um
    # intermediário na rede injetasse preços falsos na pesquisa.
    return ssl.create_default_context()


def _get_json(url: str) -> dict:
    """Realiza GET na URL e retorna JSON. Levanta exceção em caso de erro."""
    req = urllib.request.Request(
        url,
        headers={
            'Accept': 'application/json',
            'User-Agent': 'WEBBER-System/1.0 (integração PNCP)',
        },
    )
    with urllib.request.urlopen(req, timeout=_get_timeout(), context=_ssl_ctx()) as resp:
        return json.loads(resp.read().decode('utf-8'))


class PNCPClient:
    """Encapsula chamadas à API de consulta do PNCP."""

    def buscar_contratos(self, data_ini: date, data_fim: date,
                         cnpj: str = '', uf: str = '',
                         termo: str = '', pagina: int = 1,
                         tamanho: int = 20,
                         timeout_override: int = None) -> dict:
        """
        GET /contratos
        Retorna contratos publicados no período.
        timeout_override permite usar timeout menor que o padrão do sistema.

        IMPORTANTE: este endpoint do PNCP não tem parâmetro de UF — "uf" é
        ignorado silenciosamente pela API se enviado (confirmado testando
        direto contra a API: uf=BA e uf=SP retornam o mesmo total nacional
        de registros). O filtro de UF é aplicado depois, no lado do cliente,
        em _filtrar_uf(). O filtro de órgão também tem nome de parâmetro
        diferente do de /atas: aqui é "cnpjOrgao", não "cnpj".
        """
        params = {
            'dataInicial': data_ini.strftime('%Y%m%d'),
            'dataFinal':   data_fim.strftime('%Y%m%d'),
            'pagina':      pagina,
            'tamanhoPagina': tamanho,
        }
        if cnpj:
            params['cnpjOrgao'] = cnpj.replace('.', '').replace('/', '').replace('-', '')
        url = f"{PNCP_BASE}/contratos?{urllib.parse.urlencode(params)}"
        timeout = timeout_override if timeout_override else _get_timeout()
        req = urllib.request.Request(
            url,
            headers={'Accept': 'application/json', 'User-Agent': 'WEBBER-System/1.0'},
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def buscar_atas(self, data_ini: date, data_fim: date,
                    cnpj: str = '', uf: str = '',
                    pagina: int = 1, tamanho: int = 50) -> dict:
        """
        GET /atas
        Retorna atas de registro de preços vigentes no período.

        IMPORTANTE: este endpoint não tem parâmetro de UF nem retorna UF no
        payload de cada ata (diferente de /contratos, que ao menos devolve
        unidadeOrgao.ufSigla) — então "uf" nem é enviado à API nem pode ser
        filtrado depois no cliente. O único filtro efetivo aqui é "cnpj"
        (esse sim funciona nesse endpoint, confirmado por teste direto).
        """
        params = {
            'dataInicial': data_ini.strftime('%Y%m%d'),
            'dataFinal':   data_fim.strftime('%Y%m%d'),
            'pagina':      pagina,
            'tamanhoPagina': tamanho,
        }
        if cnpj:
            params['cnpj'] = cnpj.replace('.', '').replace('/', '').replace('-', '')
        url = f"{PNCP_BASE}/atas?{urllib.parse.urlencode(params)}"
        return _get_json(url)

    def buscar_contratacoes(self, data_ini: date, data_fim: date,
                            uf: str = '', modalidade: int = 8,
                            pagina: int = 1, tamanho: int = 50) -> dict:
        """
        GET /contratacoes/publicacao
        Retorna editais/contratações publicadas.
        Modalidade 8 = Pregão Eletrônico.
        """
        params = {
            'dataInicial': data_ini.strftime('%Y%m%d'),
            'dataFinal':   data_fim.strftime('%Y%m%d'),
            'codigoModalidadeContratacao': modalidade,
            'pagina':      pagina,
            'tamanhoPagina': tamanho,
        }
        if uf:
            params['uf'] = uf
        url = f"{PNCP_BASE}/contratacoes/publicacao?{urllib.parse.urlencode(params)}"
        return _get_json(url)


def _normalizar_contrato(item: dict) -> dict:
    """Normaliza um item de /contratos para o formato interno.
    Campo de controle é "numeroControlePNCP" (maiúsculo) — não
    "numeroControlePncp"; a grafia errada fazia numero_certame sair
    sempre vazio."""
    orgao = item.get('orgaoEntidade') or {}
    unidade = item.get('unidadeOrgao') or {}
    return {
        'numero_pncp':    item.get('numeroContratoEmpenho', '') or item.get('numeroControlePNCP', ''),
        'objeto':         item.get('objetoContrato', ''),
        'valor_global':   _dec(item.get('valorGlobal')),
        'valor_unitario': None,
        'quantidade':     None,
        'unidade_medida': '',
        'orgao_nome':     orgao.get('razaoSocial', ''),
        'orgao_cnpj':     orgao.get('cnpj', ''),
        'uf':             unidade.get('ufSigla', ''),
        'data_referencia': _data(item.get('dataPublicacaoPncp') or item.get('dataVigenciaInicio')),
        'numero_certame': item.get('numeroControlePNCP', ''),
        'modalidade':     item.get('modalidadeNome', ''),
        'tipo_registro':  'contrato',
    }


def _normalizar_ata(item: dict) -> dict:
    """Normaliza um item de /atas para o formato interno.
    Campo do objeto é "objetoContratacao" nesta API — não "objeto" (bug
    anterior fazia o objeto sair sempre vazio, o que também quebrava o
    filtro por termo, já que ele compara contra esse campo)."""
    return {
        'numero_pncp':    item.get('numeroControlePNCPAta', ''),
        'objeto':         item.get('objetoContratacao', ''),
        'valor_global':   None,
        'valor_unitario': None,
        'quantidade':     None,
        'unidade_medida': '',
        'orgao_nome':     item.get('nomeOrgao', ''),
        'orgao_cnpj':     item.get('cnpjOrgao', ''),
        'uf':             '',  # /atas não retorna UF — ver nota em PNCPClient.buscar_atas
        'data_referencia': _data(item.get('vigenciaInicio')),
        'numero_certame': item.get('numeroControlePNCPAta', ''),
        'modalidade':     'Ata de Registro de Preços',
        'tipo_registro':  'ata',
    }


def _dec(val) -> Decimal | None:
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except InvalidOperation:
        return None


def _data(val: str | None) -> date | None:
    if not val:
        return None
    try:
        # PNCP retorna ISO 8601: "2024-12-01T00:00:00" ou "2024-12-01"
        parte_data = str(val).split('T')[0]
        y, m, d = parte_data.split('-')
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def _filtrar_termo(registros: list, termo: str) -> list:
    """Filtra registros cujo objeto contenha o termo (case-insensitive)."""
    if not termo:
        return registros
    t = termo.lower()
    return [r for r in registros if t in r.get('objeto', '').lower()]


def _filtrar_uf(registros: list, uf: str) -> list:
    """Filtra registros pela UF já extraída (só populada para contratos —
    ver nota em PNCPClient.buscar_atas). Como a API não filtra por UF no
    servidor, isso só reduz o que já veio na página consultada — não
    substitui informar um CNPJ para resultados relevantes."""
    if not uf:
        return registros
    return [r for r in registros if not r.get('uf') or r['uf'].upper() == uf.upper()]


PNCP_ITENS_BASE = 'https://pncp.gov.br/api/pncp/v1'

# Códigos de modalidade do PNCP (Manual de Integração, tabela "Modalidade de Contratação")
MODALIDADES_PNCP = {
    4: 'Concorrência - Eletrônica',
    6: 'Pregão - Eletrônico',
    8: 'Dispensa',
    9: 'Inexigibilidade',
}
MAX_PAGINAS_VARREDURA = 120   # por modalidade (50 registros por página)
MAX_RESULTADOS = 200
ORCAMENTO_SEGUNDOS = 45       # tempo máximo de varredura do PNCP por busca (gunicorn corta em 120 s)
CACHE_TTL = 15 * 60


INTERVALO_MIN = 1.0   # segundos entre chamadas ao PNCP numa varredura
_ultima_chamada = [0.0]


def _get_json_pncp(url: str, timeout: int, tentativas: int = 3):
    """
    GET com ritmo controlado e nova tentativa em 429. O PNCP limita a taxa por
    cliente: em rajada devolve "Too Many Requests" após ~13 chamadas, com
    penalidade de ~10 s; em ritmo de ~1 chamada/s não bloqueia.
    """
    import time
    req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'WEBBER-System/1.0'})
    for n in range(tentativas):
        espera = _ultima_chamada[0] + INTERVALO_MIN - time.monotonic()
        if espera > 0:
            time.sleep(espera)
        _ultima_chamada[0] = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as resp:
                corpo = resp.read()
            return json.loads(corpo.decode('utf-8')) if corpo else None
        except urllib.error.HTTPError as e:
            if e.code != 429 or n == tentativas - 1:
                raise
            time.sleep(12)


def _sem_acento(txt: str) -> str:
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', txt or '') if unicodedata.category(c) != 'Mn').lower()


def _bate_termo(objeto: str, palavras: list[str]) -> bool:
    alvo = _sem_acento(objeto)
    return all(p in alvo for p in palavras)


def _normalizar_contratacao(item: dict) -> dict:
    orgao = item.get('orgaoEntidade') or {}
    unidade = item.get('unidadeOrgao') or {}
    return {
        'numero_pncp':    item.get('numeroControlePNCP', ''),
        'objeto':         item.get('objetoCompra', '') or '',
        'valor_global':   _dec(item.get('valorTotalHomologado') or item.get('valorTotalEstimado')),
        'homologada':     bool(_dec(item.get('valorTotalHomologado'))),
        'valor_unitario': None,
        'quantidade':     None,
        'unidade_medida': '',
        'orgao_nome':     orgao.get('razaoSocial', ''),
        'orgao_cnpj':     orgao.get('cnpj', ''),
        'uf':             unidade.get('ufSigla', ''),
        'data_referencia': _data(item.get('dataPublicacaoPncp')),
        'numero_certame': item.get('numeroControlePNCP', ''),
        'modalidade':     item.get('modalidadeNome', ''),
        'tipo_registro':  'contratacao',
    }


def _varrer_modalidade(base: dict, mod: int, timeout: int, prazo_final: float) -> tuple[list, dict]:
    """
    Publicações de uma modalidade (UF/CNPJ/período já filtrados no servidor).
    Cada página fica em cache: se o tempo da busca esgotar, a próxima busca com os
    mesmos filtros retoma de onde parou, sem repetir chamadas ao PNCP.
    """
    import time
    from django.core.cache import cache
    nome = MODALIDADES_PNCP.get(mod, str(mod))
    prefixo = 'pncp:pag2:' + urllib.parse.urlencode(sorted({**base, 'mod': mod}.items()))
    registros = []
    situacao = {'modalidade': nome, 'paginas_lidas': 0, 'total_paginas': None, 'total_registros': None,
                'completa': False, 'erro': ''}
    pagina, total_pag = 1, 1
    while pagina <= min(total_pag, MAX_PAGINAS_VARREDURA):
        chave = f'{prefixo}:{pagina}'
        dados = cache.get(chave)
        if dados is None:
            if time.monotonic() > prazo_final:
                break
            params = {**base, 'codigoModalidadeContratacao': mod, 'pagina': pagina}
            try:
                bruto = _get_json_pncp(f'{PNCP_BASE}/contratacoes/publicacao?{urllib.parse.urlencode(params)}', timeout) or {}
            except Exception as e:
                situacao['erro'] = f'PNCP interrompeu na página {pagina} ({getattr(e, "reason", e)}).'
                logger.warning('PNCP contratacoes/publicacao mod=%s pag=%s erro: %s', mod, pagina, e)
                break
            dados = {
                'total_paginas': int(bruto.get('totalPaginas') or 0),
                'total_registros': int(bruto.get('totalRegistros') or 0),
                'registros': [_normalizar_contratacao(i) for i in (bruto.get('data') or [])],
            }
            cache.set(chave, dados, CACHE_TTL)
        total_pag = dados['total_paginas']
        situacao['total_paginas'] = total_pag
        situacao['total_registros'] = dados['total_registros']
        registros.extend(dados['registros'])
        situacao['paginas_lidas'] = pagina
        pagina += 1
    situacao['completa'] = situacao['paginas_lidas'] >= min(total_pag, MAX_PAGINAS_VARREDURA)
    return registros, situacao


ESPELHO_CONTRATACOES = '/modulo-contratacoes/1_consultarContratacoes_PNCP_14133'


MAX_PAGINAS_ESPELHO = 40     # 20.000 contratações (páginas de 500, ~1 s cada)


def _contratacoes_espelho(data_ini: date, data_fim: date, uf: str, cnpj: str, mod: int,
                          prazo_final: float | None = None) -> tuple[list, dict]:
    """
    Mesmas contratações do PNCP, pelo espelho do Dados Abertos Compras.gov.br: páginas
    de 500 e resposta em ~2 s, mas só cobre o que nasceu no Compras.gov.br (falta parte
    de estados/municípios que usam outras plataformas) — por isso complementa, não
    substitui, a varredura do PNCP.
    """
    import time
    from django.core.cache import cache
    from .comprasgov import _get_json  # mesmo cliente seguro (host fixo, SSL verificado)
    params = {
        'tamanhoPagina': 500,
        'dataPublicacaoPncpInicial': data_ini.isoformat(),
        'dataPublicacaoPncpFinal': data_fim.isoformat(),
        'codigoModalidade': mod,
    }
    if uf:
        params['unidadeOrgaoUfSigla'] = uf.upper()
    if cnpj:
        params['orgaoEntidadeCnpj'] = ''.join(c for c in cnpj if c.isdigit())
    saida = []
    situacao = {'paginas_lidas': 0, 'total_paginas': None, 'total_registros': None, 'completa': False}
    prefixo = 'espelho:pag:' + urllib.parse.urlencode(sorted(params.items()))
    for pagina in range(1, MAX_PAGINAS_ESPELHO + 1):
        dados = cache.get(f'{prefixo}:{pagina}')
        if dados is None:
            if prazo_final and time.monotonic() > prazo_final:
                break
            dados = _get_json(ESPELHO_CONTRATACOES, {**params, 'pagina': pagina})
            cache.set(f'{prefixo}:{pagina}', dados, CACHE_TTL)
        situacao['paginas_lidas'] = pagina
        situacao['total_paginas'] = int(dados.get('totalPaginas') or 0)
        situacao['total_registros'] = int(dados.get('totalRegistros') or 0)
        for i in (dados.get('resultado') or []):
            if i.get('contratacaoExcluida'):
                continue
            saida.append({
                'numero_pncp':    i.get('numeroControlePNCP', ''),
                'objeto':         i.get('objetoCompra', '') or '',
                'valor_global':   _dec(i.get('valorTotalHomologado') or i.get('valorTotalEstimado')),
                'homologada':     bool(i.get('existeResultado')) or bool(_dec(i.get('valorTotalHomologado'))),
                'valor_unitario': None,
                'quantidade':     None,
                'unidade_medida': '',
                'orgao_nome':     i.get('orgaoEntidadeRazaoSocial', ''),
                'orgao_cnpj':     i.get('orgaoEntidadeCnpj', ''),
                'uf':             i.get('unidadeOrgaoUfSigla', ''),
                'data_referencia': _data(i.get('dataPublicacaoPncp')),
                'numero_certame': i.get('numeroControlePNCP', ''),
                'modalidade':     i.get('modalidadeNome', ''),
                'tipo_registro':  'contratacao',
            })
        if not dados.get('paginasRestantes'):
            situacao['completa'] = True
            break
    return saida, situacao


def buscar_contratacoes(data_ini: date, data_fim: date, uf: str = '', cnpj: str = '',
                        termo: str = '', modalidades=(6,), similaridade_minima: int = 40,
                        natureza: str = 'qualquer') -> tuple[list, list, list, dict]:
    """
    GET /contratacoes/publicacao — ao contrário de /contratos e /atas, este endpoint
    filtra UF, CNPJ e modalidade NO SERVIDOR. A palavra-chave (ou a descrição do item
    do mapa) não é filtro da API: o universo já reduzido é varrido e cada objeto
    recebe uma nota de similaridade (modulo_pncp.similaridade); ficam os de nota
    >= similaridade_minima, do mais parecido para o menos.

    Sem UF e sem CNPJ (todo o Brasil) a varredura do PNCP é inviável (~65 mil pregões
    em 60 dias, ~4 s por página): usa só o espelho do Dados Abertos, que cobre o que
    passou pelo Compras.gov.br. Contratações sem resultado homologado são descartadas —
    não têm preço praticado para importar.
    """
    import time
    from .similaridade import ranquear, filtrar_natureza
    timeout = _get_timeout()
    base = {
        'dataInicial': data_ini.strftime('%Y%m%d'),
        'dataFinal':   data_fim.strftime('%Y%m%d'),
        'tamanhoPagina': 50,
    }
    if uf:
        base['uf'] = uf.upper()
    if cnpj:
        base['cnpj'] = ''.join(c for c in cnpj if c.isdigit())

    from .comprasgov import ErroComprasGov
    prazo_final = time.monotonic() + ORCAMENTO_SEGUNDOS
    universo, avisos, situacoes = [], [], []
    vistos = {}
    nacional = not uf and not cnpj
    for mod in modalidades:
        try:
            espelho, sit_esp = _contratacoes_espelho(data_ini, data_fim, uf, cnpj, mod, prazo_final)
        except ErroComprasGov as e:
            espelho, sit_esp = [], {'completa': True}
            logger.warning('Espelho Dados Abertos mod=%s: %s', mod, e)
        if nacional:
            registros = []
            sit = {'modalidade': MODALIDADES_PNCP.get(mod, str(mod)), 'paginas_lidas': sit_esp.get('paginas_lidas', 0),
                   'total_paginas': sit_esp.get('total_paginas'), 'total_registros': sit_esp.get('total_registros'),
                   'completa': sit_esp.get('completa', False), 'erro': '', 'nacional': True}
            if not sit['completa'] and sit['total_paginas']:
                avisos.append(
                    f'{sit["modalidade"]}: {sit["total_registros"]} contratações no Brasil — lidas '
                    f'{sit["paginas_lidas"] * 500}. Clique em Buscar novamente para continuar ou reduza o período.'
                )
        else:
            registros, sit = _varrer_modalidade(base, mod, timeout, prazo_final)
        for r in espelho + registros:
            n = r['numero_pncp']
            if not n:
                continue
            # mesma contratação nas duas bases: prevalece a versão que já tem homologação
            if n not in vistos or (vistos[n].get('homologada') is False and r.get('homologada')):
                vistos[n] = r
        sit['do_espelho'] = len(espelho)
        situacoes.append(sit)
        if sit.get('nacional'):
            continue
        if sit['erro']:
            avisos.append(f'{sit["modalidade"]}: {sit["erro"]}')
        elif not sit['completa'] and sit['total_paginas']:
            if sit['total_paginas'] > MAX_PAGINAS_VARREDURA:
                avisos.append(
                    f'{sit["modalidade"]}: {sit["total_registros"]} publicações no período — acima do limite de '
                    f'{MAX_PAGINAS_VARREDURA * 50}. Reduza o período para cobrir tudo.'
                )
            else:
                avisos.append(
                    f'{sit["modalidade"]}: varridas {sit["paginas_lidas"]} de {sit["total_paginas"]} páginas '
                    '(o PNCP limita a velocidade de consulta). Clique em Buscar novamente para continuar de onde parou.'
                )

    universo = list(vistos.values())
    if nacional:
        avisos.append(
            'Busca em todo o Brasil: cobre as contratações publicadas pelo Compras.gov.br. '
            'Para incluir estados e municípios de outras plataformas, escolha uma UF.'
        )
    sem_resultado = sum(1 for r in universo if r.get('homologada') is False)
    universo = [r for r in universo if r.get('homologada') is not False]
    universo, ocultos = filtrar_natureza(universo, natureza, lambda r: r['objeto'])
    if sem_resultado:
        ocultos['sem preço homologado'] = sem_resultado
    achados = ranquear(universo, termo, 'objeto', minimo=similaridade_minima if termo.strip() else 0)
    if len(achados) > MAX_RESULTADOS:
        achados = achados[:MAX_RESULTADOS]
    return achados, avisos, situacoes, ocultos


def _partes_controle(numero_controle: str):
    """'07777800000162-1-000038/2026' → ('07777800000162', 2026, 38)."""
    import re
    m = re.fullmatch(r'(\d{14})-\d+-(\d{1,6})/(\d{4})', (numero_controle or '').strip())
    if not m:
        return None
    return m.group(1), int(m.group(3)), int(m.group(2))


def itens_homologados(numero_controle: str) -> list[dict]:
    """
    Itens de uma contratação com o valor unitário HOMOLOGADO de cada fornecedor
    (GET /orgaos/{cnpj}/compras/{ano}/{seq}/itens e .../itens/{n}/resultados).
    Itens sem resultado não entram: valor estimado de edital não é preço praticado.
    """
    partes = _partes_controle(numero_controle)
    if not partes:
        raise ValueError('Número de controle PNCP inválido.')
    cnpj, ano, seq = partes
    timeout = _get_timeout()
    base = f'{PNCP_ITENS_BASE}/orgaos/{cnpj}/compras/{ano}/{seq}/itens'
    itens = []
    for pagina in range(1, 11):
        lote = _get_json_pncp(f'{base}?pagina={pagina}&tamanhoPagina=500', timeout) or []
        itens.extend(lote)
        if len(lote) < 500:
            break

    saida = []
    for item in [i for i in itens if i.get('temResultado')][:150]:
        for r in (_get_json_pncp(f'{base}/{int(item["numeroItem"])}/resultados', timeout) or []):
            valor = _dec(r.get('valorUnitarioHomologado'))
            if not valor or valor <= 0 or r.get('dataCancelamento') or r.get('moedaEstrangeira'):
                continue
            saida.append({
                'numero_item': int(item['numeroItem']),
                'descricao': (item.get('descricao') or '')[:500],
                'unidade_medida': (item.get('unidadeMedida') or '')[:30],
                'quantidade': _dec(r.get('quantidadeHomologada')),
                'valor_unitario': valor,
                'fornecedor': (r.get('nomeRazaoSocialFornecedor') or '')[:200],
                'fornecedor_ni': (r.get('niFornecedor') or '')[:20],
                'data_referencia': _data(r.get('dataInclusao')),
            })
    return saida


def buscar_preview(data_ini: date, data_fim: date,
                   cnpj: str = '', uf: str = '',
                   termo: str = '',
                   incluir_contratos: bool = True,
                   incluir_atas: bool = True,
                   modalidades=(6,), natureza: str = 'qualquer') -> dict:
    """
    Consulta o PNCP e retorna preview sem salvar nada.
    Sem CNPJ: contratações filtradas por UF + modalidade no servidor e palavra-chave
    (obrigatória) na varredura. Atas pelo PNCP só com CNPJ — sem ele, atas de RP vêm
    pela pesquisa por código CATMAT/CATSER (painel Compras.gov.br).
    """
    from .similaridade import ranquear, filtrar_natureza
    registros, erros, situacoes, ocultos = [], [], [], {}

    if incluir_contratos:
        try:
            achados, avisos, situacoes, ocultos = buscar_contratacoes(
                data_ini, data_fim, uf=uf, cnpj=cnpj, termo=termo,
                modalidades=modalidades, natureza=natureza,
            )
            registros.extend(achados)
            erros.extend(avisos)
        except Exception as e:
            erros.append(f'Contratações: {e}')
            logger.warning('PNCP buscar_contratacoes erro: %s', e)

    if incluir_atas:
        if not cnpj:
            erros.append(
                'Atas de RP pelo PNCP exigem CNPJ (a API não filtra UF nem objeto). Para atas sem CNPJ, '
                'use "Pesquisar preços no Compras.gov.br" pelo código CATMAT/CATSER — inclui atas de todo o país.'
            )
        else:
            try:
                resp = PNCPClient().buscar_atas(data_ini, data_fim, cnpj=cnpj)
                atas = [_normalizar_ata(item) for item in (resp.get('data') or [])]
                atas, ocultos_atas = filtrar_natureza(atas, natureza, lambda r: r['objeto'])
                for k, v in ocultos_atas.items():
                    ocultos[k] = ocultos.get(k, 0) + v
                registros.extend(ranquear(atas, termo, 'objeto', minimo=40 if termo.strip() else 0))
            except Exception as e:
                erros.append(f'Atas: o PNCP não respondeu ({getattr(e, "reason", e)}). Tente novamente ou reduza o período.')
                logger.warning('PNCP buscar_atas erro: %s', e)

    return {'total': len(registros), 'registros': registros, 'erros': erros, 'varredura': situacoes,
            'ocultos_natureza': ocultos}


class ImportadorPNCP:
    """
    Executa a importação de registros PNCP selecionados para um Mapa de Preços.
    Cria FonteConsultada (tipo II) + PrecoColetado para cada registro importado.
    """

    def executar(self, importacao, ids_selecionados: list[int]) -> dict:
        from modulo_mapa_precos.models import FonteConsultada, PrecoColetado, ItemMapa
        from .models import PNCPRegistro

        importacao.status = 'em_andamento'
        importacao.save(update_fields=['status'])

        mapa     = importacao.mapa
        usuario  = importacao.created_by
        log      = []
        importados = 0

        # Item destino escolhido na tela (pncp_confirmar); senão, o primeiro do mapa
        item_mapa = getattr(importacao, '_item_override', None) or mapa.itens.first()
        if not item_mapa:
            importacao.status = 'erro'
            importacao.erro_mensagem = (
                'O mapa não possui itens cadastrados. '
                'Adicione ao menos um item antes de importar do PNCP.'
            )
            importacao.save(update_fields=['status', 'erro_mensagem'])
            return {'importados': 0, 'erros': [importacao.erro_mensagem]}

        registros = PNCPRegistro.objects.filter(
            importacao=importacao,
            id__in=ids_selecionados,
            importado=False,
        )

        for reg in registros:
            try:
                # Cria ou reutiliza a FonteConsultada tipo II para esta importação
                fonte, _ = FonteConsultada.objects.get_or_create(
                    mapa=mapa,
                    tipo=importacao.tipo_fonte,
                    referencia=f'PNCP — Importação #{importacao.pk}',
                    defaults={
                        'descricao': (
                            f'Importado do PNCP em {importacao.created_at.strftime("%d/%m/%Y") if importacao.created_at else "—"}. '
                            f'Período: {importacao.periodo_inicio} a {importacao.periodo_fim}.'
                        ),
                        'data_consulta': importacao.periodo_fim,
                        'infrutífera': False,
                    }
                )

                # Só preço unitário entra no mapa: o valor global de um contrato/ata não é
                # preço do item e distorceria a estimativa (sobrepreço).
                valor_unit = reg.valor_unitario
                if not valor_unit or valor_unit <= 0:
                    log.append(
                        f'✗ {reg.numero_pncp or reg.objeto[:40]}: sem preço unitário no PNCP '
                        f'(valor global R$ {reg.valor_global or "—"} não é preço do item). '
                        'Use a consulta Compras.gov.br por CATMAT/CATSER.'
                    )
                    continue

                preco = PrecoColetado.objects.create(
                    item=item_mapa,
                    fonte=fonte,
                    valor_unitario=valor_unit,
                    origem_orgao_empresa=reg.orgao_nome[:255] if reg.orgao_nome else 'PNCP',
                    numero_certame=reg.numero_certame[:100] if reg.numero_certame else '',
                    data_referencia=reg.data_referencia or importacao.periodo_fim,
                    valido=True,
                    observacao=(
                        f'Importado do PNCP. Objeto: {reg.objeto[:200]}. '
                        f'Modalidade: {reg.modalidade}. '
                        f'Valor global: R$ {reg.valor_global or "—"}.'
                    ),
                )

                reg.preco_coletado = preco
                reg.importado = True
                reg.save(update_fields=['preco_coletado', 'importado'])

                importados += 1
                log.append(f'✓ {reg.numero_pncp or reg.objeto[:40]} — R$ {valor_unit}')

            except Exception as e:
                log.append(f'✗ {reg.numero_pncp}: {e}')
                logger.exception('Erro ao importar registro PNCP %s', reg.pk)

        importacao.status = 'concluida'
        importacao.total_importados = importados
        importacao.log = log
        importacao.save(update_fields=['status', 'total_importados', 'log'])

        return {'importados': importados, 'log': log}
