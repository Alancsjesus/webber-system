"""
ChecklistEngine — avaliador de completude de artefatos de planejamento.

Regras são declarativas: apenas o engine decide o que bloqueia a submissão.
Todos os campos avaliados são opcionais no banco (blank=True, null=True).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional, Any


# ─── Estruturas de dados ──────────────────────────────────────────────────────

@dataclass
class RegraChecklist:
    campo: str
    descricao: str
    base_legal: str = ''
    obrigatorio: bool = False
    avaliador: Optional[Callable[[Any], tuple[bool, str]]] = field(default=None, repr=False)


@dataclass
class ResultadoRegra:
    campo: str
    descricao: str
    base_legal: str
    obrigatorio: bool
    ok: bool
    detalhe: str = ''


@dataclass
class ResultadoChecklist:
    score: int
    total: int
    bloqueadores: list[ResultadoRegra]
    avisos: list[ResultadoRegra]
    pode_submeter: bool

    @property
    def percentual(self) -> int:
        return round(self.score * 100 / self.total) if self.total else 100


# ─── Avaliadores reutilizáveis ────────────────────────────────────────────────

def _nao_vazio(obj: Any, campo: str) -> tuple[bool, str]:
    """Campo texto ou FK: verdadeiro se preenchido."""
    val = getattr(obj, campo, None)
    if val is None or val == '' or val == []:
        return False, 'Campo não preenchido.'
    return True, ''


def _nao_nulo(obj: Any, campo: str) -> tuple[bool, str]:
    """BooleanField com null=True: verdadeiro se não for None."""
    val = getattr(obj, campo, None)
    if val is None:
        return False, 'Campo não respondido (Sim/Não).'
    return True, ''


def _avaliador_pca(obj: Any, _: str) -> tuple[bool, str]:
    """PCA: OK se previsto=True OU (previsto=False e justificativa preenchida)."""
    previsto = getattr(obj, 'pca_previsto', None)
    if previsto is None:
        return False, 'Indicar se a contratação consta no PCA.'
    if previsto is False:
        justif = getattr(obj, 'pca_justificativa_ausencia', '')
        if not justif:
            return False, 'Previsão ausente no PCA exige justificativa.'
    return True, ''


def _avaliador_classificacao_sensivel(obj: Any, _: str) -> tuple[bool, str]:
    """ETP sensível: deve ser respondido (True/False); se True, justificativa obrigatória."""
    val = getattr(obj, 'classificacao_sensivel', None)
    if val is None:
        return False, 'Avaliação de sigilo não respondida.'
    if val is True:
        justif = getattr(obj, 'classificacao_sensivel_justificativa', '')
        if not justif:
            return False, 'ETP classificado como sensível exige justificativa.'
    return True, ''


def _avaliador_qualificacao_juridica(obj: Any, _: str) -> tuple[bool, str]:
    """Qualificação jurídica: OK se preenchida OU suprimida com justificativa."""
    texto = getattr(obj, 'qualificacao_juridica', '')
    suprimida = getattr(obj, 'qualificacao_juridica_suprimida', None)
    if texto:
        return True, ''
    if suprimida is True:
        justif = getattr(obj, 'qualificacao_juridica_suprimida_justificativa', '')
        if justif:
            return True, ''
        return False, 'Supressão de qualificação jurídica exige justificativa.'
    return False, 'Informar requisitos de qualificação jurídica ou justificar supressão.'


def _avaliador_qualificacao_economica(obj: Any, _: str) -> tuple[bool, str]:
    """Qualificação econômico-financeira: OK se preenchida OU dispensada."""
    texto = getattr(obj, 'qualificacao_economica', '')
    dispensada = getattr(obj, 'qualificacao_economica_dispensada', None)
    if texto:
        return True, ''
    if dispensada is True:
        return True, ''
    return False, 'Informar requisitos de qualificação econômico-financeira ou marcar como dispensada (IN SAEB 010/2024).'


def _avaliador_consorcio(obj: Any, _: str) -> tuple[bool, str]:
    """Consórcio: deve ser respondido; vedação requer justificativa."""
    val = getattr(obj, 'permite_consorcio', None)
    if val is None:
        return False, 'Indicar se permite participação de consórcios (Lei 14.133, art. 15).'
    if val is False:
        justif = getattr(obj, 'permite_consorcio_justificativa', '')
        if not justif:
            return False, 'Vedação de consórcios exige justificativa.'
    return True, ''


def _avaliador_itens_simpas(obj: Any, _: str) -> tuple[bool, str]:
    """DFD: pelo menos um item deve ter item_catalogo (com código SIMPAS)."""
    try:
        total = obj.itens.count()
        if total == 0:
            return False, 'Nenhum item cadastrado no DFD.'
        com_catalogo = obj.itens.filter(item_catalogo__isnull=False).count()
        if com_catalogo == 0:
            return False, f'Nenhum dos {total} itens está vinculado ao catálogo (SIMPAS).'
        if com_catalogo < total:
            sem = total - com_catalogo
            return True, f'{sem} item(ns) sem código SIMPAS.'
        return True, ''
    except Exception:
        return False, 'Erro ao verificar itens do DFD.'


def _avaliador_fiscal_contrato(obj: Any, _: str) -> tuple[bool, str]:
    """DFD: fiscal do contrato deve estar indicado."""
    val = getattr(obj, 'fiscal_contrato_id', None)
    if not val:
        return False, 'Fiscal do contrato não indicado.'
    return True, ''


def _avaliador_parcelamento_etp(obj: Any, _: str) -> tuple[bool, str]:
    """ETP: tipo de parcelamento e justificativa devem estar preenchidos."""
    tipo = getattr(obj, 'tipo_parcelamento', '')
    justif = getattr(obj, 'parcelamento_justificativa', '')
    if not tipo:
        return False, 'Tipo de parcelamento não selecionado.'
    if not justif:
        return False, 'Justificativa do parcelamento/lote único não preenchida.'
    return True, ''


def _avaliador_estimativa_etp(obj: Any, _: str) -> tuple[bool, str]:
    """ETP: estimativa de valor deve estar preenchida."""
    val = getattr(obj, 'estimativa_valor', None)
    if val is None:
        return False, 'Estimativa de valor não preenchida.'
    return True, ''


def _avaliador_prazo_vigencia_tr(obj: Any, _: str) -> tuple[bool, str]:
    """TR: tipo de prazo de vigência deve ser selecionado."""
    val = getattr(obj, 'tipo_prazo_vigencia', '')
    if not val:
        return False, 'Tipo de prazo de vigência não selecionado.'
    return True, ''


# ─── Regras por artefato ──────────────────────────────────────────────────────

REGRAS_DFD: list[RegraChecklist] = [
    RegraChecklist(
        campo='unidade_demandante',
        descricao='Unidade demandante identificada',
        base_legal='',
        obrigatorio=False,
        avaliador=lambda obj, c: (_nao_nulo(obj, 'unidade_demandante_id')),
    ),
    RegraChecklist(
        campo='itens_com_simpas',
        descricao='Itens vinculados ao catálogo (código SIMPAS)',
        base_legal='Decreto 22.886/2024, Art. 5º, I',
        obrigatorio=False,
        avaliador=_avaliador_itens_simpas,
    ),
    RegraChecklist(
        campo='fiscal_contrato',
        descricao='Fiscal do contrato indicado',
        base_legal='Lei 14.133/2021, art. 117',
        obrigatorio=False,
        avaliador=_avaliador_fiscal_contrato,
    ),
    RegraChecklist(
        campo='pca_previsto',
        descricao='Previsão no PCA ou justificativa de ausência',
        base_legal='Lei 14.133, art. 12, VII',
        obrigatorio=False,
        avaliador=_avaliador_pca,
    ),
    RegraChecklist(
        campo='local_entrega',
        descricao='Local de entrega/execução informado',
        base_legal='',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_vazio(obj, 'local_entrega'),
    ),
]

REGRAS_ETP: list[RegraChecklist] = [
    RegraChecklist(
        campo='necessidade_contratacao',
        descricao='Necessidade da contratação descrita',
        base_legal='Lei 14.133, art. 18, §1º, I',
        obrigatorio=True,
        avaliador=lambda obj, c: _nao_vazio(obj, 'necessidade_contratacao'),
    ),
    RegraChecklist(
        campo='estimativa_valor',
        descricao='Estimativa das quantidades e valor',
        base_legal='Lei 14.133, art. 18, §1º, IV e VI',
        obrigatorio=True,
        avaliador=_avaliador_estimativa_etp,
    ),
    RegraChecklist(
        campo='parcelamento',
        descricao='Parcelamento/lote único com justificativa',
        base_legal='Lei 14.133, art. 18, §1º, VIII e art. 40, V',
        obrigatorio=True,
        avaliador=_avaliador_parcelamento_etp,
    ),
    RegraChecklist(
        campo='posicionamento_conclusivo',
        descricao='Posicionamento conclusivo',
        base_legal='Lei 14.133, art. 18, §1º, XIII',
        obrigatorio=True,
        avaliador=lambda obj, c: _nao_vazio(obj, 'posicionamento_conclusivo'),
    ),
    RegraChecklist(
        campo='classificacao_sensivel',
        descricao='Avaliação de sigilo do ETP',
        base_legal='Decreto 22.598/2024, art. 8º',
        obrigatorio=True,
        avaliador=_avaliador_classificacao_sensivel,
    ),
    RegraChecklist(
        campo='descricao_solucao',
        descricao='Descrição da solução escolhida',
        base_legal='Lei 14.133, art. 18, §1º, V',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_vazio(obj, 'descricao_solucao'),
    ),
    RegraChecklist(
        campo='alinhamento_planesp',
        descricao='Alinhamento ao PLANESP/PCA',
        base_legal='Específico SSP-BA',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_vazio(obj, 'alinhamento_planesp'),
    ),
    RegraChecklist(
        campo='contratacoes_correlatas',
        descricao='Contratações correlatas/interdependentes',
        base_legal='Lei 14.133, art. 18, §1º, XI',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_vazio(obj, 'contratacoes_correlatas'),
    ),
    RegraChecklist(
        campo='impacto_ambiental',
        descricao='Impactos ambientais e medidas mitigadoras',
        base_legal='Lei 14.133, art. 18, §1º, XII',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_vazio(obj, 'impacto_ambiental'),
    ),
    RegraChecklist(
        campo='providencias_pre_contrato',
        descricao='Providências antes da celebração do contrato',
        base_legal='Lei 14.133, art. 18, §1º, X',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_vazio(obj, 'providencias_pre_contrato'),
    ),
]

REGRAS_TR: list[RegraChecklist] = [
    RegraChecklist(
        campo='objeto_contratacao',
        descricao='Objeto da contratação descrito',
        base_legal='Lei 14.133, art. 6º, XXIII, a',
        obrigatorio=True,
        avaliador=lambda obj, c: _nao_vazio(obj, 'objeto_contratacao'),
    ),
    RegraChecklist(
        campo='tipo_prazo_vigencia',
        descricao='Tipo de prazo de vigência selecionado',
        base_legal='Lei 14.133, art. 40, §1º, II',
        obrigatorio=True,
        avaliador=_avaliador_prazo_vigencia_tr,
    ),
    RegraChecklist(
        campo='adequacao_orcamentaria',
        descricao='Adequação orçamentária informada',
        base_legal='Lei 14.133, art. 6º, XXIII, j',
        obrigatorio=True,
        avaliador=lambda obj, c: _nao_vazio(obj, 'adequacao_orcamentaria'),
    ),
    RegraChecklist(
        campo='permite_consorcio',
        descricao='Posição sobre participação de consórcios',
        base_legal='Lei 14.133, art. 15',
        obrigatorio=False,
        avaliador=_avaliador_consorcio,
    ),
    RegraChecklist(
        campo='qualificacao_juridica',
        descricao='Qualificação jurídica exigida ou suprimida com justificativa',
        base_legal='Lei 14.133, art. 62, I',
        obrigatorio=False,
        avaliador=_avaliador_qualificacao_juridica,
    ),
    RegraChecklist(
        campo='qualificacao_economica',
        descricao='Qualificação econômico-financeira ou dispensa fundamentada',
        base_legal='Lei 14.133, art. 62, IV + IN SAEB 010/2024',
        obrigatorio=False,
        avaliador=_avaliador_qualificacao_economica,
    ),
    RegraChecklist(
        campo='local_entrega',
        descricao='Local de entrega/execução informado',
        base_legal='',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_vazio(obj, 'local_entrega'),
    ),
    RegraChecklist(
        campo='prazo_recebimento_provisorio_dias',
        descricao='Prazo de recebimento provisório definido',
        base_legal='IN SEGES/ME 77/2022',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_nulo(obj, 'prazo_recebimento_provisorio_dias'),
    ),
    RegraChecklist(
        campo='prazo_pagamento_dias',
        descricao='Prazo de pagamento definido',
        base_legal='IN SEGES/ME 77/2022',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_nulo(obj, 'prazo_pagamento_dias'),
    ),
    RegraChecklist(
        campo='degrau_lances',
        descricao='Degrau mínimo entre lances definido',
        base_legal='Lei 14.133, art. 57',
        obrigatorio=False,
        avaliador=lambda obj, c: _nao_nulo(obj, 'degrau_lances'),
    ),
]


# ─── Engine ───────────────────────────────────────────────────────────────────

class ChecklistEngine:
    """
    Avalia um objeto (DFD, ETP ou TR) contra um conjunto de regras declarativas.

    Uso:
        resultado = ChecklistEngine.avaliar_etp(etp_instance)
        resultado.pode_submeter  # True se não há bloqueadores pendentes
        resultado.bloqueadores   # list[ResultadoRegra] obrigatórios não-OK
        resultado.avisos         # list[ResultadoRegra] recomendados não-OK
    """

    @classmethod
    def _avaliar(cls, obj: Any, regras: list[RegraChecklist]) -> ResultadoChecklist:
        bloqueadores: list[ResultadoRegra] = []
        avisos: list[ResultadoRegra] = []
        score = 0

        for regra in regras:
            avaliador = regra.avaliador or (lambda o, c: _nao_vazio(o, c))
            try:
                ok, detalhe = avaliador(obj, regra.campo)
            except Exception as exc:
                ok, detalhe = False, f'Erro na avaliação: {exc}'

            if ok:
                score += 1

            resultado = ResultadoRegra(
                campo=regra.campo,
                descricao=regra.descricao,
                base_legal=regra.base_legal,
                obrigatorio=regra.obrigatorio,
                ok=ok,
                detalhe=detalhe,
            )

            if not ok:
                if regra.obrigatorio:
                    bloqueadores.append(resultado)
                else:
                    avisos.append(resultado)

        return ResultadoChecklist(
            score=score,
            total=len(regras),
            bloqueadores=bloqueadores,
            avisos=avisos,
            pode_submeter=len(bloqueadores) == 0,
        )

    @classmethod
    def avaliar_dfd(cls, dfd) -> ResultadoChecklist:
        return cls._avaliar(dfd, REGRAS_DFD)

    @classmethod
    def avaliar_etp(cls, etp) -> ResultadoChecklist:
        return cls._avaliar(etp, REGRAS_ETP)

    @classmethod
    def avaliar_tr(cls, tr) -> ResultadoChecklist:
        return cls._avaliar(tr, REGRAS_TR)
