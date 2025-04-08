import os
import requests
import time
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


def iniciar_script():
    global last_processed_row
    valor = entry.get()
    if not valor.isdigit():
        messagebox.showerror("Erro", "Digite um número válido!")
        return
    
    last_processed_row = int(valor)
    root.destroy() 
    executar_script()


def executar_script():
    global last_processed_row
    load_dotenv()
    id_value = os.getenv("ID")

    url = f"https://script.google.com/a/macros/angelscapital.com.br/s/{id_value}/exec"
    driver = webdriver.Chrome()
    driver.get("https://fomento.eucard.com.br/transferencias")

    time.sleep(3)  

    #LOGIN
    cpf_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='CPF *']")))
    cpf_field.click() 
    cpf_field.send_keys(os.getenv("CPF"))  

    #SENHA
    senha_field = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Senha *']")))
    senha_field.click() 
    senha_field.send_keys(os.getenv("SENHA"))

    time.sleep(1)

    #ENTRAR
    entrar_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.q-btn__content.text-center")))
    entrar_button.click()

    time.sleep(1)

    #ABRIR MENU
    menu_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'toolbar__hamburguer')]")))
    menu_button.click()

    time.sleep(1)

    #CLICAR NO "EUCARD"
    eucard_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'q-item') and contains(., 'Eucard')]")))
    eucard_button.click()

    time.sleep(1)

    #CLICAR NO "TRANSFERÊNCIAS"
    transferencias_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/transferencias' and contains(@class, 'menu__item')]")))
    transferencias_link.click()

    time.sleep(15)

    #CLICAR NA SETA
    dropdown_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//i[contains(@class, 'q-select__dropdown-icon')]")))
    dropdown_button.click()

    #CLICAR NO 100
    item_100 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='q-item__label' and text()='100']")))
    item_100.click()
    

    def exibir_popup_erro(mensagem):
        root = tk.Tk()
        root.withdraw()  # Oculta a janela principal
        messagebox.showerror("Erro de Leitura", mensagem)
        root.destroy()

    def ler_celula(cell):
        params = {"action": "read", "cell": cell}
        response = requests.get(url, params=params)
        
        try:
            response = requests.get(url, params=params, timeout=10)  # Define um timeout de 10 segundos

            if response.status_code == 200:
                data = response.json()
                return data.get("value", None)
            
            elif response.status_code == 400:
                mensagem_erro = f"Erro 400: Solicitação inválida.\nVerifique se a célula '{cell}' está escrita corretamente."
            
            elif response.status_code == 404:
                mensagem_erro = f"Erro 404: A célula '{cell}' não foi encontrada.\nPode ser um problema com a planilha ou a API."

            elif response.status_code == 500:
                mensagem_erro = "Erro 500: Erro interno do servidor.\nTente novamente mais tarde."

            else:
                mensagem_erro = f"Erro inesperado ({response.status_code}): {response.text}"
            
        except requests.ConnectionError:
            mensagem_erro = "Erro de conexão: Verifique sua conexão com a internet."
        
        except requests.Timeout:
            mensagem_erro = "Erro de timeout: O servidor demorou muito para responder."
        
        except Exception as e:
            mensagem_erro = f"Erro desconhecido: {str(e)}"

        exibir_popup_erro(mensagem_erro)
        return None

    def escrever_celula(cell, value):
        params = {"action": "write", "cell": cell, "value": value}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"célula {cell}")
        else:
            print(f"Erro ao escrever na célula {cell}: {response.status_code} - {response.text}")


    while True:

        rows_to_process = []  # Lista para armazenar as linhas com status "PROCESSANDO"

        for row in range(last_processed_row, 1000):
            cell_a = f"A{row}"
            value_a = ler_celula(cell_a)

            if not value_a or value_a.strip() == "":
                print("Fim da planilha. Encerrando...")
                exit()

            cell_h = f"H{row}"
            value_h = ler_celula(cell_h)

            if value_h.strip().upper() == "PROCESSANDO":
                rows_to_process.append(row)  

            if len(rows_to_process) >= 3:  # Se encontrou 3 linhas "PROCESSANDO", interrompe a busca
                break

        if len(rows_to_process) == 0:
            print("Nenhuma transferência com status 'PROCESSANDO' encontrada. Encerrando...")
            break
        

        for row in rows_to_process:

            cell_a = f"A{row}"
            value_a = ler_celula(cell_a)

            cell_h = f"H{row}"
            value_h = ler_celula(cell_h)

            cell_b = f"B{row}"
            value_b = ler_celula(cell_b)

            cell_f = f"f{row}"
            value_f = ler_celula(cell_f)


            try:
                #CAPTURAR NOME PAINELFOMENTO
                xpathnome = f"//td[@class='text-left' and contains(text(), '{value_a}')]"
                nome_td = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpathnome)))
                nome = nome_td.text

                #CAPTURAR NÚMERO CARTAO
                tdnumerocartao = f"//td[@class='text-left' and contains(text(), '{value_a}')]/following-sibling::td[contains(text(), '{value_b}')]"
                td_centro = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, tdnumerocartao)))
                numero_td = td_centro.text

                #CAPTURAR O FAVORECIDO
                xpath_td_nome = f"//td[@class='text-center' and contains(text(), '{value_f}')]"
                td_nome = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath_td_nome)))
                favorecido = td_nome.text



                #CAPTURAR BOTÃO DE SELECIONAR
                botaoselecionar = xpathnome + "/preceding-sibling::td[1]//div[contains(@class, 'q-toggle')]"
                botao1 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, botaoselecionar)))
                #CLICAR NO BOTÃO
                actions = ActionChains(driver)
                actions.move_to_element(botao1).click().perform()

                #print(f"Nome capturado na linha {row}: {nome}, Número capturado: {numero_td}, Favorecido capturado: {favorecido}")

                cell_h = f"H{row}"
                escrever_celula(cell_h, "LIBERADO")

                #print("Nome capturado:", nome)
            except Exception as e:
                print(f"Erro ao buscar o nome na linha {row}: {str(e)}")

        last_processed_row = rows_to_process[-1] + 1 

        time.sleep(3)


        try:
            #ENVIAR TRANSFERÊNCIAS SELECIONADAS
            botaotransferencias = "//span[contains(@class, 'q-btn__content') and span[text()='Enviar Transferências Selecionadas']]"
            botao2 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, botaotransferencias)))
            #CLICAR NO BOTÃO
            actions = ActionChains(driver)
            actions.move_to_element(botao2).click().perform()
            #print("Botão 'Enviar Transferências Selecionadas' clicado com sucesso!")


            time.sleep(2)


            #ENVIAR
            botao_enviar = "//span[@class='block' and text()='Enviar']"
            botao3 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, botao_enviar)))
            #CLICAR NO BOTÃO
            actions = ActionChains(driver)
            actions.move_to_element(botao3).click().perform()

        except Exception as e:
                print(f"Erro ao clicar no botão de transferências: {str(e)}")


        time.sleep(15)


# Interface
root = tk.Tk()
root.title("Liberação de TEDS")
root.geometry("300x150")
root.configure(bg="gray")

label = tk.Label(root, text="Digite a célula inicial:", bg="gray", fg="white")
label.pack(pady=5)

entry = tk.Entry(root)
entry.pack(pady=5)

botao = tk.Button(root, text="Iniciar", command=iniciar_script, bg="darkgray", fg="white")
botao.pack(pady=10)

root.mainloop()