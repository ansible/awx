from django.core.exceptions import ValidationError
from awx.main.models.credential import validate_ssh_private_key

import pytest

def test_valid_rsa_key():
    begin = """-----BEGIN RSA PRIVATE KEY-----"""
    end = """-----END RSA PRIVATE KEY-----"""
    unvalidated_key = build_key(begin, body, end)
    key_data = validate_ssh_private_key(unvalidated_key)
    assert key_data['key_type'] == 'rsa'

def test_invalid_key():
    unvalidated_key = build_key(key_begin, body, "END KEY")
    with pytest.raises(ValidationError):
        validate_ssh_private_key(unvalidated_key)

def test_key_type_empty():
    unvalidated_key = build_key(key_begin, body, key_end)
    key_data = validate_ssh_private_key(unvalidated_key)
    assert key_data['key_type'] == 'rsa1'


def build_key(begin, body, end):
    return """%s%s%s""" % (begin, body, end)

key_begin = """-----BEGIN PRIVATE KEY-----"""
key_end = """-----END PRIVATE KEY-----"""

body = """
uFZFyag7VVqI+q/oGnQu+wj/pMi5ox+Qz5L3W0D745DzwgDXOeObAfNlr9NtIKbn
sZ5E0+rYB4Q/U0CYr5juNJQV1dbxq2Em1160axboe2QbvX6wE6Sm6wW9b9cr+PoF
MoYQebUnCY0ObrLbrRugSfZc17lyxK0ZGRgPXKhpMg6Ecv8XpvhjUYU9Esyqfuco
/p26Q140/HsHeHYNma0dQHCEjMr/qEzOY1qguHj+hRf3SARtM9Q+YNgpxchcDDVS
O+n+8Ljd/p82bpEJwxmpXealeWbI6gB9/R6wcCL+ZyCZpnHJd/NJ809Vtu47ZdDi
E6jvqS/3AQhuQKhJlLSDIzezB2VKKrHwOvHkg/+uLoCqHN34Gk6Qio7x69SvXy88
a7q9D1l/Zx60o08FyZyqlo7l0l/r8EY+36cuI/lvAvfxc5VHVEOvKseUjFRBiCv9
MkKNxaScoYsPwY7SIS6gD93tg3eM5pA0nfMfya9u1+uq/QCM1gNG3mm6Zd8YG4c/
Dx4bmsj8cp5ni/Ffl/sKzKYq1THunJEFGXOZRibdxk/Fal3SQrRAwy7CgLQL8SMh
IWqcFm25OtSOP1r1LE25t5pQsMdmp0IP2fEF0t/pXPm1ZfrTurPMqpo4FGm2hkki
U3sH/o6nrkSOjklOLWlwtTkkL4dWPlNwc8OYj8zFizXJkAfv1spzhv3lRouNkw4N
Mm22W7us2f3Ob0H5C07k26h6VuXX+0AybD4tIIcUXCLoNTqA0HvqhKpEuHu3Ck10
RaB8xHTxgwdhGVaNHMfy9B9l4tNs3Tb5k0LyeRRGVDhWCFo6axYULYebkj+hFLLY
+JE5RzPDFpTf1xbuT+e56H/lLFCUdDu0bn+D0W4ifXaVFegak4r6O4B53CbMqr+R
t6qDPKLUIuVJXK0J6Ay6XgmheXJGbgKh4OtDsc06gsTCE1nY4f/Z82AQahPBfTtF
J2z+NHdsLPn//HlxspGQtmLpuS7Wx0HYXZ+kPRSiE/vmITw85R2u8JSHQicVNN4C
2rlUo15TIU3tTx+WUIrHKHPidUNNotRb2p9n9FoSidU6upKnQHAT/JNv/zcvaia3
Bhl/wagheWTDnFKSmJ4HlKxplM/32h6MfHqsMVOl4F6eZWKaKgSgN8doXyFJo+sc
yAC6S0gJlD2gQI24iTI4Du1+UGh2MGb69eChvi5mbbdesaZrlR1dRqZpHG+6ob4H
nYLndRvobXS5l6pgGTDRYoUgSbQe21a7Uf3soGl5jHqLWc1zEPwrxV7Wr31mApr6
8VtGZcLSr0691Q1NLO3eIfuhbMN2mssX/Sl4t+4BibaucNIMfmhKQi8uHtwAXb47
+TMFlG2EQhZULFM4fLdF1vaizInU3cBk8lsz8i71tDc+5VQTEwoEB7Gksy/XZWEt
6SGHxXUDtNYa+G2O+sQhgqBjLIkVTV6KJOpvNZM+s8Vzv8qoFnD7isKBBrRvF1bP
GOXEG1jd7nSR0WSwcMCHGOrFEELDQPw3k5jqEdPFgVODoZPr+drZVnVz5SAGBk5Y
wsCNaDW+1dABYFlqRTepP5rrSu9wHnRAZ3ZGv+DHoGqenIC5IBR0sQ==
"""
