# Este é um script para criar todas as tabelas no seu banco de dados MySQL.
# Execute este arquivo UMA VEZ para configurar o banco.

import os
import sys

# Adiciona o diretório raiz do projeto ao início do path do Python.
# Isso garante que o pacote 'app' seja encontrado.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Importa a Base e o engine de dentro do pacote 'app'
from app.database import Base, engine

# Importa todos os seus modelos de dentro do pacote 'app'
from app.models import User, Store, Product, Order, OrderItem 

print("Conectando ao banco de dados para criar as tabelas...")

# O comando abaixo cria todas as tabelas definidas nos seus modelos
# que herdam da Base.
Base.metadata.create_all(bind=engine)

print("Tabelas criadas com sucesso!")

