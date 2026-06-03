import re
import secrets
from datetime import datetime

class DataParser:
    """
    Analizador y normalizador de datos de tarjetas de crédito.
    Utiliza expresiones regulares avanzadas para parsear información
    estructurada en diversos formatos (ej. CSV, pipes, espacios, barras, etc.).
    """

    # Expresión regular robusta para detectar:
    # 1. Número de tarjeta (13 a 19 dígitos)
    # 2. Mes de expiración (1 o 2 dígitos, opcionalmente precedido por separador)
    # 3. Año de expiración (2 o 4 dígitos, opcionalmente precedido por separador)
    # 4. Código de seguridad/CVV (3 o 4 dígitos, opcionalmente precedido por separador)
    # Ejemplo: 4111-1111-1111-1111|12/28|123
    CARD_PATTERN = re.compile(
        r"(?P<number>\b\d{13,19}\b)"                        # Tarjeta
        r"(?:\D+(?P<month>\b(?:0?[1-9]|1[0-2])\b))?"       # Mes (opcional)
        r"(?:\D+(?P<year>\b\d{4}|\d{2}\b))?"                # Año (opcional, preferible 4 dígitos primero)
        r"(?:\D+(?P<cvv>\b\d{3,4}\b))?"                     # CVV (opcional)
    )

    @classmethod
    def parse_entry(cls, text_entry: str) -> dict:
        """
        Analiza una sola cadena de texto e identifica los componentes de la tarjeta.
        Si faltan campos (mes, año o CVV), autogenera valores lógicos válidos.

        Args:
            text_entry (str): Línea de texto a analizar.

        Returns:
            dict: Diccionario con llaves 'card', 'month', 'year', 'cvv' y 'formatted'.
        """
        # Limpiar espacios en blanco al inicio y al final
        clean_text = text_entry.strip()
        
        # Eliminar guiones del número de la tarjeta en caso de estar espaciado
        # conservando el resto del formato de delimitadores
        match_number_with_dashes = re.search(r"(\d{4}[-\s]\d{4,6}[-\s]\d{4,6}[-\s]?\d{0,4})", clean_text)
        if match_number_with_dashes:
            original_num = match_number_with_dashes.group(1)
            normalized_num = original_num.replace("-", "").replace(" ", "")
            clean_text = clean_text.replace(original_num, normalized_num)

        match = cls.CARD_PATTERN.search(clean_text)
        if not match:
            raise ValueError(f"No se pudo extraer un formato de tarjeta válido de: '{text_entry}'")

        data = match.groupdict()
        current_year = datetime.today().year

        # Mes
        if data["month"]:
            month = data["month"]
            if len(month) == 1:
                month = f"0{month}"
        else:
            # Generar mes aleatorio
            month = f"{secrets.randbelow(12) + 1:02d}"

        # Año
        if data["year"]:
            year = data["year"]
            if len(year) == 2:
                year = f"20{year}"
        else:
            # Generar año válido (año actual + 1 a 6 años)
            year = str(current_year + secrets.randbelow(6) + 1)

        # CVV
        if data["cvv"]:
            cvv = data["cvv"]
        else:
            # Generar CVV de 3 dígitos por defecto
            cvv = f"{secrets.randbelow(900) + 100:03d}"

        card_number = data["number"]
        formatted = f"{card_number}|{month}|{year}|{cvv}"

        return {
            "number": card_number,
            "month": month,
            "year": year,
            "cvv": cvv,
            "formatted": formatted
        }

    @classmethod
    def parse_text_block(cls, text_block: str) -> list[dict]:
        """
        Parsea un bloque completo de texto (líneas de archivo o múltiples tarjetas)
        y devuelve una lista de tarjetas parseadas con éxito.
        """
        results = []
        for line in text_block.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = cls.parse_entry(line)
                results.append(parsed)
            except ValueError:
                # Ignorar líneas basura
                continue
        return results
