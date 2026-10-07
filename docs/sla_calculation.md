# SLA & Downtime Budget Calculation Specification

## 1. Mathematical Formulation

### 1.1 Total Observation Window
For a rolling window of $W$ days:
$$\text{Total Window Minutes} = W \times 24 \times 60$$

For example, a 30-day window:
$$W_{30} = 30 \times 24 \times 60 = 43,200 \text{ minutes}$$

### 1.2 Allowed Downtime Budget
Given a target SLA availability percentage $S_{\text{target}}$ (e.g. 99.0%):
$$\text{Allowed Downtime (min)} = \text{Total Window Minutes} \times \left(1 - \frac{S_{\text{target}}}{100}\right)$$

For 99.0% over 30 days:
$$\text{Allowed Downtime} = 43,200 \times 0.01 = 432.0 \text{ minutes}$$

### 1.3 Observed Availability
$$\text{Availability } \% = \frac{\text{Total Checks} - \text{Effective Failures}}{\text{Total Checks}} \times 100$$
Where:
- $\text{Effective Failures} = \text{Failed Checks} + (\text{Degraded Checks if } \texttt{count\_degraded\_as\_downtime} = \text{true})$

### 1.4 Downtime Budget Consumption
$$\text{Budget Consumption } \% = \min\left(100, \frac{\text{Used Downtime}}{\text{Allowed Downtime}} \times 100\right)$$

## 2. Compliance State Rules

- **VIOLATED:** $\text{Availability } \% < S_{\text{target}}$ OR $\text{Used Downtime} > \text{Allowed Downtime}$.
- **AT_RISK:** $\text{Budget Consumption} \ge 75.0\%$ OR Availability is within 0.2% of violation threshold.
- **COMPLIANT:** All parameters safely within bounds.

## 3. Rule-Based Risk Scoring (0–100)

$$\text{Risk Score} = 0.40 \cdot \text{BudgetRisk} + 0.30 \cdot \text{BurnRisk} + 0.15 \cdot \text{TrendRisk} + 0.15 \cdot \text{LatencyRisk}$$

### Mandatory Guardrails
- If $\text{Budget Consumption} \ge 75\%$, minimum risk $\ge 50$.
- If $\text{Budget Consumption} \ge 90\%$, minimum risk $\ge 75$.
- If $\text{Budget Consumption} > 100\%$, minimum risk $\ge 90$ and state is `VIOLATED`.

### Hysteresis
Enters high-risk state at risk $\ge 50$; exits only when score falls below $40$.
