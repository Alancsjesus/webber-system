"""
DocumentEngine — gera texto de artefatos (DFD, ETP, TR) a partir de campos
estruturados, usando templates Jinja2 configuráveis por SecaoArtefato
(campo `template_texto`).

Seções sem template_texto preenchido caem em um valor padrão calculado
diretamente do campo/contexto homônimo ao `codigo` da seção — mesma
estratégia usada hoje (sem templates) em exportacao/pdf_utils.py.
"""
from __future__ import annotations
import jinja2

_ENV = jinja2.Environment(undefined=jinja2.ChainableUndefined, autoescape=False)


def _fmt_valor(v):
    try:
        return f'R$ {float(v):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (TypeError, ValueError):
        return ''


def _get_secoes_ativas(tipo, modalidade=None):
    """Seções ativas de um tipo de artefato, filtradas por modalidade quando aplicável."""
    from core.models import SecaoArtefato
    qs = list(SecaoArtefato.objects.filter(tipo=tipo, ativo=True).order_by('ordem'))
    if modalidade and qs:
        qs = [s for s in qs if not s.aplica_modalidades or modalidade in s.aplica_modalidades]
    return qs


# ─── Contextos por tipo de artefato ───────────────────────────────────────────

def _contexto_dfd(dfd) -> dict:
    def _fiscais_texto():
        partes = []
        if dfd.fiscal_contrato_id:
            partes.append(f'Fiscal: {dfd.fiscal_contrato.get_full_name() or dfd.fiscal_contrato.username}')
        if dfd.fiscal_suplente_id:
            partes.append(f'Fiscal suplente: {dfd.fiscal_suplente.get_full_name() or dfd.fiscal_suplente.username}')
        if dfd.gestor_contrato_id:
            partes.append(f'Gestor: {dfd.gestor_contrato.get_full_name() or dfd.gestor_contrato.username}')
        if dfd.gestor_suplente_id:
            partes.append(f'Gestor suplente: {dfd.gestor_suplente.get_full_name() or dfd.gestor_suplente.username}')
        return '\n'.join(partes)

    def _pca_texto():
        if dfd.pca_previsto is True:
            return 'Contratação prevista no Plano de Contratações Anual (PCA), conforme Lei 14.133, art. 12, VII.'
        if dfd.pca_previsto is False:
            just = dfd.pca_justificativa_ausencia or ''
            return f'Não prevista no PCA. Justificativa: {just}' if just else 'Não prevista no PCA.'
        return ''

    def _itens_texto():
        partes = [
            f'- {item.objeto} — {item.quantidade} {item.unidade_medida} — {_fmt_valor(item.valor_total_estimado)}'
            for item in dfd.itens.all()
        ]
        return '\n'.join(partes)

    return {
        'numero_sei':           dfd.numero_sei or '',
        'descricao':            dfd.descricao or '',
        'valor_estimado':       _fmt_valor(dfd.valor_estimado) if dfd.valor_estimado else '',
        'area_aplicacao':       ', '.join(dfd.area_aplicacao or []),
        'prazo_necessidade':    dfd.prazo_necessidade.strftime('%d/%m/%Y') if dfd.prazo_necessidade else '',
        'modalidade_aquisicao': dfd.get_modalidade_aquisicao_display() if dfd.modalidade_aquisicao else '',
        'observacoes':          dfd.observacoes or '',
        'local_entrega':        dfd.local_entrega or '',
        # 'responsaveis' é o codigo padrão da seção (ver setup_dev.py/ArtefatoAdmin);
        # 'fiscais_responsaveis' fica como alias para quem referenciar o nome antigo.
        'responsaveis':         _fiscais_texto(),
        'fiscais_responsaveis': _fiscais_texto(),
        'pca':                  _pca_texto(),
        'itens':                _itens_texto(),
    }


def _contexto_etp(etp) -> dict:
    def _parcelamento_texto():
        partes = []
        tipo_label = dict(etp.PARCELAMENTO_CHOICES).get(etp.tipo_parcelamento, '')
        if tipo_label:
            partes.append(f'Tipo: {tipo_label}')
        if etp.parcelamento_justificativa:
            partes.append(f'Justificativa: {etp.parcelamento_justificativa}')
        return '\n'.join(partes)

    def _cota_meepp_texto():
        partes = []
        if etp.reserva_cota_me_epp:
            partes.append('Reserva de cota de 25% para ME/EPP: SIM (LC 123/2006, Art. 48, III)')
        else:
            partes.append('Reserva de cota de 25% para ME/EPP: NÃO')
            if etp.reserva_cota_justificativa:
                partes.append(f'Justificativa: {etp.reserva_cota_justificativa}')
        if etp.licitacao_exclusiva_me_epp:
            partes.append('Licitação exclusiva ME/EPP: SIM (até R$80.000)')
        return '\n'.join(partes)

    def _classificacao_sensivel_texto():
        val = etp.classificacao_sensivel
        if val is None:
            return ''
        label = 'Sensível' if val else 'Não sensível'
        just = etp.classificacao_sensivel_justificativa or ''
        return f'{label} — {just}' if just else label

    return {
        'numero_sei':                etp.numero_sei or '',
        'necessidade':                etp.necessidade_contratacao or '',
        'requisitos':                 etp.requisitos_contratacao or '',
        'levantamento_mercado':       etp.levantamento_mercado or '',
        'solucao':                    etp.descricao_solucao or '',
        'justificativa':              etp.justificativa_solucao or '',
        'estimativa_valor':           _fmt_valor(etp.estimativa_valor) if etp.estimativa_valor else '',
        'riscos':                     etp.riscos or '',
        'sustentabilidade':           etp.sustentabilidade or '',
        'parcelamento':               _parcelamento_texto(),
        'cota_me_epp':                _cota_meepp_texto(),
        'observacoes':                etp.observacoes or '',
        'posicionamento_conclusivo':  etp.posicionamento_conclusivo or '',
        'classificacao_sensivel':     _classificacao_sensivel_texto(),
        'alinhamento_planesp':        etp.alinhamento_planesp or '',
        'contratacoes_correlatas':    etp.contratacoes_correlatas or '',
        'impacto_ambiental':          etp.impacto_ambiental or '',
        'providencias_pre_contrato':  etp.providencias_pre_contrato or '',
        'compra_vs_locacao':          etp.compra_vs_locacao or '',
    }


def _contexto_tr(tr) -> dict:
    def _permite_consorcio_texto():
        val = tr.permite_consorcio
        if val is None:
            return ''
        partes = ['Permite participação de consórcios (Lei 14.133, art. 15).' if val
                  else 'Veda participação de consórcios.']
        if val is False and tr.permite_consorcio_justificativa:
            partes.append(f'Justificativa: {tr.permite_consorcio_justificativa}')
        return '\n'.join(partes)

    def _qualificacao_juridica_texto():
        if tr.qualificacao_juridica_suprimida:
            just = tr.qualificacao_juridica_suprimida_justificativa or ''
            return f'Suprimida — {just}' if just else 'Suprimida'
        return tr.qualificacao_juridica or ''

    def _qualificacao_economica_texto():
        if tr.qualificacao_economica_dispensada:
            return 'Dispensada'
        return tr.qualificacao_economica or ''

    def _prazos_texto():
        partes = []
        for campo, label in [
            ('prazo_recebimento_provisorio_dias', 'Recebimento Provisório'),
            ('prazo_recebimento_definitivo_dias', 'Recebimento Definitivo'),
            ('prazo_liquidacao_dias',             'Liquidação'),
            ('prazo_pagamento_dias',              'Pagamento'),
            ('prazo_providencia_irregularidade_dias', 'Providência por Irregularidade'),
        ]:
            v = getattr(tr, campo, None)
            if v is not None:
                partes.append(f'{label}: {v} dia(s)')
        return '\n'.join(partes)

    # ── Seções do checklist oficial PGE-BA (seed_secoes_tr.py) ────────────────

    def _cond_gerais_texto():
        partes = []
        if tr.tipo_objeto:
            partes.append(f'Tipo de objeto: {tr.get_tipo_objeto_display()}')
        partes.append(f'Contratação delegada: {"Sim" if tr.contratacao_delegada else "Não"}')
        partes.append(f'Sistema de Registro de Preços (ARP): {"Sim" if tr.sistema_registro_precos else "Não"}')
        return '\n'.join(partes)

    def _fundamentacao_texto():
        partes = []
        if tr.justificativa:
            partes.append(tr.justificativa)
        etp = getattr(tr, 'etp', None)
        if etp and etp.necessidade_contratacao:
            partes.append(f'Necessidade (ETP): {etp.necessidade_contratacao}')
        return '\n'.join(partes)

    def _solucao_texto():
        etp = getattr(tr, 'etp', None)
        return (etp.descricao_solucao or '') if etp else ''

    def _req_sustentabilidade_texto():
        if not tr.req_sustentabilidade:
            return 'Não exige critérios de sustentabilidade.'
        partes = ['Exige critérios de sustentabilidade.']
        if tr.req_sustentabilidade_criterios:
            partes.append(tr.req_sustentabilidade_criterios)
        return '\n'.join(partes)

    def _req_marca_texto():
        if not tr.req_indicacao_marca:
            return 'Sem indicação de marca ou modelo.'
        partes = ['Indica marca/modelo.']
        if tr.req_indicacao_marca_justific:
            partes.append(f'Justificativa: {tr.req_indicacao_marca_justific}')
        return '\n'.join(partes)

    def _req_exame_texto():
        partes = [f'Exame de adequação: {tr.get_req_exame_adequacao_display()}']
        if tr.req_exame_descricao:
            partes.append(tr.req_exame_descricao)
        return '\n'.join(partes)

    def _req_vistoria_texto():
        partes = [f'Vistoria prévia: {tr.get_req_vistoria_display()}']
        if tr.req_vistoria_detalhes:
            partes.append(tr.req_vistoria_detalhes)
        return '\n'.join(partes)

    def _req_subcontratacao_texto():
        partes = [f'Subcontratação: {tr.get_req_subcontratacao_display()}']
        if tr.req_subcontratacao_descricao:
            partes.append(tr.req_subcontratacao_descricao)
        if tr.req_subcontratacao_mep:
            partes.append('Obrigatório subcontratar ME/EPP (art. 48, II, LC 123/2006).')
        return '\n'.join(partes)

    def _req_garantia_prop_texto():
        return 'Exige garantia de proposta (art. 58).' if tr.req_garantia_proposta else 'Não exige garantia de proposta.'

    def _req_garantia_contr_texto():
        if not tr.req_garantia_contratacao:
            return 'Não exige garantia da contratação.'
        partes = ['Exige garantia da contratação (art. 96).']
        if tr.req_garantia_percentual is not None:
            partes.append(f'Percentual: {tr.req_garantia_percentual}%')
        if tr.req_garantia_modalidade:
            partes.append(f'Modalidade: {tr.get_req_garantia_modalidade_display()}')
        return '\n'.join(partes)

    def _bens_nao_luxo_texto():
        return ('Declaração: o objeto não se enquadra como bem de luxo (art. 20, Lei 14.133/2021).'
                if tr.bens_nao_luxo else 'Objeto pode se enquadrar como bem de luxo — avaliar enquadramento.')

    def _bens_reserva_cota_texto():
        if not tr.bens_reserva_cota:
            return 'Sem reserva de cota para ME/EPP.'
        return f'Reserva de cota de {tr.bens_reserva_cota_percentual}% para ME/EPP (art. 48, III, LC 123/2006).'

    def _bens_carta_solidariedade_texto():
        return ('Exige carta de solidariedade do fabricante.' if tr.bens_carta_solidariedade
                else 'Não exige carta de solidariedade do fabricante.')

    def _bens_garantia_tecnica_texto():
        partes = []
        if tr.bens_garantia_tecnica_prazo:
            partes.append(f'Prazo de garantia técnica: {tr.bens_garantia_tecnica_prazo} mês(es)')
        if tr.bens_garantia_tecnica_det:
            partes.append(tr.bens_garantia_tecnica_det)
        return '\n'.join(partes)

    def _serv_transicao_texto():
        if not tr.serv_transicao_contratual:
            return 'Não exige transição contratual.'
        partes = ['Exige transição contratual com transferência de conhecimento.']
        if tr.serv_transicao_descricao:
            partes.append(tr.serv_transicao_descricao)
        return '\n'.join(partes)

    def _hab_fiscal_texto():
        return f'Esfera de habilitação fiscal: {tr.get_hab_fiscal_esfera_display()}' if tr.hab_fiscal_esfera else ''

    def _parcelamento_etp_texto():
        etp = getattr(tr, 'etp', None)
        if not etp:
            return ''
        tipos = {'lote_unico': 'Lote único', 'lotes': 'Dividido em lotes', 'por_item': 'Por item'}
        partes = []
        if etp.tipo_parcelamento:
            partes.append(f'Tipo: {tipos.get(etp.tipo_parcelamento, etp.tipo_parcelamento)}')
        if etp.parcelamento_justificativa:
            partes.append(f'Justificativa: {etp.parcelamento_justificativa}')
        if etp.reserva_cota_me_epp:
            partes.append('Reserva de cota de 25% para ME/EPP: SIM (LC 123/2006, Art. 48, III)')
            if etp.licitacao_exclusiva_me_epp:
                partes.append('Licitação exclusiva ME/EPP: SIM (até R$80.000)')
        elif etp.reserva_cota_justificativa:
            partes.append(f'Reserva de cota ME/EPP: NÃO — {etp.reserva_cota_justificativa}')
        return '\n'.join(partes)

    return {
        'numero_sei':              tr.numero_sei or '',
        'objeto':                  tr.objeto_contratacao or '',
        'justificativa':           tr.justificativa or '',
        'requisitos':              tr.requisitos_contratacao or '',
        'obrigacoes_contratada':   tr.obrigacoes_contratada or '',
        'obrigacoes_contratante':  tr.obrigacoes_contratante or '',
        'criterios_selecao':       tr.criterios_selecao or '',
        'criterios_medicao':       tr.criterios_medicao or '',
        'prazo_vigencia':          tr.prazo_observacao or '',
        'local_entrega':           tr.local_entrega or '',
        'garantia':                tr.garantia_contrato or '',
        'estimativa_valor':        _fmt_valor(tr.estimativa_valor) if tr.estimativa_valor else '',
        'observacoes':             tr.observacoes or '',
        'adequacao_orcamentaria':  tr.adequacao_orcamentaria or '',
        'permite_consorcio':       _permite_consorcio_texto(),
        'qualificacao_juridica':   _qualificacao_juridica_texto(),
        'qualificacao_economica':  _qualificacao_economica_texto(),
        'prazos_execucao':         _prazos_texto(),
        'degrau_lances':           str(tr.degrau_lances) if tr.degrau_lances is not None else '',
        # Checklist oficial PGE-BA — seções adicionais (ver seed_secoes_tr.py)
        'cond_gerais':             _cond_gerais_texto(),
        'fundamentacao':           _fundamentacao_texto(),
        'solucao':                 _solucao_texto(),
        'req_sustentabilidade':    _req_sustentabilidade_texto(),
        'req_marca':               _req_marca_texto(),
        'req_exame':               _req_exame_texto(),
        'req_vistoria':            _req_vistoria_texto(),
        'req_subcontratacao':      _req_subcontratacao_texto(),
        'req_garantia_prop':       _req_garantia_prop_texto(),
        'req_garantia_contr':      _req_garantia_contr_texto(),
        'bens_nao_luxo':           _bens_nao_luxo_texto(),
        'bens_reserva_cota':       _bens_reserva_cota_texto(),
        'bens_carta_solidariedade': _bens_carta_solidariedade_texto(),
        'bens_validade':           tr.bens_validade_pereciveis or '',
        'bens_garantia_tecnica':   _bens_garantia_tecnica_texto(),
        'serv_transicao':          _serv_transicao_texto(),
        'serv_regime_execucao':    tr.serv_regime_execucao or '',
        'serv_materiais':          tr.serv_materiais or '',
        'serv_qualificacao':       tr.serv_qualificacao_tecnica or '',
        'serv_parcelas_relevancia': tr.serv_parcelas_relevancia or '',
        'hab_fiscal':              _hab_fiscal_texto(),
        'hab_juridica':            _qualificacao_juridica_texto(),   # alias — checklist renomeou a seção
        'hab_economica':           _qualificacao_economica_texto(),  # alias — checklist renomeou a seção
        'hab_tecnica_servicos':    tr.serv_qualificacao_tecnica or '',
        'parcelamento_etp':        _parcelamento_etp_texto(),
    }


_CONTEXTOS = {'DFD': _contexto_dfd, 'ETP': _contexto_etp, 'TR': _contexto_tr}


def renderizar_secao(tipo: str, secao, obj) -> str:
    """
    Resolve o texto de UMA seção: `template_texto` (Jinja2) se houver, senão o valor
    bruto do contexto na mesma chave que `secao.codigo`. Usado tanto pelo preview
    (`DocumentEngine.gerar`) quanto pelos exports PDF/HTML (`exportacao/pdf_utils.py`
    e os templates em `templates/exportacao/`).
    """
    contexto_fn = _CONTEXTOS.get(tipo)
    if contexto_fn is None:
        raise ValueError(f'Tipo de artefato desconhecido: {tipo}')

    contexto = contexto_fn(obj)
    if secao.template_texto:
        try:
            texto = _ENV.from_string(secao.template_texto).render(**contexto)
        except jinja2.TemplateError:
            texto = ''
    else:
        texto = contexto.get(secao.codigo, '') or ''

    return (texto or '').strip()


class DocumentEngine:
    """
    Gera o texto das seções configuradas para um artefato (DFD, ETP ou TR).

    Uso:
        secoes = DocumentEngine.gerar('TR', tr_instance, modalidade=tr.modalidade_aquisicao)
        # [{'secao_id', 'codigo', 'titulo', 'obrigatorio', 'texto'}, ...]
    """

    @classmethod
    def gerar(cls, tipo: str, obj, modalidade: str = None) -> list[dict]:
        resultado = []
        for secao in _get_secoes_ativas(tipo, modalidade):
            texto = renderizar_secao(tipo, secao, obj)
            if not texto:
                continue

            resultado.append({
                'secao_id':    secao.id,
                'codigo':      secao.codigo,
                'titulo':      secao.titulo,
                'obrigatorio': secao.obrigatorio,
                'texto':       texto,
            })
        return resultado
