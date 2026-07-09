from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database.connection import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    industry = Column(String(100), nullable=True)
    status = Column(String(50), default="New")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())