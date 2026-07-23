from quantresearch.backtest import BacktestEngine
from quantresearch.signals import Signal


def test_backtest_engine_basic():


    prices = [
        100,
        120,
    ]


    signals = [
        Signal.BUY,
        Signal.SELL,
    ]


    engine = BacktestEngine(
        prices=prices,
        signals=signals,
        initial_cash=100000,
    )


    result = engine.run()


    assert result.equity_curve[-1] == 120000