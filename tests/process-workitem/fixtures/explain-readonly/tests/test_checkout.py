from src.checkout import order_total


def test_total_without_discount():
    assert order_total([{"qty": 2, "unit_price": 5.0}]) == 10.0
