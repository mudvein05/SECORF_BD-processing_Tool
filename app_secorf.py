"""
app_secorf.py
=============
Interfaz gráfica de escritorio (GUI) para la búsqueda masiva, cotejo
y extracción de datos de licencias en la plataforma SECORF (INAB).

Autor: Equipo ORF / INAB
Licencia: MIT
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import pandas as pd
from secorf_core import SecorfScraper, generate_variations

CONFIG_FILE = "config.json"

def cargar_config_local():
    """Carga configuración local si existe."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def guardar_config_local(usuario):
    """Guarda usuario para conveniencia local."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"usuario": usuario}, f, indent=4)
    except Exception:
        pass


class SecorfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Consultor Automatizado SECORF - INAB")
        self.root.geometry("840x670")
        self.root.minsize(720, 520)

        cfg = cargar_config_local()
        self.archivo_excel = tk.StringVar(value="")
        self.usuario = tk.StringVar(value=cfg.get("usuario", ""))
        self.password = tk.StringVar(value="")
        self.recordar_usuario = tk.BooleanVar(value=bool(cfg.get("usuario")))

        self.cancelar_flag = False
        self.is_running = False

        self._crear_interfaz()

    def _crear_interfaz(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Frame superior: Credenciales y Archivo
        frame_top = ttk.LabelFrame(self.root, text="Autenticación y Archivo de Entrada", padding=15)
        frame_top.pack(fill="x", padx=15, pady=10)

        # Usuario y Contraseña
        ttk.Label(frame_top, text="Correo Institucional:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame_top, textvariable=self.usuario, width=32).grid(row=0, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(frame_top, text="Contraseña:").grid(row=0, column=2, sticky="w", padx=(15, 0), pady=4)
        ttk.Entry(frame_top, textvariable=self.password, show="*", width=24).grid(row=0, column=3, sticky="w", padx=5, pady=4)

        ttk.Checkbutton(frame_top, text="Recordar correo en este equipo", variable=self.recordar_usuario).grid(row=1, column=1, sticky="w", padx=5, pady=(0, 6))

        # Archivo Excel
        ttk.Label(frame_top, text="Archivo Excel:").grid(row=2, column=0, sticky="w", pady=8)
        ttk.Entry(frame_top, textvariable=self.archivo_excel, width=60).grid(row=2, column=1, columnspan=2, sticky="we", padx=5, pady=8)
        ttk.Button(frame_top, text="Examinar...", command=self._seleccionar_archivo).grid(row=2, column=3, sticky="w", padx=5, pady=8)

        # Frame de Acciones y Estado
        frame_mid = ttk.Frame(self.root, padding=10)
        frame_mid.pack(fill="x", padx=15)

        self.btn_iniciar = tk.Button(
            frame_mid, text="▶ Iniciar Procesamiento", bg="#2e7d32", fg="white",
            font=("Arial", 11, "bold"), relief="flat", padx=16, pady=8, command=self._iniciar_hilo
        )
        self.btn_iniciar.pack(side="left", padx=5)

        self.btn_cancelar = tk.Button(
            frame_mid, text="⏹ Cancelar", bg="#c62828", fg="white",
            font=("Arial", 11, "bold"), relief="flat", padx=16, pady=8, state="disabled", command=self._cancelar
        )
        self.btn_cancelar.pack(side="left", padx=5)

        self.lbl_estado = ttk.Label(frame_mid, text="Listo para iniciar.", font=("Arial", 10, "italic"))
        self.lbl_estado.pack(side="right", padx=10)

        # Barra de progreso
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=20, pady=8)

        # Log en tiempo real
        frame_log = ttk.LabelFrame(self.root, text="Registro de Consultas en Vivo", padding=10)
        frame_log.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self.txt_log = tk.Text(frame_log, wrap="word", font=("Consolas", 9), bg="#1e1e1e", fg="#e0e0e0")
        scrollbar = ttk.Scrollbar(frame_log, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scrollbar.set)
        
        self.txt_log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _log(self, mensaje):
        self.txt_log.insert(tk.END, mensaje + "\n")
        self.txt_log.see(tk.END)

    def _seleccionar_archivo(self):
        fn = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx *.xls")])
        if fn:
            self.archivo_excel.set(fn)

    def _iniciar_hilo(self):
        if not self.usuario.get().strip() or not self.password.get().strip():
            messagebox.showwarning("Atención", "Por favor ingresa tu correo institucional y contraseña de SECORF.")
            return

        if not self.archivo_excel.get().strip() or not os.path.exists(self.archivo_excel.get()):
            messagebox.showerror("Error", "Por favor selecciona un archivo Excel válido.")
            return

        if self.recordar_usuario.get():
            guardar_config_local(self.usuario.get().strip())

        self.cancelar_flag = False
        self.is_running = True
        self.btn_iniciar.config(state="disabled")
        self.btn_cancelar.config(state="normal")
        self.txt_log.delete('1.0', tk.END)

        t = threading.Thread(target=self._procesar)
        t.daemon = True
        t.start()

    def _cancelar(self):
        if self.is_running:
            self.cancelar_flag = True
            self._log("\n[!] Solicitud de cancelación enviada por el usuario...")

    def _procesar(self):
        input_path = self.archivo_excel.get()
        base_dir, file_name = os.path.split(input_path)
        name_no_ext, ext = os.path.splitext(file_name)
        output_path = os.path.join(base_dir, f"{name_no_ext}_PROCESADO{ext}")

        try:
            self._log(">>> Cargando archivo Excel...")
            df = pd.read_excel(input_path)
            total = len(df)
            self._log(f">>> Total de registros a revisar: {total}\n")

            self._log(">>> Conectando con SECORF (INAB)...")
            scraper = SecorfScraper(self.usuario.get(), self.password.get())
            scraper.login()
            self._log(">>> Sesión iniciada exitosamente en SECORF.\n")

            secorf_col = []
            area_pol_col = []
            licencia_secorf_col = []
            expediente_secorf_col = []
            estado_secorf_col = []
            titular_secorf_col = []

            for idx in range(total):
                if self.cancelar_flag:
                    self._log("\n>>> PROCESAMIENTO CANCELADO.")
                    break

                row = df.iloc[idx]
                res_val = row.iloc[0]
                exp_val = row.iloc[1] if len(row) > 1 else ""
                tit_val = row.iloc[2] if len(row) > 2 else ""

                self.lbl_estado.config(text=f"Procesando {idx+1}/{total} ({(idx+1)*100//total}%)")
                self.progress['value'] = ((idx + 1) / total) * 100

                if (pd.isna(res_val) or not str(res_val).strip()) and (pd.isna(exp_val) or not str(exp_val).strip()):
                    self._log(f"[{idx+1}/{total}] Fila vacía -> SECORF: NO")
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

                for q in queries:
                    try:
                        matches = scraper.search_query(q)
                    except Exception:
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

                    self._log(f"[{idx+1}/{total}] [SI] Encontrado con '{matched_q}' | Area Pol: {area_pol} | Lic: {lic_found}")
                    secorf_col.append('SI')
                    area_pol_col.append(area_pol)
                    licencia_secorf_col.append(lic_found)
                    expediente_secorf_col.append(exp_found)
                    estado_secorf_col.append(est_found)
                    titular_secorf_col.append(tit_found)
                else:
                    self._log(f"[{idx+1}/{total}] [NO] No localizado en SECORF")
                    secorf_col.append('NO')
                    area_pol_col.append('')
                    licencia_secorf_col.append('')
                    expediente_secorf_col.append('')
                    estado_secorf_col.append('')
                    titular_secorf_col.append('')

                # Guardado de seguridad cada 10 registros
                if (idx + 1) % 10 == 0 or (idx + 1) == total:
                    df_temp = df.iloc[:idx+1].copy()
                    df_temp['Secorf'] = secorf_col
                    df_temp['area_pol'] = area_pol_col
                    df_temp['licencia_secorf'] = licencia_secorf_col
                    df_temp['expediente_secorf'] = expediente_secorf_col
                    df_temp['estado_secorf'] = estado_secorf_col
                    df_temp['titular_secorf'] = titular_secorf_col
                    df_temp.to_excel(output_path, index=False)

            self._log(f"\n==========================================")
            self._log(f"¡PROCESO FINALIZADO!")
            self._log(f"Resultados guardados en:\n{output_path}")
            self.lbl_estado.config(text="Completado.")
            messagebox.showinfo("Completado", f"Archivo procesado guardado exitosamente en:\n{output_path}")

        except Exception as ex:
            self._log(f"\n[ERROR]: {str(ex)}")
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(ex)}")

        finally:
            self.is_running = False
            self.btn_iniciar.config(state="normal")
            self.btn_cancelar.config(state="disabled")

if __name__ == '__main__':
    root = tk.Tk()
    app = SecorfApp(root)
    root.mainloop()
