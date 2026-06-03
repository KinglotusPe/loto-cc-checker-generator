import sys
import logging
import os

# Configuración global de registros
LOG_FILE = "tarjetas.log"

def setup_logger():
    """
    Configura y expone un logger estructurado para el registro de eventos 
    y excepciones de red del sistema de tarjetas.
    """
    logger = logging.getLogger("CC_Toolkit")
    logger.setLevel(logging.INFO)
    
    # Evitar duplicar manejadores
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

logger = setup_logger()

class ProgressBar:
    """
    Manejador asíncrono y en tiempo real para visualizar barras de progreso 
    dinámicas por consola sin saturar el búfer de salida.
    """

    def __init__(self, total: int, prefix: str = 'Progreso:', suffix: str = 'Completado', decimals: int = 1, length: int = 40, fill: str = '#'):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.iteration = 0

    def update(self, increment: int = 1):
        """Incrementa la iteración actual y actualiza la barra en consola."""
        self.iteration += increment
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.iteration / float(self.total)))
        filled_length = int(self.length * self.iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        
        # Escribir en consola en la misma línea
        sys.stdout.write(f'\r\033[94m{self.prefix}\033[0m |{bar}| {percent}% {self.suffix}')
        sys.stdout.flush()
        
        if self.iteration >= self.total:
            sys.stdout.write('\n')
            sys.stdout.flush()

    def reset(self, new_total: int = None):
        """Restablece la iteración de la barra de progreso."""
        self.iteration = 0
        if new_total is not None:
            self.total = new_total
