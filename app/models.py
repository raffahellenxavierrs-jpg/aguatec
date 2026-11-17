from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), default='piscicultor')  # 'piscicultor' ou 'admin'
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tanques = db.relationship('Tanque', backref='proprietario', lazy=True, cascade='all, delete-orphan')

    @property
    def is_active(self):
        return self.ativo

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self):
        return self.perfil == 'admin'

    def __repr__(self):
        return f'<Usuario {self.email}>'


class Tanque(db.Model):
    __tablename__ = 'tanques'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao_local = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    medicoes = db.relationship('Medicao', backref='tanque', lazy=True, cascade='all, delete-orphan')
    limites = db.relationship('LimiteAlerta', backref='tanque', lazy=True, cascade='all, delete-orphan')
    alertas = db.relationship('Alerta', backref='tanque', lazy=True, cascade='all, delete-orphan')

    def ultima_medicao(self):
        return Medicao.query.filter_by(tanque_id=self.id).order_by(Medicao.data_hora.desc()).first()

    def __repr__(self):
        return f'<Tanque {self.nome}>'


class Medicao(db.Model):
    __tablename__ = 'medicoes'

    id = db.Column(db.Integer, primary_key=True)
    tanque_id = db.Column(db.Integer, db.ForeignKey('tanques.id'), nullable=False)
    data_hora = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    oxigenio_dissolvido = db.Column(db.Float, nullable=False)  # mg/L
    ph = db.Column(db.Float, nullable=False)
    temperatura = db.Column(db.Float, nullable=False)  # °C
    origem = db.Column(db.String(30), default='sensor')  # 'sensor', 'manual', 'simulador'

    alertas = db.relationship('Alerta', backref='medicao', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'tanque_id': self.tanque_id,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None,
            'oxigenio_dissolvido': self.oxigenio_dissolvido,
            'ph': self.ph,
            'temperatura': self.temperatura,
            'origem': self.origem
        }

    def __repr__(self):
        return f'<Medicao {self.id} Tanque={self.tanque_id}>'


class LimiteAlerta(db.Model):
    __tablename__ = 'limites_alerta'

    id = db.Column(db.Integer, primary_key=True)
    tanque_id = db.Column(db.Integer, db.ForeignKey('tanques.id'), nullable=False)
    parametro = db.Column(db.String(30), nullable=False)  # 'oxigenio', 'ph', 'temperatura'
    valor_minimo = db.Column(db.Float, nullable=True)
    valor_maximo = db.Column(db.Float, nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<LimiteAlerta {self.parametro} Min={self.valor_minimo} Max={self.valor_maximo}>'


class Alerta(db.Model):
    __tablename__ = 'alertas'

    id = db.Column(db.Integer, primary_key=True)
    tanque_id = db.Column(db.Integer, db.ForeignKey('tanques.id'), nullable=False)
    medicao_id = db.Column(db.Integer, db.ForeignKey('medicoes.id'), nullable=False)
    parametro = db.Column(db.String(30), nullable=False)
    valor_observado = db.Column(db.Float, nullable=False)
    limite_acionado = db.Column(db.Float, nullable=False)
    data_hora = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = db.Column(db.String(20), default='ativo')  # 'ativo', 'reconhecido', 'resolvido'

    def to_dict(self):
        return {
            'id': self.id,
            'tanque_id': self.tanque_id,
            'medicao_id': self.medicao_id,
            'parametro': self.parametro,
            'valor_observado': self.valor_observado,
            'limite_acionado': self.limite_acionado,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None,
            'status': self.status
        }

    def __repr__(self):
        return f'<Alerta {self.parametro} Val={self.valor_observado}>'
