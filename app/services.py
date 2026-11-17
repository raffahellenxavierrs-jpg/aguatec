from datetime import datetime, timezone
from app.models import db, Medicao, LimiteAlerta, Alerta

LIMITES_PADRAO = [
    {
        'parametro': 'oxigenio',
        'valor_minimo': 4.0,  # mg/L - abaixo disso peixes sofrem asfixia
        'valor_maximo': 12.0
    },
    {
        'parametro': 'ph',
        'valor_minimo': 6.5,
        'valor_maximo': 8.5
    },
    {
        'parametro': 'temperatura',
        'valor_minimo': 24.0,  # °C
        'valor_maximo': 32.0
    }
]

def inicializar_limites_padrao(tanque_id):
    """Cria os limites recomendados para piscicultura quando um novo tanque é criado."""
    for item in LIMITES_PADRAO:
        limite = LimiteAlerta(
            tanque_id=tanque_id,
            parametro=item['parametro'],
            valor_minimo=item['valor_minimo'],
            valor_maximo=item['valor_maximo'],
            ativo=True
        )
        db.session.add(limite)
    db.session.commit()

def processar_e_salvar_medicao(tanque_id, oxigenio, ph, temperatura, origem='sensor', data_hora=None):
    """
    Registra a medição e verifica automaticamente se viola os limites configurados,
    gerando os alertas correspondentes.
    """
    if data_hora is None:
        data_hora = datetime.now(timezone.utc)

    medicao = Medicao(
        tanque_id=tanque_id,
        data_hora=data_hora,
        oxigenio_dissolvido=float(oxigenio),
        ph=float(ph),
        temperatura=float(temperatura),
        origem=origem
    )
    db.session.add(medicao)
    db.session.flush()  # Garante que medicao.id esteja disponível

    alertas_gerados = []
    limites = LimiteAlerta.query.filter_by(tanque_id=tanque_id, ativo=True).all()

    valores = {
        'oxigenio': medicao.oxigenio_dissolvido,
        'ph': medicao.ph,
        'temperatura': medicao.temperatura
    }

    for lim in limites:
        val = valores.get(lim.parametro)
        if val is None:
            continue

        if lim.valor_minimo is not None and val < lim.valor_minimo:
            alerta = Alerta(
                tanque_id=tanque_id,
                medicao_id=medicao.id,
                parametro=lim.parametro,
                valor_observado=val,
                limite_acionado=lim.valor_minimo,
                data_hora=medicao.data_hora,
                status='ativo'
            )
            db.session.add(alerta)
            alertas_gerados.append(alerta)

        elif lim.valor_maximo is not None and val > lim.valor_maximo:
            alerta = Alerta(
                tanque_id=tanque_id,
                medicao_id=medicao.id,
                parametro=lim.parametro,
                valor_observado=val,
                limite_acionado=lim.valor_maximo,
                data_hora=medicao.data_hora,
                status='ativo'
            )
            db.session.add(alerta)
            alertas_gerados.append(alerta)

    db.session.commit()
    return medicao, alertas_gerados
