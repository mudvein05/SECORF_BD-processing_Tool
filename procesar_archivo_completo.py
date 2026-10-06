"""
procesar_archivo_completo.py
============================
Script en línea de comandos (CLI) para procesar por lotes
un archivo Excel contra la plataforma SECORF (INAB).

Uso:
    python procesar_archivo_completo.py [ruta_archivo.xlsx]

Autor: Equipo ORF / INAB
Licencia: MIT
"""

import sys
import os
import getpass
import time
import json
import pandas as pd
from secorf_core import SecorfScraper, generate_variations

CONFIG_FILE = "config.json"

def obtener_credenciales():
    usuario = os.environ.get("SECORF_USUARIO")
    password = os.environ.get("SECORF_PASSWORD")

    if not usuario and os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                usuario = cfg.get("usuario")
        except Exception:
            pass

    if not usuario:
        usuario = input("Ingrese correo institucional SECORF: ").strip()
    else:
        print(f"Usuario SECORF: {usuario}")

    if not password:
        password = getpass.getpass("Ingrese contraseña de SECORF: ").strip()

    return usuario, password


def main():
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        # Archivo por defecto si existe en la carpeta
        default_file = "PruebaPrueba_Busqueda_SECORF.xlsx"
        if os.path.exists(default_file):
            input_path = default_file
        else:
            input_path = input("Ingrese la ruta del archivo Excel: ").strip().strip('"')

    if not os.path.exists(input_path):
        print(f"Error: El archivo no existe: {input_path}")
        return

    base_dir, file_name = os.path.split(input_path)
    name_no_ext, ext = os.path.splitext(file_name)
    output_path = os.path.join(base_dir, f"{name_no_ext}_PROCESADO{ext}")

    usuario, password = obtener_credenciales()

    print(f"\nCargando archivo: {input_path}")
    df = pd.read_excel(input_path)
    total_filas = len(df)
    print(f"Total de registros a procesar: {total_filas}")

    print("Conectando con SECORF...")
    scraper = SecorfScraper(usuario, password)
    scraper.login()
    print("Sesión iniciada con éxito.\n")

    secorf_col = []
    area_pol_col = []
    licencia_secorf_col = []
    expediente_secorf_col = []
    estado_secorf_col = []
    titular_secorf_col = []

    start_time = time.time()
    for idx in range(total_filas):
        row = df.iloc[idx]
        res_val = row.iloc[0]
        exp_val = row.iloc[1] if len(row) > 1 else ""
        tit_val = row.iloc[2] if len(row) > 2 else ""

        if (pd.isna(res_val) or not str(res_val).strip()) and (pd.isna(exp_val) or not str(exp_val).strip()):
            print(f"[{idx+1}/{total_filas}] Fila vacía -> Secorf: NO")
            secorf_col.append('NO')
            area_pol_col.append('')
            licencia_secorf_col.append('')
            expediente_secorf_col.append('')
            estado_secorf_col.append('')
            titular_secorf_col.append('')
            continue

        queries = generate_variations(res_val)
        if pd.notna(exp_val) and str(exp_val).strip() and str(exp_val).strip() not in queries:
            queries.append(str(exp_val).strip())

        found = False
        area_pol = ""
        match_cols = None
        matched_q = ""

        print(f"[{idx+1}/{total_filas}] Cotejando: Resol='{res_val}' | Exp='{exp_val}'")
        for q in queries:
            try:
                matches = scraper.search_query(q)
            except Exception as e:
                print(f"    Reintentando sesión tras desconexión: {e}")
                scraper.login()
                matches = scraper.search_query(q)

            if matches:
                found = True
                matched_q = q
                m = matches[0]
                match_cols = m['cols']
                btn = m['btn_name']
                if btn:
                    area_pol = scraper.get_area_total(btn, q, m['html'])
                break

        if found:
            lic_found = match_cols[5] if len(match_cols) > 5 else ''
            exp_found = match_cols[6] if len(match_cols) > 6 else ''
            est_found = match_cols[8] if len(match_cols) > 8 else ''
            tit_found = match_cols[1] if len(match_cols) > 1 else ''
            print(f"    -> [SI] Encontrado ('{matched_q}') | Area: {area_pol} | Lic: {lic_found} | Exp: {exp_found} | Est: {est_found}")
            secorf_col.append('SI')
            area_pol_col.append(area_pol)
            licencia_secorf_col.append(lic_found)
            expediente_secorf_col.append(exp_found)
            estado_secorf_col.append(est_found)
            titular_secorf_col.append(tit_found)
        else:
            print(f"    -> [NO] No localizado en SECORF")
            secorf_col.append('NO')
            area_pol_col.append('')
            licencia_secorf_col.append('')
            expediente_secorf_col.append('')
            estado_secorf_col.append('')
            titular_secorf_col.append('')

        # Guardado progresivo cada 10 registros
        if (idx + 1) % 10 == 0 or (idx + 1) == total_filas:
            df_temp = df.iloc[:idx+1].copy()
            df_temp['Secorf'] = secorf_col
            df_temp['area_pol'] = area_pol_col
            df_temp['licencia_secorf'] = licencia_secorf_col
            df_temp['expediente_secorf'] = expediente_secorf_col
            df_temp['estado_secorf'] = estado_secorf_col
            df_temp['titular_secorf'] = titular_secorf_col
            df_temp.to_excel(output_path, index=False)

    elapsed = round(time.time() - start_time, 1)
    print(f"\n==========================================")
    print(f"Proceso finalizado en {elapsed} segundos.")
    print(f"Archivo guardado en:\n{output_path}")

if __name__ == '__main__':
    main()
