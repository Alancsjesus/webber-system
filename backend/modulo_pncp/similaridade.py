"""
Similaridade entre o objeto demandado (palavra-chave ou descrição do item) e o
objeto/descrição de cada resultado de pesquisa de preços.

Tudo local, sem biblioteca nem serviço externo:
  * normaliza (minúsculas, sem acento, só letras/números) e descarta palavras
    genéricas de edital ("aquisição", "registro de preços", "eventual"...);
  * reduz plurais simples (coletes → colete, balísticos → balistico);
  * números contam (24.000 = 24000) e só casam se forem iguais;
  * cada termo da consulta casa com o melhor termo do resultado: igual (1,0),
    prefixo com 4+ letras (0,9) ou grafia próxima (até 0,85, cobre erros de digitação);
  * termos raros no universo pesquisado pesam mais (IDF): "balistico" vale mais que "material".
A nota (0–100) é a parcela ponderada do objeto demandado encontrada no resultado.
"""
import math
import re
import unicodedata
from difflib import SequenceMatcher

STOPWORDS = {
    'a', 'o', 'as', 'os', 'e', 'ou', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas',
    'para', 'pra', 'por', 'pelo', 'pela', 'com', 'sem', 'sob', 'um', 'uma', 'uns', 'umas', 'ao', 'aos',
    'que', 'se', 'sua', 'seu', 'suas', 'seus', 'ate', 'tipo', 'via', 'cada', 'conforme', 'demais',
    # jargão de edital que aparece em quase todo objeto
    'aquisicao', 'aquisicoe', 'contratacao', 'contratacoe', 'registro', 'preco', 'futura', 'futuro',
    'eventual', 'eventuai', 'fornecimento', 'empresa', 'especializada', 'prestacao', 'objeto', 'visando',
    'atender', 'atendimento', 'demanda', 'necessidade', 'secretaria', 'municipal', 'municipio', 'estadual',
    'edital', 'termo', 'referencia', 'anexo', 'quantidade', 'especificacoe', 'lote', 'iten', 'item',
    'unidade', 'destinado', 'destinada', 'atraves', 'selecao', 'proposta', 'vantajosa', 'melhor',
    'resultado', 'apta', 'gerar', 'pregao', 'eletronico', 'dispensa', 'licitacao', 'processo', 'mediante',
    'sistema', 'srp', 'pmba', 'ssp', 'diversos', 'diversas', 'geral', 'gerai', 'uso',
}


def _sem_acento(txt: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', txt or '') if unicodedata.category(c) != 'Mn').lower()


def _radical(t: str) -> str:
    """Plural → singular, só os casos regulares do português."""
    if len(t) <= 3:
        return t
    for suf, novo in (('oes', 'ao'), ('aes', 'ao'), ('ais', 'al'), ('eis', 'el'), ('ois', 'ol'), ('ns', 'm')):
        if t.endswith(suf):
            return t[:-len(suf)] + novo
    if t.endswith('res') or t.endswith('zes') or t.endswith('ses'):
        return t[:-2]
    if t.endswith('s'):
        return t[:-1]
    return t


def tokens(txt: str) -> list[str]:
    # "24.000" → "24000": capacidade/medida conta e precisa bater exatamente
    norm = re.sub(r'(?<=\d)[.](?=\d{3}\b)', '', _sem_acento(txt))
    brutos = re.findall(r'[a-z0-9]+', norm)
    out = []
    for b in brutos:
        if len(b) < 2 or (b.isdigit() and int(b) == 0):
            continue
        if b.isdigit():
            out.append(b)
            continue
        r = _radical(b)
        if r not in STOPWORDS and b not in STOPWORDS:
            out.append(r)
    return out


def _parecido(q: str, t: str) -> float:
    if q == t:
        return 1.0
    if q.isdigit() or t.isdigit():
        return 0.0
    if len(q) >= 4 and len(t) >= 4 and (t.startswith(q) or q.startswith(t)):
        return 0.9
    if abs(len(q) - len(t)) > 3 or len(q) < 5:
        return 0.0
    m = SequenceMatcher(None, q, t)
    if m.real_quick_ratio() < 0.8 or m.quick_ratio() < 0.8:
        return 0.0
    r = m.ratio()
    return round(r * 0.85, 3) if r >= 0.8 else 0.0


class Ranqueador:
    """
    Pré-computa, para cada termo da consulta, a afinidade com todo o vocabulário do
    universo (uma vez só), e a partir daí pontua cada texto com consultas a dicionário.
    """

    def __init__(self, consulta: str, universo: list[str]):
        self.consulta = list(dict.fromkeys(tokens(consulta)))
        docs = [set(tokens(t)) for t in universo]
        n = max(len(docs), 1)
        df = {}
        for d in docs:
            for t in d:
                df[t] = df.get(t, 0) + 1
        vocab = set(df) | set(self.consulta)
        # IDF suavizado. Termo que não aparece em nenhum resultado (ex.: "nível III-A",
        # detalhe de especificação ausente dos objetos de edital) não diferencia ninguém:
        # peso baixo, para não derrubar todas as notas abaixo do corte.
        self.peso = {
            q: (math.log((n + 1) / (df[q] + 0.5)) + 1) if df.get(q) else 0.3
            for q in self.consulta
        }
        self.afinidade = {
            q: {t: s for t in vocab if (s := _parecido(q, t)) > 0}
            for q in self.consulta
        }
        self._cache_docs = dict(zip(universo, docs))

    def nota(self, texto: str) -> int:
        if not self.consulta:
            return 0
        doc = self._cache_docs.get(texto)
        if doc is None:
            doc = set(tokens(texto))
        total = sum(self.peso.values())
        obtido = 0.0
        for q in self.consulta:
            af = self.afinidade[q]
            melhor = max((af.get(t, 0.0) for t in doc), default=0.0)
            obtido += self.peso[q] * melhor
        return round(100 * obtido / total) if total else 0


def ranquear(registros: list[dict], consulta: str, campo: str, minimo: int = 0) -> list[dict]:
    """Adiciona 'similaridade' a cada registro, filtra pelo mínimo e ordena (nota desc)."""
    if not tokens(consulta):
        for r in registros:
            r['similaridade'] = None
        return registros
    rq = Ranqueador(consulta, [r.get(campo) or '' for r in registros])
    for r in registros:
        r['similaridade'] = rq.nota(r.get(campo) or '')
    saida = [r for r in registros if r['similaridade'] >= minimo]
    saida.sort(key=lambda r: (-r['similaridade'], -(int(str(r.get('data_referencia') or '0000-00-00').replace('-', '')[:8] or 0))))
    return saida


# ── Natureza da contratação: aquisição × locação × serviço ───────────────────
# Cruzamento do objeto demandado com o objeto de cada resultado, para não
# apresentar locação no lugar de aquisição (e vice-versa). Prefixos cobrem
# flexões e abreviações comuns em edital ("prest. de serv. de instalaç...").
NATUREZAS = {
    'locacao':   re.compile(r'\b(loca(cao|coes|r|da|do|das|dos)\b|alug|arrendament|comodato)'),
    'servico':   re.compile(r'\b(manuten|instala|desinstala|reparo|conserto|assistencia tecnica|higieniza'
                            r'|limpeza|recarga|remanejament|presta|servic|serv\b)'),
    'aquisicao': re.compile(r'\b(aquisi|adquiri|compra|fornecimento)'),
}
NATUREZA_ROTULO = {'aquisicao': 'Aquisição', 'locacao': 'Locação', 'servico': 'Serviço', 'qualquer': 'Qualquer'}


def naturezas(texto: str) -> set[str]:
    alvo = _sem_acento(texto)
    return {n for n, rx in NATUREZAS.items() if rx.search(alvo)}


def natureza_demanda(*textos) -> tuple[str, str]:
    """
    Natureza do objeto demandado: o primeiro texto (na ordem recebida) que indicar
    uma natureza decide. Locação/serviço prevalecem sobre aquisição quando o mesmo
    texto traz as duas ("locação com fornecimento de..."). Sem indicação, assume
    aquisição — o caso mais comum — e a tela permite trocar.
    """
    for i, t in enumerate(textos):
        ns = naturezas(t or '')
        for n in ('locacao', 'servico', 'aquisicao'):
            if n in ns:
                return n, i
    return 'aquisicao', -1


def compativel(demanda: str, texto: str) -> bool:
    """Resultado sem natureza identificável é mantido; com natureza, precisa conter a demandada."""
    if demanda == 'qualquer':
        return True
    ns = naturezas(texto)
    return not ns or demanda in ns


def filtrar_natureza(registros: list[dict], demanda: str, texto_de) -> tuple[list[dict], dict]:
    """Mantém os compatíveis e conta os ocultados por natureza encontrada."""
    mantidos, ocultos = [], {}
    for r in registros:
        texto = texto_de(r)
        ns = naturezas(texto)
        r['natureza'] = sorted(ns)
        if compativel(demanda, texto):
            mantidos.append(r)
        else:
            chave = '/'.join(NATUREZA_ROTULO[n] for n in sorted(ns))
            ocultos[chave] = ocultos.get(chave, 0) + 1
    return mantidos, ocultos
