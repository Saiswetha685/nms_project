from typing import Dict, Any, List
from backend.app.llm.claude_client import ClaudeClient

class ExplanationService:
    @staticmethod
    async def get_service_risk_explanation(
        service_name: str,
        service_type: str,
        status: str,
        sla_target: float,
        availability: float,
        budget_used_percent: float,
        remaining_budget_mins: float,
        rule_risk: float,
        ml_prob: float,
        top_factors: List[Dict[str, Any]],
        forecast_hours: float = None,
        recent_incident_count: int = 0
    ) -> str:
        """
        Generates operational risk explanation using Claude LLM,
        or deterministic template if Claude is unavailable.
        """
        top_feat_str = ", ".join([f"{f.get('description', f.get('feature'))} ({int(f.get('importance', 0)*100)}% weight)" for f in top_factors[:3]])

        # Deterministic fallback template
        template_explanation = ExplanationService._build_deterministic_template(
            service_name=service_name,
            service_type=service_type,
            status=status,
            sla_target=sla_target,
            availability=availability,
            budget_used_percent=budget_used_percent,
            remaining_budget_mins=remaining_budget_mins,
            rule_risk=rule_risk,
            ml_prob=ml_prob,
            top_factors_str=top_feat_str,
            forecast_hours=forecast_hours,
            recent_incident_count=recent_incident_count
        )

        # Build prompt for Claude
        prompt = f"""You are the senior Network Operations Center (NOC) and SLA Reliability AI Copilot.
Explain the following monitored network service health, SLA compliance status, and predictive risk in 2 concise, professional paragraphs.
Give clear operational context and prioritize what network engineers need to know.

Service Details:
- Name: {service_name} ({service_type})
- Current Status: {status}
- SLA Target: {sla_target}% | Actual Availability: {availability:.2f}%
- Downtime Budget Consumed: {budget_used_percent:.1f}% (Remaining: {remaining_budget_mins:.1f} minutes)
- Rule-Based Risk Baseline: {rule_risk:.1f}/100
- ML 6-Hour Failure Probability: {ml_prob:.2f} ({int(ml_prob*100)}%)
- Key Risk Drivers: {top_feat_str}
- Projected Budget Exhaustion: {'~' + str(forecast_hours) + ' hours' if forecast_hours else 'Stable'}
- Active / Recent Outages: {recent_incident_count}

Strict Rules:
- Do not change or dispute any of the numbers above.
- Explain the underlying physical network risk and suggest proactive remediation.
- Keep tone professional, authoritative, and concise.
"""

        claude_result = await ClaudeClient.generate_explanation(prompt)
        if claude_result:
            return claude_result.strip()
        return template_explanation

    @staticmethod
    def _build_deterministic_template(
        service_name: str,
        service_type: str,
        status: str,
        sla_target: float,
        availability: float,
        budget_used_percent: float,
        remaining_budget_mins: float,
        rule_risk: float,
        ml_prob: float,
        top_factors_str: str,
        forecast_hours: float = None,
        recent_incident_count: int = 0
    ) -> str:
        status_narrative = (
            f"The service '{service_name}' ({service_type}) is currently operating in {status} state with "
            f"{availability:.2f}% observed availability against a configured SLA commitment of {sla_target:.1f}%."
        )

        budget_narrative = (
            f"It has consumed {budget_used_percent:.1f}% of its allowable downtime budget, leaving {remaining_budget_mins:.1f} minutes "
            f"of buffer before a contractual SLA breach occurs."
        )

        if ml_prob >= 0.70 or rule_risk >= 70.0:
            risk_assessment = (
                f"SLA-Predict telemetry engines indicate CRITICAL risk: our tree-ensemble ML model estimates a {int(ml_prob*100)}% "
                f"probability of a confirmed outage or severe breach within the next 6 hours. "
                f"Primary drivers include: {top_factors_str}. "
                + (f"Statistical Holt-Winters extrapolation projects full budget exhaustion in approximately {forecast_hours:.1f} hours if unaddressed." if forecast_hours else "")
            )
            recommendation = "Immediate operator action required: inspect upstream network gateways, investigate connection pool saturation, and prepare failover procedures."
        elif ml_prob >= 0.40 or rule_risk >= 45.0:
            risk_assessment = (
                f"Elevated SLA degradation risk detected (ML probability: {int(ml_prob*100)}%, Rule baseline: {rule_risk:.1f}/100). "
                f"Contributing telemetry precursors: {top_factors_str}."
            )
            recommendation = "Recommendation: Monitor probe jitter and verify target node resource capacity to prevent escalation."
        else:
            risk_assessment = (
                f"Service telemetry is stable with low overall risk (Rule score: {rule_risk:.1f}/100, ML probability: {int(ml_prob*100)}%). "
                f"All vital performance signals are tracking within acceptable parameters."
            )
            recommendation = "Normal automated monitoring continues."

        return f"{status_narrative} {budget_narrative}\n\n{risk_assessment} {recommendation}"
