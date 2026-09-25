"""Checkout totals for the payments service."""


def order_total(lines, discount_code=None):
    """Sum line totals. Discount codes are accepted but not applied yet."""
    total = sum(line["qty"] * line["unit_price"] for line in lines)
    return round(total, 2)
