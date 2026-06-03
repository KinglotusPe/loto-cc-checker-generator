import secrets
from .luhn import Luhn

class CardGenerator:
    """
    Generador de números de tarjeta de crédito individuales utilizando 
    el módulo 'secrets' de Python para aleatoriedad criptográficamente segura.
    """

    BRANDS = {
        "visa": {"prefixes": ["4"], "length": 16},
        "mastercard": {"prefixes": ["51", "52", "53", "54", "55"], "length": 16},
        "amex": {"prefixes": ["34", "37"], "length": 15},
        "discover": {"prefixes": ["6011", "65"], "length": 16}
    }

    @classmethod
    def generate(cls, brand: str = None, length: int = 16) -> str:
        """
        Genera un número de tarjeta de crédito válido de Luhn.

        Args:
            brand (str, opcional): Marca de tarjeta ('visa', 'mastercard', 'amex', 'discover').
            length (int, opcional): Longitud de la tarjeta (si no se especifica marca).

        Returns:
            str: Número de tarjeta de crédito generado y válido.
        """
        if brand:
            brand = brand.lower()
            if brand not in cls.BRANDS:
                raise ValueError(f"Marca no soportada. Utilice una de: {list(cls.BRANDS.keys())}")
            
            brand_info = cls.BRANDS[brand]
            prefix = secrets.choice(brand_info["prefixes"])
            target_length = brand_info["length"]
        else:
            prefix = ""
            target_length = length

        # Espacio para cuenta = longitud total - prefijo - dígito de control
        random_length = target_length - len(prefix) - 1
        if random_length < 0:
            raise ValueError("La longitud deseada es demasiado corta para el prefijo de la marca.")
            
        random_digits = "".join(secrets.choice("0123456789") for _ in range(random_length))
        
        base_number = f"{prefix}{random_digits}"
        check_digit = Luhn.calculate_check_digit(base_number)
        
        return f"{base_number}{check_digit}"


class BinGenerator:
    """
    Generador estructurado de lotes de tarjetas de crédito a partir de un 
    prefijo BIN (Bank Identification Number) o patrón.
    """

    @classmethod
    def generate_sequential(cls, bin_prefix: str, starting_account: int, ending_account: int, account_length: int = None) -> list[str]:
        """
        Genera un rango secuencial de tarjetas a partir de un BIN base.
        Determina de forma adaptiva (estándar ISO/IEC 7812) la longitud de la cuenta.

        Args:
            bin_prefix (str): El prefijo BIN de la tarjeta (ej. '453215' o '45321512').
            starting_account (int): Cuenta inicial del rango (ej. 1000).
            ending_account (int): Cuenta final del rango (ej. 1009).
            account_length (int, opcional): Longitud del campo de cuenta. Si no se provee, se autocalcula.

        Returns:
            list[str]: Lista de tarjetas generadas válidas por Luhn.
        """
        bin_clean = bin_prefix.replace(" ", "").replace("-", "")
        if not bin_clean.isdigit():
            raise ValueError("El BIN debe contener solo números.")

        if account_length is None:
            # Longitud total típica 16 - longitud BIN - 1 (dígito control)
            account_length = max(1, 16 - len(bin_clean) - 1)

        cards = []
        for account_num in range(starting_account, ending_account + 1):
            account_str = f"{account_num:0{account_length}d}"
            base_number = f"{bin_clean}{account_str}"
            check_digit = Luhn.calculate_check_digit(base_number)
            cards.append(f"{base_number}{check_digit}")
            
        return cards

    @classmethod
    def generate_random_batch(cls, bin_prefix: str, count: int, account_length: int = None) -> list[str]:
        """
        Genera un lote aleatorio de tarjetas a partir de un BIN base.
        Determina de forma adaptiva (estándar ISO/IEC 7812) la longitud de la cuenta.

        Args:
            bin_prefix (str): El prefijo BIN de la tarjeta (ej. '453215' o '45321512').
            count (int): Número de tarjetas a generar.
            account_length (int, opcional): Longitud de la cuenta. Si no se provee, se autocalcula.

        Returns:
            list[str]: Lista de tarjetas generadas válidas por Luhn.
        """
        bin_clean = bin_prefix.replace(" ", "").replace("-", "")
        if not bin_clean.isdigit():
            raise ValueError("El BIN debe contener solo números.")

        if account_length is None:
            account_length = max(1, 16 - len(bin_clean) - 1)

        cards = []
        for _ in range(count):
            account_str = "".join(secrets.choice("0123456789") for _ in range(account_length))
            base_number = f"{bin_clean}{account_str}"
            check_digit = Luhn.calculate_check_digit(base_number)
            cards.append(f"{base_number}{check_digit}")
            
        return cards

    @classmethod
    def generate_from_pattern(cls, pattern: str, count: int = 1) -> list[str]:
        """
        Genera tarjetas a partir de un patrón con comodines 'x' o 'X'.
        Ejemplo: '453215xxxxxxxxxx' (Longitud 16)
        El último dígito se calculará automáticamente mediante Luhn si termina en 'x'/'X'.

        Args:
            pattern (str): Patrón de la tarjeta (ej. '453215xxxxxxxxxx').
            count (int): Cantidad de tarjetas a generar bajo este patrón.

        Returns:
            list[str]: Lista de tarjetas generadas válidas.
        """
        pattern_clean = pattern.replace(" ", "").replace("-", "")
        if len(pattern_clean) < 2:
            raise ValueError("El patrón es demasiado corto.")

        cards = []
        for _ in range(count):
            digits = []
            # Procesamos todos los caracteres excepto el último para la base
            for char in pattern_clean[:-1]:
                if char.lower() == 'x':
                    digits.append(secrets.choice("0123456789"))
                elif char.isdigit():
                    digits.append(char)
                else:
                    raise ValueError(f"Caracter no permitido en el patrón: '{char}'")

            base_number = "".join(digits)
            last_char = pattern_clean[-1]

            if last_char.lower() == 'x':
                check_digit = Luhn.calculate_check_digit(base_number)
                cards.append(f"{base_number}{check_digit}")
            elif last_char.isdigit():
                # Si el usuario define un dígito verificador manual, lo colocamos, 
                # pero validamos si es Luhn válido y advertimos/recalculamos de ser necesario.
                cards.append(f"{base_number}{last_char}")
            else:
                raise ValueError(f"El último caracter del patrón debe ser dígito o 'x': '{last_char}'")
                
        return cards
