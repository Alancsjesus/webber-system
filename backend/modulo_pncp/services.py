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
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


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


def buscar_preview(data_ini: date, data_fim: date,
                   cnpj: str = '', uf: str = '',
                   termo: str = '',
                   incluir_contratos: bool = True,
                   incluir_atas: bool = True) -> dict:
    """
    Consulta a API do PNCP e retorna preview sem salvar nada.
    Usada pelo frontend para o usuário validar antes de importar.
    """
    client = PNCPClient()
    registros = []
    erros = []

    # A API do PNCP não tem parâmetro de UF em /contratos nem em /atas — sem
    # CNPJ, a página consultada vem de um universo nacional de ~300-600 mil
    # registros no período, e a chance de algum bater com o objeto/UF
    # procurados é próxima de zero. Avisar de antemão em vez de deixar o
    # usuário concluir errado que "não tem resultado" ou esperar um timeout.
    if not cnpj and (incluir_contratos or incluir_atas):
        erros.append(
            'Sem CNPJ, o PNCP retorna uma amostra de todo o Brasil (centenas de milhares de '
            'registros no período) — UF e palavra-chave só filtram essa amostra pequena, '
            'não a busca em si. Informe o CNPJ do órgão de referência para resultados relevantes.'
        )

    if incluir_contratos:
        # Contratos usa timeout reduzido (8s) — sem filtro de objeto tende a ser lento
        # Resultado parcial é aceito: se timeout, atas ainda funcionam
        try:
            resp = client.buscar_contratos(
                data_ini, data_fim, cnpj=cnpj,
                termo=termo, timeout_override=12,
            )
            for item in (resp.get('data') or []):
                registros.append(_normalizar_contrato(item))
        except TimeoutError:
            erros.append(
                'Contratos: a API do PNCP não respondeu a tempo. Informe o CNPJ do órgão '
                'de referência (é o único filtro que reduz o volume nesse endpoint) ou '
                'desmarque "Contratos" e consulte apenas Atas de RP.'
            )
            logger.warning('PNCP buscar_contratos timeout')
        except Exception as e:
            code = getattr(e, 'code', None)
            if code in (422, 400):
                erros.append(
                    'Contratos: parâmetros rejeitados pela API do PNCP. '
                    'Reduza o período ou informe o CNPJ do órgão.'
                )
            else:
                erros.append(f'Contratos: {e}')
            logger.warning('PNCP buscar_contratos erro: %s', e)

    if incluir_atas:
        try:
            resp = client.buscar_atas(data_ini, data_fim, cnpj=cnpj)
            for item in (resp.get('data') or []):
                registros.append(_normalizar_ata(item))
        except TimeoutError:
            erros.append(
                'Atas: timeout na API do PNCP. Informe o CNPJ do órgão de referência — '
                'é o único filtro que esse endpoint aceita além do período.'
            )
        except Exception as e:
            code = getattr(e, 'code', None)
            if code == 422:
                erros.append(
                    'Atas: a API do PNCP retornou 422 — muitos registros ou parâmetros inválidos. '
                    'Reduza o período para ≤ 90 dias ou informe o CNPJ do órgão.'
                )
            elif code == 400:
                erros.append(f'Atas: parâmetro inválido na API do PNCP (400). Detalhe: {e}')
            else:
                erros.append(f'Atas: {e}')
            logger.warning('PNCP buscar_atas erro: %s', e)

    if uf:
        registros = _filtrar_uf(registros, uf)
    if termo:
        registros = _filtrar_termo(registros, termo)

    return {
        'total': len(registros),
        'registros': registros,
        'erros': erros,
    }


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

        # Garante que existe ao menos um item no mapa para vincular os preços
        item_mapa = mapa.itens.first()
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
                        'infrutifera': False,
                    }
                )

                # Calcula valor unitário: usa o informado; se não houver, usa valor_global
                valor_unit = reg.valor_unitario or reg.valor_global

                preco = PrecoColetado.objects.create(
                    item=item_mapa,
                    fonte=fonte,
                    valor_unitario=valor_unit or Decimal('0'),
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
