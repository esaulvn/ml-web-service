import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Union
import joblib
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing_extensions import Annotated

import db_models
import schemas
import db_flows
from db_models import SessionLocal, engine

SECRET_KEY = secrets.token_bytes(32)

if SECRET_KEY is None:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db_models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
config = {'models_pricing': {'logreg': 5, 'ds_tree': 5, 'rd_forest': 10}, 'starting_credits': 100}

app = FastAPI()


@app.get("/")
def index():
    return {"text": "Классификация товаров"}


@app.on_event("startup")
def startup_event():
    global model, model_type
    model_type = 'logreg'
    model = load_model(model_type)

def verify_password(clean, hashed):
    return pwd_context.verify(clean, hashed)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    user = db_flows.get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Вы не авторизованы",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db_flows.get_user(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: Annotated[schemas.User, Depends(get_current_user)]):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db_flows.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    user = db_models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db_flows.create_user(db=db, user=user)
    db_flows.create_user_credits(db=db, credits=schemas.Credits(amount=config['starting_credits']),
                                 username=user.username)
    return user


@app.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)
) -> schemas.Token:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)

    return schemas.Token(access_token=access_token, token_type="bearer")


def load_model(model_type: str = 'logreg'):
    models_path = os.path.join(os.path.dirname(os.path.abspath(__file__))[:-4], 'models')
    with open(models_path + f'/{model_type}.joblib', 'rb') as f:
        model_instance = joblib.load(f)
    return model_instance


@app.post("/predict")
def predict(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
            data: dict, requested_model_type: str = 'logreg', db: Session = Depends(get_db)):
    input_text = data

    global model, model_type
    if requested_model_type != model_type:
        model_type = requested_model_type
        model = load_model(model_type)

    model_price = config['models_pricing'][model_type]
    user_credits = db_flows.get_user_credits(db=db, username=current_user.username)

    if user_credits.amount < model_price:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Недостаточно кредитов для использования данной модели, у вас {user_credits.amount} кредитов."
        )
    else:
        pred_result = model.predict(input_text)
        prediction = schemas.PredictionCreate(model_type=model_type, datetime=datetime.now(timezone.utc))
        db_flows.create_prediction(db=db, prediction=prediction, username=current_user.username)
        db_flows.change_user_credits(db=db, credits=schemas.Credits(amount=user_credits.amount - model_price),
                                     username=current_user.username)
        return {'pred_result': pred_result.tolist()}
