import os
import shutil
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time
import threading
import logging
from pathlib import Path

# ===== Configuração de Logging =====
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===== Variáveis globais do OCR =====
reader_ocr = None
ocr_pronto = False
ocr_usando_gpu = False  # ✅ Para armazenar se está usando GPU

def limpar_nome(nome):
    """Remove caracteres inválidos para nomes de arquivos/pastas."""
    return "".join(c for c in nome if c not in r'<>:"/\|?*')

# ================== TELA DE CARREGAMENTO COM PROGRESSO ==================
def criar_tela_progresso(janela_pai, texto="Processando...", subtitulo=""):
    """Cria janela de progresso com melhor posicionamento."""
    splash = tk.Toplevel(janela_pai)
    splash.title("Aguarde")
    splash.geometry("400x180")
    splash.resizable(False, False)
    
    # Centralizar janela
    splash.transient(janela_pai)
    splash.grab_set()

    tk.Label(splash, text=texto, font=("Arial", 12, "bold")).pack(pady=10)
    if subtitulo:
        tk.Label(splash, text=subtitulo, font=("Arial", 10), fg="gray").pack(pady=2)

    barra = ttk.Progressbar(splash, orient="horizontal", mode="determinate", length=350)
    barra.pack(pady=10)
    percentual_label = tk.Label(splash, text="0%", font=("Arial", 10, "bold"))
    percentual_label.pack()

    splash.update()
    return splash, barra, percentual_label

def atualizar_progresso(splash, barra, percentual_label, atual, total, status=""):
    """Atualiza progresso com status opcional."""
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
        # Validar se tem as colunas necessárias
        if 'Id' not in df.columns or 'Name' not in df.columns:
            messagebox.showerror("Erro", "CSV deve conter as colunas 'Id' e 'Name'")
            return
        if df.empty:
            messagebox.showerror("Erro", "CSV está vazio")
            return
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao ler CSV:\n{e}")
        return

    diretorio_base = Path(arquivo_csv).parent

    splash, barra, percentual_label = criar_tela_progresso(janela, "Movendo pastas e arquivos...")
    total = len(df)
    inicio = time.time()

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        id_pasta = str(row['Id']).strip()
        nome_completo = limpar_nome(str(row['Name']).strip())

        nova_pasta_path = diretorio_base / nome_completo
        nova_pasta_path.mkdir(exist_ok=True)

        # ✅ Mover pasta com o ID
        pasta_id_path = diretorio_base / id_pasta
        if pasta_id_path.exists() and pasta_id_path.is_dir():
            destino = nova_pasta_path / id_pasta
            shutil.move(str(pasta_id_path), str(destino))
            logging.info(f"✔️ Pasta movida: {id_pasta} → {nome_completo}/")
        else:
            logging.warning(f"⚠️ Pasta não encontrada: {id_pasta}")

        # ✅ Mover arquivos com o ID no início do nome
        for arquivo in diretorio_base.iterdir():
            if arquivo.is_file() and arquivo.name.startswith(id_pasta):
                destino_arquivo = nova_pasta_path / arquivo.name
                shutil.move(str(arquivo), str(destino_arquivo))
                logging.info(f"✔️ Arquivo movido: {arquivo.name} → {nome_completo}/")

        atualizar_progresso(splash, barra, percentual_label, i, total, f"Processando: {nome_completo}")

    splash.destroy()
    fim = time.time()
    tempo = round(fim - inicio, 2)
    messagebox.showinfo("Concluído", f"Processo finalizado!\nTempo total: {tempo}s")

# ================== FUNÇÃO MOVER PASTAS APENAS SE EXISTIREM ==================
def mover_pastas_por_csv_se_existir():
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
        # Validar se tem as colunas necessárias
        if 'Id' not in df.columns or 'Name' not in df.columns:
            messagebox.showerror("Erro", "CSV deve conter as colunas 'Id' e 'Name'")
            return
        if df.empty:
            messagebox.showerror("Erro", "CSV está vazio")
            return
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao ler CSV:\n{e}")
        return

    diretorio_base = Path(arquivo_csv).parent

    splash, barra, percentual_label = criar_tela_progresso(janela, "Movendo pastas existentes...")
    total = len(df)
    inicio = time.time()
    pastas_movidas = 0
    pastas_nao_encontradas = 0

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        id_pasta = str(row['Id']).strip()
        nome_completo = limpar_nome(str(row['Name']).strip())

        # ✅ Verificar se a pasta com ID existe antes de tentar mover
        pasta_id_path = diretorio_base / id_pasta
        if pasta_id_path.exists() and pasta_id_path.is_dir():
            nova_pasta_path = diretorio_base / nome_completo
            nova_pasta_path.mkdir(exist_ok=True)

            destino = nova_pasta_path / id_pasta
            shutil.move(str(pasta_id_path), str(destino))
            logging.info(f"✔️ Pasta movida: {id_pasta} → {nome_completo}/")
            pastas_movidas += 1

            # ✅ Mover arquivos com o ID no início do nome
            for arquivo in diretorio_base.iterdir():
                if arquivo.is_file() and arquivo.name.startswith(id_pasta):
                    destino_arquivo = nova_pasta_path / arquivo.name
                    shutil.move(str(arquivo), str(destino_arquivo))
                    logging.info(f"✔️ Arquivo movido: {arquivo.name} → {nome_completo}/")
        else:
            logging.warning(f"⚠️ Pasta não encontrada: {id_pasta}")
            pastas_nao_encontradas += 1

        atualizar_progresso(splash, barra, percentual_label, i, total, f"Processando: {nome_completo}")

    splash.destroy()
    fim = time.time()
    tempo = round(fim - inicio, 2)
    messagebox.showinfo("Concluído", 
                       f"Processo finalizado!\n"
                       f"Pastas movidas: {pastas_movidas}\n"
                       f"Pastas não encontradas: {pastas_nao_encontradas}\n"
                       f"Tempo total: {tempo}s")

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

    pasta_path = Path(pasta)
    arquivos = [f for f in pasta_path.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    total = len(arquivos)
    inicio = time.time()

    splash, barra, percentual_label = criar_tela_progresso(janela, "Renomeando imagens...", status_gpu)

    for i, arquivo in enumerate(arquivos, start=1):
        caminho = str(arquivo)
        try:
            results = reader_ocr.readtext(caminho)
            texto_extraido = " ".join([res[1] for res in results])
            logging.debug(f"DEBUG OCR ({arquivo.name}): {texto_extraido}")

            depois_id = re.search(r"JOGADOR\s*ID(.*)", texto_extraido, re.IGNORECASE)
            if depois_id:
                numeros = re.findall(r"\d{4,6}", depois_id.group(1))
                if numeros:
                    id_jogador = numeros[-1]
                    novo_nome = pasta_path / f"{id_jogador}.jpg"
                    # Evitar sobrescrever arquivo existente
                    if novo_nome.exists() and novo_nome != arquivo:
                        contador = 1
                        while novo_nome.exists():
                            novo_nome = pasta_path / f"{id_jogador}_{contador}.jpg"
                            contador += 1
                    arquivo.rename(novo_nome)
                    logging.info(f"✔️ Renomeado: {arquivo.name} → {novo_nome.name}")
                    atualizar_progresso(splash, barra, percentual_label, i, total, f"Renomeado: {arquivo.name}")
                    continue

            logging.warning(f"⚠️ ID não encontrado em {arquivo.name}")

        except Exception as e:
            logging.error(f"Erro ao processar {arquivo.name}: {e}")

        atualizar_progresso(splash, barra, percentual_label, i, total, f"Processando: {arquivo.name}")

    splash.destroy()
    fim = time.time()
    tempo = round(fim - inicio, 2)
    messagebox.showinfo("Concluído", f"Renomeação finalizada!\n{status_gpu}\nTempo total: {tempo}s")

# ================== FUNÇÃO ORGANIZAR ARQUIVOS POR PREFIXO ==================
def organizar_arquivos_por_prefixo():
    """Organiza arquivos por prefixo (antes do underscore) criando pastas automaticamente."""
    pasta = filedialog.askdirectory(title="Selecione a pasta com arquivos para organizar")
    if not pasta:
        messagebox.showinfo("Cancelado", "Nenhuma pasta selecionada.")
        return

    pasta_path = Path(pasta)
    arquivos = [f for f in pasta_path.iterdir() if f.is_file() and '_' in f.name]
    
    if not arquivos:
        messagebox.showinfo("Informação", "Nenhum arquivo com underscore encontrado para organizar.")
        return

    splash, barra, percentual_label = criar_tela_progresso(janela, "Organizando arquivos por prefixo...")
    total = len(arquivos)
    inicio = time.time()
    arquivos_movidos = 0

    for i, arquivo in enumerate(arquivos, start=1):
        try:
            # Extrair prefixo (parte antes do primeiro underscore)
            nome_arquivo = arquivo.name
            prefixo = nome_arquivo.split('_')[0]
            
            # Criar pasta para o prefixo se não existir
            pasta_destino = pasta_path / prefixo
            pasta_destino.mkdir(exist_ok=True)
            
            # Mover arquivo para a pasta do prefixo
            destino = pasta_destino / nome_arquivo
            shutil.move(str(arquivo), str(destino))
            arquivos_movidos += 1
            
            logging.info(f"✔️ Arquivo movido: {nome_arquivo} → {prefixo}/")
            atualizar_progresso(splash, barra, percentual_label, i, total, f"Movendo: {nome_arquivo}")
            
        except Exception as e:
            logging.error(f"Erro ao processar {arquivo.name}: {e}")

    splash.destroy()
    fim = time.time()
    tempo = round(fim - inicio, 2)
    messagebox.showinfo("Concluído", 
                       f"Organização finalizada!\n"
                       f"Arquivos movidos: {arquivos_movidos}\n"
                       f"Tempo total: {tempo}s")

# ================== FUNÇÃO LISTAR PASTAS EM ARQUIVO TXT ==================
def listar_pastas_em_txt():
    """Lista todas as pastas existentes em um arquivo .txt."""
    pasta = filedialog.askdirectory(title="Selecione a pasta para listar as subpastas")
    if not pasta:
        messagebox.showinfo("Cancelado", "Nenhuma pasta selecionada.")
        return

    pasta_path = Path(pasta)
    subpastas = [d for d in pasta_path.iterdir() if d.is_dir()]
    
    if not subpastas:
        messagebox.showinfo("Informação", "Nenhuma subpasta encontrada.")
        return

    # Criar arquivo de lista
    arquivo_lista = pasta_path / "lista_pastas.txt"
    
    try:
        with open(arquivo_lista, 'w', encoding='utf-8') as f:
            for subpasta in subpastas:
                f.write(f"{subpasta.name}\n")
        
        messagebox.showinfo("Concluído", 
                           f"Lista de pastas gerada com sucesso!\n"
                           f"Arquivo: {arquivo_lista.name}\n"
                           f"Total de pastas: {len(subpastas)}")
        
        logging.info(f"✔️ Lista de pastas gerada: {arquivo_lista.name} com {len(subpastas)} pastas")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao gerar lista de pastas:\n{e}")
        logging.error(f"Erro ao gerar lista: {e}")

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
janela.title("Gerenciador de Pastas e Imagens v2.0")
janela.geometry("420x500")

# Centralizar janela
janela.update_idletasks()
x = (janela.winfo_screenwidth() // 2) - (420 // 2)
y = (janela.winfo_screenheight() // 2) - (500 // 2)
janela.geometry(f"420x500+{x}+{y}")

# Frame principal com scrollbar
main_frame = tk.Frame(janela)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Canvas para scroll
canvas = tk.Canvas(main_frame)
scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# Título principal
label = tk.Label(scrollable_frame, text="Gerenciador de Pastas e Imagens v2.0", font=("Arial", 14, "bold"), fg="darkblue")
label.pack(pady=15)

subtitle = tk.Label(scrollable_frame, text="Escolha uma opção:", font=("Arial", 10), fg="gray")
subtitle.pack(pady=5)

btn0 = tk.Button(scrollable_frame, text="📁 Mover pastas e criar nova com base no CSV", command=mover_pastas_por_csv, width=35, height=2, font=("Arial", 10), bg="lightblue")
btn0.pack(pady=8)

btn0_1 = tk.Button(scrollable_frame, text="📁 Mover apenas pastas existentes (CSV)", command=mover_pastas_por_csv_se_existir, width=35, height=2, font=("Arial", 10), bg="lightcyan")
btn0_1.pack(pady=8)

btn1 = tk.Button(scrollable_frame, text="🖼️ Renomear imagens pelo ID do jogador", command=renomear_imagens_por_id, width=35, height=2, font=("Arial", 10), bg="lightgreen")
btn1.pack(pady=8)

btn2 = tk.Button(scrollable_frame, text="⚡ Testar CUDA/GPU", command=teste_cuda_inicial, width=35, height=2, font=("Arial", 10), bg="lightyellow")
btn2.pack(pady=8)

btn3 = tk.Button(scrollable_frame, text="🗂️ Organizar arquivos por prefixo", command=organizar_arquivos_por_prefixo, width=35, height=2, font=("Arial", 10), bg="lightcoral")
btn3.pack(pady=8)

btn4 = tk.Button(scrollable_frame, text="📋 Listar pastas em TXT", command=listar_pastas_em_txt, width=35, height=2, font=("Arial", 10), bg="plum")
btn4.pack(pady=8)

btn5 = tk.Button(scrollable_frame, text="❌ Sair", command=sair, width=35, height=2, font=("Arial", 10), bg="lightcoral")
btn5.pack(pady=8)

# ✅ Status do OCR no rodapé
status_label = tk.Label(scrollable_frame, text="OCR carregando...", font=("Arial", 10), fg="blue")
status_label.pack(pady=10)

# Informações do sistema
info_label = tk.Label(scrollable_frame, text="Versão 2.1 | Novas ferramentas: Organização por prefixo e Lista de pastas", font=("Arial", 8), fg="gray")
info_label.pack(pady=5)

# Empacotar canvas e scrollbar
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Configurar scroll com mouse
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Inicializa OCR em segundo plano ao abrir o programa
threading.Thread(target=inicializar_ocr_em_segundo_plano, daemon=True).start()

janela.mainloop()
