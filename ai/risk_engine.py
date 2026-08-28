import csv


def calculate_risk(payment):
    """
    Calculate a simple revenue-recovery risk score.

    Higher score = higher recovery priority.
    """

    if payment["status"] == "success":
        return 0

    score = 0

    amount = float(payment["amount"])
    days = int(payment["days_since_last_payment"])

    # Higher-value payments deserve higher attention.
    if amount >= 5000:
        score += 40
    elif amount >= 2000:
        score += 25
    else:
        score += 10

    # Overdue subscriptions are high priority.
    if payment["subscription_status"] == "overdue":
        score += 30

    # Repeated/longer payment gaps increase risk.
    if days >= 30:
        score += 20
    elif days >= 7:
        score += 10
    elif days >= 2:
        score += 5

    # Some failures may be recoverable with another attempt.
    if payment["failure_reason"] in [
        "insufficient_funds",
        "bank_error",
        "upi_timeout"
    ]:
        score += 10

    return min(score, 100)


def analyze_payments(file_path):
    results = []

    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for payment in reader:
            risk_score = calculate_risk(payment)

            results.append({
                "payment_id": payment["payment_id"],
                "customer_id": payment["customer_id"],
                "amount": payment["amount"],
                "status": payment["status"],
                "failure_reason": payment["failure_reason"],
                "risk_score": risk_score
            })

    return sorted(
        results,
        key=lambda x: x["risk_score"],
        reverse=True
    )


if __name__ == "__main__":
    
    payments = analyze_payments("data/payments.csv")
    print("\n=== RecoverAI Revenue Risk Analysis ===\n")

    for payment in payments:
        if payment["risk_score"] > 0:
            print(
                f'{payment["payment_id"]} | '
                f'₹{payment["amount"]} | '
                f'Risk: {payment["risk_score"]}/100 | '
                f'{payment["failure_reason"]}'
            )