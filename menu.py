import os
import shutil
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time
import threading

# ===== Variáveis globais do OCR =====
reader_ocr = None
ocr_pronto = False
ocr_usando_gpu = False  # ✅ Para armazenar se está usando GPU

def limpar_nome(nome):
    return "".join(c for c in nome if c not in r'<>:"/\|?*')

# ================== TELA DE CARREGAMENTO COM PROGRESSO ==================
def criar_tela_progresso(janela_pai, texto="Processando...", subtitulo=""):
    splash = tk.Toplevel(janela_pai)
    splash.title("Aguarde")
    splash.geometry("320x150")
    splash.resizable(False, False)

    tk.Label(splash, text=texto, font=("Arial", 12)).pack(pady=5)
    if subtitulo:
        tk.Label(splash, text=subtitulo, font=("Arial", 10), fg="gray").pack(pady=2)

    barra = ttk.Progressbar(splash, orient="horizontal", mode="determinate", length=280)
    barra.pack(pady=5)
    percentual_label = tk.Label(splash, text="0%", font=("Arial", 10))
    percentual_label.pack()

    splash.update()
    return splash, barra, percentual_label

def atualizar_progresso(splash, barra, percentual_label, atual, total):
    progresso = int((atual / total) * 100)
    barra["value"] = progresso
    percentual_label.config(text=f"{progresso}%")
    splash.update()

# ================== FUNÇÃO MOVER PASTAS E ARQUIVOS ==================
def mover_pastas_por_csv():
    root = tk.Tk()
    root.withdraw()

    arquivo_csv = filedialog.askopenfilename(
        title="Selecione o arquivo CSV",
        filetypes=[("Arquivos CSV", "*.csv")],
    )

    if not arquivo_csv:
        messagebox.showinfo("Cancelado", "Nenhum arquivo selecionado.")
        return

    try:
        df = pd.read_csv(arquivo_csv, sep=';')
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao ler CSV:\n{e}")
        return

    diretorio_base = os.path.dirname(os.path.abspath(arquivo_csv))

    splash, barra, percentual_label = criar_tela_progresso(janela, "Movendo pastas e arquivos...")
    total = len(df)
    inicio = time.time()

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        id_pasta = str(row['Id']).strip()
        nome_completo = limpar_nome(str(row['Name']).strip())

        nova_pasta_path = os.path.join(diretorio_base, nome_completo)
        if not os.path.exists(nova_pasta_path):
            os.makedirs(nova_pasta_path)

        # ✅ Mover pasta com o ID
        pasta_id_path = os.path.join(diretorio_base, id_pasta)
        if os.path.exists(pasta_id_path) and os.path.isdir(pasta_id_path):
            destino = os.path.join(nova_pasta_path, id_pasta)
            shutil.move(pasta_id_path, destino)
            print(f"✔️ Pasta movida: {id_pasta} → {nome_completo}/")
        else:
            print(f"⚠️ Pasta não encontrada: {id_pasta}")

        # ✅ Mover arquivos com o ID no início do nome
        for arquivo in os.listdir(diretorio_base):
            if arquivo.startswith(id_pasta) and os.path.isfile(os.path.join(diretorio_base, arquivo)):
                origem_arquivo = os.path.join(diretorio_base, arquivo)
                destino_arquivo = os.path.join(nova_pasta_path, arquivo)
                shutil.move(origem_arquivo, destino_arquivo)
                print(f"✔️ Arquivo movido: {arquivo} → {nome_completo}/")

        atualizar_progresso(splash, barra, percentual_label, i, total)

    splash.destroy()
    fim = time.time()
    tempo = round(fim - inicio, 2)
    messagebox.showinfo("Concluído", f"Processo finalizado!\nTempo total: {tempo}s")

# ================== FUNÇÃO RENOMEAR IMAGENS ==================
def renomear_imagens_por_id():
    import re
    import torch

    global reader_ocr, ocr_pronto, ocr_usando_gpu

    if not ocr_pronto:
        messagebox.showinfo("Aguarde", "O OCR ainda está inicializando, tente novamente em alguns segundos.")
        return

    pasta = filedialog.askdirectory(title="Selecione a pasta com imagens")
    if not pasta:
        messagebox.showinfo("Cancelado", "Nenhuma pasta selecionada.")
        return

    status_gpu = f"Usando {'GPU (CUDA)' if ocr_usando_gpu else 'CPU'}"
    print(status_gpu)
    if ocr_usando_gpu:
        print("Placa de vídeo:", torch.cuda.get_device_name(0))

    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.jpg', '.png'))]
    total = len(arquivos)
    inicio = time.time()

    splash, barra, percentual_label = criar_tela_progresso(janela, "Renomeando imagens...", status_gpu)

    for i, arquivo in enumerate(arquivos, start=1):
        caminho = os.path.join(pasta, arquivo)
        try:
            results = reader_ocr.readtext(caminho)
            texto_extraido = " ".join([res[1] for res in results])
            print(f"DEBUG OCR ({arquivo}):", texto_extraido)

            depois_id = re.search(r"JOGADOR\s*ID(.*)", texto_extraido, re.IGNORECASE)
            if depois_id:
                numeros = re.findall(r"\d{4,6}", depois_id.group(1))
                if numeros:
                    id_jogador = numeros[-1]
                    novo_nome = os.path.join(pasta, f"{id_jogador}.jpg")
                    os.rename(caminho, novo_nome)
                    print(f"✔️ Renomeado: {arquivo} → {id_jogador}.jpg")
                    atualizar_progresso(splash, barra, percentual_label, i, total)
                    continue

            print(f"⚠️ ID não encontrado em {arquivo}")

        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")

        atualizar_progresso(splash, barra, percentual_label, i, total)

    splash.destroy()
    fim = time.time()
    tempo = round(fim - inicio, 2)
    messagebox.showinfo("Concluído", f"Renomeação finalizada!\n{status_gpu}\nTempo total: {tempo}s")

# ================== TESTE CUDA AO INICIAR ==================
def teste_cuda_inicial():
    try:
        import torch
        if torch.cuda.is_available():
            messagebox.showinfo("CUDA Detectado",
                                f"Placa de vídeo: {torch.cuda.get_device_name(0)}\nCUDA ativo e pronto!")
        else:
            messagebox.showwarning("Sem CUDA",
                                   "Nenhuma GPU CUDA detectada.\nO processamento será feito na CPU.")
    except Exception as e:
        messagebox.showwarning("Aviso", f"Não foi possível verificar CUDA:\n{e}")

# ================== INICIALIZAR OCR EM SEGUNDO PLANO ==================
def inicializar_ocr_em_segundo_plano():
    global reader_ocr, ocr_pronto, ocr_usando_gpu, status_label
    try:
        import easyocr, torch
        ocr_usando_gpu = torch.cuda.is_available()
        status_label.config(text=f"OCR inicializando... (Usando {'GPU' if ocr_usando_gpu else 'CPU'})")
        print(f"Inicializando OCR em segundo plano... (Usando {'GPU' if ocr_usando_gpu else 'CPU'})")
        reader_ocr = easyocr.Reader(['pt', 'en'], gpu=ocr_usando_gpu)
        ocr_pronto = True
        status_label.config(text=f"OCR pronto! (Usando {'GPU' if ocr_usando_gpu else 'CPU'})")
        print("✅ EasyOCR carregado e pronto!")
    except Exception as e:
        status_label.config(text=f"Falha ao inicializar OCR")
        print(f"⚠️ Falha ao inicializar OCR: {e}")

# ================== MENU PRINCIPAL ==================
def sair():
    janela.quit()

janela = tk.Tk()
janela.title("Gerenciador de Pastas e Imagens")
janela.geometry("350x250")

label = tk.Label(janela, text="Escolha uma opção:", font=("Arial", 12))
label.pack(pady=10)

btn0 = tk.Button(janela, text="Mover pastas com base no CSV", command=mover_pastas_por_csv, width=30)
btn0.pack(pady=5)

btn1 = tk.Button(janela, text="Renomear imagens pelo ID do jogador", command=renomear_imagens_por_id, width=30)
btn1.pack(pady=5)

btn2 = tk.Button(janela, text="Sair", command=sair, width=30)
btn2.pack(pady=5)

# ✅ Status do OCR no rodapé
status_label = tk.Label(janela, text="OCR carregando...", font=("Arial", 9), fg="blue")
status_label.pack(pady=5)

# Inicializa OCR em segundo plano ao abrir o programa
threading.Thread(target=inicializar_ocr_em_segundo_plano, daemon=True).start()

janela.mainloop()
