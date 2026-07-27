from quantresearch.signals import Signal


def test_signal_enum():

    assert Signal.SELL.value == -1
    assert Signal.HOLD.value == 0
    assert Signal.BUY.value == 1
    assert Signal.NONE.value == 99

    assert hasattr(Signal, "BUY")
    assert hasattr(Signal, "SELL")
    assert hasattr(Signal, "HOLD")