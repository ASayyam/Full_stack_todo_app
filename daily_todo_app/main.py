from xmlrpc.client import boolean
from fastapi import FastAPI, Depends , HTTPException
from sqlalchemy import Engine
from sqlmodel import SQLModel, Field, create_engine ,Session,select
from daily_todo_app import setting
from typing import Annotated
from contextlib import asynccontextmanager

app = FastAPI()

#    engine is one for the whole application
connection_string : str = str(setting.DATABASE_URL).replace("postgresql","postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode":"require"}, pool_recycle=300,
    pool_size=10, echo=True)
# echo true terminal py sary code ko in order perform kr k dikha dy ga
# create model:

class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(index=True , min_length=3, max_length=54)
    is_completed: bool = Field(default=False)


def create_tables():                
   SQLModel.metadata.create_all(engine)


# todo1: Todo = Todo(content="first task")
# todo2: Todo = Todo(content="first task")


# session = Session(engine) # ye session ka instance create ho ra hy or engine ic liye likha k engina k through connectivity ho gi
# # todo app k ander jitni group of task hn gi to utny session create hn gy
# # like har user k liye login ka naya session create hota hy..separate session for each transaction

# session.add(todo1)                # abi ye data sirf add ho ra hy k kon kon sa database mein create krna hy
# session.add(todo2)
# print(f"Before Commit {todo1}")
# session.commit()   # commit ki command sy data database mein create ho jaye ga
# session.refresh(todo1) # refresh
# print(f"After Commit {todo1}")
# session.close


def get_session():
     with session(engine) as session:
          yield session


# yani hum ye keh ry hn k jb bhi hmari app start ho to sb sy pehly tables create hn or ic sy pehly koi bhi action perform na ho
@asynccontextmanager
async def lifespan(app:FastAPI):        # ic k through kuch aisy kaam perform hn gy jo app k satrt hony sy pehly hony chaheyin
     print("Creating Tables")
     create_tables()
     print("Tables created")
     yield 


app: FastAPI = FastAPI(listen=lifespan, title="daily Todo App", version= "1.0.0")     # lifespan k function k liye contextmanager chaeye ho ga  v


@app.get("/")
async def root():
    return {"message": "Welcome to daily todo app"}


@app.post("/todos/",response_model=Todo)
async def create_todo(todo:Todo,session:Annotated[Session,Depends(get_session)]):
    session.add(todo)                # abi ye data sirf add ho ra hy k kon kon sa database mein create krna hy
    session.commit()   # commit ki command sy data database mein create ho jaye ga
    session.refresh(todo) 
    return todo

@app.get("/todos/", response_model=list[Todo])
async def get_all(session:Annotated[Session,Depends(get_session)]):
        todo = session.exec(select(Todo)).all()

@app.get("/todos/{id}")
async def get_single_todo(id:int ,session:Annotated[Session, Depends(get_session)]):
     todo = session.exec(select(Todo).where(Todo.id == id)).first()
     return todo

@app.put("/todos/{id}")
async def edit_todo(todo:Todo, session:Annotated[Session,Depends(get_session)]):
     existing_todo = session.exec(select(Todo).where(Todo.id == todo.id)).first()
     if existing_todo:
          existing_todo.content = todo.content
          existing_todo.is_completed = todo.is_completed
          session.add(existing_todo)
          session.commit()
          session.refresh(existing_todo)
          return existing_todo
     else:
          raise HTTPException (status_code=404, detail= "No task found")


@app.delete("/todos/{id}")
async def delete_todo(id:int,session:Annotated[Session,Depends(get_session)]):
      todo = session.exec(select(Todo).where(Todo.id == id)).first()
      if todo:
           session.delete(todo)
           session.commit()
           session.refresh(todo)
           return {"message": "Task deleted successfully"}
      else:
           raise HTTPException (status_code=404, detail= "No task found")
     










