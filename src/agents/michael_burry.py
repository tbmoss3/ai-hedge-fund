from __future__ import annotations

from datetime import datetime, timedelta
import json
from typing import Optional
from typing_extensions import Literal

from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.tools.api import (
    get_company_news,
    get_financial_metrics,
    get_insider_trades,
    get_market_cap,
    search_line_items,
    get_prices,
)
from src.utils.llm import call_llm
from src.utils.progress import progress
from src.utils.api_key import get_api_key_from_state
from src.agents.memo_schema import InvestmentMemo, should_generate_memo, generate_investment_memo


class MichaelBurrySignal(BaseModel):
    """Schema returned by the LLM."""

    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float  # 0–100
    reasoning: str




class MichaelBurryMemoOutput(BaseModel):
    """Extended output model for generating investment memos."""
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(description="Confidence 0-100")
    reasoning: str = Field(description="Reasoning for the decision")
    thesis: str = Field(description="2-3 sentence investment thesis")
    bull_case: list[str] = Field(description="3 bullet points for bull case")
    bear_case: list[str] = Field(description="3 bullet points for bear case")
    target_price: float = Field(description="Target price based on valuation")

def michael_burry_agent(state: AgentState, agent_id: str = "michael_burry_agent"):
    """Analyse stocks using Michael Burry's deep‑value, contrarian framework."""
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")
    data = state["data"]
    end_date: str = data["end_date"]  # YYYY‑MM‑DD
    tickers: list[str] = data["tickers"]

    # We look one year back for insider trades / news flow
    start_date = (datetime.fromisoformat(end_date) - timedelta(days=365)).date().isoformat()

    analysis_data: dict[str, dict] = {}
    burry_analysis: dict[str, dict] = {}

    for ticker in tickers:
        # ------------------------------------------------------------------
        # Fetch raw data
        # ------------------------------------------------------------------
        progress.update_status(agent_id, ticker, "Fetching financial metrics")
        metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=5, api_key=api_key)

        progress.update_status(agent_id, ticker, "Fetching line items")
        line_items = search_line_items(
            ticker,
            [
                "free_cash_flow",
                "net_income",
                "total_debt",
                "cash_and_equivalents",
                "total_assets",
                "total_liabilities",
                "outstanding_shares",
                "issuance_or_purchase_of_equity_shares",
            ],
            end_date,
            api_key=api_key,
        )

        progress.update_status(agent_id, ticker, "Fetching insider trades")
        insider_trades = get_insider_trades(ticker, end_date=end_date, start_date=start_date)

        progress.update_status(agent_id, ticker, "Fetching company news")
        news = get_company_news(ticker, end_date=end_date, start_date=start_date, limit=250)

        progress.update_status(agent_id, ticker, "Fetching market cap")
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)

        # ------------------------------------------------------------------
        # Run sub‑analyses
        # ------------------------------------------------------------------
        progress.update_status(agent_id, ticker, "Analyzing value")
        value_analysis = _analyze_value(metrics, line_items, market_cap)

        progress.update_status(agent_id, ticker, "Analyzing balance sheet")
        balance_sheet_analysis = _analyze_balance_sheet(metrics, line_items)

        progress.update_status(agent_id, ticker, "Analyzing insider activity")
        insider_analysis = _analyze_insider_activity(insider_trades)

        progress.update_status(agent_id, ticker, "Analyzing contrarian sentiment")
        contrarian_analysis = _analyze_contrarian_sentiment(news)

        # ------------------------------------------------------------------
        # Aggregate score & derive preliminary signal
        # ------------------------------------------------------------------
        total_score = (
            value_analysis["score"]
            + balance_sheet_analysis["score"]
            + insider_analysis["score"]
            + contrarian_analysis["score"]
        )
        max_score = (
            value_analysis["max_score"]
            + balance_sheet_analysis["max_score"]
            + insider_analysis["max_score"]
            + contrarian_analysis["max_score"]
        )

        if total_score >= 0.7 * max_score:
            signal = "bullish"
        elif total_score <= 0.3 * max_score:
            signal = "bearish"
        else:
            signal = "neutral"

        # ------------------------------------------------------------------
        # Collect data for LLM reasoning & output
        # ------------------------------------------------------------------
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_score,
            "value_analysis": value_analysis,
            "balance_sheet_analysis": balance_sheet_analysis,
            "insider_analysis": insider_analysis,
            "contrarian_analysis": contrarian_analysis,
            "market_cap": market_cap,
        }

        progress.update_status(agent_id, ticker, "Generating LLM output")
        burry_output = _generate_burry_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        burry_analysis[ticker] = {
            "signal": burry_output.signal,
            "confidence": burry_output.confidence,
            "reasoning": burry_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "Done", analysis=burry_output.reasoning)

    # ----------------------------------------------------------------------
    # Return to the graph
    # ----------------------------------------------------------------------
    message = HumanMessage(content=json.dumps(burry_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(burry_analysis, "Michael Burry Agent")

    state["data"]["analyst_signals"][agent_id] = burry_analysis

    progress.update_status(agent_id, None, "Done")

    return {"messages": [message], "data": state["data"]}


###############################################################################
# Sub‑analysis helpers
###############################################################################


def _latest_line_item(line_items: list):
    """Return the most recent line‑item object or *None*."""
    return line_items[0] if line_items else None


# ----- Value ----------------------------------------------------------------

def _analyze_value(metrics, line_items, market_cap):
    """Free cash‑flow yield, EV/EBIT, other classic deep‑value metrics."""

    max_score = 6  # 4 pts for FCF‑yield, 2 pts for EV/EBIT
    score = 0
    details: list[str] = []

    # Free‑cash‑flow yield
    latest_item = _latest_line_item(line_items)
    fcf = getattr(latest_item, "free_cash_flow", None) if latest_item else None
    if fcf is not None and market_cap:
        fcf_yield = fcf / market_cap
        if fcf_yield >= 0.15:
            score += 4
            details.append(f"Extraordinary FCF yield {fcf_yield:.1%}")
        elif fcf_yield >= 0.12:
            score += 3
            details.append(f"Very high FCF yield {fcf_yield:.1%}")
        elif fcf_yield >= 0.08:
            score += 2
            details.append(f"Respectable FCF yield {fcf_yield:.1%}")
        else:
            details.append(f"Low FCF yield {fcf_yield:.1%}")
    else:
        details.append("FCF data unavailable")

    # EV/EBIT (from financial metrics)
    if metrics:
        ev_ebit = getattr(metrics[0], "ev_to_ebit", None)
        if ev_ebit is not None:
            if ev_ebit < 6:
                score += 2
                details.append(f"EV/EBIT {ev_ebit:.1f} (<6)")
            elif ev_ebit < 10:
                score += 1
                details.append(f"EV/EBIT {ev_ebit:.1f} (<10)")
            else:
                details.append(f"High EV/EBIT {ev_ebit:.1f}")
        else:
            details.append("EV/EBIT data unavailable")
    else:
        details.append("Financial metrics unavailable")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- Balance sheet --------------------------------------------------------

def _analyze_balance_sheet(metrics, line_items):
    """Leverage and liquidity checks."""

    max_score = 3
    score = 0
    details: list[str] = []

    latest_metrics = metrics[0] if metrics else None
    latest_item = _latest_line_item(line_items)

    debt_to_equity = getattr(latest_metrics, "debt_to_equity", None) if latest_metrics else None
    if debt_to_equity is not None:
        if debt_to_equity < 0.5:
            score += 2
            details.append(f"Low D/E {debt_to_equity:.2f}")
        elif debt_to_equity < 1:
            score += 1
            details.append(f"Moderate D/E {debt_to_equity:.2f}")
        else:
            details.append(f"High leverage D/E {debt_to_equity:.2f}")
    else:
        details.append("Debt‑to‑equity data unavailable")

    # Quick liquidity sanity check (cash vs total debt)
    if latest_item is not None:
        cash = getattr(latest_item, "cash_and_equivalents", None)
        total_debt = getattr(latest_item, "total_debt", None)
        if cash is not None and total_debt is not None:
            if cash > total_debt:
                score += 1
                details.append("Net cash position")
            else:
                details.append("Net debt position")
        else:
            details.append("Cash/debt data unavailable")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- Insider activity -----------------------------------------------------

def _analyze_insider_activity(insider_trades):
    """Net insider buying over the last 12 months acts as a hard catalyst."""

    max_score = 2
    score = 0
    details: list[str] = []

    if not insider_trades:
        details.append("No insider trade data")
        return {"score": score, "max_score": max_score, "details": "; ".join(details)}

    shares_bought = sum(t.transaction_shares or 0 for t in insider_trades if (t.transaction_shares or 0) > 0)
    shares_sold = abs(sum(t.transaction_shares or 0 for t in insider_trades if (t.transaction_shares or 0) < 0))
    net = shares_bought - shares_sold
    if net > 0:
        score += 2 if net / max(shares_sold, 1) > 1 else 1
        details.append(f"Net insider buying of {net:,} shares")
    else:
        details.append("Net insider selling")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- Contrarian sentiment -------------------------------------------------

def _analyze_contrarian_sentiment(news):
    """Very rough gauge: a wall of recent negative headlines can be a *positive* for a contrarian."""

    max_score = 1
    score = 0
    details: list[str] = []

    if not news:
        details.append("No recent news")
        return {"score": score, "max_score": max_score, "details": "; ".join(details)}

    # Count negative sentiment articles
    sentiment_negative_count = sum(
        1 for n in news if n.sentiment and n.sentiment.lower() in ["negative", "bearish"]
    )
    
    if sentiment_negative_count >= 5:
        score += 1  # The more hated, the better (assuming fundamentals hold up)
        details.append(f"{sentiment_negative_count} negative headlines (contrarian opportunity)")
    else:
        details.append("Limited negative press")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


###############################################################################
# LLM generation
###############################################################################

def _generate_burry_output(
    ticker: str,
    analysis_data: dict,
    state: AgentState,
    agent_id: str,
) -> MichaelBurrySignal:
    """Call the LLM to craft the final trading signal in Burry's voice."""

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an AI agent emulating Dr. Michael J. Burry. Your mandate:
                - Hunt for deep value in US equities using hard numbers (free cash flow, EV/EBIT, balance sheet)
                - Be contrarian: hatred in the press can be your friend if fundamentals are solid
                - Focus on downside first – avoid leveraged balance sheets
                - Look for hard catalysts such as insider buying, buybacks, or asset sales
                - Communicate in Burry's terse, data‑driven style

                When providing your reasoning, be thorough and specific by:
                1. Start with the key metric(s) that drove your decision
                2. Cite concrete numbers (e.g. "FCF yield 14.7%", "EV/EBIT 5.3")
                3. Highlight risk factors and why they are acceptable (or not)
                4. Mention relevant insider activity or contrarian opportunities
                5. Use Burry's direct, number-focused communication style with minimal words
                
                For example, if bullish: "FCF yield 12.8%. EV/EBIT 6.2. Debt-to-equity 0.4. Net insider buying 25k shares. Market missing value due to overreaction to recent litigation. Strong buy."
                For example, if bearish: "FCF yield only 2.1%. Debt-to-equity concerning at 2.3. Management diluting shareholders. Pass."
                """,
            ),
            (
                "human",
                """Based on the following data, create the investment signal as Michael Burry would:

                Analysis Data for {ticker}:
                {analysis_data}

                Return the trading signal in the following JSON format exactly:
                {{
                  "signal": "bullish" | "bearish" | "neutral",
                  "confidence": float between 0 and 100,
                  "reasoning": "string"
                }}
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    # Default fallback signal in case parsing fails
    def create_default_michael_burry_signal():
        return MichaelBurrySignal(signal="neutral", confidence=0.0, reasoning="Parsing error – defaulting to neutral")

    return call_llm(
        prompt=prompt,
        pydantic_model=MichaelBurrySignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_michael_burry_signal,
    )

def generate_michael_burry_memo(
        ticker: str,
        analysis_data: dict[str, any],
        current_price: float,
        state: AgentState,
        agent_id: str = "michael_burry_agent",
) -> MichaelBurryMemoOutput:
    """Generate full investment memo with thesis, bull/bear cases, and target price."""

    # Get valuation data for target price calculation
    market_cap = analysis_data.get("market_cap")

    # Calculate target price estimate based on available data
    if market_cap and current_price and current_price > 0:
        shares_outstanding = market_cap / current_price
        # Use valuation analysis if available
        val_analysis = analysis_data.get("valuation_analysis", {})
        intrinsic_range = val_analysis.get("intrinsic_value_range", {})
        reasonable_value = intrinsic_range.get("reasonable")
        if reasonable_value and shares_outstanding > 0:
            target_price_estimate = reasonable_value / shares_outstanding
        else:
            # Fallback: estimate based on margin of safety or 15% upside
            mos = val_analysis.get("margin_of_safety_vs_fair_value", 0) or 0
            target_price_estimate = current_price * (1 + max(mos, 0.15))
    else:
        target_price_estimate = current_price * 1.15 if current_price else 0.0

    # Build facts for memo generation
    facts = {
        "score": analysis_data.get("score"),
        "max_score": analysis_data.get("max_score"),
        "signal": analysis_data.get("signal"),
        "analysis_details": {k: v.get("details") if isinstance(v, dict) else str(v)[:200]
                            for k, v in analysis_data.items() if k.endswith("_analysis")},
        "market_cap": market_cap,
        "current_price": current_price,
        "target_price_estimate": target_price_estimate,
    }

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are Michael Burry generating a detailed investment memo.

Based on the analysis facts, create a comprehensive investment memo with:
1. A clear bullish or bearish signal (not neutral - pick a direction)
2. Confidence level 0-100
3. A 2-3 sentence investment thesis summarizing the key investment case
4. Exactly 3 bullet points for the bull case
5. Exactly 3 bullet points for the bear case
6. A target price based on short interest, contrarian value opportunities, and catalysts

Return JSON only with exactly these fields:
{
  "signal": "bullish" or "bearish",
  "confidence": int 0-100,
  "reasoning": "brief reasoning",
  "thesis": "2-3 sentence investment thesis",
  "bull_case": ["point 1", "point 2", "point 3"],
  "bear_case": ["point 1", "point 2", "point 3"],
  "target_price": float
}"""
            ),
            (
                "human",
                "Ticker: {ticker}\nFacts:\n{facts}\n\nGenerate the investment memo JSON."
            ),
        ]
    )

    prompt = template.invoke({
        "facts": json.dumps(facts, indent=2),
        "ticker": ticker,
    })

    def create_default_memo():
        return MichaelBurryMemoOutput(
            signal="neutral",
            confidence=50,
            reasoning="Insufficient data for full memo",
            thesis="Unable to generate thesis due to insufficient data.",
            bull_case=["Data unavailable", "Data unavailable", "Data unavailable"],
            bear_case=["Data unavailable", "Data unavailable", "Data unavailable"],
            target_price=target_price_estimate if target_price_estimate else current_price
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=MichaelBurryMemoOutput,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_memo,
    )


def run_michael_burry_with_memo(
    state: AgentState,
    agent_id: str = "michael_burry_agent"
) -> tuple[dict, dict[str, Optional[InvestmentMemo]]]:
    """
    Run Michael Burry analysis and generate InvestmentMemo if conviction >= 70%.

    Returns:
        tuple: (analysis_dict, dict of ticker -> InvestmentMemo or None)
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")

    memos = {}

    # Run the standard agent first
    result = michael_burry_agent(state, agent_id)

    for ticker in tickers:
        # Get current price
        prices = get_prices(ticker, end_date=end_date, limit=1, api_key=api_key)
        current_price = prices[0].close if prices else 0.0

        # Get the analysis for this ticker
        analysis = state["data"]["analyst_signals"].get(agent_id, {}).get(ticker, {})
        confidence = analysis.get("confidence", 0)
        signal = analysis.get("signal", "neutral")

        # Check if we should generate a memo
        if should_generate_memo(confidence) and signal != "neutral":
            progress.update_status(agent_id, ticker, "Generating investment memo")

            # Get market cap for analysis data
            market_cap = get_market_cap(ticker, end_date, api_key=api_key)

            # Build analysis data dict
            analysis_data = {
                "ticker": ticker,
                "signal": signal,
                "confidence": confidence,
                "market_cap": market_cap,
            }

            # Generate memo
            memo_output = generate_michael_burry_memo(
                ticker=ticker,
                analysis_data=analysis_data,
                current_price=current_price,
                state=state,
                agent_id=agent_id,
            )

            # Build key metrics
            key_metrics = {
                "signal": signal,
                "confidence": confidence,
                "market_cap": market_cap,
            }

            # Create the InvestmentMemo
            memo = generate_investment_memo(
                ticker=ticker,
                analyst="Michael Burry",
                signal=memo_output.signal,
                conviction=memo_output.confidence,
                current_price=current_price,
                target_price=memo_output.target_price,
                time_horizon="medium",
                thesis=memo_output.thesis,
                bull_case=memo_output.bull_case,
                bear_case=memo_output.bear_case,
                metrics=key_metrics,
            )

            memos[ticker] = memo
        else:
            memos[ticker] = None

    return state["data"]["analyst_signals"].get(agent_id, {}), memos
