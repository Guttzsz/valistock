from datetime import date

from app.utils.timezone import today

# Default thresholds. A company's Configuracao overrides dias_alerta_1/2/3,
# but the NORMAL/ATENCAO/URGENTE/VENCE_HOJE/VENCIDO labels are fixed status bands.
DIAS_ALERTA_PADRAO_1 = 7
DIAS_ALERTA_PADRAO_2 = 3
DIAS_ALERTA_PADRAO_3 = 1


def dias_restantes(data_validade: date, referencia: date | None = None) -> int:
    referencia = referencia or today()
    return (data_validade - referencia).days


def status_validade(data_validade: date, referencia: date | None = None) -> str:
    dias = dias_restantes(data_validade, referencia)
    if dias < 0:
        return "vencido"
    if dias == 0:
        return "vence_hoje"
    if dias <= 3:
        return "urgente"
    if dias <= 7:
        return "atencao"
    return "normal"
