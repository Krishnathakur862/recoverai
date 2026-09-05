from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from database import Base


class Payment(Base):

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(String, unique=True, index=True)
    customer_id = Column(String, index=True)

    amount = Column(Float)
    currency = Column(String)

    status = Column(String)
    payment_method = Column(String)

    failure_reason = Column(String, nullable=True)

    days_since_last_payment = Column(Integer)

    subscription_status = Column(String)

    risk_score = Column(Float, default=0)
    risk_level = Column(String, default="NONE")

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class RecoveryAction(Base):

    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(String, index=True)

    action_type = Column(String)

    ai_reason = Column(String)

    confidence = Column(Float)

    status = Column(String, default="PENDING")

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    executed_at = Column(
        DateTime,
        nullable=True
    )


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(String, index=True)

    event = Column(String)

    decision = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )