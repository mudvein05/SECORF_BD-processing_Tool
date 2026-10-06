"""
secorf_core.py
==============
Módulo principal para la automatización, consulta y extracción de datos
desde la plataforma institucional SECORF (Instituto Nacional de Bosques - INAB).

Autor: Equipo ORF / INAB
Licencia: MIT
"""

import urllib.request
import urllib.parse
import http.cookiejar
import re
import pandas as pd

class SecorfScraper:
    """Manejador de sesión y consultas a la plataforma SECORF."""

    def __init__(self, usuario, password):
        self.usuario = usuario.strip()
        self.password = password.strip()
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.current_page_html = None

    def login(self):
        """Inicia sesión en SECORF y valida las credenciales."""
        req = urllib.request.Request('https://secorf.inab.gob.gt/Login', headers=self.headers)
        html = self.opener.open(req).read().decode('utf-8', errors='ignore')
        
        vs = re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', html).group(1)
        vsg = re.search(r'id="__VIEWSTATEGENERATOR"\s+value="([^"]+)"', html).group(1)
        ev = re.search(r'id="__EVENTVALIDATION"\s+value="([^"]+)"', html).group(1)

        data = {
            '__VIEWSTATE': vs,
            '__VIEWSTATEGENERATOR': vsg,
            '__EVENTVALIDATION': ev,
            'Usuario': self.usuario,
            'Password': self.password,
            'btnAceptar': 'Entrar al Sistema'
        }
        post_req = urllib.request.Request(
            'https://secorf.inab.gob.gt/Login',
            data=urllib.parse.urlencode(data).encode('utf-8'),
            headers=self.headers
        )
        resp = self.opener.open(post_req)
        content = resp.read().decode('utf-8', errors='ignore')

        if "Usuario o Contrase" in content or "Login" in resp.geturl():
            raise ValueError("Credenciales inválidas en SECORF o error de inicio de sesión.")
            
        self.reset_search_page()

    def reset_search_page(self):
        """Navega a la pantalla de Obligaciones Ingresadas para renovar el ViewState."""
        req = urllib.request.Request('https://secorf.inab.gob.gt/Vistas/ObligacionesIngresadas.aspx', headers=self.headers)
        self.current_page_html = self.opener.open(req).read().decode('utf-8', errors='ignore')

    def search_query(self, query):
        """Realiza una búsqueda por texto en la grilla de Obligaciones Ingresadas."""
        if not query or not str(query).strip():
            return []
        query = str(query).strip()

        vs_cur = re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', self.current_page_html).group(1)
        vsg_cur = re.search(r'id="__VIEWSTATEGENERATOR"\s+value="([^"]+)"', self.current_page_html).group(1)
        ev_cur = re.search(r'id="__EVENTVALIDATION"\s+value="([^"]+)"', self.current_page_html).group(1)

        search_data = {
            '__EVENTTARGET': 'ctl00$MainContent$Btnbusqueda',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': vs_cur,
            '__VIEWSTATEGENERATOR': vsg_cur,
            '__EVENTVALIDATION': ev_cur,
            'ctl00$MainContent$txtBusqueda': query,
            'ctl00_MainContent_txtBusqueda_ClientState': f'{{"enabled":true,"emptyMessage":"","validationText":"{query}","valueAsString":"{query}","lastSetTextBoxValue":"{query}"}}',
            'ctl00_MainContent_RadWindowManager1_ClientState': '',
            'ctl00_MenuPrincipal_ClientState': '',
            'ctl00_MainContent_GrdExpediente_ClientState': ''
        }

        resp = self.opener.open(
            urllib.request.Request(
                'https://secorf.inab.gob.gt/Vistas/ObligacionesIngresadas',
                data=urllib.parse.urlencode(search_data).encode('utf-8'),
                headers=self.headers
            )
        )
        html_res = resp.read().decode('utf-8', errors='ignore')
        self.current_page_html = html_res

        rows = re.findall(r'<tr[^>]*class="(?:rgRow|rgAltRow)"[^>]*>(.*?)</tr>', html_res, re.DOTALL)
        matched = []
        for r in rows:
            cols = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)]
            btn_match = re.search(r'<input\s+type="image"\s+name="([^"]+)"', r)
            btn_name = btn_match.group(1) if btn_match else None
            
            # Verificar si la consulta coincide con alguna de las columnas clave
            q_norm = query.lower()
            if any(q_norm in c.lower() for c in cols):
                matched.append({
                    'cols': cols,
                    'btn_name': btn_name,
                    'html': html_res
                })
        return matched

    def get_area_total(self, btn_name, query, html_page):
        """
        Accede al expediente de la obligación haciendo postback en su botón de selección
        y extrae el valor acumulado de 'Área Total' de la pestaña de polígonos.
        """
        try:
            vs_res = re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', html_page).group(1)
            vsg_res = re.search(r'id="__VIEWSTATEGENERATOR"\s+value="([^"]+)"', html_page).group(1)
            ev_res = re.search(r'id="__EVENTVALIDATION"\s+value="([^"]+)"', html_page).group(1)

            select_data = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': vs_res,
                '__VIEWSTATEGENERATOR': vsg_res,
                '__EVENTVALIDATION': ev_res,
                'ctl00$MainContent$txtBusqueda': query,
                'ctl00_MainContent_txtBusqueda_ClientState': '',
                'ctl00_MainContent_RadWindowManager1_ClientState': '',
                'ctl00_MenuPrincipal_ClientState': '',
                'ctl00_MainContent_GrdExpediente_ClientState': '',
                f'{btn_name}.x': '15',
                f'{btn_name}.y': '15'
            }

            resp_exp = self.opener.open(
                urllib.request.Request(
                    'https://secorf.inab.gob.gt/Vistas/ObligacionesIngresadas',
                    data=urllib.parse.urlencode(select_data).encode('utf-8'),
                    headers=self.headers
                )
            )
            html_exp = resp_exp.read().decode('utf-8', errors='ignore')

            # Siempre renovar la página de búsqueda para la siguiente iteración
            self.reset_search_page()

            # Patrón 1: Pie de tabla GrdPoligonos: Área Total: </td><td> 0.2463
            m = re.search(r'[aá]rea\s+total:?\s*</td>\s*<td[^>]*>\s*([\d\.,]+)', html_exp, re.IGNORECASE)
            if m:
                return m.group(1).strip()

            # Patrón 2: Cualquier celda con Área Total y celda siguiente con número
            m2 = re.search(r'[aá]rea\s+total[^<]*</t[dh]>\s*<t[dh][^>]*>\s*([\d\.,]+)', html_exp, re.IGNORECASE)
            if m2:
                return m2.group(1).strip()

            return "0.0000"
        except Exception as e:
            self.reset_search_page()
            return ""


def generate_variations(res_str):
    """
    Genera variaciones de formato para una resolución de licencia forestal.
    Resuelve inconsistencias de escritura en el tercer conjunto de datos (correlativo):
    - Con o sin ceros a la izquierda (1 dígito, 2 dígitos con 0X, 3 dígitos con 00X).
    - Con y sin sufijo POA final (-1, -2).
    """
    if not res_str or pd.isna(res_str):
        return []
    res = str(res_str).strip()
    variations = []

    # Quitar sufijo POA (-1, -2 al final tras año de 4 dígitos)
    base_res = re.sub(r'(?<=\d{4})-\d{1,2}$', '', res)
    has_poa = (base_res != res)

    candidates = [base_res, res] if has_poa else [res]

    for cand in candidates:
        parts = cand.split('-')
        if len(parts) >= 4 and parts[2].isdigit():
            val = int(parts[2])
            # Variantes de correlativo: 2 dígitos (0X), 3 dígitos (00X), y dígito natural
            formats = [f"{val:02d}", f"{val:03d}", str(val)]
            for fmt in formats:
                p_copy = list(parts)
                p_copy[2] = fmt
                v = "-".join(p_copy)
                if v not in variations:
                    variations.append(v)
        else:
            if cand not in variations:
                variations.append(cand)

    return variations
