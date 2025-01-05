import os
import requests
import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import backtrader

load_dotenv() 

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
CHAT_ID_TELEGRAM = os.getenv("CHAT_ID_TELEGRAM")


# - Conexão com a API do Telegram, usando Token e ID do meu bot
def enviar_mensagem_telegram(token, chat_id, mensagem):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  
        return response.json()  
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")
        return {"ok": False, "error": str(e)}
    

# - Capturar o preço da cripto via API (Binance)
def capturar_preco_binance(symbol="BTCUSDT", interval="1m", limit=15):
    
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição à Binance: {e}")
        return None
    

# - Informa o preço em M1 no segundo 00:00:58    
def precos_zerosegundo(symbol="BTCUSDT", interval="1m"):   
    while True:
        # Horário atual
        current_time = datetime.now()
        
        # Verificamos se estamos no segundo 58 (Candle fecha perto do segundo 58/59)
        if current_time.second == 58:
            time.sleep(2)  # Aguarda até o fechamento do candle
            result = capturar_preco_binance(symbol=symbol, interval=interval)
            if result:
                kline = result[-2]  # Usa o penúltimo candle (último fechado)
                price = float(kline[4])  # Preço de fechamento
                timestamp = int(kline[0])  # Timestamp em ms
                readable_time = datetime.fromtimestamp(timestamp / 1000)
                print(f"\nPreço em M1: {price}")
                return {"price": price, "timestamp": readable_time}
            else:
                print("Erro ao capturar o preço!")
        
        # Espera por 1 segundo antes de tentar novamente
        time.sleep(1)


# - Lista dos tipos de candle
def identificar_candle(candle, prev_candle=None):

    # Definir as variáveis do candle
    open_price = candle["open"]
    close_price = candle["close"]
    high_price = candle["high"]
    low_price = candle["low"]

    # Calcular o tamanho do corpo e das sombras
    body = abs(close_price - open_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    # Identificar tipos de candles
    if body <= 0.1 * (high_price - low_price):  # Se o corpo é pequeno comparado com a altura total
        if upper_shadow >= 2 * body and lower_shadow >= 2 * body:
            return "Doji"
        elif upper_shadow >= 2 * body:
            return "Inverted Hammer"
        elif lower_shadow >= 2 * body:
            return "Hammer"
    
    if close_price > open_price and body > 0.5 * (high_price - low_price):
        return "Bullish Engulfing"
    
    if open_price > close_price and body > 0.5 * (high_price - low_price):
        return "Bearish Engulfing"

    return "Desconhecido"


# - Captura o candle em M1 e classifica-o
def capturar_identificar_candle(symbol="BTCUSDT", interval="1m"):
    data = capturar_preco_binance(symbol=symbol, interval=interval, limit=1)
    if data:
        candle = data[-1]
        ohlc_current = {
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4])
        }
        return identificar_candle(ohlc_current)  # Retorna apenas o tipo do candle
    return None


# - Calcular suporte e resistencia (Utilizado no TP/SL)
def calcular_suporte_resistencia(symbol="BTCUSDT", interval="1m", limit=15):

    dados = capturar_preco_binance(symbol, interval, limit)

    if not dados:
        print("Erro ao obter dados da API. Não foi possível calcular suporte e resistência.")
        return None, None

    # Extraindo valores de alta (high) e baixa (low) dos candles
    try:
        valores_high = [float(candle[2]) for candle in dados]
        valores_low = [float(candle[3]) for candle in dados]

        # Calculando suporte e resistência
        suporte = min(valores_low)
        resistencia = max(valores_high)

        return suporte, resistencia

    except (IndexError, ValueError) as e:
        print(f"Erro ao processar dados da API: {e}")
        return None, None
    

# - Cálculo EMA
def calcular_ema7(prices, period):
    # Calculando a EMA com maior precisão
    k = 2 / (period + 1)
    
    # Usando o valor inicial da EMA como o primeiro preço (ou a média dos primeiros preços)
    ema = [np.mean(prices[:period])]  # Primeira EMA é a média dos primeiros 'period' preços

    # Calculando os valores subsequentes da EMA
    for price in prices[period:]:
        # Fórmula da EMA: EMA = (Preço atual - EMA anterior) * k + EMA anterior
        ema.append((price - ema[-1]) * k + ema[-1])

    return ema[-1]  # Retorna o último valor da EMA (mais recente)


# - Cálculo EMA50
def calcular_ema50(prices, period):
    # Período da EMA50
    period = 50
    
    # Calculando o multiplicador
    k = 2 / (period + 1)
    
    # Usando o valor inicial da EMA como a média dos primeiros 'period' preços
    ema = [np.mean(prices[:period])]  # Primeira EMA é a média dos primeiros 50 preços

    # Calculando os valores subsequentes da EMA
    for price in prices[period:]:
        # Fórmula da EMA: EMA = (Preço atual - EMA anterior) * k + EMA anterior
        ema.append((price - ema[-1]) * k + ema[-1])

    return ema[-1]  # Retorna o último valor da EMA (mais recente)


# - Cálculo RSI
def calcular_rsi(prices, period=14):
    # Inicializa variáveis de ganhos e perdas acumulados
    gains = 0
    losses = 0
    
    # Calcular as diferenças entre os preços (dia a dia)
    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains += change
        else:
            losses -= change  # Usa o valor absoluto de perdas
    
    # Média dos ganhos e perdas (Primeira média simples)
    avg_gain = gains / period
    avg_loss = losses / period
    
    # Evitar divisão por zero
    if avg_loss == 0:
        return 100
    
    # Calculando o RS (Relative Strength)
    rs = avg_gain / avg_loss
    
    # Calculando o RSI
    rsi = 100 - (100 / (1 + rs))
    
    # Para os próximos períodos, usamos as médias exponenciais para calcular a média
    for i in range(period + 1, len(prices)):
        change = prices[i] - prices[i - 1]
        
        # Atualiza ganho e perda
        if change > 0:
            gain = change
            loss = 0
        else:
            gain = 0
            loss = -change
        
        # Média exponencial acumulada (smoothing)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        # Evitar divisão por zero
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    return rsi


# - Aplica o cálculo de EMA50 e RSI no preço em M1
def calcular_ema_rsi(symbol="BTCUSDT", interval="1m", limit=100):
    # Captura os candles (data de preços) para o período solicitado
    candles = capturar_preco_binance(symbol=symbol, interval=interval, limit=limit)
    if not candles:
        print("Erro ao obter data de candles.")
        return None
    
    # Extrair os preços de fechamento dos candles
    close_prices = [float(candle[4]) for candle in candles]
    
    # Calcular EMA50 (50 períodos)
    EMA50 = calcular_ema7(close_prices, 50)
    
    # Calcular EMA7 (7 períodos)
    EMA7 = calcular_ema7(close_prices, 7)
    
    # Calcular RSI com 14 períodos
    rsi = calcular_rsi(close_prices, 14)
    
    return {"EMA50": EMA50, "EMA7": EMA7, "RSI": rsi}
   

# - Abrir ordem LONG
def abrir_ordem_compra(preco_atual, saldo_investido):

    quantidade = saldo_investido / preco_atual

    # Armazena os detalhes da ordem de compra
    ordem = {
        "preco_compra": preco_atual,
        "quantidade": quantidade,
        "valor_investido": saldo_investido,
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }                                       

    # Cria a mensagem de log
    mensagem_telegram = (f"+ Compra realizada! {quantidade:.4f} a ${preco_atual:.2f}\n"
                         f"+ Horário da abertura da ordem: {ordem['timestamp']}")                                                                                            
    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)

    return ordem


# - Abrir ordem SHORT
def abrir_ordem_venda(preco_atual, saldo_investido):

    quantidade = saldo_investido / preco_atual

    # Armazena os detalhes da ordem de venda
    ordem = {
        "preco_venda": preco_atual,
        "quantidade": quantidade,
        "valor_investido": saldo_investido,
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }                                       

    # Cria a mensagem de log
    mensagem_telegram = (f"- Venda realizada! {quantidade:.4f} a ${preco_atual:.2f}\n"
                         f"- Horário da abertura da ordem: {ordem['timestamp']}")                                                                                            
    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)

    return ordem


# - Função para listar e fechar posições abertas
def fechar_ordem(ordem_aberta, ordem_compra, ordem_venda, preco_atual, saldo_usdt, leverage):

    if ordem_aberta == "LONG" and not None:

        quantidade = ordem_compra["quantidade"]
        valor_atual = quantidade * preco_atual
        despesa = valor_atual * 0.008 #Taxa Taker

        valor_investido = ordem_compra["valor_investido"]
        lucro_prejuizo = valor_atual - valor_investido - despesa

        saldo_usdt += lucro_prejuizo

        saldo_investido = saldo_usdt * leverage

        mensagem_telegram = (f"ORDEM FECHADA! \n"
                             f"Saldo atual em USDT: {saldo_usdt:.2f}"
                             f"Lucro/Prejuízo: {lucro_prejuizo:.2f}")
        enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
        return saldo_investido
        
    if ordem_aberta == "SHORT" and not None:

        quantidade = ordem_venda["quantidade"]
        valor_atual = quantidade * preco_atual
        despesa = valor_atual * 0.008 #Taxa Taker

        valor_investido = ordem_venda["valor_investido"]
        lucro_prejuizo = valor_investido - valor_atual - despesa
        saldo_usdt += lucro_prejuizo

        saldo_investido = saldo_usdt * leverage

        mensagem_telegram = (f"ORDEM FECHADA! \n"
                             f"Saldo atual em USDT: {saldo_usdt:.2f}"
                             f"Lucro/Prejuízo: {lucro_prejuizo:.2f}")
        enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
        return saldo_investido
    


# - run()
def run():

    saldo_usdt = float(input("Informe o saldo a ser investido: "))
    leverage = 10
    saldo_investido = saldo_usdt * leverage
    print(f"Saldo inicial com leverage aplicado: ${saldo_investido:.2f} USD")
    print("Iniciando ...\n")

   
    ordem_compra = None
    ordem_venda = None
    preco_momento_compra = None
    preco_momento_venda = None
    #ultimos_candle_tipos = []
    ordem_aberta = None
    

    while True:
        

        # Captura o preço em M1
        preco_info = precos_zerosegundo(symbol="BTCUSDT", interval="1m")
        preco_atual = preco_info["price"]


        # Informa o tipo de candle
        # candle_tipo = capturar_identificar_candle(symbol="BTCUSDT", interval="1m")
        # print(f"{candle_tipo}")


        suporte, resistencia = calcular_suporte_resistencia(symbol="BTCUSDT", interval="5m", limit=15)
        if suporte is not None and resistencia is not None:
            print(f"Suporte: {suporte}, Resistência: {resistencia}")
        else:
            print("Não foi possível calcular os pontos de suporte e resistência.")

        # Atualiza a lista com os últimos dois tipos de candle
        # ultimos_candle_tipos.append(candle_tipo)
        # if len(ultimos_candle_tipos) > 2:
        #     ultimos_candle_tipos.pop(0)  # Remove o mais antigo, mantendo o tamanho da lista em 2


        # Calcula e exibe os valores de EMA7, EMA50 e RSI
        indicadores = calcular_ema_rsi(symbol="BTCUSDT", interval="1m")
        if indicadores is not None and "EMA7" in indicadores and "EMA50" in indicadores and "RSI" in indicadores:
            print(f"EMA50: {indicadores['EMA50']:.2f} | RSI: {indicadores['RSI']:.2f} | EMA7: {indicadores['EMA7']:.2f}")

        data = capturar_preco_binance(symbol="BTCUSDT", interval="1m", limit=30)



        # ---------------------------------------------------------------------------------------------- #

        # Abrir ordem LONG
        if (saldo_usdt > 0 and not ordem_aberta and 
        preco_atual < indicadores["EMA7"] and indicadores["EMA7"] > indicadores["EMA50"] and indicadores["RSI"] > 30):
            ordem_compra = abrir_ordem_compra(preco_atual, saldo_investido)
            preco_momento_compra = preco_atual
            suporte_momento_compra = suporte
            suporte_sl = suporte_momento_compra * 0.995
            take_profit = preco_momento_compra + ((preco_momento_compra - suporte_sl) * 2)  # Take Profit
            ordem_aberta = "LONG"  

        #TP/SL ordem LONG
        if ordem_aberta == "LONG":
            if preco_atual is not None and preco_momento_compra is not None:
                if preco_atual <= suporte_sl:
                    mensagem_telegram = "STOPLOSS ACIONADO!"
                    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
                    fechar_ordem(ordem_aberta, ordem_compra, ordem_venda, preco_atual, saldo_usdt, leverage)
                    ordem_aberta = None
                elif preco_atual >= take_profit:
                    mensagem_telegram = "TAKE PROFIT ACIONADO!"
                    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
                    fechar_ordem(ordem_aberta, ordem_compra, ordem_venda, preco_atual, saldo_usdt, leverage)
                    ordem_aberta = None

    # ---------------------------------------------------------------------------------------------- #

        #Abrir ordem SHORT
        if (saldo_usdt > 0 and not ordem_aberta and 
        preco_atual > indicadores["EMA7"] and indicadores["EMA7"] < indicadores["EMA50"] and indicadores["RSI"] < 70): 
            ordem_venda = abrir_ordem_venda(preco_atual, saldo_investido)
            preco_momento_venda = preco_atual
            suporte_moment_venda = suporte
            suporte_sl = suporte_moment_venda * 0.995
            take_profit = preco_momento_venda - ((suporte_sl - preco_momento_venda) * 2)  # Take Profit
            ordem_aberta = "SHORT"  

        #StopLoss ordem SHORT
        if ordem_aberta == "SHORT":
            if preco_atual is not None and preco_momento_venda is not None:
                if preco_atual >= suporte_sl:
                    mensagem_telegram = "STOPLOSS ACIONADO!"
                    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
                    fechar_ordem(ordem_aberta, ordem_compra, ordem_venda, preco_atual, saldo_usdt, leverage)
                    ordem_aberta = None
                elif preco_atual <= take_profit:
                    mensagem_telegram = "TAKE PROFIT ACIONADO!"
                    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
                    fechar_ordem(ordem_aberta, ordem_compra, ordem_venda, preco_atual, saldo_usdt, leverage)
                    ordem_aberta = None

    # ---------------------------------------------------------------------------------------------- #

        # Verifica os últimos dois candles para condição de compra/venda
        # tipos_de_candles = []
        # data = capturar_preco_binance(symbol="BTCUSDT", interval="1m", limit=3)
        # if data:
        #     for candle_data in data:
        #         ohlc = {
        #             'open': float(candle_data[1]),
        #             'high': float(candle_data[2]),
        #             'low': float(candle_data[3]),
        #             'close': float(candle_data[4])
        #         }
        #         tipos_de_candles.append(identificar_candle(ohlc))

if __name__ == "__main__":
    run()


    #TAXA MAKER: 0,02%
    #TAXA TAKER: 0,04%
    #Pode abaixar se rolar negociações todos os dias ...