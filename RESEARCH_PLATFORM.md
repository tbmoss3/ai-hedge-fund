# AI Research Team - Human-in-the-Loop Investment Platform

A human-in-the-loop investment research platform forked from [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund). AI analysts generate investment memos; you (the human portfolio manager) review and approve the best ideas.

## Key Changes from Original

- **Removed**: AI Portfolio Manager, Risk Manager, automated trading
- **Added**: Human review dashboard with approve/reject workflow
- **Kept**: 7 famous investor agents (Buffett, Munger, Lynch, Fisher, Burry, Ackman, Druckenmiller)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   CONTINUOUS MONITORING                      │
│   7 AI Analysts scan S&P 500 + Russell 2000 bi-weekly       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   THRESHOLD FILTER (≥70%)                    │
│   Only high-conviction memos surface to your inbox           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   YOUR DASHBOARD                             │
│   Review memos → Approve/Reject → Track investments          │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start (Docker)

1. Clone and configure:
```bash
git clone https://github.com/tbmoss3/ai-hedge-fund.git
cd ai-hedge-fund
cp .env.example .env
# Edit .env with your API keys
```

2. Start the platform:
```bash
cd docker
docker-compose -f docker-compose.research.yml up -d
```

3. Access the dashboard:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key for LLM calls (~$25/mo) |
| `FISCAL_API_KEY` | Fiscal.ai API key for fundamentals |
| `DB_PASSWORD` | PostgreSQL password |

### Scanner Configuration (`config/scanner.yaml`)

```yaml
scanner:
  conviction_threshold: 70  # Only surface memos with ≥70% conviction
  batch_size: 100           # Tickers per batch
  rate_limit_delay: 1.0     # Seconds between batches

schedule:
  frequency: biweekly       # Scan every 2 weeks
```

## Dashboard Views

### 1. Inbox
- Review pending investment memos
- Filter by analyst, signal direction, conviction level
- Approve or reject each memo

### 2. Investments
- Track approved investments
- See entry price, current price, P&L
- Close positions when ready

### 3. Leaderboard
- See which analysts perform best
- Win rate, average return by analyst

## Analyst Roster

| Analyst | Philosophy | Time Horizon |
|---------|------------|--------------|
| Warren Buffett | Quality businesses, owner earnings, margin of safety | Long |
| Charlie Munger | Mental models, moat focus, concentrated bets | Long |
| Peter Lynch | Growth at reasonable price, "buy what you know" | Medium |
| Phil Fisher | Scuttlebutt research, long-term growth compounders | Long |
| Michael Burry | Contrarian deep dives, asymmetric bets | Medium |
| Bill Ackman | Activist value, catalyst-driven | Medium |
| Stanley Druckenmiller | Macro + micro, momentum, position sizing | Short |

## Running the Scanner Manually

```bash
# Scan specific tickers
python -m src.cli.scan --tickers AAPL,MSFT,NVDA

# Scan with specific analysts
python -m src.cli.scan --tickers AAPL --analysts warren_buffett,michael_burry

# Full universe scan (S&P 500 + Russell 2000)
python -m src.cli.scan --full-universe
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/inbox` | List pending memos |
| POST | `/api/inbox/{id}/approve` | Approve memo, create investment |
| POST | `/api/inbox/{id}/reject` | Reject memo |
| GET | `/api/investments` | List investments |
| PATCH | `/api/investments/{id}/close` | Close investment |
| GET | `/api/analysts/leaderboard` | Analyst performance |

## Estimated Costs

| Service | Cost |
|---------|------|
| DeepSeek-V3 LLM | ~$25/mo (bi-weekly full scan) |
| Fiscal.ai | Your existing plan |
| **Total** | ~$25/mo |

## License

MIT (inherited from ai-hedge-fund)
