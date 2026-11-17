from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmacao = request.form.get('confirmacao', '')

        # Validações dos campos obrigatórios
        if not nome or not email or not senha:
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return render_template('auth/cadastro.html', nome=nome, email=email)

        if senha != confirmacao:
            flash('As senhas digitadas não coincidem.', 'danger')
            return render_template('auth/cadastro.html', nome=nome, email=email)

        if len(senha) < 6:
            flash('A senha deve conter no mínimo 6 caracteres.', 'danger')
            return render_template('auth/cadastro.html', nome=nome, email=email)

        # Verificar se o e-mail já existe (RF01 / CA01)
        if Usuario.query.filter_by(email=email).first():
            flash('Este endereço de e-mail já está em uso.', 'danger')
            return render_template('auth/cadastro.html', nome=nome, email=email)

        # Se for o primeiro usuário cadastrado, torna administrador para facilitar
        perfil = 'admin' if Usuario.query.count() == 0 else 'piscicultor'

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            perfil=perfil,
            ativo=True
        )
        novo_usuario.set_senha(senha)

        db.session.add(novo_usuario)
        db.session.commit()

        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/cadastro.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Informe seu e-mail e senha.', 'warning')
            return render_template('auth/login.html', email=email)

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.checar_senha(senha):
            flash('E-mail ou senha incorretos.', 'danger')
            return render_template('auth/login.html', email=email)

        if not usuario.ativo:
            flash('Esta conta foi desativada pelo administrador.', 'danger')
            return render_template('auth/login.html', email=email)

        login_user(usuario)
        flash(f'Bem-vindo(a), {usuario.nome}!', 'success')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão encerrada com sucesso.', 'info')
    return redirect(url_for('auth.login'))
