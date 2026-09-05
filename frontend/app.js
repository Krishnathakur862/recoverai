const API_URL = "http://127.0.0.1:8000";

let latestPayments = [];


// =========================
// LOAD DASHBOARD
// =========================

async function loadDashboard() {

    try {

        // Get dashboard statistics
        const dashboardResponse =
            await fetch(API_URL + "/dashboard");

        // Get individual payment risk analysis
        const riskResponse =
            await fetch(API_URL + "/risk-analysis");

        // Get recovery actions
        const recoveryResponse =
            await fetch(API_URL + "/recovery-actions");


        if (
            !dashboardResponse.ok ||
            !riskResponse.ok ||
            !recoveryResponse.ok
        ) {
            throw new Error("API request failed");
        }


        const dashboard =
            await dashboardResponse.json();

        const riskData =
            await riskResponse.json();

        const recoveryData =
            await recoveryResponse.json();


        const payments =
            riskData.results || [];

        const recoveryActions =
            recoveryData.recovery_actions || [];

        latestPayments = payments;



        // =========================
        // KPI CARDS
        // =========================

        setText(
            "totalPayments",
            dashboard.total_payments
        );

        setText(
            "successfulPayments",
            dashboard.successful_payments
        );

        setText(
            "failedPayments",
            dashboard.failed_payments
        );

        setText(
            "revenueAtRisk",
            formatCurrency(
                dashboard.revenue_at_risk
            )
        );



        // =========================
        // REVENUE
        // =========================

        setText(
            "bigRevenueRisk",
            formatCurrency(
                dashboard.revenue_at_risk
            )
        );

        setText(
            "successfulRevenue",
            formatCurrency(
                dashboard.total_revenue
            )
        );

        setText(
            "failedRevenue",
            formatCurrency(
                dashboard.revenue_at_risk
            )
        );


        const totalValue =
            Number(dashboard.total_revenue) +
            Number(dashboard.revenue_at_risk);


        const riskPercentage =
            totalValue > 0
                ? Math.round(
                    (
                        Number(
                            dashboard.revenue_at_risk
                        ) /
                        totalValue
                    ) * 100
                )
                : 0;


        setText(
            "riskPercentage",
            riskPercentage + "%"
        );


        const riskBar =
            document.getElementById("riskBar");


        if (riskBar) {

            riskBar.style.width =
                riskPercentage + "%";
        }



        // =========================
        // RISK DISTRIBUTION
        // =========================

        const high =
            dashboard.risk_distribution.high || 0;

        const medium =
            dashboard.risk_distribution.medium || 0;

        const low =
            dashboard.risk_distribution.low || 0;


        const totalRisk =
            high + medium + low || 1;


        setText(
            "riskTotal",
            totalRisk
        );

        setText(
            "highRisk",
            high
        );

        setText(
            "highRiskText",
            high
        );

        setText(
            "mediumRisk",
            medium
        );

        setText(
            "lowRisk",
            low
        );


        const highBar =
            document.getElementById("highBar");

        const mediumBar =
            document.getElementById("mediumBar");

        const lowBar =
            document.getElementById("lowBar");


        if (highBar) {

            highBar.style.width =
                (high / totalRisk * 100) + "%";
        }


        if (mediumBar) {

            mediumBar.style.width =
                (medium / totalRisk * 100) + "%";
        }


        if (lowBar) {

            lowBar.style.width =
                (low / totalRisk * 100) + "%";
        }



        // =========================
        // RECOVERY QUEUE
        // =========================

        setText(
            "queueCount",
            recoveryData.count + " payments"
        );


        const table =
            document.getElementById("paymentTable");


        if (table) {

            table.innerHTML = "";


            recoveryActions.forEach(
                function (action) {

                    const row =
                        document.createElement("tr");


                    const paymentId =
                        escapeHTML(
                            action.payment_id
                        );


                    const customerId =
                        escapeHTML(
                            action.customer_id
                        );


                    const amount =
                        formatCurrency(
                            action.amount
                        );


                    const failureReason =
                        action.failure_reason ||
                        "Unknown";


                    const riskLevel =
                        action.risk_level ||
                        "LOW";


                    const riskScore =
                        action.risk_score ?? 0;


                    const actionType =
                        escapeHTML(
                            action.action_type
                        );


                    const confidence =
                        Math.round(
                            Number(
                                action.confidence || 0
                            ) * 100
                        );


                    row.innerHTML =

                        "<td>" +

                            "<div class=\"customer-id\">" +

                                customerId +

                            "</div>" +

                        "</td>" +


                        "<td>" +

                            "<div class=\"amount\">" +

                                amount +

                            "</div>" +

                        "</td>" +


                        "<td>" +

                            "<div class=\"reason\">" +

                                formatReason(
                                    failureReason
                                ) +

                            "</div>" +

                        "</td>" +


                        "<td>" +

                            "<div class=\"method\">" +

                                actionType +

                            "</div>" +

                        "</td>" +


                        "<td>" +

                            "<span class=\"risk-badge " +

                                String(
                                    riskLevel
                                ).toLowerCase() +

                            "\">" +

                                riskLevel +

                                " · " +

                                riskScore +

                            "</span>" +

                        "</td>" +


                        "<td>" +

                            "<button " +

                                "class=\"action-btn\" " +

                                "type=\"button\" " +

                                "onclick=\"showRecovery('" +

                                    escapeAttribute(
                                        action.payment_id
                                    ) +

                                    "', '" +

                                    escapeAttribute(
                                        action.failure_reason
                                    ) +

                                "')\">" +

                                "Recover" +

                            "</button>" +

                        "</td>";


                    table.appendChild(row);

                }
            );
        }



        // =========================
        // ANALYTICS PAGE
        // =========================

        const analyticsSuccess =
            Number(
                dashboard.successful_payments
            ) || 0;


        const analyticsFailed =
            Number(
                dashboard.failed_payments
            ) || 0;


        const analyticsRecovery =
            Number(
                dashboard.revenue_at_risk
            ) || 0;


        const analyticsRevenue =
            Number(
                dashboard.total_revenue
            ) || 0;



        // Analytics KPI values

        setText(
            "analyticsRecoveryValue",
            formatCurrency(
                analyticsRecovery
            )
        );


        setText(
            "analyticsSuccessValue",
            formatCurrency(
                analyticsRevenue
            )
        );


        setText(
            "analyticsFailedValue",
            analyticsFailed
        );



        // =========================
        // SUCCESS / FAILURE
        // =========================

        const analyticsTransactionTotal =
            analyticsSuccess +
            analyticsFailed;


        const successPercent =
            analyticsTransactionTotal > 0

                ? (
                    analyticsSuccess /
                    analyticsTransactionTotal
                ) * 100

                : 0;


        const failedPercent =
            analyticsTransactionTotal > 0

                ? (
                    analyticsFailed /
                    analyticsTransactionTotal
                ) * 100

                : 0;



        setText(
            "analyticsSuccessPercent",
            Math.round(
                successPercent
            ) + "%"
        );


        setText(
            "analyticsFailedPercent",
            Math.round(
                failedPercent
            ) + "%"
        );



        // Success bar

        const analyticsSuccessBar =
            document.getElementById(
                "analyticsSuccessBar"
            );


        if (analyticsSuccessBar) {

            analyticsSuccessBar.style.width =
                successPercent + "%";
        }



        // Failed bar

        const analyticsFailedBar =
            document.getElementById(
                "analyticsFailedBar"
            );


        if (analyticsFailedBar) {

            analyticsFailedBar.style.width =
                failedPercent + "%";
        }



        // =========================
        // AI RISK MIX
        // =========================

        setText(
            "analyticsHighRisk",
            high
        );


        setText(
            "analyticsMediumRisk",
            medium
        );


        setText(
            "analyticsLowRisk",
            low
        );



        // =========================
        // AI ANALYSIS
        // =========================

        updateAIAnalysis(
            payments
        );



        // =========================
        // AI INSIGHT
        // =========================

        generateInsight(
            dashboard,
            payments,
            high,
            medium,
            low
        );


        console.log(
            "RecoverAI dashboard loaded successfully."
        );

    }


    catch (error) {

        console.error(
            "RecoverAI connection error:",
            error
        );


        const aiInsight =
            document.getElementById(
                "aiInsight"
            );


        const aiInsightText =
            document.getElementById(
                "aiInsightText"
            );


        if (aiInsight) {

            aiInsight.textContent =
                "Unable to load live payment intelligence.";
        }


        if (aiInsightText) {

            aiInsightText.textContent =
                "Check that the RecoverAI FastAPI backend is running on port 8000.";
        }

    }

}



// =========================
// AI ANALYSIS
// =========================

function updateAIAnalysis(payments) {

    const highPayments =
        payments.filter(
            function (p) {

                return p.risk_level === "HIGH";

            }
        );


    const mediumPayments =
        payments.filter(
            function (p) {

                return p.risk_level === "MEDIUM";

            }
        );


    const lowPayments =
        payments.filter(
            function (p) {

                return p.risk_level === "LOW";

            }
        );


    const totalElement =
        document.getElementById(
            "analysisTotal"
        );


    const highElement =
        document.getElementById(
            "analysisHigh"
        );


    const mediumElement =
        document.getElementById(
            "analysisMedium"
        );


    const lowElement =
        document.getElementById(
            "analysisLow"
        );


    if (totalElement) {

        totalElement.textContent =
            payments.length;
    }


    if (highElement) {

        highElement.textContent =
            highPayments.length;
    }


    if (mediumElement) {

        mediumElement.textContent =
            mediumPayments.length;
    }


    if (lowElement) {

        lowElement.textContent =
            lowPayments.length;
    }



    // No payments

    if (payments.length === 0) {

        setText(
            "topRiskPayment",
            "--"
        );

        setText(
            "topRiskScore",
            "--"
        );

        setText(
            "topRiskAmount",
            "₹0"
        );

        setText(
            "topRiskReason",
            "--"
        );

        setText(
            "factorReason",
            "No failed payments detected."
        );

        setText(
            "factorAmount",
            "No transaction available."
        );

        setText(
            "factorMethod",
            "No payment method available."
        );

        setText(
            "factorReasonScore",
            "+0"
        );

        setText(
            "factorAmountScore",
            "+0"
        );

        setText(
            "factorMethodScore",
            "+0"
        );

        setText(
            "aiDecision",
            "LOW RISK"
        );

        setText(
            "aiRecommendedAction",
            "No recovery action required."
        );

        return;
    }



    // Highest-risk payment

    const top =
        [...payments].sort(
            function (a, b) {

                return (
                    Number(b.risk_score) -
                    Number(a.risk_score)
                );

            }
        )[0];


    setText(
        "topRiskPayment",
        top.payment_id
    );


    setText(
        "topRiskScore",
        Number(
            top.risk_score
        ).toFixed(0)
    );


    setText(
        "topRiskAmount",
        formatCurrency(
            top.amount
        )
    );


    setText(
        "topRiskReason",
        formatReason(
            top.failure_reason
        )
    );



    // Risk factors

    setText(
        "factorReason",
        formatReason(
            top.failure_reason
        )
    );


    setText(
        "factorAmount",
        formatCurrency(
            top.amount
        )
    );


    setText(
        "factorMethod",
        String(
            top.payment_method
        ).toUpperCase()
    );



    // Simple explainable factor scores

    let reasonScore = 0;


    if (
        top.failure_reason ===
        "expired_card"
    ) {

        reasonScore = 30;

    }

    else if (
        top.failure_reason ===
        "card_declined"
    ) {

        reasonScore = 25;

    }

    else if (
        top.failure_reason ===
        "bank_error"
    ) {

        reasonScore = 20;

    }

    else if (
        top.failure_reason ===
        "upi_timeout"
    ) {

        reasonScore = 15;

    }

    else if (
        top.failure_reason ===
        "insufficient_funds"
    ) {

        reasonScore = 10;

    }



    const amountScore =

        Number(top.amount) >= 5000

            ? 25

            : Number(top.amount) >= 2000

                ? 15

                : 10;



    const methodScore =

        top.payment_method === "card"

            ? 20

            : top.payment_method === "netbanking"

                ? 15

                : 10;



    setText(
        "factorReasonScore",
        "+" + reasonScore
    );


    setText(
        "factorAmountScore",
        "+" + amountScore
    );


    setText(
        "factorMethodScore",
        "+" + methodScore
    );


    setText(
        "aiDecision",
        top.risk_level + " RISK"
    );


    setText(
        "aiRecommendedAction",
        getRecoveryRecommendation(
            top.failure_reason
        )
    );

}



// =========================
// AI INSIGHT
// =========================

function generateInsight(
    summary,
    payments,
    high,
    medium,
    low
) {

    const insight =
        document.getElementById(
            "aiInsight"
        );


    const insightText =
        document.getElementById(
            "aiInsightText"
        );


    // These elements may not exist in the new HTML.

    if (
        !insight ||
        !insightText
    ) {

        return;
    }



    if (high > 0) {

        const top =
            payments.find(
                function (p) {

                    return p.risk_level === "HIGH";

                }
            );


        insight.textContent =
            high +
            " high-priority payment requires immediate attention.";


        insightText.textContent =
            top.payment_id +
            " has a risk score of " +
            top.risk_score +
            "/100 and represents " +
            formatCurrency(top.amount) +
            " in potential recovery value.";

    }


    else if (medium > 0) {

        insight.textContent =
            medium +
            " medium-risk payments are ready for recovery.";


        insightText.textContent =
            "RecoverAI recommends prioritizing these transactions after the highest-risk cases.";

    }


    else {

        insight.textContent =
            "Payment recovery queue is under control.";


        insightText.textContent =
            "No high-priority recovery cases were detected.";

    }

}



// =========================
// RECOVERY ACTION
// =========================

async function showRecovery(
    paymentId,
    failureReason
) {

    const recommendation =
        getRecoveryRecommendation(
            failureReason
        );


    const confirmed =
        confirm(

            "RECOVERAI RECOVERY ACTION\n\n" +

            "Payment: " +
            paymentId +

            "\n" +

            "Failure: " +
            formatReason(
                failureReason
            ) +

            "\n\n" +

            "Recommended action:\n" +

            recommendation +

            "\n\nExecute this recovery action?"

        );


    if (!confirmed) {

        return;
    }


    try {

        const response =
            await fetch(

                API_URL +
                "/recovery-actions/" +
                encodeURIComponent(
                    paymentId
                ) +
                "/execute",

                {
                    method: "POST"
                }

            );


        if (!response.ok) {

            throw new Error(
                "Recovery execution failed"
            );

        }


        const result =
            await response.json();


        console.log(
            "Recovery result:",
            result
        );


        alert(

            "Recovery action executed successfully.\n\n" +

            "Payment: " +
            paymentId

        );


        await loadDashboard();

    }


    catch (error) {

        console.error(
            "Recovery error:",
            error
        );


        alert(

            "Unable to execute recovery action.\n\n" +

            "Please check that the RecoverAI backend is running."

        );

    }

}



// =========================
// RECOVERY RECOMMENDATIONS
// =========================

function getRecoveryRecommendation(
    reason
) {

    const recommendations = {

        insufficient_funds:
            "Retry the payment after a short interval and notify the customer.",

        card_declined:
            "Prompt the customer to retry with another card or payment method.",

        expired_card:
            "Request updated card details before retrying the payment.",

        bank_error:
            "Retry the transaction and provide an alternative payment method.",

        upi_timeout:
            "Initiate a UPI retry and provide an alternative payment option."

    };


    return (
        recommendations[reason] ||
        "Initiate a targeted payment recovery workflow."
    );

}



// =========================
// PAGE NAVIGATION
// =========================

function goToSection(
    sectionId,
    clickedElement
) {

    const sections = [

        "dashboard",

        "aiRiskAnalysis",

        "recoveryQueue",

        "analytics",

        "settings"

    ];


    // Hide every section

    sections.forEach(
        function (id) {

            const section =
                document.getElementById(id);


            if (!section) {

                return;

            }


            section.style.display =
                id === sectionId
                    ? "block"
                    : "none";

        }
    );


    // Update active navigation item

    document
        .querySelectorAll(".nav-link")
        .forEach(
            function (link) {

                link.classList.remove(
                    "active"
                );

            }
        );


    if (clickedElement) {

        clickedElement.classList.add(
            "active"
        );

    }


    // Update page heading

    updatePageHeading(
        sectionId
    );


    // Scroll to selected section

    const target =
        document.getElementById(
            sectionId
        );


    if (target) {

        target.scrollIntoView({

            behavior: "smooth",

            block: "start"

        });

    }

}



// =========================
// PAGE HEADING
// =========================

function updatePageHeading(
    sectionId
) {

    const title =
        document.getElementById(
            "pageTitle"
        );


    const description =
        document.getElementById(
            "pageDescription"
        );


    if (
        !title ||
        !description
    ) {

        return;

    }


    const pages = {

        dashboard: {

            title:
                "Revenue Recovery Dashboard",

            description:
                "AI-powered visibility into payment failures and recovery opportunities."

        },


        aiRiskAnalysis: {

            title:
                "AI Risk Analysis",

            description:
                "Explainable AI analysis of failed payments and recovery probability."

        },


        recoveryQueue: {

            title:
                "Priority Recovery Queue",

            description:
                "Failed payments ranked by AI-generated recovery risk score."

        },


        analytics: {

            title:
                "Revenue Analytics",

            description:
                "Financial overview of payment performance and recovery opportunities."

        },


        settings: {

            title:
                "Settings",

            description:
                "RecoverAI system configuration and AI engine status."

        }

    };


    const page =
        pages[sectionId] ||
        pages.dashboard;


    title.textContent =
        page.title;


    description.textContent =
        page.description;

}



// =========================
// SCROLL TO RECOVERY QUEUE
// =========================

function focusRecovery() {

    goToSection(
        "recoveryQueue"
    );

}



// =========================
// SCROLL TO AI ANALYSIS
// =========================

function focusAIAnalysis() {

    goToSection(
        "aiRiskAnalysis"
    );

}



// =========================
// SECURITY HELPERS
// =========================

function escapeHTML(value) {

    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}



function escapeAttribute(value) {

    return String(value)

        .replace(
            /\\/g,
            "\\\\"
        )

        .replace(
            /'/g,
            "\\'"
        )

        .replace(
            /"/g,
            "&quot;"
        );

}



// =========================
// FORMAT CURRENCY
// =========================

function formatCurrency(value) {

    return new Intl.NumberFormat(

        "en-IN",

        {

            style: "currency",

            currency: "INR",

            maximumFractionDigits: 0

        }

    ).format(
        Number(value) || 0
    );

}



// =========================
// FORMAT FAILURE REASON
// =========================

function formatReason(reason) {

    return String(
        reason || "Unknown"
    )

        .replaceAll(
            "_",
            " "
        )

        .replace(
            /\b\w/g,
            function (letter) {

                return letter.toUpperCase();

            }
        );

}



// =========================
// HELPER
// =========================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (element) {

        element.textContent =
            value;

    }

}



// =========================
// START DASHBOARD
// =========================

loadDashboard();