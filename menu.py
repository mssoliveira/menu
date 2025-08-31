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

            depois_id = re.search(r"JOGADOR\s*ID\s*=?\s*(\d+)", texto_extraido, re.IGNORECASE)
            if depois_id:
                id_jogador = depois_id.group(1)
                # Manter a extensão original do arquivo
                extensao = arquivo.suffix.lower()
                novo_nome = pasta_path / f"{id_jogador}{extensao}"
                # Evitar sobrescrever arquivo existente
                if novo_nome.exists():
                    contador = 1
                    while novo_nome.exists():
                        novo_nome = pasta_path / f"{id_jogador}_{contador}{extensao}"
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

# ================== FUNÇÃO MOVER FACES POR FPK ==================
def mover_faces_por_fpk():
    """Busca face.fpk em todas as pastas da parte 1, extrai nome do jogador e move arquivos da parte 2."""
    
    logging.info("🚀 Iniciando função mover_faces_por_fpk")
    
    # Selecionar diretório da parte 1 (faces)
    diretorio_faces = filedialog.askdirectory(title="Selecione o diretório da PARTE 1 (onde estão as faces)")
    if not diretorio_faces:
        logging.info("❌ Nenhum diretório de faces selecionado - operação cancelada")
        messagebox.showinfo("Cancelado", "Nenhum diretório de faces selecionado.")
        return
    
    logging.info(f"📁 Diretório PARTE 1 selecionado: {diretorio_faces}")
    
    # Selecionar diretório da parte 2 (arquivos)
    diretorio_arquivos = filedialog.askdirectory(title="Selecione o diretório da PARTE 2 (onde estão os arquivos)")
    if not diretorio_arquivos:
        logging.info("❌ Nenhum diretório de arquivos selecionado - operação cancelada")
        messagebox.showinfo("Cancelado", "Nenhum diretório de arquivos selecionado.")
        return
    
    logging.info(f"📁 Diretório PARTE 2 selecionado: {diretorio_arquivos}")
    
    diretorio_faces_path = Path(diretorio_faces)
    diretorio_arquivos_path = Path(diretorio_arquivos)
    
    # Buscar todas as pastas que contêm face.fpk (busca recursiva em subdiretórios)
    pastas_com_face = []
    total_diretorios_verificados = 0
    
    def buscar_face_fpk_recursivo(diretorio):
        """Função recursiva para buscar face.fpk em todos os subdiretórios"""
        nonlocal total_diretorios_verificados
        for item in diretorio.iterdir():
            if item.is_dir():
                total_diretorios_verificados += 1
                # Verificar se esta pasta contém face.fpk
                face_fpk = item / "face.fpk"
                if face_fpk.exists():
                    pastas_com_face.append(item)
                    logging.info(f"✅ face.fpk encontrado em: {item}")
                # Continuar buscando em subdiretórios
                buscar_face_fpk_recursivo(item)
    
    logging.info("🔍 Iniciando busca recursiva por face.fpk...")
    # Iniciar busca recursiva
    buscar_face_fpk_recursivo(diretorio_faces_path)
    
    logging.info(f"📊 Resumo da busca: {len(pastas_com_face)} pastas com face.fpk encontradas em {total_diretorios_verificados} diretórios verificados")
    
    if not pastas_com_face:
        logging.warning("⚠️ Nenhuma pasta com face.fpk encontrada na parte 1")
        messagebox.showinfo("Informação", "Nenhuma pasta com face.fpk encontrada na parte 1.")
        return
    
    splash, barra, percentual_label = criar_tela_progresso(janela, "Processando faces...", "Buscando e movendo arquivos")
    total = len(pastas_com_face)
    inicio = time.time()
    
    logging.info(f"🔄 Iniciando processamento de {total} pastas com face.fpk")
    
    faces_processadas = 0
    arquivos_movidos = 0
    erros = 0
    total_itens_ignorados = 0
    
    for i, pasta_face in enumerate(pastas_com_face, start=1):
        try:
            logging.info(f"🔍 Processando pasta {i}/{total}: {pasta_face.name}")
            
            # Ler o arquivo face.fpk
            face_fpk_path = pasta_face / "face.fpk"
            logging.info(f"📄 Lendo arquivo: {face_fpk_path}")
            
            # Buscar pela linha que contém 'Assets/pes16/model/character/face/real/'
            nome_jogador = None
            linhas_lidas = 0
            try:
                with open(face_fpk_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for linha in f:
                        linhas_lidas += 1
                        if 'Assets/pes16/model/character/face/real/' in linha:
                            # Extrair o nome do jogador após 'real/'
                            partes = linha.split('Assets/pes16/model/character/face/real/')
                            if len(partes) > 1:
                                nome_jogador = partes[1].strip().split('/')[0].strip()
                                logging.info(f"🎯 Nome do jogador encontrado: '{nome_jogador}' na linha {linhas_lidas}")
                                break
                
                if not nome_jogador:
                    logging.warning(f"⚠️ Nome do jogador não encontrado em {pasta_face.name} após ler {linhas_lidas} linhas")
                    continue
                    
            except Exception as e:
                logging.warning(f"⚠️ Erro ao ler face.fpk em {pasta_face.name}: {e}")
                continue
            
            # Buscar pasta do jogador na parte 2
            pasta_jogador = diretorio_arquivos_path / nome_jogador
            logging.info(f"🔍 Procurando pasta do jogador: {pasta_jogador}")
            
            if not pasta_jogador.exists() or not pasta_jogador.is_dir():
                logging.warning(f"⚠️ Pasta do jogador '{nome_jogador}' não encontrada na parte 2")
                continue
            
            logging.info(f"✅ Pasta do jogador encontrada: {pasta_jogador}")
            
            # Mover todo o conteúdo da pasta do jogador para o mesmo diretório onde está a pasta ID (não dentro dela)
            diretorio_destino = pasta_face.parent  # Diretório pai da pasta ID
            logging.info(f"📁 Diretório de destino: {diretorio_destino}")
            
            arquivos_movidos_pasta = 0
            pastas_movidas_pasta = 0
            itens_ignorados = 0
            
            # Processar todos os itens (arquivos e pastas) dentro da pasta do jogador
            for item in pasta_jogador.iterdir():
                destino = diretorio_destino / item.name
                
                # Verificar se o item já existe - se existir, não copiar
                if destino.exists():
                    logging.info(f"⏭️ Item já existe, ignorando: {item.name}")
                    itens_ignorados += 1
                    continue
                
                try:
                    if item.is_file():
                        # Copiar arquivo
                        shutil.copy2(str(item), str(destino))
                        arquivos_movidos_pasta += 1
                        logging.info(f"📋 Arquivo copiado: {item.name} → {destino.name}")
                    elif item.is_dir():
                        # Copiar pasta inteira com seu conteúdo
                        shutil.copytree(str(item), str(destino))
                        pastas_movidas_pasta += 1
                        logging.info(f"📁 Pasta copiada: {item.name} → {destino.name}")
                        
                except Exception as e:
                    logging.error(f"❌ Erro ao copiar {item.name}: {e}")
            
            total_itens = arquivos_movidos_pasta + pastas_movidas_pasta
            if total_itens > 0:
                arquivos_movidos += arquivos_movidos_pasta
                faces_processadas += 1
                logging.info(f"✅ {pasta_face.name}: {arquivos_movidos_pasta} arquivos e {pastas_movidas_pasta} pastas movidos para {diretorio_destino}")
                if itens_ignorados > 0:
                    logging.info(f"⏭️ {itens_ignorados} itens ignorados por já existirem")
                    total_itens_ignorados += itens_ignorados
            else:
                if itens_ignorados > 0:
                    logging.warning(f"⚠️ {pasta_face.name}: Todos os {itens_ignorados} itens já existem, nada foi movido")
                    total_itens_ignorados += itens_ignorados
                else:
                    logging.warning(f"⚠️ {pasta_face.name}: Nenhum item movido de '{nome_jogador}'")
            
        except Exception as e:
            logging.error(f"❌ Erro ao processar {pasta_face.name}: {e}")
            erros += 1
        
        atualizar_progresso(splash, barra, percentual_label, i, total, f"Processando: {pasta_face.name}")
    
    splash.destroy()
    fim = time.time()
    tempo = round(fim - inicio, 2)
    
    # Log final detalhado
    logging.info("=" * 60)
    logging.info("📊 RESUMO FINAL DO PROCESSAMENTO")
    logging.info("=" * 60)
    logging.info(f"🔍 Total de diretórios verificados: {total_diretorios_verificados}")
    logging.info(f"📁 Total de pastas com face.fpk encontradas: {len(pastas_com_face)}")
    logging.info(f"✅ Faces processadas com sucesso: {faces_processadas}")
    logging.info(f"📋 Total de arquivos movidos: {arquivos_movidos}")
    logging.info(f"⏭️ Total de itens ignorados (já existiam): {total_itens_ignorados}")
    logging.info(f"❌ Erros encontrados: {erros}")
    logging.info(f"⏱️ Tempo total de processamento: {tempo}s")
    logging.info("=" * 60)
    
    messagebox.showinfo("Concluído", 
                       f"Processo de faces finalizado!\n"
                       f"Faces processadas: {faces_processadas}\n"
                       f"Total de arquivos movidos: {arquivos_movidos}\n"
                       f"Erros encontrados: {erros}\n"
                       f"Tempo total: {tempo}s")
    
    logging.info(f"✅ Processo de faces concluído: {faces_processadas} faces, {arquivos_movidos} arquivos movidos em {tempo}s")

# ================== FUNÇÃO MOVER PASTA COMPLETA POR FPK ==================
def mover_pasta_completa_por_fpk():
    """Busca face.fpk em todas as pastas da parte 1, extrai nome do jogador e move a pasta completa da parte 2."""
    
    logging.info("🚀 Iniciando função mover_pasta_completa_por_fpk")
    
    # Selecionar diretório da parte 1 (faces)
    diretorio_faces = filedialog.askdirectory(title="Selecione o diretório da PARTE 1 (onde estão as faces)")
    if not diretorio_faces:
        logging.info("❌ Nenhum diretório de faces selecionado - operação cancelada")
        messagebox.showinfo("Cancelado", "Nenhum diretório de faces selecionado.")
        return
    
    logging.info(f"📁 Diretório PARTE 1 selecionado: {diretorio_faces}")
    
    # Selecionar diretório da parte 2 (arquivos)
    diretorio_arquivos = filedialog.askdirectory(title="Selecione o diretório da PARTE 2 (onde estão os arquivos)")
    if not diretorio_arquivos:
        logging.info("❌ Nenhum diretório de arquivos selecionado - operação cancelada")
        messagebox.showinfo("Cancelado", "Nenhum diretório de arquivos selecionado.")
        return
    
    logging.info(f"📁 Diretório PARTE 2 selecionado: {diretorio_arquivos}")
    
    diretorio_faces_path = Path(diretorio_faces)
    diretorio_arquivos_path = Path(diretorio_arquivos)
    
    # Buscar todas as pastas que contêm face.fpk (busca recursiva em subdiretórios)
    pastas_com_face = []
    total_diretorios_verificados = 0
    
    def buscar_face_fpk_recursivo(diretorio):
        """Função recursiva para buscar face.fpk em todos os subdiretórios"""
        nonlocal total_diretorios_verificados
        for item in diretorio.iterdir():
            if item.is_dir():
                total_diretorios_verificados += 1
                # Verificar se esta pasta contém face.fpk
                face_fpk = item / "face.fpk"
                if face_fpk.exists():
                    pastas_com_face.append(item)
                    logging.info(f"✅ face.fpk encontrado em: {item}")
                # Continuar buscando em subdiretórios
                buscar_face_fpk_recursivo(item)
    
    logging.info("🔍 Iniciando busca recursiva por face.fpk...")
    # Iniciar busca recursiva
    buscar_face_fpk_recursivo(diretorio_faces_path)
    
    logging.info(f"📊 Resumo da busca: {len(pastas_com_face)} pastas com face.fpk encontradas em {total_diretorios_verificados} diretórios verificados")
    
    if not pastas_com_face:
        logging.warning("⚠️ Nenhuma pasta com face.fpk encontrada na parte 1")
        messagebox.showinfo("Informação", "Nenhuma pasta com face.fpk encontrada na parte 1.")
        return
    
    splash, barra, percentual_label = criar_tela_progresso(janela, "Processando faces...", "Buscando e movendo pastas completas")
    total = len(pastas_com_face)
    inicio = time.time()
    
    logging.info(f"🔄 Iniciando processamento de {total} pastas com face.fpk")
    
    faces_processadas = 0
    pastas_movidas = 0
    erros = 0
    total_itens_ignorados = 0
    
    for i, pasta_face in enumerate(pastas_com_face, start=1):
        try:
            logging.info(f"🔍 Processando pasta {i}/{total}: {pasta_face.name}")
            
            # Ler o arquivo face.fpk
            face_fpk_path = pasta_face / "face.fpk"
            logging.info(f"📄 Lendo arquivo: {face_fpk_path}")
            
            # Buscar pela linha que contém 'Assets/pes16/model/character/face/real/'
            nome_jogador = None
            linhas_lidas = 0
            try:
                with open(face_fpk_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for linha in f:
                        linhas_lidas += 1
                        if 'Assets/pes16/model/character/face/real/' in linha:
                            # Extrair o nome do jogador após 'real/'
                            partes = linha.split('Assets/pes16/model/character/face/real/')
                            if len(partes) > 1:
                                nome_jogador = partes[1].strip().split('/')[0].strip()
                                logging.info(f"🎯 Nome do jogador encontrado: '{nome_jogador}' na linha {linhas_lidas}")
                                break
                
                if not nome_jogador:
                    logging.warning(f"⚠️ Nome do jogador não encontrado em {pasta_face.name} após ler {linhas_lidas} linhas")
                    continue
                    
            except Exception as e:
                logging.warning(f"⚠️ Erro ao ler face.fpk em {pasta_face.name}: {e}")
                continue
            
            # Buscar pasta do jogador na parte 2
            pasta_jogador = diretorio_arquivos_path / nome_jogador
            logging.info(f"🔍 Procurando pasta do jogador: {pasta_jogador}")
            
            if not pasta_jogador.exists() or not pasta_jogador.is_dir():
                logging.warning(f"⚠️ Pasta do jogador '{nome_jogador}' não encontrada na parte 2")
                continue
            
            logging.info(f"✅ Pasta do jogador encontrada: {pasta_jogador}")
            
            # Mover a pasta completa do jogador para um nível acima do diretório onde está a pasta ID
            diretorio_destino = pasta_face.parent.parent  # Diretório pai do diretório pai da pasta ID
            logging.info(f"📁 Diretório de destino: {diretorio_destino}")
            
            # Verificar se a pasta do jogador já existe no destino
            destino_pasta_completa = diretorio_destino / nome_jogador
            if destino_pasta_completa.exists():
                logging.info(f"⏭️ Pasta do jogador já existe, ignorando: {nome_jogador}")
                total_itens_ignorados += 1
                continue
            
            try:
                # Copiar a pasta completa do jogador com todo seu conteúdo
                shutil.copytree(str(pasta_jogador), str(destino_pasta_completa))
                logging.info(f"📁 Pasta completa copiada com sucesso: {pasta_jogador} → {destino_pasta_completa}")
                
                # Contar arquivos copiados
                arquivos_copiados = sum(1 for _ in destino_pasta_completa.rglob('*') if _.is_file())
                pastas_movidas += 1
                faces_processadas += 1
                
                logging.info(f"✅ {pasta_face.name}: Pasta completa '{nome_jogador}' copiada com {arquivos_copiados} arquivos")
                
            except Exception as e:
                logging.error(f"❌ Erro ao copiar pasta completa '{nome_jogador}' para {pasta_face.name}: {e}")
                erros += 1
                continue
            
        except Exception as e:
            logging.error(f"❌ Erro ao processar {pasta_face.name}: {e}")
            erros += 1
        
        atualizar_progresso(splash, barra, percentual_label, i, total, f"Processando: {pasta_face.name}")
    
    splash.destroy()
    fim = time.time()
    tempo = round(fim - inicio, 2)
    
    # Log final detalhado
    logging.info("=" * 60)
    logging.info("📊 RESUMO FINAL DO PROCESSAMENTO")
    logging.info("=" * 60)
    logging.info(f"🔍 Total de diretórios verificados: {total_diretorios_verificados}")
    logging.info(f"📁 Total de pastas com face.fpk encontradas: {len(pastas_com_face)}")
    logging.info(f"✅ Faces processadas com sucesso: {faces_processadas}")
    logging.info(f"📁 Total de pastas completas movidas: {pastas_movidas}")
    logging.info(f"⏭️ Total de pastas ignoradas (já existiam): {total_itens_ignorados}")
    logging.info(f"❌ Erros encontrados: {erros}")
    logging.info(f"⏱️ Tempo total de processamento: {tempo}s")
    logging.info("=" * 60)
    
    messagebox.showinfo("Concluído", 
                       f"Processo de faces finalizado!\n"
                       f"Faces processadas: {faces_processadas}\n"
                       f"Pastas completas movidas: {pastas_movidas}\n"
                       f"Pastas ignoradas: {total_itens_ignorados}\n"
                       f"Erros encontrados: {erros}\n"
                       f"Tempo total: {tempo}s")
    
    logging.info(f"✅ Processo de faces concluído: {faces_processadas} faces, {pastas_movidas} pastas completas movidas em {tempo}s")

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
janela.geometry("800x800")

# Centralizar janela
janela.update_idletasks()
x = (janela.winfo_screenwidth() // 2) - (800 // 2)
y = (janela.winfo_screenheight() // 2) - (800 // 2)
janela.geometry(f"800x800+{x}+{y}")

# Frame principal centralizado
main_frame = tk.Frame(janela)
main_frame.pack(fill=tk.BOTH, expand=True)

# Frame central para centralizar o conteúdo
center_frame = tk.Frame(main_frame)
center_frame.pack(expand=True, fill=tk.BOTH)

# Canvas para scroll centralizado
canvas = tk.Canvas(center_frame, width=600)  # Largura fixa para centralizar
scrollbar = tk.Scrollbar(center_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

# Centralizar o conteúdo no canvas
canvas.create_window((300, 0), window=scrollable_frame, anchor="n")  # 300 = 600/2 para centralizar
canvas.configure(yscrollcommand=scrollbar.set)

# Título principal centralizado
label = tk.Label(scrollable_frame, text="Gerenciador de Pastas e Imagens v2.0", font=("Arial", 16, "bold"), fg="darkblue")
label.pack(pady=20)

subtitle = tk.Label(scrollable_frame, text="Escolha uma opção:", font=("Arial", 12), fg="gray")
subtitle.pack(pady=10)

btn4 = tk.Button(scrollable_frame, text="1. Listar todas as pastas em um arquivo .txt", command=listar_pastas_em_txt, width=35, height=2, font=("Arial", 10), bg="plum")
btn4.pack(pady=8)

btn1 = tk.Button(scrollable_frame, text="2. Renomear imagens pelo ID do jogador", command=renomear_imagens_por_id, width=35, height=2, font=("Arial", 10), bg="lightgreen")
btn1.pack(pady=8)

btn_faces = tk.Button(scrollable_frame, text="3. Mover todo conteúdo do jogador por FPK", command=mover_faces_por_fpk, width=35, height=2, font=("Arial", 10), bg="orange")
btn_faces.pack(pady=8)

btn_faces_completa = tk.Button(scrollable_frame, text="4. Mover pasta completa do jogador por FPK", command=mover_pasta_completa_por_fpk, width=35, height=2, font=("Arial", 10), bg="darkorange")
btn_faces_completa.pack(pady=8)

btn0_1 = tk.Button(scrollable_frame, text="5. Mover apenas pastas existentes (CSV)", command=mover_pastas_por_csv_se_existir, width=35, height=2, font=("Arial", 10), bg="lightcyan")
btn0_1.pack(pady=8)

btn0 = tk.Button(scrollable_frame, text="6. Mover pastas e criar nova com base no CSV", command=mover_pastas_por_csv, width=35, height=2, font=("Arial", 10), bg="lightblue")
btn0.pack(pady=8)

btn5 = tk.Button(scrollable_frame, text="❌ Sair", command=sair, width=35, height=2, font=("Arial", 10), bg="lightcoral")
btn5.pack(pady=8)

# btn2 = tk.Button(scrollable_frame, text="⚡ Testar CUDA/GPU", command=teste_cuda_inicial, width=35, height=2, font=("Arial", 10), bg="lightyellow")
# btn2.pack(pady=8)

# ✅ Status do OCR no rodapé
status_label = tk.Label(scrollable_frame, text="OCR carregando...", font=("Arial", 10), fg="blue")
status_label.pack(pady=10)

# Informações do sistema
info_label = tk.Label(scrollable_frame, text="Versão 2.3", font=("Arial", 8), fg="gray")
info_label.pack(pady=5)

# Empacotar canvas e scrollbar centralizados
canvas.pack(side="left", fill="both", expand=True, padx=(100, 0))  # Margem esquerda para centralizar
scrollbar.pack(side="right", fill="y", padx=(0, 100))  # Margem direita para centralizar

# Configurar scroll com mouse
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Inicializa OCR em segundo plano ao abrir o programa
threading.Thread(target=inicializar_ocr_em_segundo_plano, daemon=True).start()

janela.mainloop()
