"""Backup manual do banco de producao.

Exporta os dados de todas as tabelas para arquivos .csv (um por tabela) dentro de uma
pasta com data e hora, usando COPY (o mesmo mecanismo interno do pg_dump). Nao depende
de instalar nada alem do psycopg2, que ja e uma dependencia do projeto.

Isto e um backup DOS DADOS, nao da estrutura das tabelas: a estrutura ja esta versionada
no proprio repositorio, em migrations/versions/. Para restaurar do zero: rode
`alembic upgrade head` num banco vazio (recria as tabelas) e depois recarregue os CSVs.

Uso (PowerShell):
  cd C:\\code\\saas\\backend
  $env:DATABASE_URL = "postgresql://...sua string de producao..."
  .venv\\Scripts\\python.exe scripts\\backup_db.py
"""
import csv  # noqa: F401  (import mantido para deixar explicita a dependencia do formato CSV)
import os
import sys
from datetime import datetime, timezone

import psycopg2


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Defina a variavel DATABASE_URL antes de rodar este script.")
        sys.exit(1)

    pasta = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(pasta, exist_ok=True)

    conn = psycopg2.connect(database_url)
    try:
        cur = conn.cursor()
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        tabelas = [linha[0] for linha in cur.fetchall()]

        print(f"Encontradas {len(tabelas)} tabelas. Exportando para '{pasta}/':\n")
        for tabela in tabelas:
            caminho = os.path.join(pasta, f"{tabela}.csv")
            with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
                cur.copy_expert(f'COPY "{tabela}" TO STDOUT WITH CSV HEADER', arquivo)
            tamanho_kb = os.path.getsize(caminho) / 1024
            print(f"  {tabela}.csv ({tamanho_kb:.1f} KB)")
    finally:
        conn.close()

    print(f"\nBackup concluido em: {os.path.abspath(pasta)}")
    print("Guarde essa pasta (compactada) num lugar seguro: Google Drive, HD externo, etc.")


if __name__ == "__main__":
    main()
