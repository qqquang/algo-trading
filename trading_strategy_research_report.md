# Comprehensive Trading Strategy Research Report

Version: 1.0  
Prepared for: Codex CLI user  
Scope: Multi-asset, multi-horizon, systematic and discretionary strategies

Disclaimer: This document is for research and educational purposes only and is not investment advice. Past performance does not guarantee future results. Strategy metrics are indicative ranges based on published research and practitioner experience; your results will vary due to costs, liquidity, slippage, execution quality, and market regime changes.

---

## Executive Summary

### Top 3 Most Profitable (Risk-Adjusted, Implementable) Overall

1) Multi-Asset Time-Series Momentum (TSMOM) — Position/Algorithmic
   - Core: Go long assets making higher 6–12m highs, short/flat losers. Apply across liquid futures (rates, FX, equity index, metals, energy, ags) and/or ETFs.
   - Why it ranks: Robust across decades and assets; well-documented academic edge; diversification lowers portfolio drawdowns.
   - Typical metrics (pre-cost, diversified): Sharpe 0.6–1.0, win rate 35–45%, PF 1.3–1.8, max DD 15–30%. Low turnover; scalable.
   - Commitment: Low screen time (weekly/monthly), moderate capital (futures margin or ETF implementations).

2) Equity Mean-Reversion (Short-Horizon Pullbacks) — Swing/Algorithmic
   - Core: Buy short-term oversold large-cap equities/indices using RSI(2)/Connors RSI/Bollinger Band tags; hold 1–3 days.
   - Why it ranks: Equity indices/stocks exhibit strong short-horizon mean reversion; implementation is simple and diversified across many names.
   - Typical metrics (pre-cost, large-cap liquid, conservative filters): Win rate 58–70%, RR 1.0–1.4, PF 1.2–1.6, max DD 10–20% (portfolio-level with risk targeting).
   - Commitment: Moderate screen time at session open/close; small to mid capital (cash equities or liquid ETFs).

3) Systematic Options Premium Selling with Risk Controls — Algorithmic/Position
   - Core: Sell defined-risk spreads (e.g., 15–30 delta iron condors/credit spreads) when implied volatility (IV) is elevated vs. realized; avoid binary events.
   - Why it ranks: Options markets often overprice tail risk and gap risk; harvesting volatility premium with robust risk controls can be profitable.
   - Typical metrics (pre-cost, across major indices/liquid underlyings): Win rate 55–75%, RR ~0.5–1.0, PF 1.1–1.4; tail losses without controls.
   - Commitment: Low to moderate screen time; moderate capital (options permissions, margin) with strong risk discipline.

Key success factors
- Diversification across assets, horizons, and independent signals
- Volatility-based position sizing and portfolio risk limits
- Execution discipline (slippage-aware entries, no overtrading)
- Regime detection: Adapt exposure to trend/volatility shifts
- Continuous tracking: Out-of-sample validation, walk-forward tuning

Common pitfalls
- Overfitting parameters to recent regimes
- Ignoring costs, borrow constraints, or liquidity
- Averaging into losers without guardrails
- Overconcentration (single asset, single style)
- Trading through binary events without hedges (options)

Capital and time commitments (indicative)
- TSMOM via ETFs: $5k–$25k; via futures: $15k+ (micro contracts facilitate smaller accounts); weekly updates.
- Equity mean reversion: $5k–$25k; daily session open/close checks; automation recommended.
- Options premium selling: $10k–$50k; 2–3x weekly checks; extra caution around earnings/macro events.

---

## Research Framework Applied

For each category (Scalping, Day Trading, Swing, Position, Algorithmic), this report details:
- Market conditions & instruments
- Technical components (indicators/settings, patterns, MTF confluence, volume)
- Risk management (sizing, stops, take-profits, max DD, correlation controls)
- Performance expectations (win rate, RR, PF, Sharpe, DD duration)
- Implementation requirements (tools, expertise, screen time, psychology)
- Step-by-step entry/exit rules, examples, and common mistakes

Metrics are expressed as indicative ranges for well-executed, risk-managed implementations on liquid instruments with conservative costs.

---

## Category: Scalping (1–5 minute)

Overview: High-frequency, small targets, cost-sensitive. Works best on highly liquid instruments with tight spreads and consistent intraday microstructure (index futures, major FX, top-cap equities). Execution quality dominates edge.

### Top 3 Scalping Strategies

1) VWAP Band Mean-Reversion (Liquid Index Futures/Equities)
   - Market conditions: Ranging/mild-trend intraday; midday lull; stable liquidity.
   - Instruments: ES/NQ futures (or micros), SPY/QQQ, large-cap single stocks; major FX pairs (EURUSD, USDJPY).
   - Technicals: VWAP with 2σ bands (StdDev on 1–5m), 9/20 EMA slope as regime filter; tick/volume footprint optional.
   - Entry: Fade price at ±2σ from VWAP when EMA slope flat/contrary spike; confirmation via decelerating delta/footprint or rejection wick.
   - Exit: Base target: return to VWAP; secondary at mid-band; stop at 1.2–1.5× recent swing or 0.5–0.8× ATR(14, 1m).
   - Risk mgmt: Risk per trade ≤0.25–0.5% acct; max 3 consecutive fades per side; avoid just before macro releases.
   - Performance: Win 55–65%; RR 0.8–1.2; PF 1.1–1.4; fragile to spread/slippage.

2) EMA Pullback Continuation (Opening Trend)
   - Conditions: Strong opening drive with breadth confirmation; trend day candidates.
   - Instruments: ES/NQ, liquid stocks with >$50M 1m volume in first 30m.
   - Technicals: 9/20 EMA (1–2m), ADX(14) > 20 filter, Opening Range (OR) reference, cumulative tick/breadth (for index futures).
   - Entry: After break of OR high/low, wait for pullback to 9 EMA with bull/bear bar close in trend direction; enter on minor consolidation breakout.
   - Exit: Scale at 1R; trail behind 9 EMA or last swing low/high; hard stop below/above pullback swing.
   - Risk mgmt: Risk ≤0.5% per trade; 2–3 attempts max; stop trading if OR fails multiple times.
   - Performance: Win 40–55%; RR 1.2–1.8; PF 1.1–1.5.

3) Opening Range Breakout (1–5m ORB)
   - Conditions: High volatility open; catalysts (earnings, macro); broad market thrust.
   - Instruments: Index futures, gapping stocks with premarket volume; major FX around session overlap.
   - Technicals: Define OR as first 5–15m; use ATR(14, 5m) to size brackets; volume surge filter (≥1.5× baseline).
   - Entry: Stop order at OR break with buffer (0.1–0.2× ATR); no trade if whipsaws inside OR >2x.
   - Exit: Target 1–2× ATR; trail on 9/20 EMA cross; stop opposite OR edge.
   - Risk mgmt: Risk ≤0.5% per attempt; max 2 attempts per side; stand down after 2 failed breaks.
   - Performance: Win 35–50%; RR 1.4–2.2; PF 1.1–1.5; sensitive to slippage.

Implementation
- Tools: Fast data/feed, DOM/footprint optional, low-latency broker, hotkeys.
- Screen time: Continuous for first 2 hours of session; optional midday fade window.
- Psychology: High stress; quick decisions; strict loss limits.
- Mistakes: Overtrading chop; widening stops; trading news spikes; ignoring costs.
- Capital: Futures micros possible with $2–5k; US stocks subject to PDT $25k for frequent intraday trades.

---

## Category: Day Trading (15m–4h intraday)

Overview: Intraday positions with larger swings than scalps. Edges concentrate around session open/close, VWAP behavior, gaps, and news windows.

### Top 3 Day Trading Strategies

1) 15-Min Opening Range Breakout (ORB) with ATR Brackets
   - Market conditions: Trend days, strong breadth/sector alignment.
   - Instruments: ES/NQ/RTY futures, SPY/QQQ, liquid sectors; major FX during London/NY overlap.
   - Technicals: OR(15m), ATR(14, 15m), VWAP, cumulative tick; volume surge filter.
   - Entry rules:
     1) Wait full 15m OR; no pre-break entries.
     2) If breadth > +700 tick (indices) and leader sectors confirm, place stop at OR high + 0.1× ATR (long) or OR low - 0.1× ATR (short).
     3) If price revisits OR midpoint after breakout, stand aside (likely chop).
   - Exits: Scale 1 at +1× ATR; trail remainder on 20 EMA (15m) or fixed 1.5–2× ATR; stop at opposite OR edge after entry.
   - Risk mgmt: 0.5–1.0% per trade; max 2 attempts each side; no trades within 10m of major news.
   - Performance: Win 40–55%; RR 1.3–2.0; PF 1.2–1.6.

2) VWAP Reversion/Fade to Mean
   - Conditions: Ranging day; failed morning breakout; decreasing intraday ATR.
   - Instruments: Index futures, SPY/QQQ, liquid single names.
   - Technicals: VWAP + 2σ bands; 30–60m ATR contraction; Delta/footprint for signs of absorption.
   - Entry: At +2σ band with rejection (long mean reversion toward VWAP if below; inverse for shorts). Prefer confluence with prior day high/low.
   - Exit: Primary target VWAP; secondary mid-band; stop beyond 2.5σ or last swing outside band.
   - Risk mgmt: Risk ≤0.5% per trade; limit to 2–3 total fades per day.
   - Performance: Win 55–65%; RR 0.9–1.3; PF 1.1–1.4.

3) Gap-and-Go (Momentum Continuation)
   - Conditions: Significant news/earnings gaps with sustained premarket trend; high relative volume.
   - Instruments: Large-cap equities and sector ETFs; avoid illiquid small caps unless specialized.
   - Technicals: Premarket high/low reference; 5–10m OR; Relative Volume (RVOL) > 2; 20 EMA trend filter.
   - Entry: Break of premarket high after consolidation above VWAP; or first pullback to 20 EMA with RVOL > 2.
   - Exit: Partial at 1–1.5R; trail below 20 EMA; hard stop below VWAP/pullback low.
   - Risk mgmt: Avoid into halts; no adds if RVOL drops; 0.5–1.0% risk cap.
   - Performance: Win 35–55%; RR 1.5–2.5; PF 1.2–1.7.

Implementation
- Tools: Real-time news, economic calendar, scanner (gaps, RVOL), VWAP bands.
- Screen time: Heaviest in first 2 hours; review into close.
- Psychology: Patience to avoid mid-day chop; discipline to skip news windows.
- Capital: PDT $25k for US equities day trading; futures margins for ES/NQ micros ~$1–2k/contract.

---

## Category: Swing Trading (Multi-day to Multi-week)

Overview: Short-horizon edges that persist over several days to weeks. Combines mean reversion in equities with short-term trend continuation setups.

### Top 3 Swing Strategies

1) Equity Mean Reversion: RSI(2)/Connors RSI Pullback
   - Market conditions: Range-bound to mild uptrend; works best in indices and large caps.
   - Instruments: S&P 500 constituents, SPY/QQQ/sector ETFs; global large-cap ETFs.
   - Technicals: RSI(2) < 10 for longs; Connors RSI < 10–15; Bollinger Band(20,2) lower band tag; 50/200 DMA trend filter to prefer long-only.
   - Entry: Next open after signal or intraday on reversal bar; avoid entering on day of large macro reports.
   - Exit: Time-based 2–3 trading days; or exit on RSI(2) > 70/80; or close at middle band.
   - Risk mgmt: Volatility targeting (e.g., 10–15% annualized per position); stop at 1.5× ATR(14) below entry; portfolio stop if VIX spike > threshold.
   - Performance: Win 60–70%; RR 0.9–1.3; PF 1.2–1.6; short side weaker.

2) Breakout-Pullback to 20 EMA (Trend Continuation)
   - Conditions: Clear uptrend with higher highs/lows; sector strength.
   - Instruments: Strong names with RS outperformance; commodity ETFs in trend.
   - Technicals: 20 EMA rising; prior breakout above resistance; volume contraction on pullback; inside-day/NR7 patterns.
   - Entry: Buy first higher low touching 20 EMA with reversal candle; add if breaks minor swing high.
   - Exit: Partial at prior high; trail on 10 EMA or swing lows; time stop 10 trading days.
   - Risk mgmt: Risk 0.5–1.0% per name; cap sector correlation; do not add into breakdown of 20 EMA on volume.
   - Performance: Win 45–60%; RR 1.4–2.2; PF 1.3–1.8.

3) Index Mean Reversion via Bollinger Reversion (Long-Only)
   - Conditions: Ranging broad index; volatility spikes.
   - Instruments: SPY/QQQ/IEFA/EEM; futures equivalents.
   - Technicals: Close below lower Bollinger(20,2) and > 200 DMA; VIX percentile > 60; breadth washout (e.g., %>20 DMA < 20%).
   - Entry: Buy on close below lower band; scale if second tag with smaller range.
   - Exit: Middle band or RSI(2) > 80; time stop 5 days.
   - Risk mgmt: Use vol targeting; avoid in sustained downtrends (below 200 DMA).
   - Performance: Win 58–65%; RR 0.9–1.2; PF 1.1–1.4.

Implementation
- Tools: End-of-day screeners; Python/backtesting (pandas, vectorbt, backtrader); broker API.
- Screen time: Low; daily review at close; weekly rebalance checks.
- Psychology: Comfort with overnight risk; patience through multi-day holds.
- Capital: $5k–$25k typical; lower min via ETFs. Reg-T margin optional; manage risk.

---

## Category: Position Trading (Weeks to Months)

Overview: Focus on intermediate to long-term trends and regime filters. Lower turnover, more scalable and tax efficient (jurisdiction-dependent).

### Top 3 Position Strategies

1) Multi-Asset Time-Series Momentum (TSMOM)
   - Conditions: Persistent medium/long-term trends; broad diversification across assets.
   - Instruments: Global futures (rates, FX, equity indices, commodities) or ETFs (hedged where appropriate).
   - Technicals: 12-1 month momentum; breakout rules (e.g., 50/200 DMA cross, 6/12m high/low); vol targeting.
   - Entry: Long if return(12m) > 0 and price > 200 DMA; short/flat if negative (ETF route: flat or inverse ETFs if available/liquid).
   - Exit: Opposite signal or trailing stop (3× ATR on weekly); monthly rebalance.
   - Risk mgmt: Target 10–15% portfolio vol; risk parity weights; cap per-asset risk at 1–2%.
   - Performance: Sharpe 0.6–1.0; PF 1.3–2.0; DD 15–30%; works across decades.

2) 200-Day Moving Average Timing (Global Equity/ETF Timing)
   - Conditions: Reduce deep bear market drawdowns; capture equity risk premium above trend.
   - Instruments: Broad ETFs (SPY/ACWI/IEFA/EEM) + bonds (AGG/IEF) + diversifiers (GLD/DBC).
   - Technicals: Price vs. 200 DMA filter; monthly rebalance; defensive sleeve when below trend.
   - Entry/Exit: Long equity ETF when above 200 DMA; rotate to bonds/cash when below; optional add of trend-following on diversifiers.
   - Risk mgmt: Vol targeting 8–12%; correlation caps; rebalance drift control.
   - Performance: Sharpe 0.5–0.8; DD reduced vs. buy/hold; lower tail risk.

3) Factor Tilt Portfolio (Value/Quality/Momentum)
   - Conditions: Long-term structural premia; multi-year horizons.
   - Instruments: Factor ETFs or systematically screened stocks; quarterly/annual rebalance.
   - Technicals: Composite ranks (e.g., value: EV/EBIT, P/B; quality: ROIC, margin stability; momentum: 12-1m); risk parity.
   - Entry/Exit: Buy top decile/quantile; rebalance quarterly; drop deteriorating ranks.
   - Risk mgmt: Sector/industry caps; stop trading if factor crowding spikes (monitor spreads); optional trend overlay to cut left tails.
   - Performance: Sharpe 0.5–0.9 long-term; periods of underperformance; diversification across factors critical.

Implementation
- Tools: Monthly data pipeline; ETF/stock screener; position-sizing and vol-targeting engine.
- Screen time: Low; weekly/monthly updates.
- Psychology: Tolerance for extended underperformance against benchmarks.
- Capital: $10k+ for ETFs; futures route requires more capital/margin but is capital efficient at scale.

---

## Category: Algorithmic / Quantitative (Systematic)

Overview: Rule-based systems with backtesting, risk targeting, and portfolio construction. Emphasis on breadth, diversification, and statistical robustness.

### Top 3 Quant Strategies

1) Cross-Sectional Momentum (12-1) with Portfolio Vol Targeting
   - Universe: Liquid equities (e.g., top 1000 by mkt cap), or futures cross-asset.
   - Signal: 12-month return excluding last month; rebalance monthly.
   - Portfolio: Top decile long, bottom decile short (or long-only tilt); vol target 10–15%; max position 2–3%.
   - Risk mgmt: Risk parity weights; sector caps; turnover controls (buffer zones).
   - Performance: Sharpe 0.6–1.0 (long-short) historically; capacity limits in small caps.

2) Statistical Arbitrage Pairs/Cointegration Trading
   - Universe: Highly related equities/ETFs (e.g., same sector), or index-component pairs.
   - Signal: Engle–Granger cointegration; trade z-score deviations ±2.0–2.5; half-life-based exit.
   - Entry/Exit: Enter spread at ±2σ; scale to ±3σ; exit at mean or z=0.5; time stop at 1–2 half-lives.
   - Risk mgmt: Beta/hedge ratio estimation; cap single-spread risk 0.5–1.0%; stop trading if residual variance jumps.
   - Performance: Win 55–65%; RR 0.9–1.3; PF 1.1–1.4; stable in range-bound regimes; vulnerable to structural breaks.

3) Options Volatility Premium Harvesting (Defined-Risk)
   - Universe: Index ETFs (SPY, QQQ, IWM), large-cap single names; weekly/monthly expiries.
   - Signal: IV rank > 50; term structure in contango; realized < implied; avoid binary events.
   - Structures: Iron condors/credit spreads at 15–30 delta; 30–45 DTE; take profits at 50–70% max credit.
   - Risk mgmt: Hard stop on spread value at 1.5–2.0× credit received; mechanical roll with risk-off triggers (VIX spike); tail hedges optional.
   - Performance: Win 60–75%; RR ~0.6–1.0; PF 1.1–1.4; tail-aware management essential.

Implementation
- Tools: Python backtesting (pandas/NumPy/vectorbt/backtrader), stats (statsmodels), optimization (cvxpy), broker API (IBKR/Tradier), options analytics (OptionStrat/quantlib).
- Screen time: Scheduled rebalances; monitoring for regime/vol spikes.
- Psychology: System discipline; tolerance for tracking error and model risk.
- Capital: Varies by universe; options permissions and collateral for spreads.

---

## Market Conditions & Regime Adaptation

- Trending markets: Favor TSMOM, EMA pullback continuation, ORB.
- Ranging markets: Favor VWAP reversion, pairs trading, equity mean reversion.
- High volatility: Reduce size, widen stops; prefer breakout/volatility expansion strategies; avoid short premium into events.
- Low volatility: Mean reversion and premium selling benefit; reduce expectations for breakout follow-through.
- Early bull: Trend continuation in leaders; breakout-pullback setups.
- Late bull: Factor rotation (quality/defensive); options premium caution.
- Bear: Trend-following shorts; long-vol overlays; defensive timing models.

Regime detection tools
- Volatility: Rolling ATR percentile; VIX/VVIX thresholds (e.g., VIX > 25 risk-off).
- Breadth: % above 200 DMA, advance/decline lines; McClellan oscillator.
- Trend: Slope of 200 DMA; 12-1m momentum breadth.
- Macro calendar: CPI, NFP, FOMC, ECB; earnings seasons.

---

## Technical Analysis Components (Settings & Confluence)

- Moving averages: 9/20 EMA (intra), 20/50 EMA (swing), 100/200 SMA (position). Crosses and pullbacks.
- VWAP + bands: 1–2 standard deviations on 1–5m for intraday fades; session VWAP anchor.
- RSI: Short-horizon RSI(2), Connors RSI for mean reversion; RSI(14) for momentum context.
- Bollinger Bands: 20 period, 2 standard deviations; tag and reversion rules.
- ATR: Stops/targets sized in ATR units; ATR percentiles for regime detection.
- Patterns: ORB, inside day (ID), NR7; 3-bar pullback; failed breakouts as reversal cues.
- Volume: Relative volume (RVOL) filters; volume contraction on pullbacks; accumulation/distribution checks.
- Multi-timeframe: Align lower timeframe entries with higher timeframe trend (e.g., 1–5m entries with 15–60m trend).

Support/Resistance Methodologies
- Prior day high/low/close; premarket extremes; weekly pivots.
- Anchored VWAP from major pivots/news; confluent with static S/R.
- Supply/demand zones from swing structure; wick rejections.

---

## Risk Management Framework

Position sizing
- Fixed fractional: Risk 0.25–1.0% of equity per trade (shorter horizons at low end).
- Volatility-based: Size so that position contributes to target vol (e.g., 10–15% annualized); use ATR-based dollar risk.
- Kelly fraction: Use 0.25–0.5 Kelly on robust edges; avoid full Kelly.

Stops and exits
- Initial: ATR(14) multiples or structural swing highs/lows.
- Trailing: EMA trails (9/20), parabolic SAR, or chandelier (3× ATR).
- Time-based: Close after N bars/days to avoid decay of edge.

Take-profit methods
- Fixed RR brackets (1.0–2.0R) with partials.
- VWAP/mean targets for reversion strategies.
- Momentum-based exits for trend strategies (MA cross exit).

Drawdown tolerances
- Per-strategy: 8–15% (shorter horizons generally lower); portfolio: 15–25% for diversified multi-asset.
- Circuit breakers: Reduce exposure by 50% after DD > strategy threshold; pause and review at portfolio DD limit.

Correlation risk
- Cap sector/asset exposure; apply risk parity weights; maintain cash sleeve.

---

## Performance Metrics & Expectations

- Win rate: Mean reversion 55–70%; breakout/trend 35–55%.
- Risk:Reward: Reversion 0.8–1.3; momentum 1.2–2.5.
- Profit factor: 1.1–1.8 for robust retail systems pre-cost; higher when well-diversified.
- Sharpe: 0.4–1.0 realistic for live portfolios; higher requires breadth and discipline.
- Max consecutive losses: 6–12 for trend systems; plan psychologically and financially.
- Drawdown duration: Trend systems may see long plateaus; reversion recovers faster but suffers in crash regimes.

---

## Specific Research Questions Addressed

Top 3 by category: Provided in each section above.

Best by market cycles
- Trending: TSMOM, ORB, EMA pullback continuation.
- Ranging: VWAP mean reversion, Bollinger reversion, pairs/stat arb.
- High volatility: Breakouts with ATR brackets; defensive sizing; avoid short gamma.
- Low volatility: Options premium selling; equity mean reversion.

Minimum capital (indicative)
- Scalping futures (micros): $2–5k; standard futures: $10k+.
- US equities day trading (PDT): $25k+ recommended.
- Swing equities/ETFs: $5–25k.
- Options spreads: $10–50k depending on width and diversification.

Broker/spread considerations
- Scalping: ECN/low-latency routing, raw spreads, low per-share commissions.
- Futures: Low commissions (<$2/side), high uptime, stable margins.
- FX: True ECN with tight spreads; avoid dealing-desk markups.
- Options: Tight spreads on index/large caps; avoid illiquid strikes.

Implementation requirements
- Tools: Charting (TradingView, NinjaTrader), backtesting (Python: pandas/vectorbt/backtrader; R: quantstrat), broker APIs (IBKR, Tradier), news feeds, economic calendars.
- Expertise: From basic (swing) to advanced (stat arb/options risk). Start simple, automate gradually.
- Screen time: Scalping/day trading heavy; swing/position light; systematic allows batching.
- Psychology: High-frequency trading is stressful; position/systematic require patience with underperformance.

Market-specific adaptation
- Volatility regimes: Size down in spikes; widen stops; switch from reversion to breakout when ATR percentiles high.
- Seasonality: Turn-of-month, holiday effects, earnings seasons; cautious use—edges are small, trade only with confluence.
- News events: Stand aside +/- 10 minutes around tier-1 events for intraday; avoid short premium through earnings/FOMC.

---

## Detailed Step-by-Step Rules (Representative Examples)

Example A: Equity RSI(2) Mean Reversion (Swing, Long-Only)
1) Universe: S&P 500 + liquid ETFs.
2) Filters: Above 200 DMA; AvgDollarVol > $20M; no earnings within 2 days.
3) Signal: RSI(2) < 10 or Close < Lower Bollinger(20,2).
4) Entry: Next open; if gap > 1.5× ATR adverse, skip.
5) Sizing: Target 12% annualized vol per position; cap 1% equity per name.
6) Exit: When RSI(2) > 70 or at middle band; time stop 3 days.
7) Risk: Portfolio VaR cap 5% at 95% conf; halt if VIX > 35 and breadth extremes persist.

Example B: Futures TSMOM (Weekly)
1) Universe: 30–60 liquid futures; or ETF proxies if futures unavailable.
2) Signal: Price > 200 DMA and 12-1m return > 0 → long; else short/flat.
3) Sizing: Risk parity; target 12% portfolio vol.
4) Execution: Weekly rebalance; limit orders with slippage allowance; avoid week of rollover for entries unless urgent.
5) Exit: Opposite signal; 3× ATR weekly trailing stop as override.
6) Risk: Max asset weight 5%; sector caps; portfolio DD circuit breaker 20%.

Example C: Options Iron Condor (45 DTE)
1) Underlying: SPY/QQQ/IWM.
2) Conditions: IV Rank > 50; VIX term structure upward sloping; no major event inside 3 days of expiry.
3) Structure: Sell 20-delta short strikes; buy 10-delta wings; collect >$1.50 credit per $5 wide on SPY.
4) Management: Take profit at 50–60% credit; stop at 1.75× initial credit; roll or close if breach of short strike with VIX spike.
5) Risk: Limit total short premium at risk to ≤10% of equity; do not overlap too many expiries; hedge tail with cheap OTM puts during risk-off.

---

## Comparative Analysis

Profitability ranking (risk-adjusted, implementability)
1) TSMOM (Position/Quant)
2) Equity Mean Reversion (Swing)
3) Options Premium Selling (Defined-Risk) (Quant/Position)
4) Cross-Sectional Momentum (Quant)
5) Day ORB with ATR Brackets (Day)
6) VWAP Reversion (Day)
7) Pairs/Cointegration (Quant)
8) EMA Pullback Continuation (Scalp/Day)
9) Scalping VWAP Bands (Scalp)

Time investment vs. return
- Lowest time: TSMOM, 200DMA timing, factor tilt, options premiums (non-earnings weeks).
- Moderate: Equity mean reversion (EOD scans), swing breakouts.
- Highest: Scalping/day trading.

Skill level matrix (beginner → advanced)
- Beginner: 200DMA timing, basic ETF rotations, long-only RSI(2) swing.
- Intermediate: ORB day trading with strict rules, Bollinger reversion, cross-sectional momentum long-only.
- Advanced: Pairs/cointegration, defined-risk options program, multi-asset TSMOM with futures and vol targeting.

---

## Actionable Recommendations

- Beginners
  - Start with long-only equity mean reversion (RSI(2)) on indices/large caps, automated entries/exits, strict risk.
  - Learn vol targeting and portfolio tracking; avoid intraday until consistent.
  - Tools: TradingView for signals; Python for backtests; IBKR for execution.

- Experienced traders
  - Build a diversified core: TSMOM (ETFs or futures) + equity mean reversion + options premium module.
  - Add cross-sectional momentum or pairs for breadth; use regime filters.
  - Automate risk/position sizing; enforce portfolio-level drawdown controls.

- Diversification combos
  - Core trend (TSMOM) + short-horizon reversion (RSI(2)) + optional options income when vol/term-structure favorable.
  - Keep correlations low by mixing horizons and signals.

- Learning path
  1) Risk basics and expectancy; position sizing.
  2) Mean reversion swing with automation.
  3) Momentum timing and vol targeting.
  4) Options spreads risk management and event handling.
  5) Pairs/cointegration and broader quant toolkit.

- Budget estimates
  - Software: $0–$50/mo (charting) + $0–$50/mo (data/backtesting) initially.
  - Commissions: Prefer IBKR-tiered or futures discount brokers.
  - Hardware: Dual monitors; low-latency not required unless scalping.

---

## Tools, Platforms, and Implementation

- Data/Backtesting: Python (pandas, numpy, vectorbt, backtrader), statsmodels, TA-Lib; R (TTR, quantstrat).
- Execution: Interactive Brokers TWS API, Tradier, TradeStation; for crypto, exchange APIs (with caution and risk controls).
- Charting/Scanning: TradingView, NinjaTrader, Thinkorswim; custom Python dashboards (Streamlit, Dash).
- Automation: Cron-based scripts; Dockerized services; logging to SQLite/Postgres; alerting via email/Slack.
- Monitoring: Performance dashboards; risk limits; drawdown alerts; Monte Carlo stress.

Screen time & psychology
- Scalping/day: High attention; strict daily loss limits; performance drift when fatigued.
- Swing/position: Scheduled reviews; discipline to avoid tinkering; acceptance of tracking error.

---

## Data Sources and References (for follow-up validation)

- Academic: SSRN working papers on momentum/mean reversion; AQR, Alpha Architect research blogs.
- Practitioner: Books by Andreas Clenow (trend following), Larry Connors (short-term trading), Ralph Vince (money management).
- Aggregators: Quantpedia for strategy taxonomies and summaries.
- Broker stats: CME liquidity reports; broker slippage/commission schedules.
- Case studies: Professional trader interviews (Trend Following, Market Wizards) for qualitative insights.

---

## Critical Success Factors

- Verifiable edges with out-of-sample tests and walk-forward validation.
- Emphasis on risk controls: sizing, stops, correlation, and circuit breakers.
- Clear execution plans with pre-defined scenarios; no on-the-fly improvisation.
- Continuous improvement: periodic parameter reviews, but avoid overfitting; use cross-validation.
- Documentation: Trade logs, post-trade tagging, expectancy and error-rate tracking.

---

## Additional Considerations

- Taxes: Higher turnover (scalping/day) typically short-term rates; futures 60/40 tax treatment in some jurisdictions; consult a tax professional.
- Regulation: US PDT rules ($25k) for equities; options permissions; futures suitability; local compliance.
- Technology costs: Data feeds, platforms, and commissions materially affect edge; negotiate rates at scale.
- Broker selection: Stability, risk controls (brackets, OCO), API reliability, borrow availability for shorts.
- Market access: After-hours liquidity differences (equities vs. futures); roll calendars for futures.
- Strategy adaptation: Regular regime checks; degrade gracefully when edges weaken; retire or refit strategies with evidence.

---

## Performance Tracking & Optimization

- Tracking: Maintain detailed trade logs (signal, context, size, entry/exit, slippage, reason codes).
- Analytics: Expectancy (E = P×W – (1–P)×L), PF, Sharpe, MAR, turnover, heat maps by regime.
- Robustness: Walk-forward optimization; nested cross-validation for parameters; sensitivity analysis.
- Stress tests: Scenario analysis (crashes, vol spikes), Monte Carlo reshuffling of trade sequences.
- Governance: Weekly review, monthly strategy council, quarterly deep-dive and parameter sanity checks.

---

## Appendices

### A. Quick Parameter Reference
- RSI(2) MR: RSI(2) < 10 entry; exit RSI(2) > 70; Alt: Connors RSI < 10–15; Time stop 3d.
- Bollinger MR: 20 period, 2σ; long on lower tag above 200 DMA; exit mid-band.
- ORB Day: OR = 15m; ATR(14, 15m) brackets; volume surge ≥1.5× baseline.
- EMA Pullback: 9/20 EMA slope; buy first HL at 9 EMA; trail 9 EMA.
- TSMOM: 12-1m momentum + above 200 DMA; weekly rebalance; 3× ATR trailing stop.
- Options Condor: 15–30 delta; 30–45 DTE; TP 50–70% credit; stop 1.75× credit; IV Rank > 50.

### B. Regime Classification Heuristics
- Volatility: ATR percentile > 70 = high vol; size down 50%.
- Trend: % of assets above 200 DMA > 60% = trend supportive for long bias.
- Breadth: NYSE cumulative A/D rising supports trend continuation setups.

### C. Example Portfolio Blueprint (Retail, $25k)
- 40% Core: ETF-based TSMOM timing (monthly).
- 30% Swing MR: RSI(2) on SPY/QQQ + top-cap names (EOD signals).
- 20% Options: Monthly iron condors on SPY/QQQ when IV Rank > 50, defined risk.
- 10% Cash buffer: Event risk and tail hedges when needed.

Risk targets: Portfolio vol 10–12%; max DD 15–20%; exposure scaled by regime.

---

End of Report

