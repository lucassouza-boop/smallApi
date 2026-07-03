import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from main import app, todos_db, reset_app


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_todos():
    """Limpa o banco de dados antes de cada teste"""
    todos_db.clear()
    globals()["next_id"] = 1
    yield
    todos_db.clear()


class TestRoot:
    """Testes para o endpoint raiz"""
    
    def test_read_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Bem-vindo à Todo API"}


class TestCreateTodo:
    """Testes para criação de tarefas"""
    
    def test_create_todo_success(self):
        payload = {
            "title": "Comprar leite",
            "description": "Comprar leite integral no supermercado",
            "completed": False
        }
        response = client.post("/api/todos", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Comprar leite"
        assert data["description"] == "Comprar leite integral no supermercado"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_todo_minimal(self):
        payload = {"title": "Tarefa simples"}
        response = client.post("/api/todos", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Tarefa simples"
        assert data["description"] is None
        assert data["completed"] is False
    
    def test_create_todo_missing_title(self):
        payload = {"description": "Sem título"}
        response = client.post("/api/todos", json=payload)
        assert response.status_code == 422
    
    def test_create_todo_empty_title(self):
        payload = {"title": ""}
        response = client.post("/api/todos", json=payload)
        assert response.status_code == 422


class TestListTodos:
    """Testes para listar tarefas"""
    
    def test_list_todos_empty(self):
        response = client.get("/api/todos")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_todos_multiple(self):
        # Criar 3 tarefas
        for i in range(3):
            payload = {"title": f"Tarefa {i+1}"}
            client.post("/api/todos", json=payload)
        
        response = client.get("/api/todos")
        assert response.status_code == 200
        todos = response.json()
        assert len(todos) == 3
        assert todos[0]["title"] == "Tarefa 1"
        assert todos[1]["title"] == "Tarefa 2"
        assert todos[2]["title"] == "Tarefa 3"
    
    def test_list_todos_filter_completed(self):
        # Criar tarefas com diferentes status
        client.post("/api/todos", json={"title": "Pendente 1", "completed": False})
        client.post("/api/todos", json={"title": "Concluída", "completed": True})
        client.post("/api/todos", json={"title": "Pendente 2", "completed": False})
        
        # Filtrar apenas concluídas
        response = client.get("/api/todos?completed=true")
        assert response.status_code == 200
        todos = response.json()
        assert len(todos) == 1
        assert todos[0]["title"] == "Concluída"
        assert todos[0]["completed"] is True
    
    def test_list_todos_filter_pending(self):
        # Criar tarefas com diferentes status
        client.post("/api/todos", json={"title": "Pendente 1", "completed": False})
        client.post("/api/todos", json={"title": "Concluída", "completed": True})
        client.post("/api/todos", json={"title": "Pendente 2", "completed": False})
        
        # Filtrar apenas pendentes
        response = client.get("/api/todos?completed=false")
        assert response.status_code == 200
        todos = response.json()
        assert len(todos) == 2
        assert todos[0]["title"] == "Pendente 1"
        assert todos[1]["title"] == "Pendente 2"


class TestGetTodo:
    """Testes para obter uma tarefa específica"""
    
    def test_get_todo_success(self):
        # Criar uma tarefa
        create_response = client.post("/api/todos", json={"title": "Minha tarefa"})
        todo_id = create_response.json()["id"]
        
        # Obter a tarefa
        response = client.get(f"/api/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Minha tarefa"
    
    def test_get_todo_not_found(self):
        response = client.get("/api/todos/999")
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"]


class TestUpdateTodo:
    """Testes para atualizar tarefas"""
    
    def test_update_todo_success(self):
        # Criar uma tarefa
        create_response = client.post("/api/todos", json={"title": "Original"})
        todo_id = create_response.json()["id"]
        
        # Atualizar
        update_payload = {"title": "Atualizada"}
        response = client.put(f"/api/todos/{todo_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Atualizada"
    
    def test_update_todo_complete(self):
        # Criar uma tarefa pendente
        create_response = client.post(
            "/api/todos",
            json={"title": "Pendente", "completed": False}
        )
        todo_id = create_response.json()["id"]
        
        # Marcar como concluída
        response = client.put(
            f"/api/todos/{todo_id}",
            json={"completed": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
    
    def test_update_todo_multiple_fields(self):
        # Criar uma tarefa
        create_response = client.post(
            "/api/todos",
            json={"title": "Original", "description": "Desc original"}
        )
        todo_id = create_response.json()["id"]
        
        # Atualizar múltiplos campos
        update_payload = {
            "title": "Novo título",
            "description": "Nova descrição",
            "completed": True
        }
        response = client.put(f"/api/todos/{todo_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Novo título"
        assert data["description"] == "Nova descrição"
        assert data["completed"] is True
    
    def test_update_todo_not_found(self):
        response = client.put("/api/todos/999", json={"title": "Nova"})
        assert response.status_code == 404


class TestDeleteTodo:
    """Testes para deletar tarefas"""
    
    def test_delete_todo_success(self):
        # Criar uma tarefa
        create_response = client.post("/api/todos", json={"title": "Para deletar"})
        todo_id = create_response.json()["id"]
        
        # Deletar
        response = client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204
        
        # Verificar que foi deletada
        get_response = client.get(f"/api/todos/{todo_id}")
        assert get_response.status_code == 404
    
    def test_delete_todo_not_found(self):
        response = client.delete("/api/todos/999")
        assert response.status_code == 404
    
    def test_delete_all_todos_success(self):
        # Criar 3 tarefas
        for i in range(3):
            client.post("/api/todos", json={"title": f"Tarefa {i+1}"})
        
        # Verificar que foram criadas
        list_response = client.get("/api/todos")
        assert len(list_response.json()) == 3
        
        # Deletar todas
        response = client.delete("/api/todos")
        assert response.status_code == 204
        
        # Verificar que foram deletadas
        list_response = client.get("/api/todos")
        assert list_response.json() == []


class TestStats:
    """Testes para endpoint de estatísticas"""
    
    def test_get_stats_empty(self):
        response = client.get("/api/todos/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["pending"] == 0
    
    def test_get_stats_with_todos(self):
        # Criar tarefas
        client.post("/api/todos", json={"title": "Pendente 1", "completed": False})
        client.post("/api/todos", json={"title": "Concluída 1", "completed": True})
        client.post("/api/todos", json={"title": "Pendente 2", "completed": False})
        client.post("/api/todos", json={"title": "Concluída 2", "completed": True})
        
        response = client.get("/api/todos/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert data["completed"] == 2
        assert data["pending"] == 2
