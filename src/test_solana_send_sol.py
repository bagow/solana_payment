from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import transfer, TransferParams
from solana.keypair import Keypair
from base58 import b58encode, b58decode

# Инициализация клиента
client = Client("https://api.devnet.solana.com")

# Пример ключей
from_keypair = Keypair.from_secret_key(b58decode('2wDDTEN2zKXw3wS3V2jPuooSoNKLHLkAs1a997nwSHoC'))  # Замените на ваш секретный ключ
to_address = "2wDDTEN2zKXw3wS3V2jPuooSoNKLHLkAs1a997nwSHoC"  # Замените на адрес получателя
amount = 0.01  # Пример суммы в SOL

try:
    # Создание транзакции
    transaction = Transaction().add(
        transfer(
            TransferParams(
                from_pubkey=from_keypair.pubkey(),
                to_pubkey=to_address,
                lamports=int(amount * 10**9)
            )
        )
    )

    # Подпись транзакции
    transaction.sign(from_keypair)

    # Отправка транзакции
    response = client.send_transaction(transaction, from_keypair)
    print(f"Full transaction response: {response}")

    # Проверка на наличие ошибок
    if 'error' in response:
        print(f"Transaction error: {response['error']}")

except Exception as e:
    print(f"Error sending transaction: {e}")
