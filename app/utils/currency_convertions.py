from enum import Enum

from app.schemas.money import Money


class Currencies(int, Enum):
    platinum = 1000
    gold = 100
    electrum = 50
    silver = 10
    copper = 1


values = {currency.name: currency.value for currency in Currencies}
currency_types = [currency.name for currency in Currencies]


def convert_to_copper(money: Money):
    money_dict = money.model_dump()
    total_copper = sum([values[k] * money_dict[k] for k in values])
    return total_copper


def convert_to_simplified(copper: int) -> dict:
    converted = {"platinum": 0, "gold": 0, "electrum": 0, "silver": 0, "copper": 0}
    for k in values:
        converted[k] = copper // values[k]
        copper -= converted[k] * values[k]

    return converted


def converto_to_type(copper: int, curr_type: str) -> dict:
    total_curr_type = copper // values[curr_type]
    reminder_copper = copper - total_curr_type * values[curr_type]

    converted = convert_to_simplified(reminder_copper)
    converted[curr_type] += total_curr_type

    return converted
