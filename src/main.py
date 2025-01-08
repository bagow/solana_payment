import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import (
    SOLANA_RPC_URL,
    GAME_WALLETS,
    GAME_WALLET_ADDRESSES,
    COMMISSION_WALLET_ADDRESS,
    COMMISSION_PERCENTAGE
)
from .solana_client import SolanaClient

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="Solana Payment API",
    description="API для работы с платежами в сети Solana",
    version="1.0.0"
)

# Инициализация клиента Solana
solana_client = SolanaClient(SOLANA_RPC_URL)


# Модели данных для API
class TransactionRequest(BaseModel):
    from_private_key: str = Field(..., description="Приватный ключ отправителя")
    to_address: str = Field(..., description="Адрес получателя")
    amount: float = Field(..., gt=0, description="Сумма перевода в SOL")


class GameTransactionRequest(BaseModel):
    from_private_key: str = Field(..., description="Приватный ключ отправителя")
    wallet_index: int = Field(..., ge=0, lt=3, description="Индекс игрового кошелька (0-2)")
    amount: float = Field(..., gt=0, description="Сумма перевода в SOL")


class BalanceRequest(BaseModel):
    public_key: str = Field(..., description="Публичный ключ кошелька")


class GameToExternalTransactionRequest(BaseModel):
    wallet_index: int = Field(..., ge=0, lt=3, description="Индекс игрового кошелька (0-2)")
    to_address: str = Field(..., description="Адрес получателя")
    amount: float = Field(..., gt=0, description="Сумма перевода в SOL")


class UserToExternalTransactionRequest(BaseModel):
    from_private_key: str = Field(..., description="Приватный ключ отправителя")
    to_address: str = Field(..., description="Адрес получателя")
    amount: float = Field(..., gt=0, description="Сумма перевода в SOL")


# API эндпоинты
@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "healthy"}


@app.post("/create_wallet")
async def create_wallet():
    """
    Создание нового кошелька Solana
    
    Returns:
        dict: Данные созданного кошелька (public_key, private_key)
    """
    try:
        wallet = solana_client.create_wallet()
        logger.info(f"Created new wallet: {wallet['public_key']}")
        return wallet
    except Exception as e:
        logger.error(f"Error creating wallet: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_balance")
async def get_balance(request: BalanceRequest):
    """
    Получение баланса кошелька
    
    Args:
        request (BalanceRequest): Данные запроса
        
    Returns:
        dict: Баланс кошелька в SOL
    """
    result = solana_client.get_balance(request.public_key)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/send_to_game_wallet")
async def send_to_game_wallet(request: GameTransactionRequest):
    """
    Отправка SOL на игровой кошелек с комиссией
    
    Args:
        request (GameTransactionRequest): Данные запроса
        
    Returns:
        dict: Результат транзакции
    """
    if request.wallet_index not in range(len(GAME_WALLET_ADDRESSES)):
        raise HTTPException(status_code=400, detail="Invalid wallet index")

    result = solana_client.send_transaction_with_commission(
        request.from_private_key,
        GAME_WALLET_ADDRESSES[request.wallet_index],
        request.amount
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/game_wallets")
async def get_game_wallets():
    """
    Получение списка игровых кошельков
    
    Returns:
        dict: Список публичных адресов игровых кошельков
    """
    return {
        "game_wallets": [
            {
                "index": i,
                "public_key": wallet["public_key"]
            } for i, wallet in enumerate(GAME_WALLETS)
        ]
    }


@app.get("/commission_info")
async def get_commission_info():
    """
    Получение информации о комиссии
    
    Returns:
        dict: Информация о комиссии и адрес комиссионного кошелька
    """
    return {
        "commission_percentage": COMMISSION_PERCENTAGE,
        "commission_wallet": COMMISSION_WALLET_ADDRESS
    }


@app.post("/send_from_game_wallet")
async def send_from_game_wallet(request: GameToExternalTransactionRequest):
    """
    Отправка SOL с игрового кошелька на произвольный адрес

    Args:
        request (GameToExternalTransactionRequest): Данные запроса

    Returns:
        dict: Результат транзакции
    """
    if request.wallet_index not in range(len(GAME_WALLET_ADDRESSES)):
        raise HTTPException(status_code=400, detail="Invalid wallet index")

    result = solana_client.send_from_game_wallet(
        request.wallet_index,
        request.to_address,
        request.amount
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/send_from_user_wallet")
async def send_from_user_wallet(request: UserToExternalTransactionRequest):
    """
    Отправка SOL с пользовательского кошелька на произвольный адрес

    Args:
        request (UserToExternalTransactionRequest): Данные запроса

    Returns:
        dict: Результат транзакции
    """
    result = solana_client.send_from_user_wallet(
        request.from_private_key,
        request.to_address,
        request.amount
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
