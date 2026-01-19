"""Constants and utilities related to analysts configuration."""

from src.agents import portfolio_manager
from src.agents.bill_ackman import bill_ackman_agent
from src.agents.charlie_munger import charlie_munger_agent
from src.agents.michael_burry import michael_burry_agent
from src.agents.phil_fisher import phil_fisher_agent
from src.agents.peter_lynch import peter_lynch_agent
from src.agents.stanley_druckenmiller import stanley_druckenmiller_agent
from src.agents.warren_buffett import warren_buffett_agent

# Define analyst configuration - single source of truth
# Only includes agents that actually exist in src/agents/
ANALYST_CONFIG = {
    "bill_ackman": {
        "display_name": "Bill Ackman",
        "description": "The Activist Investor",
        "investing_style": "Seeks to influence management and unlock value through strategic activism and contrarian investment positions.",
        "agent_func": bill_ackman_agent,
        "type": "analyst",
        "order": 0,
    },
    "charlie_munger": {
        "display_name": "Charlie Munger",
        "description": "The Rational Thinker",
        "investing_style": "Advocates for value investing with a focus on quality businesses and long-term growth through rational decision-making.",
        "agent_func": charlie_munger_agent,
        "type": "analyst",
        "order": 1,
    },
    "michael_burry": {
        "display_name": "Michael Burry",
        "description": "The Big Short Contrarian",
        "investing_style": "Makes contrarian bets, often shorting overvalued markets and investing in undervalued assets through deep fundamental analysis.",
        "agent_func": michael_burry_agent,
        "type": "analyst",
        "order": 2,
    },
    "peter_lynch": {
        "display_name": "Peter Lynch",
        "description": "The 10-Bagger Investor",
        "investing_style": "Invests in companies with understandable business models and strong growth potential using the 'buy what you know' strategy.",
        "agent_func": peter_lynch_agent,
        "type": "analyst",
        "order": 3,
    },
    "phil_fisher": {
        "display_name": "Phil Fisher",
        "description": "The Scuttlebutt Investor",
        "investing_style": "Emphasizes investing in companies with strong management and innovative products, focusing on long-term growth through scuttlebutt research.",
        "agent_func": phil_fisher_agent,
        "type": "analyst",
        "order": 4,
    },
    "stanley_druckenmiller": {
        "display_name": "Stanley Druckenmiller",
        "description": "The Macro Investor",
        "investing_style": "Focuses on macroeconomic trends, making large bets on currencies, commodities, and interest rates through top-down analysis.",
        "agent_func": stanley_druckenmiller_agent,
        "type": "analyst",
        "order": 5,
    },
    "warren_buffett": {
        "display_name": "Warren Buffett",
        "description": "The Oracle of Omaha",
        "investing_style": "Seeks companies with strong fundamentals and competitive advantages through value investing and long-term ownership.",
        "agent_func": warren_buffett_agent,
        "type": "analyst",
        "order": 6,
    },
}

# Derive ANALYST_ORDER from ANALYST_CONFIG for backwards compatibility
ANALYST_ORDER = [(config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]


def get_analyst_nodes():
    """Get the mapping of analyst keys to their (node_name, agent_func) tuples."""
    return {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}


def get_agents_list():
    """Get the list of agents for API responses."""
    return [
        {
            "key": key,
            "display_name": config["display_name"],
            "description": config["description"],
            "investing_style": config["investing_style"],
            "order": config["order"]
        }
        for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])
    ]
