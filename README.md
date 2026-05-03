# Mini Projeto - Gestão de Alunos e Tarefas

API REST Flask com autenticação JWT, SQLAlchemy ORM, CRUD de alunos e tarefas.
Repositório: https://github.com/henricsoares/ifro-deploy-mini-app
Link do Render: https://ifro-deploy-mini-app.onrender.com/heath (no modo grátis, a aplicação pode demorar 50 segundos ou mais para responder)

## Instalação

```bash
pip install -r requirements.txt
```

## Executar

```bash
gunicorn app:app
```

A API estará disponível em `http://localhost:8000`

### Banco de Dados
- **SQLite** para desenvolvimento local (`database.db`)
- **PostgreSQL** para produção (configurar variável de ambiente `DATABASE_URL`)

### Admin Automático
- **Username:** `admin`
- **Password:** `admin123`
- Criado automaticamente na primeira execução

---

## Endpoints

### Health Check
```
GET /health
```

---

## 🔐 Autenticação

### Signup - Criar Conta (Público)
```
POST /signup
Content-Type: application/json

{
  "username": "usuario1",
  "email": "usuario@example.com",
  "password": "senha123"
}
```
- Cria usuário com role `aluno`
- Retorna: `201 Created` ou `409 Conflict` se email/username já existe

### Login
```
POST /login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```
- Retorna token JWT e informações do usuário
- Use o token no header: `Authorization: Bearer {token}`

---

## 👥 Alunos (Requer JWT - Admin)

### Listar todos os alunos
```
GET /alunos
Authorization: Bearer {token}
```

### Obter um aluno
```
GET /alunos/{id}
Authorization: Bearer {token}
```

### Criar aluno
```
POST /alunos
Authorization: Bearer {token}
Content-Type: application/json

{
  "nome": "João Silva",
  "email": "joao@example.com",
  "matricula": "2024001"
}
```

### Atualizar aluno
```
PUT /alunos/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "nome": "João Santos",
  "email": "joao.santos@example.com",
  "matricula": "2024001"
}
```

### Deletar aluno
```
DELETE /alunos/{id}
Authorization: Bearer {token}
```
- Deleta também todas as tarefas associadas

---

## 📋 Tarefas (Requer JWT - Admin)

### Listar todas as tarefas
```
GET /tarefas
Authorization: Bearer {token}
```

### Obter uma tarefa
```
GET /tarefas/{id}
Authorization: Bearer {token}
```

### Listar tarefas de um aluno
```
GET /alunos/{aluno_id}/tarefas
Authorization: Bearer {token}
```

### Criar tarefa
```
POST /tarefas
Authorization: Bearer {token}
Content-Type: application/json

{
  "titulo": "Implementar API",
  "descricao": "Criar endpoints REST",
  "aluno_id": 1
}
```

### Atualizar tarefa
```
PUT /tarefas/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "titulo": "Implementar API REST",
  "descricao": "Criar endpoints REST com Flask",
  "completa": true
}
```

### Deletar tarefa
```
DELETE /tarefas/{id}
Authorization: Bearer {token}
```

---

## 📦 Usar Collection no Insomnia

1. Abra o Insomnia
2. Clique em **Import** → **From File**
3. Selecione o arquivo `collection.json`
4. As requisições estarão prontas para uso!

### Variáveis de Ambiente
- `base_url`: http://localhost:8000
- `jwt_token`: Cole o token retornado pelo login
- `aluno_id`: ID do aluno (retornado ao criar)
- `tarefa_id`: ID da tarefa (retornado ao criar)

---

## 🏗️ Estrutura

```
Models:
  - User: username, email, password_hash, role (admin/aluno)
  - Aluno: nome, email, matricula
  - Tarefa: titulo, descricao, aluno_id, completa
```

## 🔒 Segurança
- ✅ Senhas hasheadas com bcrypt (werkzeug)
- ✅ JWT para autenticação stateless
- ✅ Autorização baseada em role (admin/aluno)
- ✅ Validação de entrada em todas as rotas
- ✅ SQLAlchemy ORM para proteção contra SQL injection
