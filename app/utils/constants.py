from enum import Enum


# Currency Values
class Currencies(int, Enum):
    platinum = 1000
    gold = 100
    electrum = 50
    silver = 10
    copper = 1


values = {currency.name: currency.value for currency in Currencies}
currency_types = [currency.name for currency in Currencies]
