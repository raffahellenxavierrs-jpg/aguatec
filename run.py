from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    db.create_all()
    # Criação opcional de um usuário admin padrão se o banco estiver vazio
    if Usuario.query.count() == 0:
        admin_padrao = Usuario(
            nome="Administrador",
            email="admin@aquawatertech.com",
            perfil="admin",
            ativo=True
        )
        admin_padrao.set_senha("admin123")
        db.session.add(admin_padrao)
        db.session.commit()
        print(">> Usuário administrador inicial criado: admin@aquawatertech.com / admin123")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
