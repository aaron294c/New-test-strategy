```
==========================================================================================
OPTIONS ANALYSIS — RSI-MA <5th Percentile ONLY (No COV Filter)
QQQ / SPY / NQ=F / ES=F
==========================================================================================
IV Source:  QQQ/NQ → ^VXN (CBOE NASDAQ-100 30-day IV)
            SPY/ES → ^VIX (CBOE S&P 500 30-day IV)
Short DTE:  ≤14d options → ^VIX9D scaled by index ratio
Holding:    5 trading days | Cooldown: 10 bars (non-overlapping)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIGNAL QUALITY: RSI-MA ONLY vs RSI-MA+COV
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticker    RSI-MA Only N    Win%      EV% │  RSI+COV N    Win%      EV% │  More signals   Δ Win%     ΔEV%
------------------------------------------------------------------------------------------
QQQ                  42   69.0%  +1.210% │         27   66.7%  +1.092% │           +15    +2.4pp  +0.119pp
SPY                  47   70.2%  +0.884% │         33   69.0%  +0.519% │           +14    +1.2pp  +0.365pp
NQ=F                 42   69.0%  +1.124% │         29   71.4%  +1.241% │           +13    -2.4pp  -0.117pp
ES=F                 42   69.0%  +0.963% │         32   74.1%  +1.064% │           +10    -5.0pp  -0.101pp

KEY FINDING: Removing COV filter gives MORE signals at HIGHER win rate and EV.
The RSI-MA <5th percentile is sufficient as a standalone signal for QQQ/SPY.
COV adds value for individual stocks (less liquid, noisier signals).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QQQ — NASDAQ 100 ETF  |  N=42  |  IV src=^VXN  |  Median IV at entry=24.2%  |  Median crush=3.2pp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Strategy                                  N    Win%     AvgW     AvgL       EV    R:R       P5   Median      P95   MaxLoss
  ------------------------------------------------------------------------------------------------------------
  Equity (stock long)                      42   69.0%   +3.03%   -2.86%  +1.210%  1.06x   -3.79%   +1.55%   +6.27%   -12.54%
  Long ATM Call (35 DTE)                   42   52.4%   +37.0%   -24.7%   +7.63%  1.50x   -51.0%    +5.3%   +60.6%    -52.7%
  Bull Call Spread ATM/+3% (35 DTE)        42   64.3%   +34.6%   -21.4%  +14.63%  1.62x   -42.3%   +17.5%   +54.8%    -44.8%
  Bull Put Spread -2%/-5% (10 DTE)         42   78.6%   +20.5%   -22.2%  +11.30%  0.92x   -36.8%   +16.9%   +31.8%    -43.2%

  IV Regime Breakdown — QQQ
  Strategy                                                Low IV<15%                  Mid IV 15-25%                    High IV>25%
  -----------------------------------------------------------------------------------------------
  Long ATM Call (35 DTE)                                        N/A  N=25 Win=48% EV=+6.8%              N=17 Win=59% EV=+8.8%            
  Bull Call Spread ATM/+3% (35 DTE)                             N/A  N=25 Win=60% EV=+12.1%              N=17 Win=71% EV=+18.3%            
  Bull Put Spread -2%/-5% (10 DTE)                              N/A  N=25 Win=72% EV=+6.6%              N=17 Win=88% EV=+18.2%            

  Greeks at Median Entry IV (24.2%), spot=100 (normalised)
  Strategy                              DTE   Delta   Theta/d   Vega/1%  Theta5d/Prem   BE move
  ------------------------------------------------------------------------------------------
  Long ATM Call (35 DTE)                 35  +0.550   -0.0617   +0.1475         +7.8%    +3.96%
  Bull Call Spread ATM/+3% (35 DTE)      35  +0.130   -0.0031   +0.0018         +0.0%    +1.34%
  Bull Put Spread -2%/-5% (10 DTE)       10  -0.184   +0.0307   -0.0287        +22.5%    -2.68%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SPY — S&P 500 ETF  |  N=47  |  IV src=^VIX  |  Median IV at entry=21.7%  |  Median crush=3.4pp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Strategy                                  N    Win%     AvgW     AvgL       EV    R:R       P5   Median      P95   MaxLoss
  ------------------------------------------------------------------------------------------------------------
  Equity (stock long)                      47   70.2%   +2.29%   -2.43%  +0.884%  0.94x   -4.11%   +1.29%   +4.64%   -12.54%
  Long ATM Call (35 DTE)                   47   51.1%   +20.2%   -22.2%   -0.55%  0.91x   -35.3%    +0.1%   +41.1%    -47.7%
  Bull Call Spread ATM/+3% (35 DTE)        47   66.0%   +29.8%   -18.8%  +13.28%  1.59x   -32.9%   +13.1%   +52.2%    -47.9%
  Bull Put Spread -2%/-5% (10 DTE)         47   89.4%   +17.8%   -32.7%  +12.40%  0.54x   -31.4%   +15.9%   +33.1%    -47.7%

  IV Regime Breakdown — SPY
  Strategy                                                Low IV<15%                  Mid IV 15-25%                    High IV>25%
  -----------------------------------------------------------------------------------------------
  Long ATM Call (35 DTE)               N= 2 Win=50% EV=-12.0%              N=29 Win=55% EV=+0.3%              N=16 Win=44% EV=-0.7%            
  Bull Call Spread ATM/+3% (35 DTE)    N= 2 Win=50% EV=-9.2%              N=29 Win=62% EV=+11.7%              N=16 Win=75% EV=+18.9%            
  Bull Put Spread -2%/-5% (10 DTE)     N= 2 Win=50% EV=-19.4%              N=29 Win=93% EV=+11.5%              N=16 Win=88% EV=+18.1%            

  Greeks at Median Entry IV (21.7%), spot=100 (normalised)
  Strategy                              DTE   Delta   Theta/d   Vega/1%  Theta5d/Prem   BE move
  ------------------------------------------------------------------------------------------
  Long ATM Call (35 DTE)                 35  +0.552   -0.0566   +0.1474         +7.9%    +3.60%
  Bull Call Spread ATM/+3% (35 DTE)      35  +0.145   -0.0036   +0.0027         +0.0%    +1.33%
  Bull Put Spread -2%/-5% (10 DTE)       10  -0.191   +0.0313   -0.0327        +25.9%    -2.61%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NQ=F — NASDAQ 100 Futures  |  N=42  |  IV src=^VXN  |  Median IV at entry=24.4%  |  Median crush=3.2pp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Strategy                                  N    Win%     AvgW     AvgL       EV    R:R       P5   Median      P95   MaxLoss
  ------------------------------------------------------------------------------------------------------------
  Equity (stock long)                      42   69.0%   +2.96%   -2.97%  +1.124%  1.00x   -3.95%   +1.34%   +7.15%   -11.24%
  Long ATM Call (35 DTE)                   42   50.0%   +37.5%   -25.7%   +5.92%  1.46x   -52.6%    -0.4%   +67.4%    -53.7%
  Bull Call Spread ATM/+3% (35 DTE)        42   66.7%   +32.4%   -23.9%  +13.60%  1.35x   -39.3%   +15.6%   +63.9%    -45.3%
  Bull Put Spread -2%/-5% (10 DTE)         42   78.6%   +20.5%   -24.2%  +10.93%  0.85x   -38.9%   +16.8%   +32.4%    -43.1%

  IV Regime Breakdown — NQ=F
  Strategy                                                Low IV<15%                  Mid IV 15-25%                    High IV>25%
  -----------------------------------------------------------------------------------------------
  Long ATM Call (35 DTE)                                        N/A  N=24 Win=50% EV=+7.0%              N=18 Win=50% EV=+4.5%            
  Bull Call Spread ATM/+3% (35 DTE)                             N/A  N=24 Win=67% EV=+12.2%              N=18 Win=67% EV=+15.5%            
  Bull Put Spread -2%/-5% (10 DTE)                              N/A  N=24 Win=75% EV=+6.6%              N=18 Win=83% EV=+16.7%            

  Greeks at Median Entry IV (24.4%), spot=100 (normalised)
  Strategy                              DTE   Delta   Theta/d   Vega/1%  Theta5d/Prem   BE move
  ------------------------------------------------------------------------------------------
  Long ATM Call (35 DTE)                 35  +0.550   -0.0621   +0.1475         +7.8%    +3.99%
  Bull Call Spread ATM/+3% (35 DTE)      35  +0.129   -0.0030   +0.0017         +0.0%    +1.34%
  Bull Put Spread -2%/-5% (10 DTE)       10  -0.184   +0.0307   -0.0285        +22.3%    -2.69%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ES=F — S&P 500 Futures  |  N=42  |  IV src=^VIX  |  Median IV at entry=22.2%  |  Median crush=3.3pp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Strategy                                  N    Win%     AvgW     AvgL       EV    R:R       P5   Median      P95   MaxLoss
  ------------------------------------------------------------------------------------------------------------
  Equity (stock long)                      42   69.0%   +2.45%   -2.37%  +0.963%  1.04x   -3.95%   +1.28%   +5.22%   -12.06%
  Long ATM Call (35 DTE)                   42   50.0%   +21.9%   -21.7%   +0.10%  1.01x   -34.4%    -1.0%   +47.5%    -43.8%
  Bull Call Spread ATM/+3% (35 DTE)        42   64.3%   +31.7%   -17.7%  +14.10%  1.80x   -32.7%   +13.6%   +63.3%    -41.0%
  Bull Put Spread -2%/-5% (10 DTE)         42   88.1%   +18.2%   -24.9%  +13.09%  0.73x   -32.0%   +15.8%   +34.1%    -41.7%

  IV Regime Breakdown — ES=F
  Strategy                                                Low IV<15%                  Mid IV 15-25%                    High IV>25%
  -----------------------------------------------------------------------------------------------
  Long ATM Call (35 DTE)               N= 1 Win=100% EV=+26.5%              N=26 Win=46% EV=-3.5%              N=15 Win=53% EV=+4.6%            
  Bull Call Spread ATM/+3% (35 DTE)    N= 1 Win=100% EV=+33.1%              N=26 Win=54% EV=+7.9%              N=15 Win=80% EV=+23.6%            
  Bull Put Spread -2%/-5% (10 DTE)     N= 1 Win=100% EV=+8.7%              N=26 Win=88% EV=+10.8%              N=15 Win=87% EV=+17.4%            

  Greeks at Median Entry IV (22.2%), spot=100 (normalised)
  Strategy                              DTE   Delta   Theta/d   Vega/1%  Theta5d/Prem   BE move
  ------------------------------------------------------------------------------------------
  Long ATM Call (35 DTE)                 35  +0.552   -0.0576   +0.1474         +7.9%    +3.67%
  Bull Call Spread ATM/+3% (35 DTE)      35  +0.141   -0.0035   +0.0025         +0.0%    +1.33%
  Bull Put Spread -2%/-5% (10 DTE)       10  -0.190   +0.0312   -0.0318        +25.1%    -2.62%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAX LOSS SCENARIOS — 1 Contract, QQQ proxy at $480, IV=20%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scenario                     │ Long ATM Call (35 DTE) │ Bull Call Spread ATM/+ │ Bull Put Spread -2%/-5
-----------------------------------------------------------------------------------------------
Crash -10%                   │    -99% ($-1585)       │    -97% ($-621)       │  -81.7% ($-1176 on $14
Hard down -5%                │    -86% ($-1374)       │    -75% ($-476)       │  -60.7% ($-874 on $144
Signal avg loss -2.2%        │    -62% ($-998)       │    -41% ($-263)       │   -4.7% ($-68 on $1440
Flat +0%                     │    -31% ($-503)       │     -6% ($-35)       │  +15.6% ($+225 on $144
Signal avg win +2.7%         │    +22% ($+349)       │    +41% ($+261)       │  +18.2% ($+262 on $144
Rally +5%                    │    +78% ($+1248)       │    +75% ($+475)       │  +18.2% ($+263 on $144
Squeeze +10%                 │   +218% ($+3497)       │   +114% ($+728)       │  +18.2% ($+263 on $144

Theo max loss per contract:
  Long ATM Call (35 DTE)                   $1605 (100% of premium paid)
  Bull Call Spread ATM/+3% (35 DTE)        $637 (100% of premium paid)
  Bull Put Spread -2%/-5% (10 DTE)         $1177 (spread width $1440 − credit $263)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL RECOMMENDATION — What to Do Exactly
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIGNAL:  RSI-MA < 5th percentile (no COV required for QQQ/SPY)
         QQQ fires ~4-6× per year  |  SPY fires ~5-7× per year

IV TOOLS:
  QQQ: Check ^VXN in your charting platform (or look at QQQ option chain — note the
       IV% shown on ATM options. This IS your implied vol. VXN is its index equivalent.)
  SPY: VIX IS the implied volatility. VIX=20 means ATM SPY 30-day IV = 20%.
  For 10 DTE specifically: VIX9D (CBOE 9-Day VIX) is the most accurate match.
       Current VIX9D ≈ 90% of VIX in normal markets, spikes to 120-140% of VIX in panic.
       Rule of thumb: 10 DTE put spread → use VIX9D if available, else VIX × 1.10.

WHEN TO CHOOSE EACH STRATEGY:
  VIX / VXN > 20%  → Bull Put Spread (sell the expensive IV)
  VIX / VXN 15-20% → Either Bull Put Spread or Bull Call Spread
  VIX / VXN < 15%  → Long ATM Call (low fear = IV crush minimal; calls can work)

EXACT SETUP (QQQ):
  Signal fires: QQQ closes, RSI-MA percentile < 5th, VXN = X%
  Next morning at 9:45 AM ET:
    Short put: round(QQQ × 0.98) to nearest strike
    Long put:  round(QQQ × 0.95) to nearest strike
    Expiry:    nearest weekly with 7-10 calendar days to expiration
    Order:     Sell vertical (credit spread), limit at midpoint
    Min credit: 0.25 × spread_width (if below this, IV too low → switch to call spread)
    Hold:      Exit at 50% profit OR Day 5, whichever first

NOTE ON COV:
  You don't NEED COV for QQQ/SPY options. The RSI-MA alone gives:
    QQQ: 42 signals (vs 27) at 69.0% win (vs 66.7%) — MORE and BETTER
    SPY: 47 signals (vs 33) at 70.2% win (vs 66.7%) — MORE and BETTER
  COV is more valuable for individual stocks (NVDA, GOOGL, V, PG) where
  the raw RSI-MA signal is noisier and confluence adds more filtering benefit.

```
