from main import calculate_cart_total

def test_cart_total():
    items = [{"price": 10, "quantity": 2}]
    assert calculate_cart_total(items) == 20
