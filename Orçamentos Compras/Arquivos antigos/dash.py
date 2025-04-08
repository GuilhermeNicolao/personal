import mysql.connector
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import locale
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

root.mainloop()
