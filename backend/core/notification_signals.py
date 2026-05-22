"""
Signals para criação automática de NotificacaoInterna quando documentos
mudam de status (DFD, ETP, TR, Mapa de Preços).

Conectados via AppConfig.ready() em core/apps.py.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


def _notificar(destinatario, tipo, titulo, mensagem, url):
    """Cria uma notificação se o destinatário existir."""
    if not destinatario:
        return
    from core.models import NotificacaoInterna
    NotificacaoInterna.objects.create(
        destinatario=destinatario,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        url_destino=url,
    )


# ── ETP ───────────────────────────────────────────────────────────────────────

def _on_historico_etp(sender, instance, created, **kwargs):
    if not created:
        return
    from modulo_etp.models import ETP
    etp = instance.etp

    if instance.status_novo == 'Devolvido':
        # Notifica quem submeteu (created_by do ETP)
        _notificar(
            etp.created_by,
            'devolucao',
            f'ETP devolvido — {etp.numero_sei}',
            instance.motivo or 'Verifique os motivos no documento.',
            f'/etp/etps/{etp.pk}',
        )

    elif instance.status_novo == 'Aprovado':
        _notificar(
            etp.created_by,
            'aprovacao',
            f'ETP aprovado — {etp.numero_sei}',
            'Seu ETP foi aprovado. A próxima etapa é a elaboração do TR.',
            f'/etp/etps/{etp.pk}',
        )

    elif instance.status_novo == 'Submetido':
        # Notifica analistas da unidade licitante
        _notificar_papel_org(
            etp.org_id_id,
            ['analista', 'admin'],
            'pendente_aprovacao',
            f'ETP aguardando análise — {etp.numero_sei}',
            'Um novo ETP foi submetido para análise.',
            f'/etp/etps/{etp.pk}',
        )


# ── TR ────────────────────────────────────────────────────────────────────────

def _on_historico_tr(sender, instance, created, **kwargs):
    if not created:
        return
    from modulo_tr.models import TR
    tr = instance.tr

    if instance.status_novo == 'Devolvido':
        _notificar(
            tr.created_by,
            'devolucao',
            f'TR devolvido — {tr.numero_sei}',
            instance.motivo or 'Verifique os motivos no documento.',
            f'/analise-tecnica/trs/{tr.pk}',
        )

    elif instance.status_novo == 'Aprovado':
        _notificar(
            tr.created_by,
            'aprovacao',
            f'TR aprovado — {tr.numero_sei}',
            'Seu TR foi aprovado. O procedimento pode ser iniciado.',
            f'/analise-tecnica/trs/{tr.pk}',
        )

    elif instance.status_novo == 'Submetido':
        _notificar_papel_org(
            tr.org_id_id,
            ['analista', 'admin'],
            'pendente_aprovacao',
            f'TR aguardando análise — {tr.numero_sei}',
            'Um novo TR foi submetido para análise.',
            f'/analise-tecnica/trs/{tr.pk}',
        )


# ── Mapa de Preços ────────────────────────────────────────────────────────────

def _on_historico_mapa(sender, instance, created, **kwargs):
    if not created:
        return
    mapa = instance.mapa

    if instance.status_novo == 'Devolvido':
        _notificar(
            mapa.created_by,
            'devolucao',
            f'Mapa de Preços devolvido — #{mapa.pk}',
            instance.motivo or 'Verifique os motivos no documento.',
            f'/pesquisa/mapa/{mapa.pk}',
        )

    elif instance.status_novo == 'Aprovado':
        _notificar(
            mapa.created_by,
            'aprovacao',
            f'Mapa de Preços aprovado — #{mapa.pk}',
            'Seu Mapa de Preços foi aprovado.',
            f'/pesquisa/mapa/{mapa.pk}',
        )

    elif instance.status_novo == 'Submetido':
        _notificar_papel_org(
            mapa.org_id_id,
            ['analista', 'admin'],
            'pendente_aprovacao',
            f'Mapa de Preços aguardando análise — #{mapa.pk}',
            'Um novo Mapa de Preços foi submetido para análise.',
            f'/pesquisa/mapa/{mapa.pk}',
        )


# ── Procedimento (licitação) ──────────────────────────────────────────────────

def _on_historico_procedimento(sender, instance, created, **kwargs):
    if not created:
        return
    proc = instance.procedimento

    if instance.status_novo == 'Em Instrução' and instance.status_anterior == 'Aguardando Aprovação':
        # Devolvido para instrução
        _notificar(
            proc.created_by,
            'devolucao',
            f'Procedimento devolvido — {proc.numero}',
            instance.motivo or 'O procedimento foi devolvido para instrução.',
            f'/licitacao/{proc.pk}',
        )

    elif instance.status_novo == 'Aprovado':
        _notificar(
            proc.created_by,
            'aprovacao',
            f'Procedimento aprovado — {proc.numero}',
            'O procedimento foi aprovado e pode ser publicado.',
            f'/licitacao/{proc.pk}',
        )


# ── Helper: notificar todos os usuários de determinado papel no órgão ─────────

def _notificar_papel_org(org_id, papeis, tipo, titulo, mensagem, url):
    """Notifica todos os usuários ativos com determinado papel no órgão."""
    try:
        from core.models import UserProfile, NotificacaoInterna
        from django.contrib.auth.models import User
        perfis = UserProfile.objects.filter(
            org_id_id=org_id,
            papel__in=papeis,
            user__is_active=True,
        ).select_related('user')
        for perfil in perfis:
            NotificacaoInterna.objects.create(
                destinatario=perfil.user,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                url_destino=url,
            )
    except Exception:
        pass  # Nunca deixar signals quebrar a operação principal


# ── Registrar signals ─────────────────────────────────────────────────────────

def conectar_signals():
    """Chamado em core/apps.py ready()."""
    try:
        from modulo_etp.models import HistoricoETP
        post_save.connect(_on_historico_etp, sender=HistoricoETP)
    except Exception:
        pass

    try:
        from modulo_tr.models import HistoricoTR
        post_save.connect(_on_historico_tr, sender=HistoricoTR)
    except Exception:
        pass

    try:
        from modulo_mapa_precos.models import HistoricoMapa
        post_save.connect(_on_historico_mapa, sender=HistoricoMapa)
    except Exception:
        pass

    try:
        from modulo_licitacao.models import HistoricoProcedimento
        post_save.connect(_on_historico_procedimento, sender=HistoricoProcedimento)
    except Exception:
        pass
