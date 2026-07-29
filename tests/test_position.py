import pytest

from quantresearch.accounting.position import Position


def test_empty_position():

    position = Position()

    assert position.quantity == 0
    assert position.avg_price == 0

def test_buy_updates_position():

    position = Position()

    position.buy(
        quantity=100,
        price=100,
    )

    assert position.quantity == 100

    assert position.avg_price == 100

def test_multiple_buys_update_average_price():

    position = Position()

    position.buy(
        quantity=100,
        price=100,
    )

    position.buy(
        quantity=100,
        price=120,
    )

    assert position.quantity == 200

    assert position.avg_price == 110    

def test_sell_reduces_position():

    position = Position()

    position.buy(
        quantity=100,
        price=100,
    )

    pnl = position.sell(
        quantity=40,
        price=120,
    )

    assert pnl == 800

    assert position.quantity == 60

    assert position.avg_price == 100


def test_sell_all_position():

    position = Position()

    position.buy(
        quantity=100,
        price=100,
    )

    pnl = position.sell(
        quantity=100,
        price=120,
    )

    assert pnl == 2000

    assert position.quantity == 0

    assert position.avg_price == 0

def test_buy_negative_quantity():

    position = Position()

    with pytest.raises(ValueError):
        position.buy(
            quantity=-1,
            price=100,
        )


def test_buy_invalid_price():

    position = Position()

    with pytest.raises(ValueError):
        position.buy(
            quantity=10,
            price=0,
        )

def test_sell_more_than_position():

    position = Position()

    position.buy(
        quantity=100,
        price=100,
    )

    with pytest.raises(ValueError):
        position.sell(
            quantity=101,
            price=120,
        )

def test_sell_negative_quantity():

    position = Position()

    position.buy(
        quantity=100,
        price=100,
    )

    with pytest.raises(ValueError):
        position.sell(
            quantity=-1,
            price=120,
        )

def test_sell_invalid_price():

    position = Position()

    position.buy(
        quantity=100,
        price=100,
    )

    with pytest.raises(ValueError):
        position.sell(
            quantity=10,
            price=0,
        )


