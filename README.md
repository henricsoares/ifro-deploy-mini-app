# Mini Projeto - Gestão de Alunos e Tarefas

API REST Flask com autenticação JWT, CRUD de alunos e tarefas.

## Instalação

```bash
pip install -r requirements.txt
```

## Executar

```bash
python app.py
```

A API estará disponível em `http://localhost:5000`

### Admin Automático
- **Username:** `admin`
- **Password:** `admin123`

---

## Endpoints

### Health Check
```bash
GET /health
```

### Autenticação

#### Login
```bash
POST /login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

---

### Alunos (Requer JWT)

#### Listar todos
```bash
GET /alunos
Authorization: Bearer {token}
```

#### Obter um aluno
```bash
GET /alunos/{id}
Authorization: Bearer {token}
```

#### Criar aluno (Admin)
```bash
POST /alunos
Authorization: Bearer {token}
Content-Type: application/json

{
  "nome": "João Silva",
  "email": "joao@example.com",
  "matricula": "2024001"
}
```

#### Atualizar aluno (Admin)
```bash
PUT /alunos/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "nome": "João Santos",
  "email": "joao.santos@example.com",
  "matricula": "2024001"
}
```

#### Deletar aluno (Admin)
```bash
DELETE /alunos/{id}
Authorization: Bearer {token}
```

---

### Tarefas (Requer JWT)

#### Listar todas
```bash
GET /tarefas
Authorization: Bearer {token}
```

#### Obter uma tarefa
```bash
GET /tarefas/{id}
Authorization: Bearer {token}
```

#### Listar tarefas de um aluno
```bash
GET /alunos/{aluno_id}/tarefas
Authorization: Bearer {token}
```

#### Criar tarefa (Admin)
```bash
POST /tarefas
Authorization: Bearer {token}
Content-Type: application/json

{
  "titulo": "Implementar API",
  "descricao": "Criar endpoints REST",
  "aluno_id": "{aluno_id}"
}
```

#### Atualizar tarefa (Admin)
```bash
PUT /tarefas/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "titulo": "Implementar API REST",
  "descricao": "Criar endpoints REST com Flask",
  "completa": true
}
```

#### Deletar tarefa (Admin)
```bash
DELETE /tarefas/{id}
Authorization: Bearer {token}
```

---

## Usar Collection no Insomnia

1. Abra o Insomnia
2. Clique em **Import** → **From File**
3. Selecione o arquivo `collection.json`
4. As requisições estarão prontas para uso!
