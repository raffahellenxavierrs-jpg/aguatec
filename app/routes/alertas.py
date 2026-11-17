from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, Alerta, Tanque

alertas_bp = Blueprint('alertas', __name__)

@alertas_bp.route('/')
@login_required
def index():
    status_filtro = request.args.get('status', 'todos')

    if current_user.is_admin:
        query = Alerta.query
    else:
        tanque_ids = [t.id for t in Tanque.query.filter_by(usuario_id=current_user.id).all()]
        query = Alerta.query.filter(Alerta.tanque_id.in_(tanque_ids))

    if status_filtro != 'todos':
        query = query.filter(Alerta.status == status_filtro)

    alertas = query.order_by(Alerta.data_hora.desc()).all()

    return render_template('alertas/index.html', alertas=alertas, status_filtro=status_filtro)


@alertas_bp.route('/<int:alerta_id>/resolver', methods=['POST'])
@login_required
def resolver(alerta_id):
    alerta = db.get_or_404(Alerta, alerta_id)
    tanque = db.session.get(Tanque, alerta.tanque_id)

    if tanque.usuario_id != current_user.id and not current_user.is_admin:
        abort(403)

    alerta.status = 'resolvido'
    db.session.commit()

    flash('Alerta marcado como resolvido!', 'success')
    return redirect(request.referrer or url_for('alertas.index'))
