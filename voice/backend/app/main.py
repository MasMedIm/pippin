from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .auth import CurrentUser, authenticate_user, create_access_token, get_db
from .crud import create_move, create_task, get_moves, get_tasks, create_user
from .models import Base, Move
from .schemas import (
    MoveCreate,
    MoveOut,
    TaskCreate,
    TaskOut,
    Token,
    UserCreate,
    UserOut,
)

# Realtime helpers -----------------------------------------------------------

from pydantic import BaseModel

from .openai_realtime import create_ephemeral_session
from .llm_dispatcher import FunctionCallError, handle_function_call
from fastapi.middleware.cors import CORSMiddleware

from .database import health_check

# Create tables on startup (replace with Alembic in prod)
from .database import engine as _engine

Base.metadata.create_all(bind=_engine)


app = FastAPI(title="pippin Backend", version="0.1.0")

# Allow all CORS origins for skeleton. Adjust in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"], status_code=status.HTTP_200_OK)
def health():
    """Return application & database health status."""
    db_ok = health_check()
    return {"app": "ok", "db": "ok" if db_ok else "error"}


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------


@app.post("/api/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    from .models import User  # local import to avoid circular

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = create_user(db, user_in.email, user_in.password, user_in.full_name)
    return user


# Because OAuth2PasswordRequestForm uses form-url-encoded body, we keep established pattern
@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


# Test protected endpoint
@app.get("/api/auth/me", response_model=UserOut)
def read_me(current_user: CurrentUser):
    return current_user


# ---------------------------------------------------------------------------
# Moves & tasks endpoints (just enough for function-call test)
# ---------------------------------------------------------------------------


@app.post("/api/moves", response_model=MoveOut, status_code=status.HTTP_201_CREATED)
def create_move_route(move_in: MoveCreate, user: CurrentUser, db: Session = Depends(get_db)):
    move = create_move(db, user=user, **move_in.dict())
    return move


@app.get("/api/moves", response_model=list[MoveOut])
def list_moves(user: CurrentUser, db: Session = Depends(get_db)):
    return get_moves(db, user)


@app.post("/api/moves/{move_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task_route(move_id: int, task_in: TaskCreate, user: CurrentUser, db: Session = Depends(get_db)):
    move: Move | None = db.query(Move).filter(Move.id == move_id, Move.user_id == user.id).first()
    if not move:
        raise HTTPException(status_code=404, detail="Move not found")
    task = create_task(db, move, **task_in.dict())
    return task


@app.get("/api/moves/{move_id}/tasks", response_model=list[TaskOut])
def list_tasks_route(move_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    move: Move | None = db.query(Move).filter(Move.id == move_id, Move.user_id == user.id).first()
    if not move:
        raise HTTPException(status_code=404, detail="Move not found")
    return get_tasks(db, move)


# ---------------------------------------------------------------------------
# Realtime / WebRTC integration – Ephemeral token minting
# ---------------------------------------------------------------------------


class RealtimeSessionIn(BaseModel):
    voice: str | None = None


# No authentication required; this endpoint is publicly accessible.


@app.post("/api/realtime/session", tags=["Realtime"])
async def create_realtime_session(payload: RealtimeSessionIn):
    """Return an *ephemeral* API key for the browser to connect via WebRTC.

    The endpoint delegates to the OpenAI REST API while keeping the secret key
    on the server.
    """

    try:
        data = await create_ephemeral_session(voice=payload.voice)
        return data
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ---------------------------------------------------------------------------
# Function-call dispatcher
# ---------------------------------------------------------------------------


class FunctionCallIn(BaseModel):
    name: str
    arguments: dict


@app.post("/api/realtime/function-call", tags=["Realtime"])
def realtime_function_call(
    data: FunctionCallIn,
    db: Session = Depends(get_db),
):
    """Execute an LLM function-call event emitted via data-channel and persist to DB."""
    # Log the function call for debugging
    
    try:
        result = handle_function_call(data.name, data.arguments, db=db)
        # Serialize model instances or return raw result
        from .models import Move, Task
        from .schemas import MoveOut, TaskOut

        if isinstance(result, Move):
            payload = MoveOut.from_orm(result).dict()
        elif isinstance(result, Task):
            payload = TaskOut.from_orm(result).dict()
        else:
            payload = result

        return {"status": "ok", "result": payload}
    except FunctionCallError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


