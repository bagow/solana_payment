from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from base58 import b58encode, b58decode
from .config import COMMISSION_WALLET_ADDRESS, COMMISSION_PERCENTAGE
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class SolanaClient:
    def __init__(self, rpc_url):
        """
        Инициализация клиента Solana
        Args:
            rpc_url (str): URL-адрес RPC узла Solana
        """
        self.client = Client(rpc_url)
        
    def create_wallet(self):
        """
        Создание нового кошелька Solana
        
        Returns:
            dict: Словарь с публичным и приватным ключами
        """
        try:
            keypair = Keypair()
            public_key = str(keypair.public_key)
            private_key = b58encode(keypair.secret_key).decode('ascii')
            
            logger.info(f"Created new wallet: {public_key}")
            return {
                "public_key": public_key,
                "private_key": private_key
            }
        except Exception as e:
            logger.error(f"Error creating wallet: {str(e)}")
            raise
    
    def get_balance(self, public_key):
        """
        Получение баланса кошелька
        
        Args:
            public_key (str): Публичный ключ кошелька
            
        Returns:
            dict: Результат операции с балансом или ошибкой
        """
        try:
            response = self.client.get_balance(public_key)
            balance = response['result']['value'] / 10**9  # Конвертация из lamports в SOL
            logger.info(f"Balance for {public_key}: {balance} SOL")
            return {"success": True, "balance": balance}
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_transaction_with_commission(self, from_private_key, to_address, amount):
        """
        Отправка SOL с учетом комиссии
        
        Args:
            from_private_key (str): Приватный ключ отправителя
            to_address (str): Адрес получателя
            amount (float): Количество SOL для отправки
            
        Returns:
            dict: Результат транзакции
        """
        try:
            # Создание keypair из приватного ключа
            from_keypair = Keypair.from_secret_key(b58decode(from_private_key))
            
            # Расчет комиссии
            commission_amount = amount * (COMMISSION_PERCENTAGE / 100)
            main_amount = amount - commission_amount
            
            logger.info(f"Preparing transaction: {main_amount} SOL + {commission_amount} SOL commission")
            
            # Создание транзакции для основной суммы
            transaction = Transaction().add(
                transfer(
                    TransferParams(
                        from_pubkey=from_keypair.public_key,
                        to_pubkey=to_address,
                        lamports=int(main_amount * 10**9)
                    )
                )
            )
            
            # Добавление транзакции для комиссии
            transaction.add(
                transfer(
                    TransferParams(
                        from_pubkey=from_keypair.public_key,
                        to_pubkey=COMMISSION_WALLET_ADDRESS,
                        lamports=int(commission_amount * 10**9)
                    )
                )
            )
            
            # Отправка транзакции
            result = self.client.send_transaction(
                transaction,
                from_keypair
            )
            
            logger.info(f"Transaction successful: {result['result']}")
            return {
                "success": True, 
                "signature": result["result"],
                "main_amount": main_amount,
                "commission_amount": commission_amount
            }
            
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            return {"success": False, "error": str(e)} 