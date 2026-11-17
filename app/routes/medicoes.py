from flask import Blueprint, request, jsonify, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import db, Tanque, Medicao
from app.services import processar_e_salvar_medicao

medicoes_bp = Blueprint('medicoes', __name__)

@medicoes_bp.route('/api/medicoes', methods=['POST'])
def api_registrar_medicao():
    """
    Endpoint HTTP para recepção de medições via ESP32, simuladores ou sistemas externos.
    Formato esperado (JSON):
    {
        "tanque_id": 1,
        "oxigenio_dissolvido": 6.2,
        "ph": 7.4,
        "temperatura": 28.5,
        "origem": "sensor"  (opcional, padrão 'sensor')
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'erro': 'Formato inválido. Envie um JSON com os dados da medição.'}), 400

    tanque_id = data.get('tanque_id')
    oxigenio = data.get('oxigenio_dissolvido')
    ph = data.get('ph')
    temperatura = data.get('temperatura')
    origem = data.get('origem', 'sensor')

    if tanque_id is None or oxigenio is None or ph is None or temperatura is None:
        return jsonify({'erro': 'Campos obrigatórios: tanque_id, oxigenio_dissolvido, ph, temperatura.'}), 400

    tanque = db.session.get(Tanque, tanque_id)
    if not tanque:
        return jsonify({'erro': f'Tanque com ID {tanque_id} não encontrado.'}), 404

    try:
        oxigenio = float(oxigenio)
        ph = float(ph)
        temperatura = float(temperatura)
    except (ValueError, TypeError):
        return jsonify({'erro': 'Valores de oxigênio, pH e temperatura devem ser números válidos.'}), 400

    medicao, alertas = processar_e_salvar_medicao(
        tanque_id=tanque.id,
        oxigenio=oxigenio,
        ph=ph,
        temperatura=temperatura,
        origem=origem
    )

    return jsonify({
        'status': 'sucesso',
        'mensagem': 'Medição registrada com sucesso.',
        'medicao': medicao.to_dict(),
        'alertas_gerados': [a.to_dict() for a in alertas]
    }), 201


@medicoes_bp.route('/tanques/<int:tanque_id>/medicoes/nova', methods=['POST'])
@login_required
def inserir_medicao_manual(tanque_id):
    tanque = db.get_or_404(Tanque, tanque_id)

    # Verificação de isolamento de dados
    if tanque.usuario_id != current_user.id and not current_user.is_admin:
        abort(403)

    try:
        oxigenio = float(request.form.get('oxigenio', ''))
        ph = float(request.form.get('ph', ''))
        temperatura = float(request.form.get('temperatura', ''))
    except (ValueError, TypeError):
        flash('Por favor, informe valores numéricos válidos para todos os parâmetros.', 'danger')
        return redirect(url_for('tanques.detalhe', tanque_id=tanque.id))

    medicao, alertas = processar_e_salvar_medicao(
        tanque_id=tanque.id,
        oxigenio=oxigenio,
        ph=ph,
        temperatura=temperatura,
        origem='manual'
    )

    if alertas:
        flash(f'Medição registrada! Atenção: {len(alertas)} alerta(s) de limite foram disparados!', 'warning')
    else:
        flash('Medição registrada com sucesso e dentro dos padrões!', 'success')

    return redirect(url_for('tanques.detalhe', tanque_id=tanque.id))


@medicoes_bp.route('/api/tanques/<int:tanque_id>/historico', methods=['GET'])
@login_required
def api_historico_tanque(tanque_id):
    tanque = db.get_or_404(Tanque, tanque_id)

    if tanque.usuario_id != current_user.id and not current_user.is_admin:
        abort(403)

    limite = request.args.get('limite', default=30, type=int)
    medicoes = Medicao.query.filter_by(tanque_id=tanque.id).order_by(Medicao.data_hora.asc()).limit(limite).all()

    return jsonify([m.to_dict() for m in medicoes])
