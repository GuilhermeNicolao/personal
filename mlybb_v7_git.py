import requests
import time
from datetime import datetime, timedelta
import numpy as np
import ccxt

TOKEN_TELEGRAM = ""
CHAT_ID_TELEGRAM = ""

binance_api_key = ''
binance_secret_key = ''



# - Conectar com a Binance
exchange = ccxt.binance({
    'apiKey': binance_api_key,
    'secret': binance_secret_key,
    'enableRateLimit': True,  # Para evitar erro de limite de requisições
})


# - Especificando o mercado de futuros
exchange.options['defaultType'] = 'future'


# - Função para obter o saldo no mercado de futuros USDT
def obter_saldo_usdt():
    try:
        balance = exchange.fetch_balance({'type': 'future'})

        # Verificar o saldo em USDT no mercado de futuros
        usdt_balance = balance.get('total', {}).get('USDT', 0)
        
        return usdt_balance
    except ccxt.BaseError as e:
        print(f"Erro ao acessar a API de Futuros: {e}")
        return None


# - Função para obter as regras de quantidade mínima para operar
def obter_quantia_minima(symbol):

    try:
        market = exchange.market(symbol)
        return market['limits']['amount']['min']
    except Exception as e:
        print(f"Erro ao obter limites para operar {symbol}: {e}")
        return None
    

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
def capturar_preco_binance(symbol="BTCUSDT", interval="1m", limit=1):
    
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
        
        # Verificamos se estamos no segundo 58 (Candle fecha perto do segundo 57,58)
        if current_time.second == 58:
            # Chamada à API para obter o preço
            result = capturar_preco_binance(symbol=symbol, interval=interval)
            if result:
                kline = result[0]
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


# - Cálculo EMA
def calcular_ema(prices, period):
    # Calculando a EMA com maior precisão
    k = 2 / (period + 1)
    
    # Usando o valor inicial da EMA como o primeiro preço (ou a média dos primeiros preços)
    ema = [np.mean(prices[:period])]  # Primeira EMA é a média dos primeiros 'period' preços

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


# - Aplica o cálculo de EMA7 e RSI no preço em M1
def calcular_ema_rsi(symbol="BTCUSDT", interval="1m", limit=100):
    # Captura os candles (dados de preços) para o período solicitado
    candles = capturar_preco_binance(symbol=symbol, interval=interval, limit=limit)
    if not candles:
        print("Erro ao obter dados de candles.")
        return None
    
    # Extrair os preços de fechamento dos candles
    close_prices = [float(candle[4]) for candle in candles]
    
    # Calcular EMA7
    ema7 = calcular_ema(close_prices, 7)
    
    # Calcular RSI com 14 períodos
    rsi = calcular_rsi(close_prices, 14)
    
    return {"EMA7": ema7, "RSI": rsi}
   

# - Função para abrir uma ordem de COMPRA
def abrir_ordem_compra(symbol, leverage, order_type='market'):
    try:
        # Consultar o saldo de USDT no mercado de futuros
        saldo_usdt = obter_saldo_usdt()

        if saldo_usdt is None or saldo_usdt == 0:
            mensagem_telegram = "Saldo insuficiente para abrir uma ordem."
            enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
            return

        # Obter o preço atual do ativo 
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']  

        # Obter a quantidade mínima permitida para o par
        min_amount = obter_quantia_minima(symbol)
        if min_amount is None:
            mensagem_telegram = f"Não foi possível obter o limite mínimo para {symbol}."
            enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
            return

        # Calcular a quantidade de contratos com base no valor investido e alavancagem
        leveraged_investment = saldo_usdt * leverage  
        amount_to_buy = leveraged_investment / current_price

        # Verificar se a quantidade calculada é menor que a quantidade mínima
        if amount_to_buy < min_amount:
            mensagem_telegram = (f"A quantidade calculada ({amount_to_buy}) é menor que a quantidade mínima permitida ({min_amount}).\n"
                            f"Você precisa investir pelo menos {min_amount * current_price / leverage:.2f} USDT com alavancagem de {leverage}.")
            enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
            return

        # Verificar se o valor nominal (notional value) atende ao mínimo de 100 USDT
        notional_value = amount_to_buy * current_price
        if notional_value < 100:
            mensagem_telegram = (f"O valor nominal da ordem ({notional_value}) é menor que o limite mínimo de 100 USDT.\n"
                            f"Você precisa investir pelo menos {100 / leverage:.2f} USDT com alavancagem de {leverage}.")
            enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
            return

        # Criar a ordem de compra
        if order_type == 'market':
            # Ordem de mercado
            order = exchange.create_order(symbol, order_type, 'buy', amount_to_buy, None, {'leverage': leverage})

        mensagem_telegram = f"Ordem de compra executada!"
        enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
        return order
    
    except ccxt.BaseError as e:
        mensagem_telegram = f"Erro ao abrir ordem de compra: {e}"
        enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
        

# - Função para abrir uma ordem de VENDA
def abrir_ordem_venda(symbol, leverage, order_type='market'):
    try:
        # Consultar o saldo de USDT no mercado de futuros
        saldo_usdt = obter_saldo_usdt()

        if saldo_usdt is None or saldo_usdt == 0:
            mensagem_telegram = "Saldo insuficiente para abrir uma ordem."
            enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
            return

        # Obter o preço atual do ativo 
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']  

        # Obter a quantidade mínima permitida para o par
        min_amount = obter_quantia_minima(symbol)
        if min_amount is None:
            mensagem_telegram = f"Não foi possível obter o limite mínimo para {symbol}."
            enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
            return

        # Calcular a quantidade de contratos com base no valor investido e alavancagem
        leveraged_investment = saldo_usdt * leverage  
        amount_to_sell = leveraged_investment / current_price

        # Verificar se a quantidade calculada é menor que a quantidade mínima
        if amount_to_sell < min_amount:
            mensagem_telegram = (f"A quantidade calculada ({amount_to_sell}) é menor que a quantidade mínima permitida ({min_amount}).\n"
                            f"Você precisa investir pelo menos {min_amount * current_price / leverage:.2f} USDT com alavancagem de {leverage}.")
            enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
            return

        # Verificar se o valor nominal (notional value) atende ao mínimo de 100 USDT
        notional_value = amount_to_sell * current_price
        if notional_value < 100:
            mensagem_telegram = (f"O valor nominal da ordem ({notional_value}) é menor que o limite mínimo de 100 USDT.\n"
                            f"Você precisa investir pelo menos {100 / leverage:.2f} USDT com alavancagem de {leverage}.")
            enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
            return

        # Criar a ordem de compra
        if order_type == 'market':
            # Ordem de mercado
            order = exchange.create_order(symbol, order_type, 'sell', amount_to_sell, None, {'leverage': leverage})

        mensagem_telegram = f"Ordem de venda executada!"
        enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
        return order
    
    except ccxt.BaseError as e:
        mensagem_telegram = f"Erro ao abrir ordem de compra: {e}"
        enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)

    
# - Função para listar e fechar posições abertas
def fechar_ordem(symbol):
    try:
        # Obter todas as posições abertas
        positions = exchange.fetch_positions()

        # Corrigir formato do símbolo para corresponder ao retorno da API
        formatted_symbol = symbol + ":USDT"

        for position in positions:
            if position['symbol'] == formatted_symbol and float(position['contracts']) > 0:
                contracts = float(position['contracts'])  # Quantidade de contratos abertos
                side = position['side']  # 'long' ou 'short'

                # Determinar o lado oposto para fechar a posição
                close_side = 'sell' if side == 'long' else 'buy'

                # Fechar a posição
                order = exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=close_side,
                    amount=contracts
                )

                # Consultar o saldo de USDT após fechar a ordem
                saldo_usdt = obter_saldo_usdt()

                mensagem_telegram = (f"Ordem de fechamento executada: {order}\n"
                                     f"Saldo atual de USDT: {saldo_usdt:.2f} USDT")
                enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
                return

        mensagem_telegram = f"Não há posições abertas para {symbol}."
        enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
    except ccxt.BaseError as e:
        mensagem_telegram = f"Erro ao fechar posições abertas: {e}"
        enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)


# - run()
def run():

    # Imprimir saldo atual de USDT
    saldo_usdt = obter_saldo_usdt()
    if saldo_usdt is None:
        print("Erro ao obter o saldo de USDT.")
        return

    print(f"Saldo atual em USDT: {saldo_usdt:.2f}")

    symbol = 'BTC/USDT'
    leverage = 5

    # Exibir as informações coletadas
    print(f"\nAtivo selecionado: {symbol}")
    print(f"Valor de investimento: {saldo_usdt} USDT")
    print(f"Alavancagem: {leverage}x")


    ordem_compra = None
    ordem_venda = None
    preco_momento_compra = None
    preco_momento_venda = None
    ultimos_candle_tipos = []
    ordem_aberta = False  # Flag para verificar se há uma ordem aberta


    while True:
        
        # Captura o preço em M1
        preco_info = precos_zerosegundo(symbol="BTCUSDT", interval="1m")
        preco_atual = preco_info["price"]


        # Informa o tipo de candle
        candle_tipo = capturar_identificar_candle(symbol="BTCUSDT", interval="1m")
        print(f"{candle_tipo}")


        # Atualiza a lista com os últimos dois tipos de candle
        ultimos_candle_tipos.append(candle_tipo)
        if len(ultimos_candle_tipos) > 2:
            ultimos_candle_tipos.pop(0)  # Remove o mais antigo, mantendo o tamanho da lista em 2


        # Calcula e exibe os valores de EMA7 e RSI
        indicadores = calcular_ema_rsi(symbol="BTCUSDT", interval="1m")
        if indicadores is not None and "EMA7" in indicadores and "RSI" in indicadores:
            print(f"EMA7: {indicadores['EMA7']:.2f} | RSI: {indicadores['RSI']:.2f} \n")

            # Abrir ordem LONG: Candles Hammer / Bullish Engulfing | Preço < EMA7 | RSI < 50
            if  (saldo_usdt > 0 and not ordem_aberta and candle_tipo in ["Hammer", "Bullish Engulfing", "Doji"] and preco_atual < indicadores["EMA7"] and indicadores["RSI"] < 50):
                ordem_compra = abrir_ordem_compra(symbol, leverage)
                preco_momento_compra = preco_atual
                abertura_ordem = datetime.now()
                ordem_aberta = True  # Marca que há uma ordem aberta

            #Abrir ordem SHORT: Candles Inverted Hammer / Bearish Engulfing | Preço > EMA7 | RSI > 50    
            elif (saldo_usdt > 0 and not ordem_aberta and candle_tipo in ["Inverted Hammer", "Bearish Engulfing", "Doji"] and preco_atual > indicadores["EMA7"] and indicadores["RSI"] > 50): 
                ordem_venda = abrir_ordem_venda(symbol, leverage)
                preco_momento_venda = preco_atual
                abertura_ordem = datetime.now()
                ordem_aberta = True  # Marca que há uma ordem aberta



            # Verifica os últimos dois candles para condição de compra/venda
            tipos_de_candles = []
            data = capturar_preco_binance(symbol="BTCUSDT", interval="1m", limit=3)
            if data:
                for candle_data in data:
                    ohlc = {
                        'open': float(candle_data[1]),
                        'high': float(candle_data[2]),
                        'low': float(candle_data[3]),
                        'close': float(candle_data[4])
                    }
                    tipos_de_candles.append(identificar_candle(ohlc))

            

            # Fechar ordem LONG: Preço atual > Preço registrado na ordem de compra e últimos 2 candles Bullish Engulfing
            if ordem_compra is not None:
                if preco_atual < preco_momento_compra and ultimos_candle_tipos == ["Bearish Engulfing", "Bearish Engulfing"]:
                    mensagem_telegram = "Condição de COMPRA por BEARISH ENGULFING atendida"
                    fechar_ordem(symbol)
                    ordem_compra = None
                    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)

                if (datetime.now() - abertura_ordem) >= timedelta(minutes=30):
                    mensagem_telegram = "!! Fechando ordem de VENDA imediatamente devido ao tempo."
                    fechar_ordem(symbol)
                    ordem_compra = None
                    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)


            # Fechando a ordem se já chegou em 20 minutos
            if ordem_venda is not None:
                if preco_atual < preco_momento_venda and ultimos_candle_tipos == ["Bearish Engulfing", "Bearish Engulfing"]:
                    mensagem_telegram = "Condição de COMPRA por BEARISH ENGULFING atendida"
                    fechar_ordem(symbol)
                    ordem_venda = None
                    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)

                if (datetime.now() - abertura_ordem) >= timedelta(minutes=30):
                    mensagem_telegram = "!! Fechando ordem de VENDA imediatamente devido ao tempo."
                    fechar_ordem(symbol)
                    ordem_venda = None
                    enviar_mensagem_telegram(TOKEN_TELEGRAM, CHAT_ID_TELEGRAM, mensagem_telegram)
                            




if __name__ == "__main__":
    run()