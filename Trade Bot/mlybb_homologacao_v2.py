import requests
import time
from datetime import datetime
import numpy as np
import pandas as pd


# Aplicar Mínima e máxima do dia anterior em M15;
# Filtro baseado em volume pra confirmar a força do movimento;
# Aplicar MACD ou CCI p/ confirmar o cruzamento das EMAs.
# Montar uma base histórico ao invés de usar os preços atuais



arquivo_excel = 'database.xlsx'
df = pd.read_excel(arquivo_excel)


inicio = "01/01/2024 00:00"
fim = "01/01/2024 01:00"

df_filtrado = df[(df['Timestamp'] >= inicio) & (df['Timestamp'] <= fim)].copy()  

# Função para calcular a EMA7
def calcular_ema7(dados):
    return dados['Close'].ewm(span=7, adjust=False).mean()

# Função para calcular a EMA50
def calcular_ema50(dados):
    return dados['Close'].ewm(span=50, adjust=False).mean()

# Função para calcular o RSI
def calcular_rsi(dados, periodo=14):
    # Calcular as variações diárias
    delta = dados['Close'].diff()
    
    # Separar os ganhos e perdas
    ganho = delta.where(delta > 0, 0)
    perda = -delta.where(delta < 0, 0)
    
    # Calcular a média dos ganhos e perdas
    ganho_medio = ganho.rolling(window=periodo).mean()
    perda_media = perda.rolling(window=periodo).mean()
    
    # Calcular o RSI
    rs = ganho_medio / perda_media
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

# Função para abrir uma ordem (compra ou venda)
def abertura_ordem(tipo_ordem, saldo, preco_entrada, arquivo):
    quantidade = saldo / preco_entrada  # Calcular a quantidade de ações/ativos que podem ser comprados
    if tipo_ordem == "compra":
        arquivo.write(f"Abertura de ordem de COMPRA. Quantidade: {quantidade:.2f} BTC.\n")
    elif tipo_ordem == "venda":
        arquivo.write(f"Abertura de ordem de VENDA. Quantidade: {quantidade:.2f} BTC.\n")

# Função para fechar a ordem 
def fechar_ordem(preco_entrada, preco_atual, saldo, arquivo):
    quantidade = saldo / preco_entrada  
    lucro_prejuizo = (preco_atual - preco_entrada) * quantidade  
    if lucro_prejuizo > 0:
        arquivo.write(f"Lucro de R$ {lucro_prejuizo:.2f}.\n")
    elif lucro_prejuizo < 0:
        arquivo.write(f"Prejuizo de R$ {lucro_prejuizo:.2f}.\n")
    else:
        arquivo.write("Nenhum lucro ou prejuízo (sem variacao no preco).\n")


def run():
    # Solicitar saldo para investir
    saldo = float(input("Informe o saldo a ser investido: R$ "))

    ordemaberta = None

    df_filtrado.loc[:, 'EMA7'] = calcular_ema7(df_filtrado)
    df_filtrado.loc[:, 'EMA50'] = calcular_ema50(df_filtrado)
    df_filtrado.loc[:, 'RSI'] = calcular_rsi(df_filtrado)
    df_filtrado['EMA7'] = df_filtrado['EMA7'].round(2)
    df_filtrado['EMA50'] = df_filtrado['EMA50'].round(2)
    df_filtrado['RSI'] = df_filtrado['RSI'].round(2)

    with open("resultado.txt", "w") as arquivo:
        
        for index, row in df_filtrado.iterrows():
            timestamp = row['Timestamp']
            close = row['Close']
            rsi_atual = row['RSI']
            ema7_atual = row['EMA7']
            ema50_atual = row['EMA50']
            preco_entrada = close  # Preço de fechamento para essa linha

            
            arquivo.write(f"\nTimestamp: {timestamp}, Close: {close}\n")

        
            if preco_entrada > ema7_atual and ema7_atual > ema50_atual and rsi_atual > 30 and ordemaberta is None:
                arquivo.write("Condicoes para COMPRA atendidas.\n")
                abertura_ordem("compra", saldo, preco_entrada, arquivo)
                ordemaberta = 1
            if preco_entrada < ema7_atual and ema7_atual < ema50_atual and rsi_atual < 70 and ordemaberta is None:
                arquivo.write("Condicoes para VENDA atendidas.\n")
                abertura_ordem("venda", saldo, preco_entrada, arquivo)
                ordemaberta = 1

            preco_atual = df_filtrado['Close'].iloc[-1]

            if preco_atual > preco_entrada and ordemaberta is not None:
                fechar_ordem(preco_entrada, preco_atual, saldo, arquivo)
                ordemaberta = None


run()