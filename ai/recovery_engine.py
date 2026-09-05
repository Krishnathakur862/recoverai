def recommend_recovery_action(payment):
    """
    Recommend the best recovery action based on
    payment failure reason and AI risk level.
    """

    failure_reason = str(
        payment.get("failure_reason", "")
    ).lower()

    risk_level = str(
        payment.get("risk_level", "NONE")
    ).upper()

    subscription_status = str(
        payment.get("subscription_status", "")
    ).lower()

    days_since_last_payment = int(
        payment.get("days_since_last_payment", 0)
    )

    # Expired card
    if failure_reason == "expired_card":
        return {
            "action_type": "UPDATE_PAYMENT_METHOD",
            "reason": "The customer's card has expired. Requesting a new payment method can recover the failed payment.",
            "confidence": 0.95
        }

    # Insufficient funds
    if failure_reason == "insufficient_funds":
        return {
            "action_type": "RETRY_PAYMENT",
            "reason": "The payment failed due to insufficient funds. A later retry may successfully recover the payment.",
            "confidence": 0.88
        }

    # Card declined
    if failure_reason == "card_declined":
        if risk_level == "HIGH" or subscription_status == "overdue":
            return {
                "action_type": "URGENT_PAYMENT_UPDATE",
                "reason": "The payment was declined and the subscription is at high recovery risk. An urgent payment-method update is recommended.",
                "confidence": 0.93
            }

        return {
            "action_type": "CUSTOMER_NOTIFICATION",
            "reason": "The card was declined. The customer should be notified and asked to retry or use another payment method.",
            "confidence": 0.90
        }

    # Bank error
    if failure_reason == "bank_error":
        return {
            "action_type": "RETRY_PAYMENT",
            "reason": "A temporary bank error caused the failure. Retrying the payment later may recover the transaction.",
            "confidence": 0.86
        }

    # UPI timeout
    if failure_reason == "upi_timeout":
        return {
            "action_type": "RETRY_PAYMENT",
            "reason": "The UPI transaction timed out. A retry can recover the payment without requiring a payment-method change.",
            "confidence": 0.89
        }

    # Generic high-risk case
    if risk_level == "HIGH":
        return {
            "action_type": "URGENT_CUSTOMER_NOTIFICATION",
            "reason": "The payment has a high recovery risk and requires immediate customer attention.",
            "confidence": 0.85
        }

    # Generic medium-risk case
    if risk_level == "MEDIUM":
        return {
            "action_type": "CUSTOMER_NOTIFICATION",
            "reason": "The payment has medium recovery risk. Customer notification can encourage successful payment recovery.",
            "confidence": 0.80
        }

    # Generic low-risk case
    if risk_level == "LOW":
        return {
            "action_type": "RETRY_PAYMENT",
            "reason": "The payment has relatively low recovery risk. An automated retry is recommended.",
            "confidence": 0.75
        }

    return {
        "action_type": "NO_ACTION",
        "reason": "No recovery action is required.",
        "confidence": 0.60
    }