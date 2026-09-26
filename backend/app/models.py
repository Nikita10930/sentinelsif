from sqlalchemy import Column, Integer, String, Text, Float, Boolean, Date, DateTime, func
from .database import Base

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    department = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    hazard_type = Column(String(255), nullable=True, index=True)  # Filled in later by NLP classifier
    severity = Column(String(100), nullable=True)                 # Filled in later
    risk_score = Column(Float, nullable=True, default=0.0)
    # True if this report was flagged as a likely duplicate (cosine similarity
    # > 0.75) of a recent report in the same department. Used by
    # calculate_risk_score() to apply a reduced weight for duplicates, so
    # accidental double-submissions don't inflate the department's risk score.
    is_duplicate = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Report(id={self.report_id}, department='{self.department}', date='{self.date}')>"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False)  # e.g. "worker", "supervisor", "admin"
    hashed_password = Column(String(255), nullable=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}', role='{self.role}')>"