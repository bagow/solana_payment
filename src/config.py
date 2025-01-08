# from solana.keypair import Keypair
from solders.keypair import Keypair
from base58 import b58encode
from dotenv import load_dotenv
import os
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Основные конфигурационные параметры
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
WALLET_DATA_DIR = os.getenv("WALLET_DATA_DIR", "/app/data")
WALLET_FILE_PATH = os.path.join(WALLET_DATA_DIR, "game_wallets.json")
COMMISSION_PERCENTAGE = float(os.getenv("COMMISSION_PERCENTAGE", "5"))

def generate_wallets():
    """
    Генерация или загрузка игровых кошельков и комиссионного кошелька
    
    Returns:
        dict: Словарь с игровыми кошельками и комиссионным кошельком
        {
            "game_wallets": [...],
            "commission_wallet": {...}
        }
    """
    wallets = {
        "game_wallets": [],
        "commission_wallet": None
    }
    
    try:
        # Проверяем существование файла с кошельками
        if os.path.exists(WALLET_FILE_PATH):
            logger.info("Loading existing wallets from file")
            with open(WALLET_FILE_PATH, 'r') as f:
                return json.load(f)
        
        logger.info("Generating new wallets")
        
        # Генерируем три игровых кошелька
        for i in range(3):
            keypair = Keypair()
            wallet = {
                "public_key": str(keypair.pubkey()),
                "private_key": b58encode(keypair.secret_key).decode('ascii')
            }
            wallets["game_wallets"].append(wallet)
            logger.info(f"Generated game wallet {i+1}: {wallet['public_key']}")
        
        # Генерируем комиссионный кошелек
        commission_keypair = Keypair()
        wallets["commission_wallet"] = {
            "public_key": str(commission_keypair.pubkey()),
            "private_key": b58encode(commission_keypair.secret_key).decode('ascii')
        }
        logger.info(f"Generated commission wallet: {wallets['commission_wallet']['public_key']}")
        
        # Создаем директорию для данных, если она не существует
        os.makedirs(os.path.dirname(WALLET_FILE_PATH), exist_ok=True)
        
        # Сохраняем кошельки в файл
        with open(WALLET_FILE_PATH, 'w') as f:
            json.dump(wallets, f, indent=2)
        logger.info("Wallets saved to file successfully")
        
        return wallets
        
    except Exception as e:
        logger.error(f"Error generating wallets: {str(e)}")
        raise

# Инициализация кошельков
WALLETS = generate_wallets()
GAME_WALLETS = WALLETS["game_wallets"]
COMMISSION_WALLET = WALLETS["commission_wallet"]
GAME_WALLET_ADDRESSES = [wallet["public_key"] for wallet in GAME_WALLETS]
COMMISSION_WALLET_ADDRESS = COMMISSION_WALLET["public_key"] 
