from quantresearch.strategy import BaseStrategy


def test_strategy_base():

    strategy = BaseStrategy()

    try:
        strategy.generate([])

    except NotImplementedError:
        pass

    else:
        assert False