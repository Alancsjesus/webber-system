import json
import base64
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Orgao, UserProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Isola estado do throttle entre testes."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def orgao(db):
    return Orgao.objects.create(nome='Órgão Teste', sigla='OT', ativa=True)


@pytest.fixture
def admin_user(db, orgao):
    user = User.objects.create_user(username='admin_test', password='Admin@1234')
    user.profile.papel = 'admin'
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def regular_user(db, orgao):
    user = User.objects.create_user(username='analista_test', password='Admin@1234')
    user.profile.papel = 'analista'
    user.profile.org_id = orgao
    user.profile.save()
    return user


@pytest.fixture
def other_user(db, orgao):
    user = User.objects.create_user(username='outro_test', password='Admin@1234')
    user.profile.papel = 'solicitante'
    user.profile.org_id = orgao
    user.profile.save()
    return user


# ---------------------------------------------------------------------------
# 1. Hashing Argon2
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestArgon2Hashing:
    def test_argon2_hash_on_new_password(self):
        """Novo usuário deve ter hash Argon2."""
        user = User.objects.create_user(username='novo_user', password='Senha@Forte1')
        assert user.password.startswith('argon2$'), (
            f"Esperado hash argon2, obtido: {user.password[:20]}"
        )

    def test_pbkdf2_legacy_login_succeeds(self, api_client, orgao):
        """Usuário com hash PBKDF2 legado deve conseguir autenticar (fallback)."""
        user = User(username='legacy_pbkdf2')
        user.password = make_password('Legacy@1234', hasher='pbkdf2_sha256')
        user.save()
        UserProfile.objects.filter(user=user).update(org_id=orgao)

        resp = api_client.post('/api/token/', {
            'username': 'legacy_pbkdf2',
            'password': 'Legacy@1234',
            'captcha_token': '',
        }, format='json')
        assert resp.status_code == 200, f"Login legado falhou: {resp.data}"
        assert 'access' in resp.data


# ---------------------------------------------------------------------------
# 2. Login básico
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLoginBasic:
    def test_login_returns_tokens(self, api_client, admin_user):
        """Login correto retorna access e refresh tokens."""
        resp = api_client.post('/api/token/', {
            'username': 'admin_test',
            'password': 'Admin@1234',
            'captcha_token': '',
        }, format='json')
        assert resp.status_code == 200
        assert 'access' in resp.data
        assert 'refresh' in resp.data

    def test_login_wrong_password_returns_401(self, api_client, admin_user):
        """Senha errada deve retornar 401."""
        resp = api_client.post('/api/token/', {
            'username': 'admin_test',
            'password': 'SenhaErrada',
            'captcha_token': '',
        }, format='json')
        assert resp.status_code == 401

    def test_login_unknown_user_returns_401(self, api_client, db):
        """Usuário inexistente deve retornar 401."""
        resp = api_client.post('/api/token/', {
            'username': 'nao_existe',
            'password': 'qualquer',
            'captcha_token': '',
        }, format='json')
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 3. Rate Limiting (throttle)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRateLimiting:
    def test_login_throttled_after_5_attempts(self, api_client, db):
        """6ª tentativa de login dentro de 1 minuto deve retornar 429."""
        payload = {
            'username': 'nao_existe',
            'password': 'qualquer',
            'captcha_token': '',
        }
        for _ in range(5):
            api_client.post('/api/token/', payload, format='json')

        resp = api_client.post('/api/token/', payload, format='json')
        assert resp.status_code == 429, (
            f"Esperado 429 (Too Many Requests), obtido: {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# 4. CAPTCHA
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCaptcha:
    def test_captcha_bypass_in_test_env(self, api_client, admin_user):
        """Com HCAPTCHA_BYPASS=True (padrão de dev/test), token vazio deve ser aceito."""
        resp = api_client.post('/api/token/', {
            'username': 'admin_test',
            'password': 'Admin@1234',
            'captcha_token': '',
        }, format='json')
        assert resp.status_code == 200

    def test_captcha_invalid_rejected(self, api_client, admin_user):
        """Com CAPTCHA ativo, token inválido deve retornar 400."""
        with patch('core.serializers.verify_hcaptcha', return_value=False):
            resp = api_client.post('/api/token/', {
                'username': 'admin_test',
                'password': 'Admin@1234',
                'captcha_token': 'token_invalido',
            }, format='json')
        assert resp.status_code == 400
        assert 'captcha' in str(resp.data).lower()


# ---------------------------------------------------------------------------
# 5. Claims JWT
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJWTClaims:
    def _decode_payload(self, token: str) -> dict:
        payload_b64 = token.split('.')[1]
        padding = 4 - len(payload_b64) % 4
        payload_b64 += '=' * padding
        return json.loads(base64.b64decode(payload_b64))

    def test_jwt_claims_contain_org_context(self, api_client, admin_user):
        """Token JWT deve conter claims de contexto organizacional."""
        resp = api_client.post('/api/token/', {
            'username': 'admin_test',
            'password': 'Admin@1234',
            'captcha_token': '',
        }, format='json')
        assert resp.status_code == 200

        payload = self._decode_payload(resp.data['access'])
        assert 'papel' in payload
        assert 'orgao_id' in payload or 'org_id' in payload
        assert payload['papel'] == 'admin'

    def test_refresh_returns_new_access_token(self, api_client, admin_user):
        """Refresh token válido deve gerar novo access token."""
        resp = api_client.post('/api/token/', {
            'username': 'admin_test',
            'password': 'Admin@1234',
            'captcha_token': '',
        }, format='json')
        refresh = resp.data['refresh']

        resp2 = api_client.post('/api/token/refresh/', {'refresh': refresh}, format='json')
        assert resp2.status_code == 200
        assert 'access' in resp2.data

    def test_expired_refresh_rejected(self, api_client, admin_user):
        """Refresh token inválido/expirado deve retornar 401."""
        resp = api_client.post('/api/token/refresh/', {
            'refresh': 'token.invalido.aqui'
        }, format='json')
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 6. Gestão de senha pelo admin
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminPasswordManagement:
    def _get_jwt(self, api_client, username, password):
        resp = api_client.post('/api/token/', {
            'username': username,
            'password': password,
            'captcha_token': '',
        }, format='json')
        return resp.data.get('access')

    def test_admin_can_set_user_password(self, api_client, admin_user, other_user):
        """Admin pode redefinir a senha de qualquer usuário."""
        token = self._get_jwt(api_client, 'admin_test', 'Admin@1234')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        profile_id = other_user.profile.id
        resp = api_client.patch(
            f'/api/core/usuarios/{profile_id}/',
            {'password': 'NovaSenha@99'},
            format='json',
        )
        assert resp.status_code in (200, 204), f"Admin não conseguiu redefinir: {resp.data}"

        other_user.refresh_from_db()
        assert other_user.check_password('NovaSenha@99')

    def test_non_admin_cannot_access_other_user_profile(
        self, api_client, regular_user, other_user
    ):
        """Não-admin não pode ver nem editar perfil de outro usuário (404 por queryset)."""
        token = self._get_jwt(api_client, 'analista_test', 'Admin@1234')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        profile_id = other_user.profile.id
        resp = api_client.patch(
            f'/api/core/usuarios/{profile_id}/',
            {'password': 'TentativaHack@1'},
            format='json',
        )
        assert resp.status_code == 404, (
            f"Esperado 404 (perfil não visível para não-admin), obtido: {resp.status_code}"
        )
