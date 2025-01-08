from solana.rpc.api import Client
from .config import COMMISSION_WALLET_ADDRESS, COMMISSION_PERCENTAGE, GAME_WALLETS
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
            balance = response.value / 10 ** 9  # Конвертация из lamports в SOL
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

            # TODO: disscuss w/ D. Bagow
            # # Создание keypair из приватного ключа
            # from_keypair = Keypair.from_secret_key(b58decode(from_private_key))
            # # Создание транзакции для основной суммы
            # transaction = Transaction().add(
            #     transfer(
            #         TransferParams(
            #             from_pubkey=from_keypair.pubkey(),
            #             to_pubkey=to_address,
            #             lamports=int(main_amount * 10 ** 9)
            #         )
            #     )
            # )
            #
            # # Добавление транзакции для комиссии
            # transaction.add(
            #     transfer(
            #         TransferParams(
            #             from_pubkey=from_keypair.pubkey(),
            #             to_pubkey=COMMISSION_WALLET_ADDRESS,
            #             lamports=int(commission_amount * 10 ** 9)
            #         )
            #     )
            # )
            # # Отправка транзакции
            # result = self.client.send_transaction(
            #     transaction,
            #     from_keypair
            # )

            transaction_hash_main = self._send_transaction(
                from_private_key,
                to_address,
                main_amount
            )
            logger.info(f"Transaction MAIN successful: {transaction_hash_main}")
            transaction_commission_hash = self._send_transaction(
                from_private_key,
                to_address,
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
            # TODO: discuss w/ D.Bagow
            # Получаем приватный ключ игрового кошелька
            # game_wallet = GAME_WALLETS[game_wallet_index]
            # from_keypair = Keypair.from_secret_key(b58decode(game_wallet["private_key"]))
            #
            # # Создание транзакции
            # transaction = Transaction().add(
            #     transfer(
            #         TransferParams(
            #             from_pubkey=from_keypair.pubkey(),
            #             to_pubkey=to_address,
            #             lamports=int(amount * 10 ** 9)
            #         )
            #     )
            # )
            #
            # # Отправка транзакции
            # result = self.client.send_transaction(
            #     transaction,
            #     from_keypair
            # )

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

    def _send_transaction(
            self,
            sender_secret_key: str,
            receiver_address: str,
            amount: float,
    ) -> str:
        """Sends a transaction. Returns signature"""
        from_keypair = Keypair.from_seed(bytes.fromhex(sender_secret_key))
        to_address_pub_key = Pubkey.from_string(receiver_address)
        ixns = [
            transfer(
                TransferParams(
                    from_pubkey=from_keypair.pubkey(), to_pubkey=to_address_pub_key, lamports=int(amount * 10 ** 9)
                )
            )
        ]
        msg = Message(ixns, from_keypair.pubkey())
        transaction = Transaction(
            [from_keypair],
            msg,
            self.client.get_latest_blockhash().value.blockhash,
        )
        # Отправка транзакции
        result = self.client.send_transaction(transaction)
        return str(result.value)
