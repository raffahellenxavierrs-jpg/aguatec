from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Tanque, Alerta, Medicao

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        tanques = Tanque.query.all()
        alertas_ativos = Alerta.query.filter_by(status='ativo').order_by(Alerta.data_hora.desc()).limit(10).all()
        total_alertas_ativos = Alerta.query.filter_by(status='ativo').count()
    else:
        tanques = Tanque.query.filter_by(usuario_id=current_user.id).all()
        tanque_ids = [t.id for t in tanques]
        if tanque_ids:
            alertas_ativos = Alerta.query.filter(
                Alerta.tanque_id.in_(tanque_ids),
                Alerta.status == 'ativo'
            ).order_by(Alerta.data_hora.desc()).limit(10).all()
            total_alertas_ativos = Alerta.query.filter(
                Alerta.tanque_id.in_(tanque_ids),
                Alerta.status == 'ativo'
            ).count()
        else:
            alertas_ativos = []
            total_alertas_ativos = 0

    # Adiciona a última medição para cada tanque
    dados_tanques = []
    for t in tanques:
        ultima = t.ultima_medicao()
        alertas_tanque = Alerta.query.filter_by(tanque_id=t.id, status='ativo').count()
        dados_tanques.append({
            'tanque': t,
            'ultima_medicao': ultima,
            'alertas_ativos': alertas_tanque
        })

    return render_template(
        'dashboard.html',
        dados_tanques=dados_tanques,
        alertas_ativos=alertas_ativos,
        total_alertas_ativos=total_alertas_ativos
    )
