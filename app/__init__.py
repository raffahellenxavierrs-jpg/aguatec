from flask import Flask
from flask_login import LoginManager
from app.models import db, Usuario
from config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, realize o login para acessar esta página.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Registro de rotas e blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.tanques import tanques_bp
    from app.routes.medicoes import medicoes_bp
    from app.routes.alertas import alertas_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tanques_bp, url_prefix='/tanques')
    app.register_blueprint(medicoes_bp)
    app.register_blueprint(alertas_bp, url_prefix='/alertas')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
