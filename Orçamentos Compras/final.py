import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import sys
import subprocess
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime
import locale
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Carregar variáveis de ambiente
load_dotenv()

db_config = {
    "host": os.getenv("HOST"),
    "user": os.getenv("USER"),
    "password": os.getenv("PW"),
    "database": os.getenv("DB")
}

def get_script_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

script_dir = get_script_directory()

def run_script(script_name):
    script_path = os.path.join(script_dir, script_name)
    if not os.path.exists(script_path):
        messagebox.showerror("Erro", f"O arquivo {script_name} não foi encontrado.")
        return
    try:
        if getattr(sys, 'frozen', False):
            subprocess.Popen([script_path], shell=True)
        else:
            subprocess.Popen([sys.executable, script_path])
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir {script_name}: {e}")

def inserir_dados(entry_data, entry_produto, entry_fornecedor, entry_valor, entry_observacao):
    data = entry_data.get_date()
    produto = entry_produto.get().strip()
    fornecedor = entry_fornecedor.get().strip()
    valor = entry_valor.get().strip()
    observacao = entry_observacao.get("1.0", tk.END).strip()
    
    if not data or not produto or not fornecedor or not valor:
        messagebox.showerror("Erro", "Os campos obrigatórios não foram preenchidos!")
        return
    
    try:
        data_formatada = data.strftime("%Y-%m-%d")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO cadastro_orc (dt, produto, fornecedor, vlr_orcamento, observacao) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (data_formatada, produto, fornecedor, valor, observacao))
        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("Sucesso", "Cadastro realizado com sucesso!")
        limpar_campos(entry_data, entry_produto, entry_fornecedor, entry_valor, entry_observacao)
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao inserir os dados: {err}")

def limpar_campos(entry_data, entry_produto, entry_fornecedor, entry_valor, entry_observacao):
    entry_data.set_date(datetime.today())
    entry_produto.delete(0, tk.END)
    entry_fornecedor.delete(0, tk.END)
    entry_valor.delete(0, tk.END)
    entry_observacao.delete("1.0", tk.END)

def cadastro():
    cadastro_window = tk.Toplevel()
    cadastro_window.title("Cadastro de Orçamentos")
    cadastro_window.geometry("400x350")
    cadastro_window.config(bg="#a1a1a1")
    
    tk.Label(cadastro_window, text="Data:", bg="#a1a1a1").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    entry_data = DateEntry(cadastro_window, date_pattern='dd/mm/yyyy', width=17)
    entry_data.grid(row=0, column=1, padx=10, pady=5)
    
    tk.Label(cadastro_window, text="Produto:", bg="#a1a1a1").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    entry_produto = tk.Entry(cadastro_window, width=20)
    entry_produto.grid(row=1, column=1, padx=10, pady=5)
    
    tk.Label(cadastro_window, text="Fornecedor:", bg="#a1a1a1").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    entry_fornecedor = tk.Entry(cadastro_window, width=20)
    entry_fornecedor.grid(row=2, column=1, padx=10, pady=5)
    
    tk.Label(cadastro_window, text="Valor do Orçamento:", bg="#a1a1a1").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    entry_valor = tk.Entry(cadastro_window, width=20)
    entry_valor.grid(row=3, column=1, padx=10, pady=5)
    
    tk.Label(cadastro_window, text="Observação:", bg="#a1a1a1").grid(row=4, column=0, padx=10, pady=5, sticky="w")
    entry_observacao = tk.Text(cadastro_window, width=20, height=4)
    entry_observacao.grid(row=4, column=1, padx=10, pady=5)
    
    tk.Button(cadastro_window, text="Cadastrar", command=lambda: inserir_dados(entry_data, entry_produto, entry_fornecedor, entry_valor, entry_observacao)).grid(row=5, column=0, columnspan=2, pady=10, padx=5)

def exit_program():
    root.quit()

def telaprincipal():
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

def validacao():
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

def dashboard():
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

    # Criando a interface gráfica
    root = tk.Tk()
    root.title("Dashboard de Orçamentos")
    root.geometry("600x600")  # Aumentando o tamanho da janela para dar mais espaço
    root.configure(bg="#f4f4f4")

    def formatar_data(data_str):
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None

    def exibir_resultado(mensagem, cor):
        label_resultado.config(text=mensagem, foreground=cor)

    def carregar_produtos():
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            query = "SELECT DISTINCT produto FROM cadastro_orc ORDER BY produto"
            cursor.execute(query)
            produtos = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return produtos if produtos else ["Nenhum produto encontrado"]
        except mysql.connector.Error as err:
            print(f"Erro ao carregar produtos: {err}")
            return ["Erro ao carregar produtos"]

    def carregar_orcamentos():
        data = formatar_data(entry_data.get())
        produto = combo_produto.get().strip()

        if not data or not produto or produto == "Nenhum produto encontrado":
            exibir_resultado("Preencha todos os campos corretamente.", "red")
            return

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Consulta para obter orçamentos com o status 'APROVADO'
            query_aprovado = """
                SELECT vlr_orcamento, fornecedor FROM cadastro_orc
                WHERE dt = %s AND produto = %s AND status = 'APROVADO'
            """
            cursor.execute(query_aprovado, (data, produto))
            orcamento_aprovado = cursor.fetchone()

            if orcamento_aprovado:
                label_orcamento_aprovado.config(text=f"- Orçamento Aprovado: R$ {orcamento_aprovado[0]:,.2f} \n - Fornecedor: {orcamento_aprovado[1]}")
            else:
                label_orcamento_aprovado.config(text="Nenhum orçamento aprovado encontrado.")

            # Consulta para os orçamentos
            query_orcamentos = """
                SELECT vlr_orcamento, fornecedor FROM cadastro_orc
                WHERE dt = %s AND produto = %s
            """
            cursor.execute(query_orcamentos, (data, produto))
            orcamentos = cursor.fetchall()

            if orcamentos:
                exibir_resultado(f"{len(orcamentos)} Orçamentos encontrados.", "#0066cc")
                exibir_orcamentos_com_scroll(orcamentos)
                gerar_grafico([valor for valor, _ in orcamentos])

                # Chama a função para calcular a economia
                if orcamento_aprovado:
                    calcular_economia(orcamento_aprovado[0], [valor for valor, _ in orcamentos])
                else:
                    label_economia.config(text="Não há orçamento aprovado para calcular a economia.")
            else:
                exibir_resultado("Nenhum orçamento encontrado.", "red")

            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            exibir_resultado(f"Erro: {err}", "red")

    def gerar_grafico(valores, indice_aprovado=None):
        fig, ax = plt.subplots(figsize=(6, 4))  # Aumentando a largura do gráfico
        fig.patch.set_facecolor('#E3E3E3')  # Alterando a cor de fundo do gráfico
        ax.set_facecolor('#E3E3E3')

        # Estilizando o gráfico
        ax.plot(valores, marker='o', linestyle='-', color='#6e7587', linewidth=2, markersize=8)

        # Destacando o orçamento aprovado em verde escuro, se houver
        if indice_aprovado is not None and 0 <= indice_aprovado < len(valores):
            ax.plot(indice_aprovado, valores[indice_aprovado], marker='o', color='#006400', markersize=10)

        # Adicionando rótulos em cada ponto
        for i, valor in enumerate(valores):
            ax.text(i, valor, f'R$ {valor:,.2f}', fontsize=9, ha='right', va='bottom', color='black', fontweight='bold')

        # Títulos e rótulos com fontes personalizadas
        ax.set_xlabel('Orçamentos', fontsize=9, color='#333')
        ax.set_ylabel('Valor (R$)', fontsize=9, color='#333')
        ax.tick_params(axis='both', which='major', labelsize=10, colors='#333')

        # Adicionando uma linha de grade
        ax.grid(True, linestyle='--', alpha=0.7, color='gray', linewidth=1.2)  # Aumentando a largura da grade

        # Adicionando legenda
        ax.legend(loc='upper left', fontsize=10)

        # Ajustando o layout para melhor visualização
        plt.tight_layout()

        # Exibindo o gráfico no Tkinter
        for widget in frame_grafico.winfo_children():
            widget.destroy()  # Limpa o gráfico anterior

        canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def exibir_orcamentos_com_scroll(orcamentos):
        # Limpar a área de exibição anterior
        for widget in frame_orcamentos.winfo_children():
            widget.destroy()

        if orcamentos:
            # Criando o canvas e a barra de rolagem
            canvas = tk.Canvas(frame_orcamentos)
            scrollbar = ttk.Scrollbar(frame_orcamentos, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)

            # Criando o frame que conterá os orçamentos
            frame_interno = ttk.Frame(canvas)

            # Adicionando os orçamentos ao frame interno
            for i, (valor, fornecedor) in enumerate(orcamentos):
                ttk.Label(frame_interno, text=f"Orçamento {i+1}: R$ {valor:,.2f} - Fornecedor: {fornecedor}",
                          font=("Arial", 10)).grid(row=i, column=0, padx=5, pady=5, sticky="w")

            # Colocando o frame interno no canvas
            canvas.create_window((0, 0), window=frame_interno, anchor="nw")

            # Atualizando a área de rolagem
            frame_interno.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

            # Adicionando o canvas e a barra de rolagem ao frame principal
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")

            # Tornando a barra de rolagem visível
            scrollbar.config(command=canvas.yview)

            # Ajustar as expansões para o grid
            frame_orcamentos.grid_rowconfigure(0, weight=1)
            frame_orcamentos.grid_columnconfigure(0, weight=1)
        else:
            exibir_resultado("Nenhum orçamento encontrado.", "red")

    def calcular_economia(orcamento_aprovado, orcamentos):
        if not orcamento_aprovado or not orcamentos:
            label_economia.config(text="Não há dados suficientes.")
            return

        maior_orcamento = max(orcamentos)
        economia = ((maior_orcamento - orcamento_aprovado) / maior_orcamento) * 100
        label_economia.config(text=f"Economia: {economia:.2f}%")

    # Criando frames para organização
    frame_inputs = ttk.LabelFrame(root, text="Filtrar Orçamentos", padding=10)
    frame_inputs.place(x=20, y=20, width=460, height=120)

    frame_resultado = ttk.LabelFrame(root, padding=10)
    frame_resultado.place(x=20, y=160, width=460, height=100)

    # Aumentando o tamanho do frame que contém o gráfico
    frame_grafico = ttk.LabelFrame(root, text="Gráfico de Comparativo", padding=10)
    frame_grafico.place(x=20, y=280, width=460, height=460)  # Diminuindo a altura do frame que contém o gráfico

    # Criando frame para mostrar os orçamentos com rolagem
    frame_orcamentos = ttk.LabelFrame(root, text="Orçamentos Encontrados", padding=10)
    frame_orcamentos.place(x=20, y=160, width=460, height=100)

    # Ajustando a configuração de grid do frame_orcamentos para expandir corretamente
    frame_orcamentos.grid_rowconfigure(0, weight=1)
    frame_orcamentos.grid_columnconfigure(0, weight=1)

    # Criando frame para mostrar o orçamento aprovado
    frame_orcamento_aprovado = ttk.LabelFrame(root, padding=10)
    frame_orcamento_aprovado.place(x=490, y=20, width=250, height=120)  # Ao lado direito do frame_inputs

    label_orcamento_aprovado = ttk.Label(frame_orcamento_aprovado, text="", font=("Arial", 8, "bold"))
    label_orcamento_aprovado.pack(pady=20)

    frame_economia = ttk.LabelFrame(root, text="Economia", padding=10)
    frame_economia.place(x=490, y=160, width=250, height=80)  # Abaixo do orçamento aprovado

    label_economia = ttk.Label(frame_economia, text="", font=("Arial", 10, "bold"))
    label_economia.pack(pady=10)

    # Criando widgets dentro do frame de entrada
    label_data = ttk.Label(frame_inputs, text="Data:")
    label_data.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entry_data = ttk.Entry(frame_inputs, width=15)
    entry_data.grid(row=0, column=1, padx=5, pady=5)

    label_produto = ttk.Label(frame_inputs, text="Produto:")
    label_produto.grid(row=1, column=0, padx=5, pady=5, sticky="w")

    # Preencher a combobox com os produtos do banco
    produtos_disponiveis = carregar_produtos()
    combo_produto = ttk.Combobox(frame_inputs, values=produtos_disponiveis, state="readonly", width=27)
    combo_produto.grid(row=1, column=1, padx=5, pady=5)
    combo_produto.current(0)  # Define o primeiro item como padrão

    btn_carregar = ttk.Button(frame_inputs, text="Carregar", command=carregar_orcamentos)
    btn_carregar.grid(row=2, column=0, columnspan=2, pady=2)

    # Label de resultado dentro do frame de resultado
    label_resultado = ttk.Label(frame_resultado, text="", font=("Arial", 12, "bold"))
    label_resultado.pack()


root = tk.Tk()
root.title("Menu Principal")
root.geometry("300x350")
root.configure(bg="#dfdfdf")

title_label = tk.Label(root, text="ORÇAMENTOS - COMPRAS | GIMAVE", font=("Arial", 12, "bold"), bg="#dfdfdf", fg="#333333")
title_label.pack(pady=10)

tk.Button(root, text="ORÇAMENTOS", width=20, height=2, command=telaprincipal, bg="#72667c", fg="white").pack(pady=10)
tk.Button(root, text="CADASTRAR", width=20, height=2, command=cadastro, bg="#72667c", fg="white").pack(pady=10)
tk.Button(root, text="VALIDAÇÃO", width=20, height=2, command=validacao, bg="#72667c", fg="white").pack(pady=10)
tk.Button(root, text="DASHBOARD", width=20, height=2, command=dashboard, bg="#72667c", fg="white").pack(pady=10)
tk.Button(root, text="Sair", width=20, height=2, command=exit_program, bg="#d9534f", fg="white").pack(pady=10)

root.mainloop()
