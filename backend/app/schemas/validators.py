import re

SENHAS_FRACAS = {
    "12345678", "123456789", "1234567890", "password", "senha123", "senhasenha",
    "qwertyui", "abc12345", "11111111", "00000000", "87654321", "password1",
    "administrador", "administracao", "valistock", "valistock1", "changeme",
}


def validar_senha_forte(senha: str) -> str:
    """Regra minima de forca, aplicada em qualquer campo de senha nova (cadastro, novo
    usuario, troca de senha). Nao substitui checar contra vazamentos reais (ex.: HaveIBeenPwned),
    so evita os casos mais obvios."""
    if not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        raise ValueError("A senha precisa ter letras e numeros.")
    if senha.lower() in SENHAS_FRACAS:
        raise ValueError("Essa senha e comum demais e facil de adivinhar. Escolha outra.")
    return senha
