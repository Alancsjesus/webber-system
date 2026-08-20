import re

from django.core.exceptions import ValidationError


def _somente_digitos(valor):
    return re.sub(r'\D', '', valor or '')


def validar_cnpj(valor):
    """Valida CNPJ pelos dígitos verificadores. Levanta ValidationError se inválido."""
    digitos = _somente_digitos(valor)
    if len(digitos) != 14:
        raise ValidationError('CNPJ deve ter 14 dígitos.')
    if digitos == digitos[0] * 14:
        raise ValidationError('CNPJ inválido.')

    def _dv(base, pesos):
        soma = sum(int(d) * p for d, p in zip(base, pesos))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv1 = _dv(digitos[:12], pesos1)
    dv2 = _dv(digitos[:12] + dv1, pesos2)
    if digitos[12:14] != dv1 + dv2:
        raise ValidationError('CNPJ inválido — dígito verificador não confere.')
    return digitos


def validar_cpf(valor):
    """Valida CPF pelos dígitos verificadores. Levanta ValidationError se inválido."""
    digitos = _somente_digitos(valor)
    if len(digitos) != 11:
        raise ValidationError('CPF deve ter 11 dígitos.')
    if digitos == digitos[0] * 11:
        raise ValidationError('CPF inválido.')

    def _dv(base):
        n = len(base) + 1
        soma = sum(int(d) * (n - i) for i, d in enumerate(base))
        resto = (soma * 10) % 11
        return '0' if resto == 10 else str(resto)

    dv1 = _dv(digitos[:9])
    dv2 = _dv(digitos[:9] + dv1)
    if digitos[9:11] != dv1 + dv2:
        raise ValidationError('CPF inválido — dígito verificador não confere.')
    return digitos


def formatar_documento(digitos, tipo_pessoa):
    if tipo_pessoa == 'PJ':
        return f'{digitos[0:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:14]}'
    return f'{digitos[0:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:11]}'


def validar_documento(documento, tipo_pessoa):
    """Valida CNPJ ou CPF conforme tipo_pessoa e retorna o documento formatado."""
    if tipo_pessoa == 'PJ':
        digitos = validar_cnpj(documento)
    elif tipo_pessoa == 'PF':
        digitos = validar_cpf(documento)
    else:
        raise ValidationError('tipo_pessoa deve ser PJ ou PF.')
    return formatar_documento(digitos, tipo_pessoa)
