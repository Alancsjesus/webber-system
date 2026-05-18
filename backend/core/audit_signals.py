"""
Signals que populam AuditLog automaticamente.

Rastreados:
  - Criação de artefatos principais (DFD, ETP, TR, Procedimento, Contrato, Necessidade)
  - Exclusão dos mesmos
  - Alterações de número SEI em qualquer artefato
  - Alterações de campos monetários (valor_estimado, valor_contrato)
  - Login de usuários
"""
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver


def _log(org_id, modelo, objeto_id, objeto_repr, acao, descricao,
         usuario=None, antes=None, depois=None):
    """Grava um registro de AuditLog sem travar o request."""
    from core.models import AuditLog, Orgao
    try:
        org = Orgao.objects.get(pk=org_id) if org_id else None
        AuditLog.objects.create(
            org_id      = org,
            modelo      = modelo,
            objeto_id   = objeto_id,
            objeto_repr = str(objeto_repr)[:300],
            acao        = acao,
            descricao   = str(descricao)[:500],
            usuario     = usuario,
            antes_json  = antes,
            depois_json = depois,
        )
    except Exception:
        pass   # auditoria nunca deve quebrar o fluxo principal


def _org(instance):
    """Retorna o pk do org_id do artefato de forma segura."""
    return getattr(getattr(instance, 'org_id', None), 'pk', None) \
        or getattr(instance, 'org_id_id', None)


# ── Configuração: quais modelos rastrear e quais campos monetários ────────────

_MODELOS_RASTREADOS = {
    'modulo_demanda.DFD':                     ('numero_sei',          None),
    'modulo_etp.ETP':                          ('numero_sei',          None),
    'modulo_tr.TR':                            ('numero_sei',          None),
    'modulo_licitacao.Procedimento':           ('numero_sei',          'valor_estimado'),
    'modulo_contrato.Contrato':                ('numero_processo_sei', 'valor_contrato'),
    'modulo_planejamento.NecessidadePlanejamento': (None,              None),
}

# Mapa model_class → label legível
_LABELS = {
    'DFD':                     'DFD',
    'ETP':                     'ETP',
    'TR':                      'Termo de Referência',
    'Procedimento':            'Procedimento',
    'Contrato':                'Contrato',
    'NecessidadePlanejamento': 'Necessidade de Planejamento',
}


def _label(instance):
    return _LABELS.get(instance.__class__.__name__, instance.__class__.__name__)


# ── pre_save: captura estado ANTES da gravação ────────────────────────────────

_PRE_SAVE_STATE = {}   # {(model_label, pk): {campos: valores}}


def _connect_pre_save(sender, label, campo_sei, campo_valor):
    @receiver(pre_save, sender=sender, weak=False)
    def _pre(sender, instance, **kw):
        if not instance.pk:
            return   # criação — não há estado anterior
        try:
            old = sender.objects.get(pk=instance.pk)
            state = {}
            if campo_sei:
                state['sei'] = getattr(old, campo_sei, None)
            if campo_valor:
                state['valor'] = getattr(old, campo_valor, None)
            _PRE_SAVE_STATE[(label, instance.pk)] = state
        except sender.DoesNotExist:
            pass


# ── post_save: detecta criação e mudanças de SEI/valor ───────────────────────

def _connect_post_save(sender, label, campo_sei, campo_valor):
    @receiver(post_save, sender=sender, weak=False)
    def _post(sender, instance, created, **kw):
        nome = _label(instance)
        org  = _org(instance)

        if created:
            _log(org, label, instance.pk, str(instance), 'created',
                 f'{nome} criado: {instance}')
            return

        prev = _PRE_SAVE_STATE.pop((label, instance.pk), {})

        # SEI alterado
        if campo_sei:
            novo_sei = getattr(instance, campo_sei, None)
            velho_sei = prev.get('sei')
            if novo_sei and novo_sei != velho_sei:
                desc = (
                    f'Nº SEI vinculado a {nome} {instance}: {novo_sei}'
                    if not velho_sei
                    else f'Nº SEI alterado em {nome} {instance}: {velho_sei} → {novo_sei}'
                )
                _log(org, label, instance.pk, str(instance), 'sei_changed', desc,
                     antes={campo_sei: str(velho_sei)},
                     depois={campo_sei: str(novo_sei)})

        # Valor alterado
        if campo_valor:
            novo_val = getattr(instance, campo_valor, None)
            velho_val = prev.get('valor')
            if novo_val and novo_val != velho_val and velho_val is not None:
                _log(org, label, instance.pk, str(instance), 'value_changed',
                     f'Valor alterado em {nome} {instance}: '
                     f'R$ {float(velho_val):,.2f} → R$ {float(novo_val):,.2f}',
                     antes={campo_valor: str(velho_val)},
                     depois={campo_valor: str(novo_val)})


# ── post_delete ───────────────────────────────────────────────────────────────

def _connect_delete(sender, label):
    @receiver(post_delete, sender=sender, weak=False)
    def _del(sender, instance, **kw):
        _log(_org(instance), label, instance.pk, str(instance), 'deleted',
             f'{_label(instance)} excluído: {instance}')


# ── Login de usuários ─────────────────────────────────────────────────────────

@receiver(user_logged_in)
def _on_login(sender, request, user, **kwargs):
    try:
        profile = user.profile
        org_id  = profile.org_id_id if profile else None
    except Exception:
        org_id = None
    ip = (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
          or request.META.get('REMOTE_ADDR', ''))
    _log(org_id, 'User', user.pk,
         user.get_full_name() or user.username,
         'login',
         f'Login: {user.get_full_name() or user.username} ({user.username}) — IP {ip}',
         usuario=user)


# ── Wiring: conecta todos os modelos rastreados ───────────────────────────────

def connect_signals():
    """Chamado em CoreConfig.ready()."""
    from django.apps import apps
    for app_model, (campo_sei, campo_valor) in _MODELOS_RASTREADOS.items():
        try:
            app_label, model_name = app_model.split('.')
            sender = apps.get_model(app_label, model_name)
            label  = app_model
            _connect_pre_save(sender, label, campo_sei, campo_valor)
            _connect_post_save(sender, label, campo_sei, campo_valor)
            _connect_delete(sender, label)
        except Exception:
            pass
