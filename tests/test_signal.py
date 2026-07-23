from quantresearch.signals import Signal


def test_signal_enum():

    assert Signal.BUY.value == 2
    assert Signal.SELL.value == 3
    assert Signal.HOLD.value == 1
    assert Signal.NONE.value == 0