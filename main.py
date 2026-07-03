from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List
from models import Todo, TodoCreate, TodoUpdate

app = FastAPI(
    title="Todo API",
    description="Uma simples API para gerenciar tarefas",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database (em produção, usar banco de dados real)
todos_db = {}
next_id = 1


@app.get("/", tags=["Root"])
def read_root():
    """Endpoint raiz da API"""
    return {"message": "Bem-vindo à Todo API"}


@app.get("/api/todos", response_model=List[Todo], tags=["Todos"])
def list_todos(completed: bool = None):
    """
    Lista todas as tarefas.
    
    Query params:
    - completed: filtrar por status de conclusão (opcional)
    """
    todos = list(todos_db.values())
    
    if completed is not None:
        todos = [t for t in todos if t["completed"] == completed]
    
    return todos


@app.post("/api/todos", response_model=Todo, status_code=status.HTTP_201_CREATED, tags=["Todos"])
def create_todo(todo: TodoCreate):
    """Cria uma nova tarefa"""
    global next_id
    
    todo_id = next_id
    next_id += 1
    
    now = datetime.now()
    new_todo = {
        "id": todo_id,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "created_at": now,
        "updated_at": now
    }
    
    todos_db[todo_id] = new_todo
    return new_todo


@app.get("/api/todos/{todo_id}", response_model=Todo, tags=["Todos"])
def get_todo(todo_id: int):
    """Obtém uma tarefa específica"""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {todo_id} não encontrada"
        )
    return todos_db[todo_id]


@app.put("/api/todos/{todo_id}", response_model=Todo, tags=["Todos"])
def update_todo(todo_id: int, todo_update: TodoUpdate):
    """Atualiza uma tarefa existente"""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {todo_id} não encontrada"
        )
    
    existing_todo = todos_db[todo_id]
    
    if todo_update.title is not None:
        existing_todo["title"] = todo_update.title
    if todo_update.description is not None:
        existing_todo["description"] = todo_update.description
    if todo_update.completed is not None:
        existing_todo["completed"] = todo_update.completed
    
    existing_todo["updated_at"] = datetime.now()
    
    return existing_todo


@app.delete("/api/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Todos"])
def delete_todo(todo_id: int):
    """Deleta uma tarefa"""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {todo_id} não encontrada"
        )
    
    del todos_db[todo_id]
    return None


@app.delete("/api/todos", status_code=status.HTTP_204_NO_CONTENT, tags=["Todos"])
def delete_all_todos():
    """Deleta todas as tarefas"""
    todos_db.clear()
    return None


@app.get("/api/todos/stats/summary", tags=["Stats"])
def get_stats():
    """Retorna estatísticas das tarefas"""
    total = len(todos_db)
    completed = sum(1 for t in todos_db.values() if t["completed"])
    pending = total - completed
    
    return {
        "total": total,
        "completed": completed,
        "pending": pending
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
