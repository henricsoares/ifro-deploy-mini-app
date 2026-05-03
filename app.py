from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from sqlalchemy.exc import IntegrityError

# Inicializar Flask
app = Flask(__name__)

# Configuração do Banco de Dados
db_path = os.path.join(os.path.dirname(__file__), "database.db")
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Render usa DATABASE_URL no formato postgres://, que deve ser convertido para SQLAlchemy
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configurações JWT
app.config["JWT_SECRET_KEY"] = "super-secret-key-change-in-production"
app.config["SECRET_KEY"] = "super-secret-key-change-in-production"

# Inicializar extensões
db = SQLAlchemy(app)
jwt = JWTManager(app)

# ========== MODELS ==========


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="aluno", nullable=False)  # admin, aluno
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "criado_em": self.criado_em.isoformat(),
        }


class Aluno(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com tarefas
    tarefas = db.relationship(
        "Tarefa", backref="aluno", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "matricula": self.matricula,
            "criado_em": self.criado_em.isoformat(),
        }


class Tarefa(db.Model):
    __tablename__ = "tarefas"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, default="")
    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)
    completa = db.Column(db.Boolean, default=False)
    criada_em = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "aluno_id": self.aluno_id,
            "completa": self.completa,
            "criada_em": self.criada_em.isoformat(),
        }


# ========== INICIALIZAÇÃO ==========


def criar_admin():
    try:
        admin = User(username="admin", email="admin@example.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin criado")
    except IntegrityError:
        db.session.rollback()
        print("✓ Admin já existe")


# ========== ROTAS DE AUTENTICAÇÃO ==========


@app.route("/signup", methods=["POST"])
def signup():
    """Cria uma nova conta (usuário comum com role 'aluno')"""
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Dados incompletos"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username já existe"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email já existe"}), 409

    user = User(username=username, email=email, role="aluno")
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    aluno = Aluno(nome=username, email=email, matricula=f"ALU{user.id:04d}")
    db.session.add(aluno)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Conta criada com sucesso",
                "user": user.to_dict(),
                "aluno": aluno.to_dict(),
            }
        ),
        201,
    )


@app.route("/login", methods=["POST"])
def login():
    """Autentica um usuário e retorna JWT"""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciais inválidas"}), 401

    access_token = create_access_token(identity=username)
    return jsonify({"access_token": access_token, "user": user.to_dict()}), 200


# ========== ROTAS DE ALUNOS (CRUD) ==========


@app.route("/alunos", methods=["GET"])
@jwt_required()
def listar_alunos():
    """Lista todos os alunos"""
    alunos = Aluno.query.all()
    return jsonify([aluno.to_dict() for aluno in alunos]), 200


@app.route("/alunos/<int:aluno_id>", methods=["GET"])
@jwt_required()
def obter_aluno(aluno_id):
    """Obtém um aluno específico"""
    aluno = Aluno.query.get(aluno_id)
    if not aluno:
        return jsonify({"error": "Aluno não encontrado"}), 404

    return jsonify(aluno.to_dict()), 200


@app.route("/alunos", methods=["POST"])
@jwt_required()
def criar_aluno():
    """Cria um novo aluno - apenas admin"""
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if user.role != "admin":
        return jsonify({"error": "Apenas admin pode criar alunos"}), 403

    data = request.get_json()
    nome = data.get("nome")
    email = data.get("email")
    matricula = data.get("matricula")

    if not nome or not email or not matricula:
        return jsonify({"error": "Dados incompletos"}), 400

    if Aluno.query.filter_by(email=email).first():
        return jsonify({"error": "Email já existe"}), 409

    if Aluno.query.filter_by(matricula=matricula).first():
        return jsonify({"error": "Matrícula já existe"}), 409

    aluno = Aluno(nome=nome, email=email, matricula=matricula)
    db.session.add(aluno)
    db.session.commit()

    return (
        jsonify({"message": "Aluno criado com sucesso", "aluno": aluno.to_dict()}),
        201,
    )


@app.route("/alunos/<int:aluno_id>", methods=["PUT"])
@jwt_required()
def atualizar_aluno(aluno_id):
    """Atualiza um aluno - apenas admin"""
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if user.role != "admin":
        return jsonify({"error": "Apenas admin pode atualizar alunos"}), 403

    aluno = Aluno.query.get(aluno_id)
    if not aluno:
        return jsonify({"error": "Aluno não encontrado"}), 404

    data = request.get_json()

    if "nome" in data:
        aluno.nome = data["nome"]
    if "email" in data:
        aluno.email = data["email"]
    if "matricula" in data:
        aluno.matricula = data["matricula"]

    db.session.commit()

    return (
        jsonify({"message": "Aluno atualizado com sucesso", "aluno": aluno.to_dict()}),
        200,
    )


@app.route("/alunos/<int:aluno_id>", methods=["DELETE"])
@jwt_required()
def deletar_aluno(aluno_id):
    """Deleta um aluno - apenas admin"""
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if user.role != "admin":
        return jsonify({"error": "Apenas admin pode deletar alunos"}), 403

    aluno = Aluno.query.get(aluno_id)
    if not aluno:
        return jsonify({"error": "Aluno não encontrado"}), 404

    db.session.delete(aluno)
    db.session.commit()

    return jsonify({"message": "Aluno deletado com sucesso"}), 200


# ========== ROTAS DE TAREFAS (CRUD) ==========


@app.route("/tarefas", methods=["GET"])
@jwt_required()
def listar_tarefas():
    """Lista todas as tarefas"""
    tarefas = Tarefa.query.all()
    return jsonify([tarefa.to_dict() for tarefa in tarefas]), 200


@app.route("/tarefas/<int:tarefa_id>", methods=["GET"])
@jwt_required()
def obter_tarefa(tarefa_id):
    """Obtém uma tarefa específica"""
    tarefa = Tarefa.query.get(tarefa_id)
    if not tarefa:
        return jsonify({"error": "Tarefa não encontrada"}), 404

    return jsonify(tarefa.to_dict()), 200


@app.route("/tarefas", methods=["POST"])
@jwt_required()
def criar_tarefa():
    """Cria uma nova tarefa - apenas admin"""
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if user.role != "admin":
        return jsonify({"error": "Apenas admin pode criar tarefas"}), 403

    data = request.get_json()
    titulo = data.get("titulo")
    descricao = data.get("descricao", "")
    aluno_id = data.get("aluno_id")

    if not titulo or not aluno_id:
        return jsonify({"error": "Dados incompletos"}), 400

    aluno = Aluno.query.get(aluno_id)
    if not aluno:
        return jsonify({"error": "Aluno não encontrado"}), 404

    tarefa = Tarefa(titulo=titulo, descricao=descricao, aluno_id=aluno_id)
    db.session.add(tarefa)
    db.session.commit()

    return (
        jsonify({"message": "Tarefa criada com sucesso", "tarefa": tarefa.to_dict()}),
        201,
    )


@app.route("/tarefas/<int:tarefa_id>", methods=["PUT"])
@jwt_required()
def atualizar_tarefa(tarefa_id):
    """Atualiza uma tarefa - apenas admin"""
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if user.role != "admin":
        return jsonify({"error": "Apenas admin pode atualizar tarefas"}), 403

    tarefa = Tarefa.query.get(tarefa_id)
    if not tarefa:
        return jsonify({"error": "Tarefa não encontrada"}), 404

    data = request.get_json()

    if "titulo" in data:
        tarefa.titulo = data["titulo"]
    if "descricao" in data:
        tarefa.descricao = data["descricao"]
    if "completa" in data:
        tarefa.completa = data["completa"]

    db.session.commit()

    return (
        jsonify(
            {"message": "Tarefa atualizada com sucesso", "tarefa": tarefa.to_dict()}
        ),
        200,
    )


@app.route("/tarefas/<int:tarefa_id>", methods=["DELETE"])
@jwt_required()
def deletar_tarefa(tarefa_id):
    """Deleta uma tarefa - apenas admin"""
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    if user.role != "admin":
        return jsonify({"error": "Apenas admin pode deletar tarefas"}), 403

    tarefa = Tarefa.query.get(tarefa_id)
    if not tarefa:
        return jsonify({"error": "Tarefa não encontrada"}), 404

    db.session.delete(tarefa)
    db.session.commit()

    return jsonify({"message": "Tarefa deletada com sucesso"}), 200


@app.route("/alunos/<int:aluno_id>/tarefas", methods=["GET"])
@jwt_required()
def listar_tarefas_aluno(aluno_id):
    """Lista tarefas de um aluno específico"""
    aluno = Aluno.query.get(aluno_id)
    if not aluno:
        return jsonify({"error": "Aluno não encontrado"}), 404

    tarefas = Tarefa.query.filter_by(aluno_id=aluno_id).all()
    return jsonify([tarefa.to_dict() for tarefa in tarefas]), 200


# ========== ROTA DE HEALTH CHECK ==========


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ========== INICIALIZAÇÃO DO BANCO ==========


def init_db():
    with app.app_context():
        db.create_all()
        criar_admin()

init_db()