import mysql.connector
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from tkcalendar import DateEntry  # Importando o DateEntry

# Carregar variáveis de ambiente
load_dotenv()

db_config = {
    "host": os.getenv("HOST"),
    "user": os.getenv("USER"),
    "password": os.getenv("PW"),
    "database": os.getenv("DB")
}

def inserir_dados():
    data = entry_data.get_date()  # Obtendo a data do DateEntry
    produto = entry_produto.get().strip()
    fornecedor = entry_fornecedor.get().strip()
    valor = entry_valor.get().strip()
    observacao = entry_observacao.get("1.0", tk.END).strip()  # Pegando o texto completo do campo multilinha

    if not data or not produto or not fornecedor or not valor:
        messagebox.showerror("Erro", "Os campos: \n • Data \n • Produto \n • Fornecedor \n • Valor do Orçamento \n\n São obrigatórios!")
        return

    try:
        # Converter a data para o formato correto
        data_formatada = data.strftime("%Y-%m-%d")  # Formato YYYY-MM-DD
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO cadastro_orc (dt, produto, fornecedor, vlr_orcamento, observacao) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (data_formatada, produto, fornecedor, valor, observacao))
        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("Sucesso", "Cadastro realizado com sucesso!")
        limpar_campos()
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao inserir os dados: {err}")
    except ValueError:
        messagebox.showerror("Erro", "Data inválida! Por favor, insira a data no formato DD/MM/YYYY.")

def limpar_campos():
    entry_data.delete(0, tk.END)
    entry_produto.delete(0, tk.END)
    entry_fornecedor.delete(0, tk.END)
    entry_valor.delete(0, tk.END)
    entry_observacao.delete(1.0, tk.END)  # Limpar o campo multilinha

# Criar janela
root = tk.Tk()
root.title("Cadastro de Orçamentos")
root.geometry("400x350")  # Aumentei o tamanho da janela para acomodar o campo multilinha

# Alterar a cor de fundo da janela
root.config(bg="#a1a1a1")

# Labels com fundo da mesma cor
tk.Label(root, text="Data:", bg="#a1a1a1").grid(row=0, column=0, padx=10, pady=5, sticky="w")
entry_data = DateEntry(root, date_pattern='dd/mm/yyyy', width=17)  # Definir largura igual aos outros campos
entry_data.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Produto:", bg="#a1a1a1").grid(row=1, column=0, padx=10, pady=5, sticky="w")
entry_produto = tk.Entry(root, width=20)  # Definindo largura para os campos
entry_produto.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Fornecedor:", bg="#a1a1a1").grid(row=2, column=0, padx=10, pady=5, sticky="w")
entry_fornecedor = tk.Entry(root, width=20)
entry_fornecedor.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Valor do Orçamento:", bg="#a1a1a1").grid(row=3, column=0, padx=10, pady=5, sticky="w")
entry_valor = tk.Entry(root, width=20)
entry_valor.grid(row=3, column=1, padx=10, pady=5)

tk.Label(root, text="Observação:", bg="#a1a1a1").grid(row=4, column=0, padx=10, pady=5, sticky="w")
entry_observacao = tk.Text(root, width=20, height=4)  # Ajustei a altura para 4 linhas
entry_observacao.grid(row=4, column=1, padx=10, pady=5)

tk.Button(root, text="Cadastrar", command=inserir_dados).grid(row=5, column=0, columnspan=2, pady=10, padx=5)

root.mainloop()
