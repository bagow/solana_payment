# Solana Payment API

API для работы с платежами в сети Solana с поддержкой игровых кошельков и комиссий.

## Особенности

- Создание новых кошельков Solana
- Проверка баланса кошельков
- Отправка SOL на игровые кошельки с автоматическим расчетом комиссии
- Отправка SOL с игровых кошельков на произвольные адреса
- Отправка SOL с пользовательских кошельков на произвольные адреса
- Три предустановленных игровых кошелька
- Комиссионный кошелек для сбора комиссий
- Docker-контейнеризация
- Автоматическое сохранение данных кошельков

## Установка и запуск


2. Настройте переменные окружения в файле `.env`:
   ```text
   SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
   WALLET_DATA_DIR=/app/data
   COMMISSION_PERCENTAGE=5
   ```

3. Запустите с помощью Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Проверьте, что сервис работает:
   ```bash
   curl http://localhost:8000/health
   ```

## API Endpoints

### 1. Проверка работоспособности сервиса

- **URL:** `/health`
- **Метод:** `GET`
- **Описание:** Проверка работоспособности сервиса.
- **Пример запроса:**
  ```bash
  curl http://localhost:8000/health
  ```
- **Пример ответа:**
  ```json
  {"status": "healthy"}
  ```

### 2. Создание нового кошелька

- **URL:** `/create_wallet`
- **Метод:** `POST`
- **Описание:** Создание нового кошелька Solana.
- **Пример запроса:**
  ```bash
  curl -X POST http://localhost:8000/create_wallet
  ```
- **Пример ответа:**
  ```json
  {
    "public_key": "string",
    "private_key": "string"
  }
  ```

### 3. Получение баланса кошелька

- **URL:** `/get_balance`
- **Метод:** `POST`
- **Описание:** Получение баланса кошелька.
- **Тело запроса:**
  ```json
  {
    "public_key": "string"
  }
  ```
- **Пример запроса:**
  ```bash
  curl -X POST http://localhost:8000/get_balance -H "Content-Type: application/json" -d '{"public_key": "your_public_key"}'
  ```
- **Пример ответа:**
  ```json
  {
    "success": true,
    "balance": float
  }
  ```

### 4. Отправка SOL на игровой кошелек

- **URL:** `/send_to_game_wallet`
- **Метод:** `POST`
- **Описание:** Отправка SOL на игровой кошелек с комиссией.
- **Тело запроса:**
  ```json
  {
    "from_private_key": "string",
    "wallet_index": int,
    "amount": float
  }
  ```
- **Пример запроса:**
  ```bash
  curl -X POST http://localhost:8000/send_to_game_wallet -H "Content-Type: application/json" -d '{"from_private_key": "your_private_key", "wallet_index": 0, "amount": 0.1}'
  ```
- **Пример ответа:**
  ```json
  {
    "success": true,
    "signature": "string",
    "main_amount": float,
    "commission_amount": float
  }
  ```

### 5. Отправка SOL с игрового кошелька

- **URL:** `/send_from_game_wallet`
- **Метод:** `POST`
- **Описание:** Отправка SOL с игрового кошелька на произвольный адрес.
- **Тело запроса:**
  ```json
  {
    "wallet_index": int,
    "to_address": "string",
    "amount": float
  }
  ```
- **Пример запроса:**
  ```bash
  curl -X POST http://localhost:8000/send_from_game_wallet -H "Content-Type: application/json" -d '{"wallet_index": 0, "to_address": "your_destination_address", "amount": 0.1}'
  ```
- **Пример ответа:**
  ```json
  {
    "success": true,
    "signature": "string"
  }
  ```

### 6. Отправка SOL с пользовательского кошелька

- **URL:** `/send_from_user_wallet`
- **Метод:** `POST`
- **Описание:** Отправка SOL с пользовательского кошелька на произвольный адрес.
- **Тело запроса:**
  ```json
  {
    "from_private_key": "string",
    "to_address": "string",
    "amount": float
  }
  ```
- **Пример запроса:**
  ```bash
  curl -X POST http://localhost:8000/send_from_user_wallet -H "Content-Type: application/json" -d '{"from_private_key": "your_private_key", "to_address": "your_destination_address", "amount": 0.1}'
  ```
- **Пример ответа:**
  ```json
  {
    "success": true,
    "signature": "string"
  }
  ```

### 7. Получение списка игровых кошельков

- **URL:** `/game_wallets`
- **Метод:** `GET`
- **Описание:** Получение списка игровых кошельков.
- **Пример запроса:**
  ```bash
  curl http://localhost:8000/game_wallets
  ```
- **Пример ответа:**
  ```json
  {
    "game_wallets": [
      {
        "index": 0,
        "public_key": "string"
      },
      {
        "index": 1,
        "public_key": "string"
      },
      {
        "index": 2,
        "public_key": "string"
      }
    ]
  }
  ```

### 8. Получение информации о комиссии

- **URL:** `/commission_info`
- **Метод:** `GET`
- **Описание:** Получение информации о комиссии.
- **Пример запроса:**
  ```bash
  curl http://localhost:8000/commission_info
  ```
- **Пример ответа:**
  ```json
  {
    "commission_percentage": float,
    "commission_wallet": "string"
  }
  ```
