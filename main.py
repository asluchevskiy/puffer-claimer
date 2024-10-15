import requests
from web3 import Web3
import json
import time
import random

w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth"))

def load_wallets(file_path):
    wallets = []
    private_keys = []
    with open(file_path, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("0x") and len(line) == 42:
                # Wallets
                wallets.append(line)
            else:
                # Private keys
                private_keys.append(line)
                wallets.append(Web3.to_checksum_address(w3.eth.account.from_key(line).address))
    return wallets, private_keys

# Proxies
def load_proxies(file_path):
    try:
        with open(file_path, 'r') as f:
            proxies_list = [line.strip() for line in f.readlines()]
        return proxies_list
    except FileNotFoundError:
        print("Файл с прокси не найден, продолжим без прокси.")
        return None

# ABI
def load_contract_abi(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Mode
def choose_mode():
    print("Выберите режим:")
    print("1. Чекер")
    print("2. Клеймер")
    choice = input("Введите 1 или 2: ")
    return choice

# Proxy
def choose_proxy():
    print("Использовать прокси?")
    print("1. Да")
    print("2. Нет")
    choice = input("Введите 1 или 2: ")
    return choice == "1"

# Output
def write_checker_output(wallet_address, total_claim_amount, file_path="checker_output.txt"):
    formatted_amount = total_claim_amount / (10 ** 18)  # Преобразование в удобочитаемый формат
    with open(file_path, 'a') as f:
        f.write(f"{wallet_address}: {formatted_amount} токенов\n")
    print(f"Результаты чекера для {wallet_address} сохранены в {file_path}")

# Tx link
def get_tx_link(tx_hash):
    return f"https://etherscan.io/tx/0x{tx_hash}"

# Delay
def choose_delay_range():
    try:
        delay_min = float(input("Введите минимальную задержку в секундах: "))
        delay_max = float(input("Введите максимальную задержку в секундах: "))
        if delay_min > delay_max:
            raise ValueError
    except ValueError:
        print("Некорректный ввод, устанавливаю диапазон по умолчанию (от 10 до 30 секунд).")
        delay_min, delay_max = 10.0, 30.0
    return delay_min, delay_max

# Load
wallets, private_keys = load_wallets('wallets.txt')
proxies_list = load_proxies('proxies.txt')
abi = load_contract_abi('contract_abi.json')

# campaignId
campaign_id = "0x5614e2600ab1450f86b97d326f086872"

# Contract
contract_address = Web3.to_checksum_address("0x5ae97e4770b7034c7ca99ab7edc26a18a23cb412")

# API URL
def get_api_url(wallet_address):
    return f"https://api.hedgey.finance/token-claims/{wallet_address}"

# Use proxies
use_proxies = choose_proxy()
if use_proxies and proxies_list:
    proxies = {
        'http': proxies_list[0], 
        'https': proxies_list[0]
    }
else:
    proxies = None

# Mode
mode = choose_mode()

# Delay
delay_min, delay_max = choose_delay_range()

combined = list(zip(wallets, private_keys))
random.shuffle(combined)
wallets, private_keys = zip(*combined)

for i, wallet_address in enumerate(wallets):
    # Get api
    api_url = get_api_url(wallet_address)
    
    try:
        if proxies:
            response = requests.get(api_url, proxies=proxies)
        else:
            response = requests.get(api_url)  

    except requests.exceptions.ConnectionError as e:
        print(f"Ошибка подключения через прокси: {e}. Повторяю запрос без прокси...")
        # Response
        response = requests.get(api_url)

    # API
    if response.status_code == 200:
        claims = response.json()

        if mode == "1":
            # Total
            total_claim_amount = sum(int(claim['amount']) for claim in claims)

            # Checker
            write_checker_output(wallet_address, total_claim_amount)

        elif mode == "2":
            # Proof
            for claim in claims:
                total_claim_amount = int(claim['amount'])  
                proof = claim['proof']  # Merkle proof

                # Contract
                contract = w3.eth.contract(address=contract_address, abi=abi)

                try:
                    # Gas Limit
                    estimated_gas_limit = contract.functions.claim(
                        Web3.to_bytes(hexstr=campaign_id),  
                        proof,  # Merkle proof bytes32[]
                        total_claim_amount  
                    ).estimate_gas({
                        'from': wallet_address
                    })
                except Exception as e:
                    continue

                # Base Fee EIP-1559
                latest_block = w3.eth.get_block('latest')
                base_fee = latest_block['baseFeePerGas']
                
                # Max Priority Fee
                max_priority_fee_per_gas = w3.to_wei(2, 'gwei')

                # Max fee
                max_fee_per_gas = base_fee + max_priority_fee_per_gas

                # Nonce
                nonce = w3.eth.get_transaction_count(wallet_address)

                # Claim (EIP-1559)
                tx = contract.functions.claim(
                    Web3.to_bytes(hexstr=campaign_id),  
                    proof,  # Merkle proof как bytes32[]
                    total_claim_amount  
                ).build_transaction({
                    'from': wallet_address,
                    'nonce': nonce,  
                    'gas': estimated_gas_limit,  
                    'maxFeePerGas': max_fee_per_gas,  
                    'maxPriorityFeePerGas': max_priority_fee_per_gas  
                })

                # Send
                private_key = private_keys[i]  
                signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

                # Tx link
                tx_link = get_tx_link(tx_hash.hex())
                print(f"Транзакция отправлена для кошелька {wallet_address}: {tx_link}")

                # Delay
                delay = random.uniform(delay_min, delay_max)
                print(f"Ожидание {delay:.2f} секунд перед следующим клеймом...")
                time.sleep(delay)

    else:
        print(f"Ошибка при получении данных с API для кошелька {wallet_address}: {response.status_code}")
