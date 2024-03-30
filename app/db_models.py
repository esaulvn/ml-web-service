from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine("sqlite:///./sql_database.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    predictions = relationship("Prediction", back_populates="requester")
    credits = relationship("Credits", uselist=False, back_populates="owner")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, index=True)
    model_type = Column(String)
    requester_username = Column(String, ForeignKey("users.username"))
    requester = relationship("User", back_populates="predictions")


class Credits(Base):
    __tablename__ = "credits"

    owner_username = Column(String, ForeignKey("users.username"), primary_key=True)
    amount = Column(Integer)

    owner = relationship("User", back_populates="credits")
