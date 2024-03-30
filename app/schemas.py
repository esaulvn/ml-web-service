from typing import List, Union
from datetime import datetime
from pydantic import BaseModel


class PredictionBase(BaseModel):
    model_type: str


class PredictionCreate(PredictionBase):
    datetime: datetime


class Prediction(PredictionBase):
    id: int
    datetime: datetime
    requester_username: str

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    full_name: Union[str, None] = None
    is_active: bool
    predictions: List[Prediction] = []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class Credits(BaseModel):
    amount: int


class UserCredits(Credits):
    owner_username: str
