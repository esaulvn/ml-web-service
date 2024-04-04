from sqlalchemy.orm import Session
import db_models
import schemas


def get_user(db: Session, username: str):
    return db.query(db_models.User).filter(db_models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(db_models.User).filter(db_models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.User):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_predictions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_models.Prediction).offset(skip).limit(limit).all()


def create_prediction(db: Session, prediction: schemas.PredictionCreate, username: str):
    db_prediction = db_models.Prediction(**prediction.model_dump(), requester_username=username)
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction


def get_user_credits(db: Session, username: str):
    return db.query(db_models.Credits).filter(db_models.Credits.owner_username == username).first()


def create_user_credits(db: Session, credits: schemas.Credits, username: str):
    db_credits = db_models.Credits(**credits.model_dump(), owner_username=username)
    db.add(db_credits)
    db.commit()
    db.refresh(db_credits)
    return db_credits


def change_user_credits(db: Session, credits: schemas.Credits, username: str):
    db_credits = db.query(db_models.Credits).filter(db_models.Credits.owner_username == username).first()
    db_credits.amount = credits.amount
    db.commit()
    db.refresh(db_credits)
    return db_credits
