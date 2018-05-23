PRICES_EXCL_VAT = {
    'free': {
        'ticket_price': 0,
        'day_price': 0,
    },
    'individual': {
        'ticket_price': 35,
        'day_price': 30,
    },
    'corporate': {
        'ticket_price': 75,
        'day_price': 60,
    },
    'unwaged': {
        'ticket_price': 25,
        'day_price': 15,
    },
    'educator-employer': {
        'ticket_price': 35,
        'day_price': 30,
    },
    'educator-self': {
        'ticket_price': 25,
        'day_price': 15,
    },
}

VAT_RATE = 0.2

PRICES_INCL_VAT = {}

for rate in PRICES_EXCL_VAT:
    PRICES_INCL_VAT[rate] = {}
    for price_type in ['ticket_price', 'day_price']:
        cost = PRICES_EXCL_VAT[rate][price_type] * (1 + VAT_RATE)
        assert cost == int(cost)
        PRICES_INCL_VAT[rate][price_type] = int(cost)


def cost_excl_vat(rate, num_days):
    prices = PRICES_EXCL_VAT[rate]
    return prices['ticket_price'] + prices['day_price'] * num_days


def cost_incl_vat(rate, num_days):
    prices = PRICES_INCL_VAT[rate]
    return prices['ticket_price'] + prices['day_price'] * num_days
