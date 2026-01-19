"""Portfolio Manager Agent - aggregates signals and makes final trading decisions."""
from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
import json
from typing import Literal
from src.utils.llm import call_llm
from src.utils.progress import progress
from langchain_core.prompts import ChatPromptTemplate


class PortfolioDecision(BaseModel):
    ticker: str
    action: Literal["buy", "sell", "hold"]
    quantity: int = Field(description="Number of shares to trade")
    confidence: int = Field(description="Confidence 0-100")
    reasoning: str


class PortfolioManagerOutput(BaseModel):
    decisions: list[PortfolioDecision]


def portfolio_management_agent(state: AgentState, agent_id: str = "portfolio_manager"):
    """Aggregates analyst signals and risk assessment to make final trading decisions."""
    data = state["data"]
    tickers = data["tickers"]
    portfolio = data.get("portfolio", {})
    analyst_signals = data.get("analyst_signals", {})
    risk_assessment = data.get("risk_assessment", {})

    progress.update_status(agent_id, None, "Analyzing portfolio decisions")

    # Aggregate signals for each ticker
    aggregated_signals = {}
    for ticker in tickers:
        ticker_signals = []
        for analyst_id, signals in analyst_signals.items():
            if ticker in signals:
                ticker_signals.append({
                    "analyst": analyst_id,
                    "signal": signals[ticker].get("signal"),
                    "confidence": signals[ticker].get("confidence"),
                    "reasoning": signals[ticker].get("reasoning"),
                })
        aggregated_signals[ticker] = ticker_signals

    # Get current positions
    cash = portfolio.get("cash", 100000)
    positions = portfolio.get("positions", {})

    progress.update_status(agent_id, None, "Generating portfolio decisions")

    # Generate decisions using LLM
    decisions = generate_portfolio_decisions(
        tickers=tickers,
        aggregated_signals=aggregated_signals,
        risk_assessment=risk_assessment,
        cash=cash,
        positions=positions,
        state=state,
        agent_id=agent_id,
    )

    # Format output
    portfolio_output = {
        "decisions": [d.model_dump() for d in decisions.decisions],
        "reasoning": "Aggregated analyst signals with risk management constraints",
    }

    message = HumanMessage(content=json.dumps(portfolio_output), name=agent_id)

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(portfolio_output, agent_id)

    # Store decisions in state
    state["data"]["portfolio_decisions"] = portfolio_output

    progress.update_status(agent_id, None, "Done")

    return {"messages": [message], "data": state["data"]}


def generate_portfolio_decisions(
    tickers: list[str],
    aggregated_signals: dict,
    risk_assessment: dict,
    cash: float,
    positions: dict,
    state: AgentState,
    agent_id: str,
) -> PortfolioManagerOutput:
    """Generate portfolio decisions using LLM."""

    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a portfolio manager making final trading decisions.

Based on analyst signals and risk assessment, decide for each ticker:
- buy: If consensus is bullish with high confidence
- sell: If consensus is bearish or risk is too high
- hold: If signals are mixed or neutral

Consider:
1. Analyst consensus and confidence levels
2. Risk assessment recommendations
3. Available cash: ${cash}
4. Current positions

Return JSON with decisions for each ticker."""
        ),
        (
            "human",
            """Tickers: {tickers}

Analyst Signals:
{signals}

Risk Assessment:
{risk}

Current Positions:
{positions}

Available Cash: ${cash}

Return exactly:
{{
  "decisions": [
    {{"ticker": "XXX", "action": "buy|sell|hold", "quantity": int, "confidence": int, "reasoning": "brief reason"}}
  ]
}}"""
        ),
    ])

    prompt = template.invoke({
        "tickers": tickers,
        "signals": json.dumps(aggregated_signals, indent=2),
        "risk": json.dumps(risk_assessment, indent=2),
        "positions": json.dumps(positions, indent=2),
        "cash": cash,
    })

    def create_default():
        return PortfolioManagerOutput(
            decisions=[
                PortfolioDecision(
                    ticker=t,
                    action="hold",
                    quantity=0,
                    confidence=50,
                    reasoning="Insufficient data for decision"
                )
                for t in tickers
            ]
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=PortfolioManagerOutput,
        agent_name=agent_id,
        state=state,
        default_factory=create_default,
    )
