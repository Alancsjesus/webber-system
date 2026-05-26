import requests
from django.conf import settings


def verify_hcaptcha(token: str) -> bool:
    if getattr(settings, 'HCAPTCHA_BYPASS', True):
        return True

    secret = getattr(settings, 'HCAPTCHA_SECRET', '')
    try:
        resp = requests.post(
            'https://api.hcaptcha.com/siteverify',
            data={'secret': secret, 'response': token},
            timeout=5,
        )
        data = resp.json()
        return bool(data.get('success'))
    except Exception:
        return False
