# -*- coding: utf-8 -*-
"""Converte .xlsb das subpastas para .xlsx (preservando o layout) e aposenta o original."""
import os
import pandas as pd

RAIZ = r"D:\sistema_pma\dados_importacao"

for pasta in os.listdir(RAIZ):
    dp = os.path.join(RAIZ, pasta)
    if not os.path.isdir(dp): continue
    for arq in os.listdir(dp):
        if arq.lower().endswith(".xlsb"):
            caminho = os.path.join(dp, arq)
            print(f"🔄 Convertendo {pasta}/{arq} ...")
            sheets = pd.read_excel(caminho, engine="pyxlsb", header=None, sheet_name=None)
            saida = os.path.join(dp, arq.rsplit(".", 1)[0] + ".xlsx")
            with pd.ExcelWriter(saida, engine="openpyxl") as w:
                for nome, df in sheets.items():
                    df.to_excel(w, sheet_name=nome[:31], header=False, index=False)
            os.rename(caminho, caminho + ".old")   # aposenta o .xlsb
            print(f"   ✅ gerou {os.path.basename(saida)}")
print("\n✅ Concluído. Agora rode: python importar_pastas.py")