import pytest

from quantresearch.execution.slippage import FixedSlippageModel


def test_fixed_slippage_buy():
    model = FixedSlippageModel(slippage=0.01)

    execution_price = model.apply(
        price=100,
        side="BUY"
    )

    assert execution_price == pytest.approx(101.0)

def test_fixed_slippage_sell():
    model = FixedSlippageModel(slippage=0.01)

    execution_price = model.apply(
        price=100,
        side="SELL"
    )

    assert execution_price == pytest.approx(99.0)

def test_zero_slippage():
    model = FixedSlippageModel(slippage=0.0)

    assert model.apply(100, "BUY") == 100
    assert model.apply(100, "SELL") == 100

def test_invalid_side():
    model = FixedSlippageModel(slippage=0.01)

    with pytest.raises(ValueError):
        model.apply(price=100, side="HOLD")

def test_case_insensitive_side():
    model = FixedSlippageModel(slippage=0.01)

    assert model.apply(100, "buy") == pytest.approx(101)
    assert model.apply(100, "Sell") == pytest.approx(99)

def test_negative_slippage():
    with pytest.raises(ValueError):
        FixedSlippageModel(slippage=-0.01)