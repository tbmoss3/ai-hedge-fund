"""Risk Manager Agent - evaluates risk exposure and provides risk-adjusted recommendations."""
from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
import json
from typing import Literal
from src.utils.llm import call_llm
from src.utils.progress import progress
from langchain_core.prompts import ChatPromptTemplate


class RiskAssessment(BaseModel):
    ticker: str
    risk_level: Literal["low", "medium", "high"]
    max_position_size: float = Field(description="Maximum recommended position size as % of portfolio")
    stop_loss: float = Field(description="Recommended stop loss percentage")
    reasoning: str


class RiskManagerOutput(BaseModel):
    assessments: list[RiskAssessment]
    overall_risk: Literal["low", "medium", "high"]
    recommendations: str


def risk_management_agent(state: AgentState, agent_id: str = "risk_management_agent"):
    """Evaluates risk exposure and provides risk-adjusted recommendations."""
    data = state["data"]
    tickers = data["tickers"]
    portfolio = data.get("portfolio", {})
    analyst_signals = data.get("analyst_signals", {})

    progress.update_status(agent_id, None, "Analyzing risk exposure")

    # Aggregate signals for risk analysis
    aggregated_signals = {}
    for ticker in tickers:
        ticker_signals = []
        for analyst_id, signals in analyst_signals.items():
            if ticker in signals:
                ticker_signals.append({
                    "analyst": analyst_id,
                    "signal": signals[ticker].get("signal"),
                    "confidence": signals[ticker].get("confidence"),
                })
        aggregated_signals[ticker] = ticker_signals

    # Get current positions
    positions = portfolio.get("positions", {})
    cash = portfolio.get("cash", 100000)

    progress.update_status(agent_id, None, "Generating risk assessment")

    # Generate risk assessment using LLM
    risk_output = generate_risk_assessment(
        tickers=tickers,
        aggregated_signals=aggregated_signals,
        positions=positions,
        cash=cash,
        state=state,
        agent_id=agent_id,
    )

    # Format output
    risk_assessment = {
        "assessments": {a.ticker: a.model_dump() for a in risk_output.assessments},
        "overall_risk": risk_output.overall_risk,
        "recommendations": risk_output.recommendations,
    }

    message = HumanMessage(content=json.dumps(risk_assessment), name=agent_id)

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(risk_assessment, agent_id)

    # Store risk assessment in state
    state["data"]["risk_assessment"] = risk_assessment

    progress.update_status(agent_id, None, "Done")

    return {"messages": [message], "data": state["data"]}


def generate_risk_assessment(
    tickers: list[str],
    aggregated_signals: dict,
    positions: dict,
    cash: float,
    state: AgentState,
    agent_id: str,
) -> RiskManagerOutput:
    """Generate risk assessment using LLM."""

    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a risk manager evaluating investment risk.

For each ticker, assess:
1. Risk level (low/medium/high) based on signal consensus and confidence
2. Maximum position size (% of portfolio) - higher risk = smaller position
3. Recommended stop loss percentage
4. Brief reasoning

Risk Guidelines:
- High confidence bullish = lower risk
- Mixed signals = medium risk
- Low confidence or bearish = higher risk
- Diversification: no single position > 20%

Also assess overall portfolio risk and provide recommendations."""
        ),
        (
            "human",
            """Tickers: {tickers}

Analyst Signals:
{signals}

Current Positions:
{positions}

Available Cash: ${cash}

Return exactly:
{{
  "assessments": [
    {{"ticker": "XXX", "risk_level": "low|medium|high", "max_position_size": float, "stop_loss": float, "reasoning": "brief reason"}}
  ],
  "overall_risk": "low|medium|high",
  "recommendations": "portfolio-level risk advice"
}}"""
        ),
    ])

    prompt = template.invoke({
        "tickers": tickers,
        "signals": json.dumps(aggregated_signals, indent=2),
        "positions": json.dumps(positions, indent=2),
        "cash": cash,
    })

    def create_default():
        return RiskManagerOutput(
            assessments=[
                RiskAssessment(
                    ticker=t,
                    risk_level="medium",
                    max_position_size=10.0,
                    stop_loss=10.0,
                    reasoning="Default risk assessment"
                )
                for t in tickers
            ],
            overall_risk="medium",
            recommendations="Maintain diversified positions with appropriate stop losses."
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=RiskManagerOutput,
        agent_name=agent_id,
        state=state,
        default_factory=create_default,
    )
