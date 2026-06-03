class Luhn:
    """
    Implementación del algoritmo de Luhn (módulo 10) para validación 
    y cálculo del dígito verificador de números de tarjetas de crédito.
    """

    @staticmethod
    def validate(card_number: str) -> bool:
        """
        Valida un número de tarjeta completo utilizando el algoritmo de Luhn.
        
        Args:
            card_number (str): El número de tarjeta completo (con o sin espacios/guiones).
            
        Returns:
            bool: True si el número de tarjeta es válido, False en caso contrario.
        """
        clean_number = card_number.replace(" ", "").replace("-", "")
        if not clean_number.isdigit():
            return False
        
        total_sum = 0
        # Invertimos el número para procesarlo de derecha a izquierda
        digits = [int(d) for d in reversed(clean_number)]
        for idx, digit in enumerate(digits):
            # Se duplican las posiciones impares (1, 3, 5, ...) desde la derecha
            if idx % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total_sum += digit
            
        return total_sum % 10 == 0

    @staticmethod
    def calculate_check_digit(base_number: str) -> int:
        """
        Calcula el dígito verificador correspondiente para un número base.
        Asume que este dígito se añadirá al final (extremo derecho).
        
        Args:
            base_number (str): El número sin el dígito verificador final.
            
        Returns:
            int: El dígito verificador (0-9).
        """
        clean_base = base_number.replace(" ", "").replace("-", "")
        if not clean_base.isdigit():
            raise ValueError("El número base debe contener únicamente dígitos.")
        
        total_sum = 0
        # Invertimos el número base. Al colocarse a la izquierda del dígito 
        # verificador (que estaría en idx 0 de la tarjeta completa), los dígitos 
        # del número base en índices pares desde la derecha (idx 0, 2, 4...) de 
        # esta lista invertida corresponderán a los índices impares de la tarjeta
        # final, por lo que deben ser duplicados.
        digits = [int(d) for d in reversed(clean_base)]
        for idx, digit in enumerate(digits):
            if idx % 2 == 0:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total_sum += digit
            
        return (10 - (total_sum % 10)) % 10
