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

# Configurar a localidade para o Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

loaded_codes = []  # Lista de códigos carregados

# Função para buscar lançamentos no banco
def get_lancamentos():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cadastro_orc")
        lancamentos = cursor.fetchall()
        
        for row in lancamentos:
            row['dt'] = row['dt'].strftime("%d/%m/%Y")
            
        return lancamentos
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco: {err}")
        return []
    finally:
        if connection:
            connection.close()


# Ordenação da Treeview
def sort_lancamentos(lancamentos, column, reverse=False):
    return sorted(lancamentos, key=lambda x: x[column], reverse=reverse)

def show_lancamentos():
    lancamentos = get_lancamentos()
    if lancamentos:
        tree.delete(*tree.get_children())  # Limpa os dados
        for index, row in enumerate(lancamentos):
            formatted_vlr_orcamento = locale.currency(row['vlr_orcamento'], grouping=True, symbol=True)
            color_tag = "#d7d7d7" if index % 2 == 0 else "#cccccc"
            tree.insert("", "end", values=(row['cod'], row['dt'], row['produto'], row['fornecedor'], formatted_vlr_orcamento, row['observacao'], row['status']), tags=(color_tag))
        loaded_codes.clear()
        loaded_codes.extend([row['cod'] for row in lancamentos])
    else:
        messagebox.showinfo("Sem lançamentos", "Não há lançamentos para exibir.")

def sort_by_column(tree, column, reverse=False):
    lancamentos = get_lancamentos()
    column_map = {
        "Código": "cod",
        "Data": "dt",
        "Produto": "produto",
        "Fornecedor": "fornecedor",
        "Valor Orçamento": "vlr_orcamento",
        "Observação": "observacao",
        "Status": "status"
    }
    if column in column_map:
        lancamentos = sort_lancamentos(lancamentos, column_map[column], reverse)
    tree.delete(*tree.get_children())
    for index, row in enumerate(lancamentos):
        formatted_vlr_orcamento = locale.currency(row['vlr_orcamento'], grouping=True, symbol=True)
        color_tag = "#d7d7d7" if index % 2 == 0 else "#cccccc"
        tree.insert("", "end", values=(row['cod'], row['dt'], row['produto'], row['fornecedor'], formatted_vlr_orcamento, row['observacao'], row['status']), tags=(color_tag))

def on_item_selected(event):
    """Carrega os dados do orçamento selecionado para edição."""
    selected_item = tree.selection()
    if selected_item:
        values = tree.item(selected_item, "values")
        entry_cod.config(state="normal")
        entry_cod.delete(0, tk.END)
        entry_cod.insert(0, values[0])
        entry_cod.config(state="readonly")

        entry_data.delete(0, tk.END)
        entry_data.insert(0, values[1])
        entry_produto.delete(0, tk.END)
        entry_produto.insert(0, values[2])
        entry_fornecedor.delete(0, tk.END)
        entry_fornecedor.insert(0, values[3])
        entry_vlr_orcamento.delete(0, tk.END)
        entry_vlr_orcamento.insert(0, values[4].replace("R$ ", "").replace(".", "").replace(",", "."))
        entry_observacao.delete(0, tk.END)
        entry_observacao.insert(0, values[5])
        entry_status.delete(0, tk.END)
        entry_status.insert(0, values[6])  # Exibe o status

def save_changes():
    """Salva as alterações no banco de dados e recarrega os lançamentos."""
    cod = entry_cod.get()
    data = entry_data.get()
    produto = entry_produto.get()
    fornecedor = entry_fornecedor.get()
    vlr_orcamento = float(entry_vlr_orcamento.get())
    observacao = entry_observacao.get()
    status = entry_status.get()  # Obtém o valor do status

    # Converter DD/MM/YYYY para YYYY-MM-DD antes de salvar no banco
    try:
        data = entry_data.get().strip()  # Remover espaços extras
        if not data:
            messagebox.showerror("Erro", "O campo de data não pode estar vazio!")
            return
        data_sql = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Erro", "Formato de data inválido! Use DD/MM/YYYY.")
        return

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute(""" 
            UPDATE cadastro_orc 
            SET dt = %s, produto = %s, fornecedor = %s, vlr_orcamento = %s, observacao = %s, status = %s 
            WHERE cod = %s
        """, (data_sql, produto, fornecedor, vlr_orcamento, observacao, status, cod))
        connection.commit()
        messagebox.showinfo("Sucesso", "Orçamento atualizado com sucesso!")
        
        show_lancamentos()  # Recarrega os lançamentos após salvar
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao atualizar o orçamento: {err}")
    finally:
        if connection:
            connection.close()

def delete_lancamento():
    """Exclui o orçamento selecionado do banco de dados."""
    selected_item = tree.selection()
    if selected_item:
        cod = tree.item(selected_item, "values")[0]
        confirm = messagebox.askyesno("Excluir", f"Tem certeza que deseja excluir o orçamento de código {cod}?")
        if confirm:
            try:
                connection = mysql.connector.connect(**db_config)
                cursor = connection.cursor()
                cursor.execute("DELETE FROM cadastro_orc WHERE cod = %s", (cod,))
                connection.commit()
                messagebox.showinfo("Sucesso", f"Orçamento de código {cod} excluído com sucesso!")
                show_lancamentos()  # Recarrega os lançamentos após a exclusão
            except mysql.connector.Error as err:
                messagebox.showerror("Erro", f"Erro ao excluir o orçamento: {err}")
            finally:
                if connection:
                    connection.close()

# Criando a interface gráfica
root = tk.Tk()
root.title("Lançamentos - Cadastro Orc")
root.geometry("900x500")
root.configure(bg="#dfdfdf")

tree = ttk.Treeview(root, columns=("Código", "Data", "Produto", "Fornecedor", "Valor Orçamento", "Observação", "Status"), show="headings")
tree.heading("Código", text="Código", command=lambda: sort_by_column(tree, "Código", reverse=False))
tree.heading("Data", text="Data", command=lambda: sort_by_column(tree, "Data", reverse=False))
tree.heading("Produto", text="Produto", command=lambda: sort_by_column(tree, "Produto", reverse=False))
tree.heading("Fornecedor", text="Fornecedor", command=lambda: sort_by_column(tree, "Fornecedor", reverse=False))
tree.heading("Valor Orçamento", text="Valor Orçamento", command=lambda: sort_by_column(tree, "Valor Orçamento", reverse=False))
tree.heading("Observação", text="Observação", command=lambda: sort_by_column(tree, "Observação", reverse=False))
tree.heading("Status", text="Status", command=lambda: sort_by_column(tree, "Status", reverse=False))

tree.column("Código", width=80)
tree.column("Data", width=100)
tree.column("Produto", width=150)
tree.column("Fornecedor", width=150)
tree.column("Valor Orçamento", width=120)
tree.column("Observação", width=200)
tree.column("Status", width=100)

tree.tag_configure("#d7d7d7", background="#d7d7d7")
tree.tag_configure("#cccccc", background="#cccccc")

style = ttk.Style()
style.configure("Treeview.Heading", font=("Arial", 9, "bold"))

tree.bind("<<TreeviewSelect>>", on_item_selected)
tree.pack(fill="both", expand=True, padx=10, pady=10)

# Campos de edição
frame_edit = tk.Frame(root, bg="#dfdfdf")
frame_edit.pack(pady=10)

tk.Label(frame_edit, text="Código:", bg="#DFDFDF").grid(row=0, column=0, padx=5)
entry_cod = tk.Entry(frame_edit, state="readonly", width=10)
entry_cod.grid(row=0, column=1, padx=5)

tk.Label(frame_edit, text="Data:", bg="#DFDFDF").grid(row=0, column=2, padx=5)
entry_data = tk.Entry(frame_edit, width=12)
entry_data.grid(row=0, column=3, padx=5)

tk.Label(frame_edit, text="Produto:", bg="#DFDFDF").grid(row=0, column=4, padx=5)
entry_produto = tk.Entry(frame_edit, width=20)
entry_produto.grid(row=0, column=5, padx=5)

# Linha 2
tk.Label(frame_edit, text="Fornecedor:", bg="#DFDFDF").grid(row=1, column=0, padx=5)
entry_fornecedor = tk.Entry(frame_edit, width=20)
entry_fornecedor.grid(row=1, column=1, padx=5)

tk.Label(frame_edit, text="Valor Orçamento:", bg="#DFDFDF").grid(row=1, column=2, padx=5)
entry_vlr_orcamento = tk.Entry(frame_edit, width=12)
entry_vlr_orcamento.grid(row=1, column=3, padx=5)

tk.Label(frame_edit, text="Observação:", bg="#DFDFDF").grid(row=1, column=4, padx=5)
entry_observacao = tk.Entry(frame_edit, width=30)
entry_observacao.grid(row=1, column=5, padx=5)

tk.Label(frame_edit, text="Status:", bg="#DFDFDF").grid(row=2, column=0, padx=5)
entry_status = tk.Entry(frame_edit, width=10)  # Campo para status
entry_status.grid(row=2, column=1, padx=5)

frame_buttons = tk.Frame(root, bg="#dfdfdf")
frame_buttons.pack(pady=10)

tk.Button(frame_buttons, text="Salvar Alterações", command=save_changes, bg="#28a745", fg="white").grid(row=0, column=0, padx=5)
tk.Button(frame_buttons, text="Carregar Lançamentos", command=show_lancamentos).grid(row=0, column=1, padx=5)
tk.Button(frame_buttons, text="Excluir Orçamento", command=delete_lancamento, bg="#dc3545", fg="white").grid(row=0, column=2, padx=5)

root.mainloop()
