import mysql.connector
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
import locale

# Carregar variáveis de ambiente
load_dotenv()

db_config = {
    "host": os.getenv("HOST"),
    "user": os.getenv("USER"),
    "password": os.getenv("PW"),
    "database": os.getenv("DB")
}

# Configurar localidade para o Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

loaded_codes = []  # Lista de códigos carregados

# Criando a interface gráfica
root = tk.Tk()
root.title("Validação de Orçamentos")
root.geometry("950x550")
root.configure(bg="#dfdfdf")

# Função para formatar a data
def formatar_data(data_str):
    try:
        return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None

# Função para carregar a lista de produtos do banco
def carregar_produtos():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT produto FROM cadastro_orc ORDER BY produto")
        produtos = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return produtos if produtos else ["Nenhum produto disponível"]
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao carregar produtos: {err}")
        return ["Erro ao carregar produtos"]

# Buscar lançamentos no banco
def get_lancamentos(data_filtro, produto_filtro):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        data_filtro = formatar_data(data_filtro)
        if data_filtro is None:
            messagebox.showwarning("Aviso", "Formato de data inválido. Use DD/MM/YYYY.")
            return []

        query = "SELECT * FROM cadastro_orc WHERE dt = %s AND produto = %s"
        cursor.execute(query, (data_filtro, produto_filtro))
        lancamentos = cursor.fetchall()

        for row in lancamentos:
            row['dt'] = row['dt'].strftime("%d/%m/%Y")  # Formatar data
        
        return lancamentos
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco: {err}")
        return []
    finally:
        if connection:
            connection.close()

# Exibir lançamentos filtrados
def show_lancamentos():
    data_filtro = entry_data.get().strip()
    produto_filtro = combo_produto.get().strip()

    if not data_filtro or not produto_filtro or produto_filtro == "Nenhum produto disponível":
        messagebox.showwarning("Aviso", "Por favor, preencha a Data e o Produto.")
        return

    lancamentos = get_lancamentos(data_filtro, produto_filtro)
    if lancamentos:
        tree.delete(*tree.get_children())
        for index, row in enumerate(lancamentos):
            formatted_vlr_orcamento = locale.currency(row['vlr_orcamento'], grouping=True, symbol=True)
            color_tag = "#d7d7d7" if index % 2 == 0 else "#cccccc"
            tree.insert("", "end", values=(row['cod'], row['dt'], row['produto'], row['fornecedor'], formatted_vlr_orcamento, row['status']), tags=(color_tag))
        loaded_codes.clear()
        loaded_codes.extend([row['cod'] for row in lancamentos])
    else:
        messagebox.showinfo("Sem lançamentos", "Nenhum lançamento encontrado com os filtros informados.")

# Atualizar status do orçamento
def validar_orcamento():
    cod_selecionado = entry_codigo.get().strip()
    data_filtro = entry_data.get().strip()
    produto_filtro = combo_produto.get().strip()

    if not cod_selecionado:
        messagebox.showwarning("Aviso", "Por favor, insira o código do orçamento para validar.")
        return

    data_filtro = formatar_data(data_filtro)
    if not data_filtro:
        messagebox.showwarning("Aviso", "Formato de data inválido. Use DD/MM/YYYY.")
        return

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cursor.execute("UPDATE cadastro_orc SET status = 'APROVADO' WHERE cod = %s", (cod_selecionado,))
        cursor.execute("UPDATE cadastro_orc SET status = 'REPROVADO' WHERE dt = %s AND produto = %s AND cod <> %s",
                       (data_filtro, produto_filtro, cod_selecionado))
        
        connection.commit()
        messagebox.showinfo("Sucesso", "Orçamento validado com sucesso!")
        show_lancamentos()
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco: {err}")
    finally:
        if connection:
            connection.close()

# Criando frame de Filtro
frame_filtro = tk.Frame(root, bg="#dfdfdf")
frame_filtro.pack(pady=10)

tk.Label(frame_filtro, text="Data:", bg="#dfdfdf").grid(row=0, column=0, padx=5)
entry_data = tk.Entry(frame_filtro, width=12)
entry_data.grid(row=0, column=1, padx=5)

tk.Label(frame_filtro, text="Produto:", bg="#dfdfdf").grid(row=0, column=2, padx=5)

# Criando a Combobox para produtos
produtos_disponiveis = carregar_produtos()
combo_produto = ttk.Combobox(frame_filtro, values=produtos_disponiveis, state="readonly", width=27)
combo_produto.grid(row=0, column=3, padx=5)
combo_produto.current(0)  # Seleciona o primeiro item

btn_carregar = tk.Button(frame_filtro, text="Carregar Lançamentos", command=show_lancamentos, bg="#007bff", fg="white")
btn_carregar.grid(row=0, column=4, padx=5)

# Criando a lista de lançamentos
tree = ttk.Treeview(root, columns=("Código", "Data", "Produto", "Fornecedor", "Valor Orçamento", "Status"), show="headings")
tree.heading("Código", text="Código")
tree.heading("Data", text="Data")
tree.heading("Produto", text="Produto")
tree.heading("Fornecedor", text="Fornecedor")
tree.heading("Valor Orçamento", text="Valor Orçamento")
tree.heading("Status", text="Status")

tree.column("Código", width=80)
tree.column("Data", width=100)
tree.column("Produto", width=150)
tree.column("Fornecedor", width=150)
tree.column("Valor Orçamento", width=120)
tree.column("Status", width=100)

tree.tag_configure("#d7d7d7", background="#d7d7d7")
tree.tag_configure("#cccccc", background="#cccccc")

tree.pack(fill="both", expand=True, padx=10, pady=10)

# Criando frame para código do orçamento
frame_validar = tk.Frame(root, bg="#dfdfdf")
frame_validar.pack(pady=10)

tk.Label(frame_validar, text="Código do orçamento:", bg="#dfdfdf").grid(row=0, column=0, padx=5)
entry_codigo = tk.Entry(frame_validar, width=20)
entry_codigo.grid(row=0, column=1, padx=5)

btn_validar = tk.Button(frame_validar, text="Validar", command=validar_orcamento, bg="#28a745", fg="white")
btn_validar.grid(row=0, column=2, padx=10)

root.mainloop()
