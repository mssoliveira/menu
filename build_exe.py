#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar executável otimizado do Menu OCR
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def limpar_builds_anteriores():
    """Remove diretórios de build anteriores."""
    dirs_para_remover = ['build', 'dist', '__pycache__']
    for dir_name in dirs_para_remover:
        if os.path.exists(dir_name):
            print(f"🗑️ Removendo {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Remove arquivos .spec antigos (exceto o nosso)
    for file in Path('.').glob('*.spec'):
        if file.name != 'menu_optimized.spec':
            print(f"🗑️ Removendo {file.name}...")
            file.unlink()

def criar_executavel():
    """Cria o executável usando PyInstaller."""
    print("🚀 Iniciando criação do executável...")
    
    # Comando PyInstaller otimizado
    comando = [
        sys.executable, '-m', 'pyinstaller',
        '--onefile',           # Arquivo único
        '--noconsole',         # Sem console
        '--clean',             # Limpar cache
        '--name=Menu_OCR',     # Nome do executável
        '--distpath=dist',     # Diretório de saída
        '--workpath=build',    # Diretório de trabalho
        '--specpath=.',        # Diretório dos arquivos .spec
        'menu.py'
    ]
    
    print(f"📋 Comando: {' '.join(comando)}")
    
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        print("✅ Executável criado com sucesso!")
        print(f"📁 Localização: {os.path.abspath('dist/Menu_OCR.exe')}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar executável:")
        print(f"Erro: {e}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")
        return False

def verificar_tamanho():
    """Verifica o tamanho do executável criado."""
    exe_path = Path('dist/Menu_OCR.exe')
    if exe_path.exists():
        tamanho_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"📊 Tamanho do executável: {tamanho_mb:.1f} MB")
        
        if tamanho_mb > 500:
            print("⚠️ Executável muito grande! Considere usar --onedir em vez de --onefile")
        else:
            print("✅ Tamanho do executável está bom!")

def main():
    """Função principal."""
    print("=" * 60)
    print("🔧 CONSTRUTOR DE EXECUTÁVEL - MENU OCR")
    print("=" * 60)
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} encontrado")
    except ImportError:
        print("❌ PyInstaller não encontrado!")
        print("Execute: pip install pyinstaller")
        return
    
    # Limpar builds anteriores
    limpar_builds_anteriores()
    
    # Criar executável
    if criar_executavel():
        verificar_tamanho()
        print("\n🎉 Processo concluído com sucesso!")
        print("💡 Dica: O executável está em 'dist/Menu_OCR.exe'")
    else:
        print("\n💥 Falha na criação do executável!")
        print("🔍 Verifique os erros acima e tente novamente")

if __name__ == "__main__":
    main()
