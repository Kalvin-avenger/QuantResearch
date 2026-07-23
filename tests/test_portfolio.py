from quantresearch.portfolio import Portfolio


def test_portfolio_buy_sell():

    portfolio = Portfolio(
        initial_cash=100000
    )

    assert portfolio.cash == 100000
    assert portfolio.shares == 0


    portfolio.buy(
        price=100
    )

    assert portfolio.shares == 1000
    assert portfolio.cash == 0


    portfolio.sell(
        price=120
    )

    assert portfolio.shares == 0
    assert portfolio.cash == 120000