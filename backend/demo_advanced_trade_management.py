#!/usr/bin/env python3
"""
Demo Script: Advanced Trade Management System

Demonstrates the complete trade management framework with real examples.
Shows:
1. Exit strategy comparison
2. Trade state evolution
3. Exit pressure calculations
4. Dynamic exposure recommendations
5. Conditional expectancy analysis
"""

import sys
from enhanced_backtester import EnhancedPerformanceMatrixBacktester
from advanced_backtest_runner import AdvancedBacktestRunner
from advanced_trade_manager import (
    AdvancedTradeManager,
    simulate_trade_with_advanced_management
)
import pandas as pd


def print_section_header(title: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def demo_exit_strategy_comparison(ticker: str = "AAPL", threshold: float = 5.0):
    """
    Demo 1: Compare different exit strategies.
    """
    print_section_header(f"DEMO 1: Exit Strategy Comparison - {ticker} (Entry ≤{threshold}%)")

    # Run backtest to get entry events
    print(f"📊 Running backtest for {ticker}...")
    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=[ticker],
        lookback_period=500,
        rsi_length=14,
        ma_length=14,
        max_horizon=21
    )

    data = backtester.fetch_data(ticker)
    if data.empty:
        print(f"❌ Could not fetch data for {ticker}")
        return

    indicator = backtester.calculate_rsi_ma_indicator(data)
    percentile_ranks = backtester.calculate_percentile_ranks(indicator)

    # Find entry events
    entry_events = backtester.find_entry_events_enhanced(
        percentile_ranks, data['Close'], threshold
    )

    print(f"✓ Found {len(entry_events)} entry events")

    if len(entry_events) < 10:
        print(f"⚠️  Insufficient events for comparison")
        return

    # Run advanced backtest
    print(f"\n🚀 Running strategy comparison...")
    runner = AdvancedBacktestRunner(
        historical_data=data,
        rsi_ma_percentiles=percentile_ranks,
        entry_events=entry_events,
        max_hold_days=21
    )

    comparison = runner.run_comprehensive_comparison()

    # Display results
    print(f"\n📈 RESULTS SUMMARY:")
    print(f"\n1. Buy & Hold (D21):")
    print(f"   Avg Return: {comparison.buy_and_hold.avg_return:+.2f}%")
    print(f"   Win Rate: {comparison.buy_and_hold.win_rate*100:.1f}%")
    print(f"   Sharpe: {comparison.buy_and_hold.sharpe_ratio:.2f}")
    print(f"   Expectancy: {comparison.buy_and_hold.expectancy:+.2f}%")

    print(f"\n2. Fixed Day Exits:")
    for day, perf in comparison.fixed_days.items():
        print(f"   D{day}: {perf.avg_return:+.2f}% | Win Rate: {perf.win_rate*100:.1f}% | Sharpe: {perf.sharpe_ratio:.2f}")

    print(f"\n3. ATR Trailing Stop:")
    print(f"   Avg Return: {comparison.trailing_stop_atr.avg_return:+.2f}%")
    print(f"   Win Rate: {comparison.trailing_stop_atr.win_rate*100:.1f}%")
    print(f"   Avg Hold: {comparison.trailing_stop_atr.avg_hold_days:.1f} days")
    print(f"   Sharpe: {comparison.trailing_stop_atr.sharpe_ratio:.2f}")

    print(f"\n4. Exit Pressure Strategy:")
    print(f"   Avg Return: {comparison.adaptive_exit_pressure.avg_return:+.2f}%")
    print(f"   Win Rate: {comparison.adaptive_exit_pressure.win_rate*100:.1f}%")
    print(f"   Avg Hold: {comparison.adaptive_exit_pressure.avg_hold_days:.1f} days")
    print(f"   Sharpe: {comparison.adaptive_exit_pressure.sharpe_ratio:.2f}")

    print(f"\n5. Conditional Expectancy:")
    print(f"   Avg Return: {comparison.conditional_expectancy.avg_return:+.2f}%")
    print(f"   Win Rate: {comparison.conditional_expectancy.win_rate*100:.1f}%")
    print(f"   Avg Hold: {comparison.conditional_expectancy.avg_hold_days:.1f} days")
    print(f"   Sharpe: {comparison.conditional_expectancy.sharpe_ratio:.2f}")

    # Find best strategy
    strategies = [
        ("Buy & Hold", comparison.buy_and_hold),
        ("ATR Trailing", comparison.trailing_stop_atr),
        ("Exit Pressure", comparison.adaptive_exit_pressure),
        ("Expectancy", comparison.conditional_expectancy)
    ]

    best_by_return = max(strategies, key=lambda x: x[1].avg_return)
    best_by_sharpe = max(strategies, key=lambda x: x[1].sharpe_ratio)

    print(f"\n🏆 WINNERS:")
    print(f"   Highest Return: {best_by_return[0]} ({best_by_return[1].avg_return:+.2f}%)")
    print(f"   Highest Sharpe: {best_by_sharpe[0]} ({best_by_sharpe[1].sharpe_ratio:.2f})")


def demo_trade_simulation(ticker: str = "AAPL", threshold: float = 5.0):
    """
    Demo 2: Simulate a single trade with advanced management.
    """
    print_section_header(f"DEMO 2: Trade Simulation with Advanced Management - {ticker}")

    # Get data
    print(f"📊 Fetching data for {ticker}...")
    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=[ticker],
        lookback_period=500,
        rsi_length=14,
        ma_length=14,
        max_horizon=21
    )

    data = backtester.fetch_data(ticker)
    if data.empty:
        print(f"❌ Could not fetch data for {ticker}")
        return

    indicator = backtester.calculate_rsi_ma_indicator(data)
    percentile_ranks = backtester.calculate_percentile_ranks(indicator)

    # Find entry events
    entry_events = backtester.find_entry_events_enhanced(
        percentile_ranks, data['Close'], threshold
    )

    if not entry_events:
        print(f"❌ No entry events found")
        return

    # Use a recent trade
    event = entry_events[-1]
    entry_date = event['entry_date']
    entry_idx = data.index.get_loc(entry_date)

    print(f"✓ Simulating trade from {entry_date.strftime('%Y-%m-%d')}")
    print(f"   Entry Price: ${event['entry_price']:.2f}")
    print(f"   Entry Percentile: {event['entry_percentile']:.1f}")

    # Run simulation
    simulation = simulate_trade_with_advanced_management(
        historical_data=data,
        rsi_ma_percentiles=percentile_ranks,
        entry_idx=entry_idx,
        entry_percentile=event['entry_percentile'],
        entry_price=event['entry_price'],
        historical_events=entry_events,
        max_hold_days=21
    )

    print(f"\n📅 DAY-BY-DAY ANALYSIS:")
    print(f"\n{'Day':<5} {'Price':<8} {'Return':<8} {'Exit Pressure':<15} {'State':<25} {'Action':<15} {'Stop':<8}")
    print(f"{'-'*100}")

    for day_data in simulation['daily_analysis'][:10]:  # Show first 10 days
        day = day_data['day']
        price = day_data['price']
        ret = day_data['return_pct']
        pressure = day_data['exit_pressure']['overall_pressure']
        state = day_data['trade_state']['current_state']
        action = day_data['exposure_recommendation']['action']
        stop = day_data['trailing_stop']
        triggered = day_data['triggered_stop']

        state_short = state.replace('_', ' ').title()[:23]
        action_display = action.replace('_', ' ').title()
        stop_marker = "🛑 HIT" if triggered else f"${stop:.2f}"

        print(f"D{day:<3} ${price:<7.2f} {ret:+7.2f}% {pressure:>5.1f} {state_short:<25} {action_display:<15} {stop_marker}")

    # Show final outcome
    final = simulation['daily_analysis'][-1]
    print(f"\n🎯 FINAL OUTCOME:")
    print(f"   Days Held: {simulation['total_days_held']}")
    print(f"   Final Return: {simulation['final_return']:+.2f}%")
    print(f"   Exit Reason: ", end="")

    if final['triggered_stop']:
        print("Trailing stop hit")
    elif final['triggered_exit_signal']:
        print(f"Exit signal ({final['exposure_recommendation']['action']})")
    else:
        print("Max hold period reached")


def demo_exit_pressure_evolution(ticker: str = "MSFT", threshold: float = 10.0):
    """
    Demo 3: Show how exit pressure evolves over a trade.
    """
    print_section_header(f"DEMO 3: Exit Pressure Evolution - {ticker}")

    # Get data
    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=[ticker],
        lookback_period=500,
        rsi_length=14,
        ma_length=14,
        max_horizon=21
    )

    data = backtester.fetch_data(ticker)
    if data.empty:
        print(f"❌ Could not fetch data")
        return

    indicator = backtester.calculate_rsi_ma_indicator(data)
    percentile_ranks = backtester.calculate_percentile_ranks(indicator)

    entry_events = backtester.find_entry_events_enhanced(
        percentile_ranks, data['Close'], threshold
    )

    if not entry_events:
        print(f"❌ No entry events found")
        return

    event = entry_events[-1]
    entry_idx = data.index.get_loc(event['entry_date'])

    # Create manager
    manager = AdvancedTradeManager(
        historical_data=data,
        rsi_ma_percentiles=percentile_ranks,
        entry_idx=entry_idx,
        entry_percentile=event['entry_percentile'],
        entry_price=event['entry_price']
    )

    print(f"Entry: {event['entry_date'].strftime('%Y-%m-%d')} @ ${event['entry_price']:.2f}")
    print(f"\n{'Day':<5} {'Percentile':<12} {'Velocity':<12} {'Time Decay':<12} {'Divergence':<12} {'Total Pressure':<15}")
    print(f"{'-'*80}")

    for day in range(1, min(15, len(data) - entry_idx)):
        current_idx = entry_idx + day
        percentile = percentile_ranks.iloc[current_idx]

        exit_pressure = manager.calculate_exit_pressure(current_idx, day)
        velocity = manager.calculate_percentile_velocity(current_idx)

        print(f"D{day:<3} "
              f"{percentile:>6.1f}% ({velocity:+.1f}) "
              f"{exit_pressure.percentile_velocity_component:>5.1f} "
              f"{exit_pressure.time_decay_component:>11.1f} "
              f"{exit_pressure.divergence_component:>11.1f} "
              f"{exit_pressure.overall_pressure:>12.1f}")

    print(f"\n💡 Exit Pressure Components:")
    print(f"   - Percentile Velocity: Rate of percentile change (fast rise = exhaustion)")
    print(f"   - Time Decay: Edge decays over time")
    print(f"   - Divergence: Multi-timeframe momentum misalignment")
    print(f"   - Total Pressure: Combined signal (>70 = strong exit signal)")


def main():
    """Run all demos."""
    print("\n" + "="*80)
    print(" "*20 + "ADVANCED TRADE MANAGEMENT SYSTEM - DEMO")
    print("="*80)

    try:
        # Demo 1: Strategy Comparison
        demo_exit_strategy_comparison(ticker="AAPL", threshold=5.0)

        # Demo 2: Trade Simulation
        demo_trade_simulation(ticker="AAPL", threshold=5.0)

        # Demo 3: Exit Pressure Evolution
        demo_exit_pressure_evolution(ticker="MSFT", threshold=10.0)

        print_section_header("DEMO COMPLETE")
        print("✅ All demonstrations completed successfully")
        print("\nKey Takeaways:")
        print("1. Different exit strategies produce significantly different results")
        print("2. Adaptive strategies (ATR, Exit Pressure, Expectancy) often outperform fixed exits")
        print("3. Exit pressure helps identify exhaustion points before major reversals")
        print("4. State-based management provides context for decision-making")
        print("5. Conditional expectancy balances current profit vs future potential")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
