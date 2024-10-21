import asyncio
import functools
import os
import random
import sys

from web3 import Web3


def get_value(balance, amount_percent, amount):
    _max_value = balance
    if not amount_percent:
        value = random.randint(min(amount[0], _max_value), min(amount[1], _max_value))
    else:
        if amount_percent[0] == amount_percent[1] == 100:
            return balance
        value = random.randint(
            int(_max_value * amount_percent[0] / 100),
            min(int(_max_value * amount_percent[1] / 100), _max_value)
        )
    return value


def load_lines(filename: str) -> list:
    """
    :param filename: file path
    :return: list of all string except commented with # symbol
    """
    with open(filename) as f:
        return [row.strip() for row in f if row.strip() and not row.startswith('#')]


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller
    :param relative_path: resource relative path
    :return: resource full path
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception as ex:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def random_float(a: float, b: float, diff: int = 1) -> float:
    """
    Generates a random floating-point number in the range from a to b with the specified difference in decimal places
    :param a: min float value
    :param b: max float value
    :param diff: The difference in decimal places
    :return: float random value
    """
    random_number = random.uniform(a, b)
    try:
        precision_a = len(str(a).split('.')[1])
    except IndexError:
        precision_a = 0
    try:
        precision_b = len(str(b).split('.')[1])
    except IndexError:
        precision_b = 0
    precision = max(precision_a, precision_b)
    return round(random_number, precision + diff)


def get_explorer_address_url(address, base_explorer_url):
    base_explorer_url = base_explorer_url.strip('/')
    return f'{base_explorer_url}/address/{address}'


def get_explorer_tx_url(tx_hash, base_explorer_url):
    base_explorer_url = base_explorer_url.strip('/')
    return f'{base_explorer_url}/tx/{Web3.to_hex(tx_hash)}'


def force_sync(fn):
    """
    force async function to be sync
    :param fn: callable
    :return: callable result
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        res = fn(*args, **kwargs)
        if asyncio.iscoroutine(res):
            return asyncio.run(res)
        return res

    return wrapper
