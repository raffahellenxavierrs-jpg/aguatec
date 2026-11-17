from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, Tanque, LimiteAlerta, Medicao, Alerta
from app.services import inicializar_limites_padrao

tanques_bp = Blueprint('tanques', __name__)

@tanques_bp.route('/', methods=['GET'])
@login_required
def index():
    if current_user.is_admin:
        tanques = Tanque.query.all()
    else:
        tanques = Tanque.query.filter_by(usuario_id=current_user.id).all()
    return render_template('tanques/index.html', tanques=tanques)


@tanques_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao_local = request.form.get('descricao_local', '').strip()

        if not nome:
            flash('O nome do tanque é obrigatório.', 'danger')
            return render_template('tanques/novo.html', nome=nome, descricao_local=descricao_local)

        tanque = Tanque(
            usuario_id=current_user.id,
            nome=nome,
            descricao_local=descricao_local
        )
        db.session.add(tanque)
        db.session.commit()

        # Cria limites recomendados por padrão para conveniência do piscicultor
        inicializar_limites_padrao(tanque.id)

        flash(f'Tanque "{tanque.nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('tanques.detalhe', tanque_id=tanque.id))

    return render_template('tanques/novo.html')


@tanques_bp.route('/<int:tanque_id>')
@login_required
def detalhe(tanque_id):
    tanque = db.get_or_404(Tanque, tanque_id)

    # Verificação de isolamento de dados (RF09, CA09)
    if tanque.usuario_id != current_user.id and not current_user.is_admin:
        abort(403)

    limites = LimiteAlerta.query.filter_by(tanque_id=tanque.id).all()
    medicoes = Medicao.query.filter_by(tanque_id=tanque.id).order_by(Medicao.data_hora.desc()).limit(50).all()
    alertas = Alerta.query.filter_by(tanque_id=tanque.id).order_by(Alerta.data_hora.desc()).limit(20).all()
    ultima_medicao = tanque.ultima_medicao()

    return render_template(
        'tanques/detalhe.html',
        tanque=tanque,
        limites=limites,
        medicoes=medicoes,
        alertas=alertas,
        ultima_medicao=ultima_medicao
    )


@tanques_bp.route('/<int:tanque_id>/limites', methods=['POST'])
@login_required
def atualizar_limites(tanque_id):
    tanque = db.get_or_404(Tanque, tanque_id)

    # Verificação de isolamento de dados (RF09, CA09)
    if tanque.usuario_id != current_user.id and not current_user.is_admin:
        abort(403)

    parametros = ['oxigenio', 'ph', 'temperatura']

    for param in parametros:
        min_val = request.form.get(f'{param}_min')
        max_val = request.form.get(f'{param}_max')

        limite = LimiteAlerta.query.filter_by(tanque_id=tanque.id, parametro=param).first()
        if not limite:
            limite = LimiteAlerta(tanque_id=tanque.id, parametro=param)
            db.session.add(limite)

        try:
            limite.valor_minimo = float(min_val) if min_val not in (None, '') else None
            limite.valor_maximo = float(max_val) if max_val not in (None, '') else None
            limite.ativo = True
        except ValueError:
            flash(f'Valor inválido informado para o parâmetro {param}.', 'danger')
            return redirect(url_for('tanques.detalhe', tanque_id=tanque.id))

    db.session.commit()
    flash('Limites de alerta atualizados com sucesso!', 'success')
    return redirect(url_for('tanques.detalhe', tanque_id=tanque.id))


@tanques_bp.route('/<int:tanque_id>/excluir', methods=['POST'])
@login_required
def excluir(tanque_id):
    tanque = db.get_or_404(Tanque, tanque_id)

    if tanque.usuario_id != current_user.id and not current_user.is_admin:
        abort(403)

    nome = tanque.nome
    db.session.delete(tanque)
    db.session.commit()

    flash(f'Tanque "{nome}" foi removido.', 'info')
    return redirect(url_for('tanques.index'))
