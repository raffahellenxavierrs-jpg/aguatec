from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app.models import db, Usuario

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def verificar_admin():
    if not current_user.is_admin:
        abort(403)


@admin_bp.route('/usuarios')
def usuarios():
    lista_usuarios = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template('admin/usuarios.html', usuarios=lista_usuarios)


@admin_bp.route('/usuarios/<int:usuario_id>/toggle-status', methods=['POST'])
def toggle_status(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)

    if usuario.id == current_user.id:
        flash('Você não pode desativar sua própria conta de administrador.', 'warning')
        return redirect(url_for('admin.usuarios'))

    usuario.ativo = not usuario.ativo
    db.session.commit()

    acao = 'ativada' if usuario.ativo else 'desativada'
    flash(f'Conta do usuário "{usuario.nome}" foi {acao} com sucesso.', 'info')
    return redirect(url_for('admin.usuarios'))
