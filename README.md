# Consultor Automatizado de Licencias SECORF (INAB) 🌲🇬🇹

Herramienta de automatización y cotejo masivo de resoluciones de licencias forestales, expedientes y extracción de áreas de polígonos desde la plataforma institucional **SECORF** (*Sistema de Obligaciones de Repoblación Forestal*) del **Instituto Nacional de Bosques (INAB)**.

---

## 📋 Descripción del Proyecto

El cotejo manual de cientos de licencias en la plataforma web institucional puede tomar días debido a variaciones en la digitación histórica de resoluciones (diferencias de formato en correlativos, ausencia de ceros, omisión de sufijos POA). 

Esta herramienta automatiza el proceso mediante:
1. **Normalización y cotejo inteligente:** Genera dinámicamente variaciones numéricas de resolución (formatos de 1, 2 y 3 dígitos en el bloque correlativo, eliminación de sufijos POA `-1`, `-2`).
2. **Búsqueda recursiva:** Si la resolución no coincide, realiza una búsqueda alternativa por el número de expediente.
3. **Extracción profunda de datos:** Accede al registro de cada licencia en el portal para extraer la sumatoria del **Área Total** de los polígonos cargados en la pestaña *Punto de los Polígonos*.
4. **Exportación estructurada:** Añade columnas al Excel original (`Secorf` [SI/NO], `area_pol`, `licencia_secorf`, `expediente_secorf`, `estado_secorf`, `titular_secorf`).
5. **Guardado progresivo:** Almacena copias de seguridad cada 10 registros para garantizar la integridad de los datos ante interrupciones de red.

---

## 🚀 Estructura del Repositorio

```text
├── app_secorf.py                 # Aplicación de escritorio con interfaz gráfica (GUI Tkinter)
├── secorf_core.py               # Motor central de scraping, sesión y parseo HTTP
├── procesar_archivo_completo.py # Script de ejecución por lotes en línea de comandos (CLI)
├── INICIAR_HERRAMIENTA_SECORF.bat # Acceso directo para Windows
├── requirements.txt             # Dependencias del proyecto (pandas, openpyxl)
├── config.example.json          # Plantilla para configuración local opcional
├── .gitignore                   # Exclusión de credenciales y datos confidenciales
├── LICENSE                      # Licencia MIT
└── README.md                    # Documentación del proyecto
```

---

## 🛠️ Requisitos Previos

* **Python 3.10 o superior** instalado.
* Conexión a internet con acceso a `https://secorf.inab.gob.gt`.
* Credenciales activas de usuario institucional en SECORF.

---

## 📦 Instalación

1. Clona este repositorio o descarga los archivos:
   ```bash
   git clone https://github.com/TU_USUARIO/consultor-secorf.git
   cd consultor-secorf
   ```

2. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Uso de la Herramienta

### Opción 1: Interfaz Gráfica (Recomendada)
Para abrir la interfaz visual de escritorio:
* En Windows, haz doble clic sobre el archivo **`INICIAR_HERRAMIENTA_SECORF.bat`**, o
* Ejecuta desde la consola:
  ```bash
  python app_secorf.py
  ```

**Pasos en la interfaz:**
1. Ingresa tu correo institucional y contraseña de SECORF.
2. Haz clic en **"Examinar..."** y selecciona tu archivo Excel (debe contener columnas de resolución, expediente y titular).
3. Presiona **"▶ Iniciar Procesamiento"**.
4. Podrás ver el progreso porcentual y el log detallado de cada licencia en tiempo real.
5. Al finalizar, el sistema generará automáticamente un archivo con el sufijo `_PROCESADO.xlsx` en la misma carpeta.

---

### Opción 2: Línea de Comandos (CLI / Modo Batch)
Para procesamiento desatendido o en servidores:
```bash
python procesar_archivo_completo.py "ruta/a/tu/archivo.xlsx"
```
El script te solicitará las credenciales de forma interactiva (la contraseña se oculta al escribir). También puedes definir variables de entorno:
```bash
set SECORF_USUARIO=tu_correo@inab.gob.gt
set SECORF_PASSWORD=tu_contraseña
python procesar_archivo_completo.py "archivo.xlsx"
```

---

## 📄 Formato del Archivo Excel de Entrada

El archivo Excel (`.xlsx` o `.xls`) debe contener las siguientes columnas principales (el orden predeterminado toma las primeras 3 columnas):
1. **Columna 1:** `Resolución Licencia` (ejemplo: `40-2212-1-1.1-2010-1`, `42-604-10-1.1-2010`)
2. **Columna 2:** `Expediente` (ejemplo: `40-210-1.1-2009`)
3. **Columna 3:** `Titular`

### Columnas generadas en el archivo de salida:
* **`Secorf`:** `SI` si fue encontrada en la plataforma; `NO` en caso contrario.
* **`area_pol`:** Valor del área total registrada en la sección de coordenadas del proyecto (ej. `1.0236`, `0.4670`, `0.0000`).
* **`licencia_secorf`:** Formato exacto bajo el cual está registrada la resolución en SECORF (útil para auditoría de digitación).
* **`expediente_secorf`:** Expediente registrado en SECORF.
* **`estado_secorf`:** Estado de la obligación (`VIGENTE`, `LIBERADO`, etc.).
* **`titular_secorf`:** Nombre del titular según el portal.

---

## 🔒 Seguridad y Privacidad

* Este repositorio **NO contiene credenciales ni contraseñas almacenadas**.
* El archivo `.gitignore` está configurado para omitir archivos `.env`, `config.json` y cualquier hoja de cálculo (`*.xlsx`, `*.xls`) para evitar la filtración accidental de información institucional sensible a GitHub.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.
