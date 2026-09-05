from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
import os
import sys
import math

from datetime import datetime

# Allow backend to access the AI module
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from ai.risk_engine import calculate_risk
from ai.recovery_engine import recommend_recovery_action
from database import SessionLocal
from models import Payment, RecoveryAction, AuditLog


app = FastAPI(
    title="RecoverAI API",
    description="AI-powered payment recovery and revenue risk analysis platform",
    version="2.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# CONFIGURATION / GUARDRAILS
# =========================================================

MAX_RECOVERY_ATTEMPTS = 2
HIGH_RISK_REQUIRES_APPROVAL = True


# =========================================================
# PAYMENT DATASET
# =========================================================

DATA_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "payments.csv"
    )
)


def load_payments():
    """
    Load payment dataset while keeping empty CSV
    fields as empty strings.
    """
    return pd.read_csv(
        DATA_PATH,
        keep_default_na=False
    )


# =========================================================
# AI PAYMENT ANALYSIS
# =========================================================

def analyze_payment(row):

    payment = row.to_dict()

    amount = float(payment["amount"])
    days = int(payment["days_since_last_payment"])

    risk_score = calculate_risk(
        {
            "status": str(payment["status"]),
            "amount": str(amount),
            "days_since_last_payment": str(days),
            "subscription_status": str(payment["subscription_status"]),
            "failure_reason": str(payment["failure_reason"])
        }
    )

    # Guarantee a valid JSON number
    if not math.isfinite(float(risk_score)):
        risk_score = 0

    risk_score = float(risk_score)

    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    elif risk_score > 0:
        risk_level = "LOW"
    else:
        risk_level = "NONE"

    return {
        "payment_id": str(payment["payment_id"]),
        "customer_id": str(payment["customer_id"]),
        "amount": amount,
        "currency": str(payment["currency"]),
        "status": str(payment["status"]),
        "payment_method": str(payment["payment_method"]),
        "failure_reason": str(payment["failure_reason"]),
        "days_since_last_payment": days,
        "subscription_status": str(payment["subscription_status"]),
        "risk_score": risk_score,
        "risk_level": risk_level
    }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "RecoverAI API is running",
        "status": "active",
        "version": "2.0.0"
    }


# =========================================================
# PAYMENTS
# =========================================================

@app.get("/payments")
def get_payments():

    df = load_payments()

    payments = [
        analyze_payment(row)
        for _, row in df.iterrows()
    ]

    return {
        "total_payments": len(payments),
        "payments": payments
    }


# =========================================================
# SUMMARY
# =========================================================

@app.get("/summary")
def get_summary():

    df = load_payments()

    analyzed = [
        analyze_payment(row)
        for _, row in df.iterrows()
    ]

    successful = [
        p for p in analyzed
        if p["status"].lower() == "success"
    ]

    failed = [
        p for p in analyzed
        if p["status"].lower() == "failed"
    ]

    total_revenue = sum(
        p["amount"] for p in successful
    )

    revenue_at_risk = sum(
        p["amount"] for p in failed
    )

    high_risk = [
        p for p in failed
        if p["risk_level"] == "HIGH"
    ]

    return {
        "total_payments": len(analyzed),
        "successful_payments": len(successful),
        "failed_payments": len(failed),
        "total_revenue": total_revenue,
        "revenue_at_risk": revenue_at_risk,
        "high_risk_payments": len(high_risk)
    }


# =========================================================
# AI RISK ANALYSIS
# =========================================================

@app.get("/risk-analysis")
def risk_analysis():

    df = load_payments()

    results = [
        analyze_payment(row)
        for _, row in df.iterrows()
    ]

    results = [
        payment
        for payment in results
        if payment["risk_score"] > 0
    ]

    results.sort(
        key=lambda x: x["risk_score"],
        reverse=True
    )

    return {
        "count": len(results),
        "results": results
    }


# =========================================================
# RECOVERY ACTIONS
# =========================================================

@app.get("/recovery-actions")
def recovery_actions():

    db = SessionLocal()

    try:

        df = load_payments()
        actions = []

        for _, row in df.iterrows():

            payment = analyze_payment(row)

            # Only failed payments need recovery
            if payment["status"].lower() != "failed":
                continue

            recommendation = recommend_recovery_action(payment)

            existing_action = (
                db.query(RecoveryAction)
                .filter(
                    RecoveryAction.payment_id
                    == payment["payment_id"]
                )
                .first()
            )

            if not existing_action:

                existing_action = RecoveryAction(
                    payment_id=payment["payment_id"],
                    action_type=recommendation["action_type"],
                    ai_reason=recommendation["reason"],
                    confidence=recommendation["confidence"],
                    status="PENDING"
                )

                db.add(existing_action)
                db.commit()
                db.refresh(existing_action)

            actions.append({
                "payment_id": payment["payment_id"],
                "customer_id": payment["customer_id"],
                "amount": payment["amount"],
                "failure_reason": payment["failure_reason"],
                "risk_score": payment["risk_score"],
                "risk_level": payment["risk_level"],
                "action_type": existing_action.action_type,
                "ai_reason": existing_action.ai_reason,
                "confidence": existing_action.confidence,
                "status": existing_action.status
            })

        return {
            "count": len(actions),
            "recovery_actions": actions
        }

    finally:
        db.close()


# =========================================================
# RECOVERY EXECUTION
# =========================================================

@app.post("/recovery-actions/{payment_id}/execute")
def execute_recovery_action(
    payment_id: str,
    approved: bool = False
):

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # Find recovery action
        # -------------------------------------------------

        action = (
            db.query(RecoveryAction)
            .filter(
                RecoveryAction.payment_id == payment_id
            )
            .first()
        )

        if not action:

            return {
                "success": False,
                "error": "Recovery action not found",
                "payment_id": payment_id
            }

        # -------------------------------------------------
        # Get payment information
        # -------------------------------------------------

        df = load_payments()

        payment_row = df[
            df["payment_id"].astype(str) == str(payment_id)
        ]

        if payment_row.empty:

            return {
                "success": False,
                "error": "Payment not found",
                "payment_id": payment_id
            }

        payment = analyze_payment(
            payment_row.iloc[0]
        )

        # -------------------------------------------------
        # GUARDRAIL 1
        # Already completed
        # -------------------------------------------------

        if action.status == "COMPLETED":

            audit = AuditLog(
                payment_id=payment_id,
                event="RECOVERY_BLOCKED_ALREADY_COMPLETED",
                decision="STOP"
            )

            db.add(audit)
            db.commit()

            return {
                "success": False,
                "message": "Recovery action already completed",
                "payment_id": payment_id,
                "status": "COMPLETED",
                "guardrail": "STOP_AFTER_SUCCESS"
            }

        # -------------------------------------------------
        # Count previous execution attempts
        # -------------------------------------------------

        previous_attempts = (
            db.query(AuditLog)
            .filter(
                AuditLog.payment_id == payment_id,
                AuditLog.event.in_([
                    "RECOVERY_ACTION_EXECUTED",
                    "RECOVERY_ACTION_ATTEMPTED"
                ])
            )
            .count()
        )

        # -------------------------------------------------
        # GUARDRAIL 2
        # Maximum retry limit
        # -------------------------------------------------

        if previous_attempts >= MAX_RECOVERY_ATTEMPTS:

            audit = AuditLog(
                payment_id=payment_id,
                event="RECOVERY_BLOCKED_RETRY_LIMIT",
                decision="STOP_AFTER_RETRY_LIMIT"
            )

            db.add(audit)
            db.commit()

            return {
                "success": False,
                "message": "Recovery stopped because retry limit was reached",
                "payment_id": payment_id,
                "status": "BLOCKED",
                "attempts": previous_attempts,
                "max_attempts": MAX_RECOVERY_ATTEMPTS,
                "guardrail": "MAX_RETRY_LIMIT"
            }

        # -------------------------------------------------
        # GUARDRAIL 3
        # High risk requires approval
        # -------------------------------------------------

        if (
            payment["risk_level"] == "HIGH"
            and HIGH_RISK_REQUIRES_APPROVAL
            and not approved
        ):

            audit = AuditLog(
                payment_id=payment_id,
                event="RECOVERY_BLOCKED_APPROVAL_REQUIRED",
                decision="HIGH_RISK_REQUIRES_APPROVAL"
            )

            db.add(audit)
            db.commit()

            return {
                "success": False,
                "message": "High-risk recovery requires approval",
                "payment_id": payment_id,
                "risk_level": payment["risk_level"],
                "status": "APPROVAL_REQUIRED",
                "guardrail": "HIGH_RISK_APPROVAL"
            }

        # -------------------------------------------------
        # Record execution attempt
        # -------------------------------------------------

        attempt_audit = AuditLog(
            payment_id=payment_id,
            event="RECOVERY_ACTION_ATTEMPTED",
            decision=action.action_type
        )

        db.add(attempt_audit)

        # -------------------------------------------------
        # Execute action
        # -------------------------------------------------

        action.status = "COMPLETED"
        action.executed_at = datetime.utcnow()

        execution_audit = AuditLog(
            payment_id=payment_id,
            event="RECOVERY_ACTION_EXECUTED",
            decision=action.action_type
        )

        db.add(execution_audit)

        db.commit()
        db.refresh(action)

        return {
            "success": True,
            "message": "Recovery action executed successfully",
            "payment_id": payment_id,
            "action_type": action.action_type,
            "risk_level": payment["risk_level"],
            "amount": payment["amount"],
            "status": action.status,
            "executed_at": action.executed_at,
            "attempt": previous_attempts + 1,
            "guardrails": {
                "max_attempts": MAX_RECOVERY_ATTEMPTS,
                "high_risk_approval": HIGH_RISK_REQUIRES_APPROVAL,
                "stop_after_success": True
            }
        }

    finally:
        db.close()


# =========================================================
# RECOVERY AUDIT
# =========================================================

@app.get("/recovery-audit")
def recovery_audit():

    db = SessionLocal()

    try:

        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .all()
        )

        audit_entries = []

        for log in logs:

            audit_entries.append({
                "id": log.id,
                "payment_id": log.payment_id,
                "event": log.event,
                "decision": log.decision,
                "timestamp": (
                    log.created_at.isoformat()
                    if getattr(log, "created_at", None)
                    else None
                )
            })

        return {
            "count": len(audit_entries),
            "audit": audit_entries
        }

    finally:
        db.close()


# =========================================================
# RECOVERY IMPACT
# =========================================================

@app.get("/recovery-impact")
def recovery_impact():

    db = SessionLocal()

    try:

        df = load_payments()

        analyzed = [
            analyze_payment(row)
            for _, row in df.iterrows()
        ]

        failed_payments = [
            p for p in analyzed
            if p["status"].lower() == "failed"
        ]

        revenue_at_risk = sum(
            p["amount"]
            for p in failed_payments
        )

        completed_actions = (
            db.query(RecoveryAction)
            .filter(
                RecoveryAction.status == "COMPLETED"
            )
            .all()
        )

        completed_payment_ids = {
            str(action.payment_id)
            for action in completed_actions
        }

        completed_value = sum(
            p["amount"]
            for p in failed_payments
            if str(p["payment_id"])
            in completed_payment_ids
        )

        remaining_opportunity = max(
            revenue_at_risk - completed_value,
            0
        )

        if revenue_at_risk > 0:

            recovery_rate = (
                completed_value
                / revenue_at_risk
            ) * 100

        else:

            recovery_rate = 0

        return {
            "revenue_at_risk": round(
                revenue_at_risk,
                2
            ),
            "recovery_action_value": round(
                completed_value,
                2
            ),
            "remaining_opportunity": round(
                remaining_opportunity,
                2
            ),
            "recovery_rate": round(
                recovery_rate,
                2
            ),
            "completed_actions": len(
                completed_actions
            )
        }

    finally:
        db.close()


# =========================================================
# RECOVERY POLICY
# =========================================================

@app.get("/recovery-policy")
def recovery_policy():

    return {
        "max_recovery_attempts": MAX_RECOVERY_ATTEMPTS,
        "high_risk_requires_approval":
            HIGH_RISK_REQUIRES_APPROVAL,
        "stop_after_success": True,
        "audit_logging": True,
        "policy_status": "ACTIVE"
    }


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/dashboard")
def dashboard():

    db = SessionLocal()

    try:

        df = load_payments()

        analyzed = [
            analyze_payment(row)
            for _, row in df.iterrows()
        ]

        total_payments = len(analyzed)

        successful_payments = [
            p for p in analyzed
            if p["status"].lower() == "success"
        ]

        failed_payments = [
            p for p in analyzed
            if p["status"].lower() == "failed"
        ]

        high_risk = [
            p for p in failed_payments
            if p["risk_level"] == "HIGH"
        ]

        medium_risk = [
            p for p in failed_payments
            if p["risk_level"] == "MEDIUM"
        ]

        low_risk = [
            p for p in failed_payments
            if p["risk_level"] == "LOW"
        ]

        total_revenue = sum(
            p["amount"]
            for p in successful_payments
        )

        revenue_at_risk = sum(
            p["amount"]
            for p in failed_payments
        )

        pending_actions = (
            db.query(RecoveryAction)
            .filter(
                RecoveryAction.status == "PENDING"
            )
            .count()
        )

        completed_actions = (
            db.query(RecoveryAction)
            .filter(
                RecoveryAction.status == "COMPLETED"
            )
            .count()
        )

        total_recovery_actions = (
            pending_actions
            + completed_actions
        )

        if total_recovery_actions > 0:

            recovery_rate = (
                completed_actions
                / total_recovery_actions
            ) * 100

        else:

            recovery_rate = 0

        # Calculate completed recovery opportunity
        completed_action_records = (
            db.query(RecoveryAction)
            .filter(
                RecoveryAction.status == "COMPLETED"
            )
            .all()
        )

        completed_ids = {
            str(action.payment_id)
            for action in completed_action_records
        }

        recovery_action_value = sum(
            p["amount"]
            for p in failed_payments
            if str(p["payment_id"])
            in completed_ids
        )

        remaining_opportunity = max(
            revenue_at_risk
            - recovery_action_value,
            0
        )

        return {

            "total_payments":
                total_payments,

            "successful_payments":
                len(successful_payments),

            "failed_payments":
                len(failed_payments),

            "total_revenue":
                total_revenue,

            "revenue_at_risk":
                revenue_at_risk,

            "risk_distribution": {

                "high":
                    len(high_risk),

                "medium":
                    len(medium_risk),

                "low":
                    len(low_risk)
            },

            "recovery": {

                "pending":
                    pending_actions,

                "completed":
                    completed_actions,

                "recovery_rate":
                    round(
                        recovery_rate,
                        2
                    ),

                "recovery_action_value":
                    round(
                        recovery_action_value,
                        2
                    ),

                "remaining_opportunity":
                    round(
                        remaining_opportunity,
                        2
                    )
            },

            "agent": {

                "status":
                    "ACTIVE",

                "payments_analyzed":
                    total_payments,

                "recovery_opportunities":
                    len(failed_payments),

                "guardrails":
                    "ACTIVE",

                "audit_logging":
                    True
            }
        }

    finally:

        db.close()