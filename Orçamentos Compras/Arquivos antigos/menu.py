import tkinter as tk
from tkinter import messagebox
import os
import sys
import subprocess

# Função para obter o diretório onde o script está localizado
def get_script_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)  # Diretório do executável
    return os.path.dirname(os.path.abspath(__file__))  # Diretório do script

# Diretório do script
script_dir = get_script_directory()

def run_script(script_name):
    script_path = os.path.join(script_dir, script_name)
    if not os.path.exists(script_path):
        messagebox.showerror("Erro", f"O arquivo {script_name} não foi encontrado.")
        return
    try:
        if getattr(sys, 'frozen', False):  # Se for um .exe gerado pelo PyInstaller
            subprocess.Popen([script_path], shell=True)  
        else:
            subprocess.Popen([sys.executable, script_path])  
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir {script_name}: {e}")

def open_cadastro():
    run_script("cadastros.py")

def open_orcamentos():
    run_script("telaprincipal.py")

def open_validacao():
    run_script("validacao.py")

def open_dash():
    run_script("dash.py")

def exit_program():
    """Função para fechar o programa"""
    root.quit()

# Criando a tela de menu
root = tk.Tk()
root.title("Menu Principal")
root.geometry("300x350")  # Aumentei a altura da janela para dar espaço para o novo botão
root.configure(bg="#dfdfdf")

# Adicionando o título
title_label = tk.Label(root, text="ORÇAMENTOS - COMPRAS | GIMAVE", font=("Arial", 12, "bold"), bg="#dfdfdf", fg="#333333")
title_label.pack(pady=10)

# Adicionando os botões
button_orcamentos = tk.Button(root, text="ORÇAMENTOS", width=20, height=2, command=open_orcamentos, bg="#72667c", fg="white")
button_orcamentos.pack(pady=10)

button_cadastrar = tk.Button(root, text="CADASTRAR", width=20, height=2, command=open_cadastro, bg="#72667c", fg="white")
button_cadastrar.pack(pady=10)

button_validacao = tk.Button(root, text="VALIDAÇÃO", width=20, height=2, command=open_validacao, bg="#72667c", fg="white")
button_validacao.pack(pady=10)

button_dash = tk.Button(root, text="DASHBOARD", width=20, height=2, command=open_dash, bg="#72667c", fg="white")
button_dash.pack(pady=10)  # Novo botão para abrir o dash.py

# Adicionando o botão de sair
button_exit = tk.Button(root, text="Sair", width=20, height=2, command=exit_program, bg="#d9534f", fg="white")
button_exit.pack(pady=10)

# Iniciando o loop da interface
root.mainloop()
