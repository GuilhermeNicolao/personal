import os
import shutil
import subprocess

# Nome do script e ícone
script_nome = "final.py"
icone = os.path.abspath("icone.ico")  # Caminho absoluto do ícone

# Criar um diretório de saída separado para evitar conflito
output_dir = "orcamento_compras"
os.makedirs(output_dir, exist_ok=True)

# Comando para gerar o executável de forma mais segura
cmd = [
    "pyinstaller",
    "--onedir",  # Evita compactação total para reduzir chances de bloqueio
    "--noconsole",  # Mantém sem console, mas pode ser removido se necessário
    "--clean",  # Remove arquivos temporários
    f"--icon={icone}",  # Define o ícone com caminho absoluto
    f"--distpath={output_dir}",  # Define o diretório de saída
    "--add-data", f"{icone};.",  # Garante que o ícone seja incluído com caminho absoluto
    script_nome,
]

# Executa o comando no terminal
subprocess.run(cmd, shell=True)

# Remover pastas desnecessárias para reduzir tamanho final
for pasta in ["build", "__pycache__"]:
    if os.path.exists(pasta):
        shutil.rmtree(pasta)  # Exclui as pastas "build" e "__pycache__"

# Exibe a localização do executável final
exe_path = os.path.abspath(os.path.join(output_dir, "final"))
print(f"Executável gerado com sucesso em: {exe_path}")
