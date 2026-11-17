import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aquawatertech-secret-key-2026')

    # Trata URL do banco de dados (ajusta postgres:// para postgresql:// se fornecido por serviços em nuvem)
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = db_url or ('sqlite:///' + os.path.join(BASE_DIR, 'aquawatertech.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
