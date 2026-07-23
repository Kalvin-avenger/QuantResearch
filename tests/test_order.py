from quantresearch.orders import Order
from quantresearch.signals import Signal


def test_order_creation():

    order = Order(
        action=Signal.BUY,
        quantity=100,
    )

    assert order.action == Signal.BUY
    assert order.quantity == 100
    assert order.price is None