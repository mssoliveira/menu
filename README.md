
# 🧠 Gerenciador de Pastas e Imagens com OCR

Este aplicativo em Python permite:
- Mover pastas e arquivos com base em um arquivo CSV contendo `ID` e `Nome`.
- Renomear imagens com base no texto extraído via OCR, identificando o campo `JOGADOR ID`.

Ele possui interface gráfica (`Tkinter`), barra de progresso e opção de usar GPU (CUDA) se disponível.

---

## ⚙️ Requisitos

Instale as dependências com:

```bash
pip install -r requirements.txt
```

### Conteúdo do `requirements.txt`:

```
pandas
torch
easyocr
tk
```

> Obs: se estiver usando CUDA, instale o PyTorch compatível com sua GPU e versão do CUDA (ex: cu121, cu118 etc) via [https://pytorch.org](https://pytorch.org).

---

## 🖼️ Estrutura esperada do CSV

```csv
Id;Name
1234;João Silva
5678;Maria Costa
```

As pastas e arquivos com os nomes `1234`, `5678`, etc. serão movidos para pastas com os nomes `João Silva`, `Maria Costa`, etc.

---

## 🚀 Executando o App

```bash
python menu.py
```

### Funções disponíveis:
- Testar se o CUDA está disponível.
- Mover pastas e arquivos conforme CSV.
- Renomear imagens com base no texto extraído com OCR (`JOGADOR ID`).

---

## 📦 Gerar EXE com PyInstaller

### Pré-requisito:
Instale o PyInstaller:

```bash
pip install pyinstaller
```

---

### ✔️ Para gerar um `.exe` leve (sem modelos do EasyOCR incluídos):

> O EasyOCR baixa os modelos automaticamente na primeira execução e guarda em `C:\Users\<seu-usuario>\.EasyOCR`.

```bash
pyinstaller --onefile --noconsole menu.py
```

---

### ✅ Para gerar um `.exe` **com os modelos incluídos** (modo offline):

Inclua o diretório `.EasyOCR` com:

```bash
pyinstaller --onefile --noconsole --add-data "%USERPROFILE%\.EasyOCR;.EasyOCR" menu.py
```

> No Linux/Mac, use `:` ao invés de `;` no `--add-data`.

---

## ❓ Qual versão usar?

| Situação                                 | Incluir `.EasyOCR`? | EXE funciona offline? |
|------------------------------------------|----------------------|------------------------|
| Computador com internet                 | ❌ Não               | ✅ Sim (modelo baixa na 1ª vez) |
| Computador sem internet                 | ✅ Sim               | ✅ Sim (modelo já incluso) |
| Quer EXE mais leve e rápido de gerar    | ❌ Não               | ⚠️ Necessita internet na 1ª vez |

---

## 🧪 CUDA vs CPU

O programa detecta automaticamente se o CUDA (GPU) está disponível. Se estiver, você poderá escolher entre:
- GPU (mais rápido)
- CPU (compatível com todos)
