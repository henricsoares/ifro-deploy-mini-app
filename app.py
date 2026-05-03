from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)

# Configurações JWT
app.config["JWT_SECRET_KEY"] = "super-secret-key-change-in-production"
jwt = JWTManager(app)

# Banco de dados em memória
users_db = {}
alunos_db = {}
tarefas_db = {}

# Função para criar admin automaticamente
def criar_admin():
    if "admin" not in users_db:
        users_db["admin"] = {
            "id": str(uuid.uuid4()),
            "password": generate_password_hash("admin123"),
            "email": "admin@example.com",
            "role": "admin"
        }
        print("✓ Admin criado automaticamente (username: admin, password: admin123)")

# Criar admin ao iniciar
criar_admin()

# --- Rotas de Autenticação ---

@app.route("/login", methods=["POST"])
def login():
    """Autentica um usuário e retorna JWT"""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = users_db.get(username)
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Credenciais inválidas"}), 401

    access_token = create_access_token(identity=username)
    return jsonify({
        "access_token": access_token,
        "user": {
            "username": username,
            "email": user["email"],
            "role": user.get("role", "usuario")
        }
    }), 200


# --- Rotas de Alunos (CRUD) ---

@app.route("/alunos", methods=["GET"])
@jwt_required()
def listar_alunos():
    """Lista todos os alunos"""
    alunos = [
        {
            "id": aluno["id"],
            "nome": aluno["nome"],
            "email": aluno["email"],
            "matricula": aluno["matricula"]
        }
        for aluno in alunos_db.values()
    ]
    return jsonify(alunos), 200


@app.route("/alunos/<aluno_id>", methods=["GET"])
@jwt_required()
def obter_aluno(aluno_id):
    """Obtém um aluno específico"""
    aluno = alunos_db.get(aluno_id)
    if not aluno:
        return jsonify({"error": "Aluno não encontrado"}), 404

    return jsonify({
        "id": aluno["id"],
        "nome": aluno["nome"],
        "email": aluno["email"],
        "matricula": aluno["matricula"]
    }), 200


@app.route("/alunos", methods=["POST"])
@jwt_required()
def criar_aluno():
    """Cria um novo aluno - apenas admin"""
    current_user = get_jwt_identity()
    user = users_db.get(current_user)

    if user.get("role") != "admin":
        return jsonify({"error": "Apenas admin pode criar alunos"}), 403

    data = request.get_json()
    nome = data.get("nome")
    email = data.get("email")
    matricula = data.get("matricula")

    if not nome or not email or not matricula:
        return jsonify({"error": "Dados incompletos"}), 400

    aluno_id = str(uuid.uuid4())
    alunos_db[aluno_id] = {
        "id": aluno_id,
        "nome": nome,
        "email": email,
        "matricula": matricula
    }

    return jsonify({
        "message": "Aluno criado com sucesso",
        "id": aluno_id
    }), 201


@app.route("/alunos/<aluno_id>", methods=["PUT"])
@jwt_required()
def atualizar_aluno(aluno_id):
    """Atualiza um aluno - apenas admin"""
    current_user = get_jwt_identity()
    user = users_db.get(current_user)

    if user.get("role") != "admin":
        return jsonify({"error": "Apenas admin pode atualizar alunos"}), 403

    if aluno_id not in alunos_db:
        return jsonify({"error": "Aluno não encontrado"}), 404

    data = request.get_json()
    if "nome" in data:
        alunos_db[aluno_id]["nome"] = data["nome"]
    if "email" in data:
        alunos_db[aluno_id]["email"] = data["email"]
    if "matricula" in data:
        alunos_db[aluno_id]["matricula"] = data["matricula"]

    return jsonify({"message": "Aluno atualizado com sucesso"}), 200


@app.route("/alunos/<aluno_id>", methods=["DELETE"])
@jwt_required()
def deletar_aluno(aluno_id):
    """Deleta um aluno - apenas admin"""
    current_user = get_jwt_identity()
    user = users_db.get(current_user)

    if user.get("role") != "admin":
        return jsonify({"error": "Apenas admin pode deletar alunos"}), 403

    if aluno_id not in alunos_db:
        return jsonify({"error": "Aluno não encontrado"}), 404

    del alunos_db[aluno_id]
    # Deletar tarefas do aluno
    tarefas_para_deletar = [t_id for t_id, t in tarefas_db.items() if t["aluno_id"] == aluno_id]
    for t_id in tarefas_para_deletar:
        del tarefas_db[t_id]

    return jsonify({"message": "Aluno deletado com sucesso"}), 200


# --- Rotas de Tarefas (CRUD) ---

@app.route("/tarefas", methods=["GET"])
@jwt_required()
def listar_tarefas():
    """Lista todas as tarefas"""
    tarefas = [
        {
            "id": tarefa["id"],
            "titulo": tarefa["titulo"],
            "descricao": tarefa["descricao"],
            "aluno_id": tarefa["aluno_id"],
            "completa": tarefa["completa"],
            "criada_em": tarefa["criada_em"]
        }
        for tarefa in tarefas_db.values()
    ]
    return jsonify(tarefas), 200


@app.route("/tarefas/<tarefa_id>", methods=["GET"])
@jwt_required()
def obter_tarefa(tarefa_id):
    """Obtém uma tarefa específica"""
    tarefa = tarefas_db.get(tarefa_id)
    if not tarefa:
        return jsonify({"error": "Tarefa não encontrada"}), 404

    return jsonify({
        "id": tarefa["id"],
        "titulo": tarefa["titulo"],
        "descricao": tarefa["descricao"],
        "aluno_id": tarefa["aluno_id"],
        "completa": tarefa["completa"],
        "criada_em": tarefa["criada_em"]
    }), 200


@app.route("/tarefas", methods=["POST"])
@jwt_required()
def criar_tarefa():
    """Cria uma nova tarefa - apenas admin"""
    current_user = get_jwt_identity()
    user = users_db.get(current_user)

    if user.get("role") != "admin":
        return jsonify({"error": "Apenas admin pode criar tarefas"}), 403

    data = request.get_json()
    titulo = data.get("titulo")
    descricao = data.get("descricao")
    aluno_id = data.get("aluno_id")

    if not titulo or not aluno_id:
        return jsonify({"error": "Dados incompletos"}), 400

    if aluno_id not in alunos_db:
        return jsonify({"error": "Aluno não encontrado"}), 404

    tarefa_id = str(uuid.uuid4())
    from datetime import datetime
    tarefas_db[tarefa_id] = {
        "id": tarefa_id,
        "titulo": titulo,
        "descricao": descricao or "",
        "aluno_id": aluno_id,
        "completa": False,
        "criada_em": datetime.now().isoformat()
    }

    return jsonify({
        "message": "Tarefa criada com sucesso",
        "id": tarefa_id
    }), 201


@app.route("/tarefas/<tarefa_id>", methods=["PUT"])
@jwt_required()
def atualizar_tarefa(tarefa_id):
    """Atualiza uma tarefa - apenas admin"""
    current_user = get_jwt_identity()
    user = users_db.get(current_user)

    if user.get("role") != "admin":
        return jsonify({"error": "Apenas admin pode atualizar tarefas"}), 403

    if tarefa_id not in tarefas_db:
        return jsonify({"error": "Tarefa não encontrado"}), 404

    data = request.get_json()
    if "titulo" in data:
        tarefas_db[tarefa_id]["titulo"] = data["titulo"]
    if "descricao" in data:
        tarefas_db[tarefa_id]["descricao"] = data["descricao"]
    if "completa" in data:
        tarefas_db[tarefa_id]["completa"] = data["completa"]

    return jsonify({"message": "Tarefa atualizada com sucesso"}), 200


@app.route("/tarefas/<tarefa_id>", methods=["DELETE"])
@jwt_required()
def deletar_tarefa(tarefa_id):
    """Deleta uma tarefa - apenas admin"""
    current_user = get_jwt_identity()
    user = users_db.get(current_user)

    if user.get("role") != "admin":
        return jsonify({"error": "Apenas admin pode deletar tarefas"}), 403

    if tarefa_id not in tarefas_db:
        return jsonify({"error": "Tarefa não encontrada"}), 404

    del tarefas_db[tarefa_id]
    return jsonify({"message": "Tarefa deletada com sucesso"}), 200


@app.route("/alunos/<aluno_id>/tarefas", methods=["GET"])
@jwt_required()
def listar_tarefas_aluno(aluno_id):
    """Lista tarefas de um aluno específico"""
    if aluno_id not in alunos_db:
        return jsonify({"error": "Aluno não encontrado"}), 404

    tarefas = [
        {
            "id": tarefa["id"],
            "titulo": tarefa["titulo"],
            "descricao": tarefa["descricao"],
            "completa": tarefa["completa"],
            "criada_em": tarefa["criada_em"]
        }
        for tarefa in tarefas_db.values()
        if tarefa["aluno_id"] == aluno_id
    ]
    return jsonify(tarefas), 200


# --- Rota de Health Check ---

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
