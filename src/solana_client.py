from solana.rpc.api import Client
from .config import COMMISSION_WALLET_ADDRESS, COMMISSION_PERCENTAGE, GAME_WALLETS, COMMISSION_WALLET
import logging

from solders.keypair import Keypair
from solders.pubkey import Pubkey

from solders.system_program import TransferParams, transfer
from solders.message import Message
from solders.transaction import Transaction

# Настройка логирования
logger = logging.getLogger(__name__)


# TODO: remake to AsyncClient
class SolanaClient:
    def __init__(self, rpc_url):
        """
        Инициализация клиента Solana
        Args:
            rpc_url (str): URL-адрес RPC узла Solana
        """
        self.client = Client(rpc_url)
        response = self.client.is_connected()
        print(f"Connected to Solana RPC with url {rpc_url}: {response}")

    def create_wallet(self):
        """
        Создание нового кошелька Solana
        
        Returns:
            dict: Словарь с публичным и приватным ключами
        """
        try:
            keypair = Keypair()
            public_key = str(keypair.pubkey())
            # TODO: discuss w/ D. Bagow
            # private_key = b58encode(keypair.secret_key).decode('ascii')
            private_key = keypair.secret().hex()

            logger.info(f"Created new wallet: {public_key}")
            return {
                "public_key": public_key,
                "private_key": private_key
            }
        except Exception as e:
            logger.error(f"Error creating wallet: {str(e)}")
            raise

    def get_balance(self, public_key: str) -> dict:
        """
        Получение баланса кошелька
        
        Args:
            public_key (str): Публичный ключ кошелька
            
        Returns:
            dict: Результат операции с балансом или ошибкой
        """
        try:
            response = self.client.get_balance(Pubkey.from_string(public_key))
            balance = self.lamports_to_sol(response.value)  # Конвертация из lamports в SOL
            logger.info(f"Balance for {public_key}: {balance} SOL")
            return {"success": True, "balance": balance}
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_transaction_with_commission(self, from_private_key, to_address, amount):
        """
        Отправка SOL с учетом комиссии
        
        Args:
            from_private_key (str): Приватный ключ отправителя (secret in hex, not public key)
            to_address (str): Адрес получателя
            amount (float): Количество SOL для отправки
            
        Returns:
            dict: Результат транзакции
        """
        try:
            commission_amount = amount * (COMMISSION_PERCENTAGE / 100)
            main_amount = amount - commission_amount
            logger.info(f"Preparing transaction: {main_amount} SOL + {commission_amount} SOL commission")

            # We must check the balance of commission wallet for existing of "Rent-exempt minimum" before replenishing it
            # Rent-exempt minimum is 0.00089088 SOL. If it's lower, we transfer sol from game wallet to commission wallet (in our case only to comission wallet, not to main wallet to save resources)
            # this process should happen once per all time
            transaction_hash_main = None
            if self.get_balance(COMMISSION_WALLET_ADDRESS)['balance'] < self.lamports_to_sol(self.client.get_minimum_balance_for_rent_exemption(0).value):
                transaction_commission_hash = self._send_transaction(
                    from_private_key,
                    COMMISSION_WALLET_ADDRESS,
                    main_amount
                )
                logger.info(f"Commission wallet balance is empty. Transfer game's funds to commission wallet. Transaction COMMISSION successful: {transaction_commission_hash}")
            else:
                transaction_hash_main = self._send_transaction(
                    from_private_key,
                    to_address,
                    main_amount
                )
                logger.info(f"Transaction MAIN successful: {transaction_hash_main}")
                transaction_commission_hash = self._send_transaction(
                    from_private_key,
                    COMMISSION_WALLET_ADDRESS,
                    commission_amount
                )
                logger.info(f"Transaction COMMISSION successful: {transaction_commission_hash}")

            return {
                "success": True,
                "signature": transaction_hash_main,
                "signature_commission": transaction_commission_hash,
                "main_amount": main_amount,
                "commission_amount": commission_amount
            }

        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_from_game_wallet(self, game_wallet_index, to_address, amount):
        """
        Отправка SOL с игрового кошелька на произвольный адрес

        Args:
            game_wallet_index (int): Индекс игрового кошелька
            to_address (str): Адрес получателя
            amount (float): Количество SOL для отправки

        Returns:
            dict: Результат транзакции
        """
        try:
            game_wallet = GAME_WALLETS[game_wallet_index]
            transaction_hash = self._send_transaction(
                game_wallet["private_key"],
                to_address,
                amount
            )
            logger.info(f"Transaction successful: {transaction_hash}")
            return {
                "success": True,
                "signature": transaction_hash
            }

        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_from_user_wallet(self, from_private_key, to_address, amount):
        """
        Отправка SOL с пользовательского кошелька на произвольный адрес

        Args:
            from_private_key (str): Приватный ключ отправителя (secret in hex, not public key)
            to_address (str): Адрес получателя
            amount (float): Количество SOL для отправки

        Returns:
            dict: Результат транзакции
        """
        try:
            transaction_hash = self._send_transaction(
                from_private_key,
                to_address,
                amount
            )
            logger.info(f"Transaction successful: {transaction_hash}")
            return {
                "success": True,
                "signature": transaction_hash
            }
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            return {"success": False, "error": str(e)}

    def lamports_to_sol(self, lamports: int) -> float:
        return lamports / 10 ** 9

    def _send_transaction(
            self,
            sender_secret_key: str,
            receiver_address: str,
            amount: float,
    ) -> str:
        """Sends a transaction. Returns signature"""
        try:
            from_keypair = Keypair.from_seed(bytes.fromhex(sender_secret_key))
        except:
            from_keypair = Keypair.from_base58_string(sender_secret_key)
        to_address_pub_key = Pubkey.from_string(receiver_address)

        # Проверяем баланс
        balance = self.client.get_balance(from_keypair.pubkey()).value
        if balance < amount * 10 ** 9:
            raise ValueError("Insufficient funds")

        # Формируем транзакцию
        ixns = [
            transfer(
                TransferParams(
                    from_pubkey=from_keypair.pubkey(),
                    to_pubkey=to_address_pub_key,
                    lamports=int(amount * 10 ** 9)
                )
            )
        ]

        # Получаем актуальный blockhash
        latest_blockhash = self.client.get_latest_blockhash().value.blockhash
        msg = Message.new_with_blockhash(ixns, from_keypair.pubkey(), latest_blockhash)
        transaction = Transaction([from_keypair], msg, latest_blockhash)

        # Симулируем транзакцию
        simulation_result = self.client.simulate_transaction(transaction)
        if simulation_result.value.err is not None:
            raise ValueError(f"Transaction simulation failed: {simulation_result.value.err}")

        # Отправляем транзакцию
        result = self.client.send_transaction(transaction)
        return str(result.value)
