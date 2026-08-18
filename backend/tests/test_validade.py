from datetime import date, timedelta

from app.services.validade_service import dias_restantes, status_validade


def test_dias_restantes_calcula_diferenca_de_datas():
    hoje = date(2026, 8, 17)
    assert dias_restantes(date(2026, 8, 24), referencia=hoje) == 7
    assert dias_restantes(date(2026, 8, 12), referencia=hoje) == -5


def test_status_normal_acima_de_7_dias():
    hoje = date(2026, 8, 17)
    assert status_validade(hoje + timedelta(days=8), referencia=hoje) == "normal"


def test_status_atencao_entre_4_e_7_dias():
    hoje = date(2026, 8, 17)
    assert status_validade(hoje + timedelta(days=7), referencia=hoje) == "atencao"
    assert status_validade(hoje + timedelta(days=4), referencia=hoje) == "atencao"


def test_status_urgente_entre_1_e_3_dias():
    hoje = date(2026, 8, 17)
    assert status_validade(hoje + timedelta(days=3), referencia=hoje) == "urgente"
    assert status_validade(hoje + timedelta(days=1), referencia=hoje) == "urgente"


def test_status_vence_hoje():
    hoje = date(2026, 8, 17)
    assert status_validade(hoje, referencia=hoje) == "vence_hoje"


def test_status_vencido():
    hoje = date(2026, 8, 17)
    assert status_validade(hoje - timedelta(days=1), referencia=hoje) == "vencido"
