# 1. Function Definition (NO spaces around =)
def calculate_price(price, tax_rate=0.05):
    # 2. Variable Assignment (YES spaces around =)
    tax = price * tax_rate
    total = price + tax

    # 3. Function Call (NO spaces around =)
    return send_receipt(amount=total)