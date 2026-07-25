"""Inicializa o banco de dados local."""

from database.db import init_db

if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado em vagas.db")
