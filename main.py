import sys
import asyncio
import os
import re
import warnings
from core import Luhn, CardGenerator, BinGenerator, AsyncCardChecker, ChkrApiChecker, DataParser, ProgressBar, logger

# Ignorar advertencias de deprecación molestas del intérprete
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Asegurar compatibilidad asíncrona en Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Estilos y colores ANSI para consola
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
PURPLE = "\033[38;5;129m"
PINK = "\033[38;5;201m"

def clear_screen():
    # En algunas terminales de VS Code, cls puede causar fallos de buffer de repetición si no se vacía la salida
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')

def print_banner():
    lotus = f"""
{PURPLE}                 .
                .M.
               .M5M.
             _ \\/ \\/ _
            ( \\/   \\/ )
             \\       /
         _    \\     /    _
        ( \\    \\   /    / )
         \\ \\____\\ /____/ /
          \\      V      /
           `-._______.-'{RESET}

{PINK}{BOLD}      __        ______   _________   ______  
     | |      /  __  \\ |___   ___| /  __  \\ 
     | |      | |  | |     | |     | |  | | 
     | |      | |  | |     | |     | |  | | 
     | |____  | |__| |     | |     | |__| | 
     |______| \\______/     |_|     \\______/ {RESET}
               {CYAN}{BOLD}EL REINO DE LOTO{RESET}
"""
    print(lotus)
    print(f"{CYAN}  =========================================================={RESET}")
    print(f"{CYAN}{BOLD}   Developer: {RESET}{GREEN}KinglotusPe{RESET}")
    print(f"{CYAN}{BOLD}   GitHub:    {RESET}{BLUE}https://github.com/KinglotusPe{RESET}")
    print(f"{CYAN}{BOLD}   Telegram:  {RESET}{BLUE}https://t.me/addlist/wigY-9BP0cEwMDMx{RESET}")
    print(f"{CYAN}  =========================================================={RESET}\n")

def print_header(title: str):
    print(f"\n{PINK}{BOLD}" + "=" * 60)
    print(f"| {title.center(56)} |")
    print("=" * 60 + f"{RESET}\n")

def pause():
    input(f"\n{YELLOW}Presione Enter para continuar...{RESET}")
def menu_generar_tarjetas():
    print_header("GENERADOR UNIFICADO DE TARJETAS")
    print("Seleccione la modalidad de generación:")
    print(f"  {CYAN}1.{RESET} Por Marca (Visa, Mastercard, Amex, Discover)")
    print(f"  {CYAN}2.{RESET} Por BIN o Patrón (ej: 453215 o 453215xxxxxxxxxx)")
    print(f"  {CYAN}3.{RESET} Volver al menú principal")
    
    opc = input(f"\n{BOLD}Seleccione una opción [1-3]: {RESET}").strip()
    if opc == "3" or not opc:
        return
        
    cards = []
    if opc == "1":
        print("\nMarcas soportadas:")
        print(f"  {CYAN}1.{RESET} Visa")
        print(f"  {CYAN}2.{RESET} Mastercard")
        print(f"  {CYAN}3.{RESET} American Express")
        print(f"  {CYAN}4.{RESET} Discover")
        print(f"  {CYAN}5.{RESET} Longitud personalizada")
        brand_opc = input(f"\n{BOLD}Seleccione marca [1-5]: {RESET}").strip()
        
        try:
            qty_str = input("Cantidad de tarjetas a generar [Por defecto: 1]: ").strip()
            qty = int(qty_str) if qty_str else 1
        except ValueError:
            qty = 1

        brand_map = {"1": "visa", "2": "mastercard", "3": "amex", "4": "discover"}
        try:
            if brand_opc in brand_map:
                brand_name = brand_map[brand_opc]
                cards = [CardGenerator.generate(brand=brand_name) for _ in range(qty)]
            elif brand_opc == "5":
                length = int(input("Ingrese la longitud deseada (ej. 16, 15): ").strip())
                cards = [CardGenerator.generate(length=length) for _ in range(qty)]
            else:
                print(f"{RED}[!] Opción no válida.{RESET}")
                pause()
                return
        except Exception as e:
            print(f"{RED}[!] Error al generar por marca: {e}{RESET}")
            pause()
            return
            
    elif opc == "2":
        print(f"\nPuede ingresar un BIN simple (ej. {CYAN}453215{RESET}) o un patrón con comodines 'x' (ej. {CYAN}453215xxxxxxxxxx{RESET}).")
        pattern = input(f"{BOLD}Ingrese el BIN o Patrón: {RESET}").strip()
        if not pattern:
            print(f"{RED}[!] Entrada vacía.{RESET}")
            pause()
            return
            
        try:
            qty_str = input("Cantidad de tarjetas a generar [Por defecto: 10]: ").strip()
            qty = int(qty_str) if qty_str else 10
        except ValueError:
            qty = 10
            
        try:
            if 'x' in pattern.lower():
                cards = BinGenerator.generate_from_pattern(pattern, count=qty)
            else:
                cards = BinGenerator.generate_random_batch(pattern, count=qty)
        except Exception as e:
            print(f"{RED}[!] Error al generar desde BIN/Patrón: {e}{RESET}")
            pause()
            return
    else:
        print(f"{RED}[!] Opción no válida.{RESET}")
        pause()
        return

    # Mostrar resultados
    if cards:
        print(f"\n{GREEN}[+] Tarjetas Generadas Exitosamente ({len(cards)}):{RESET}")
        print("-" * 50)
        for c in cards:
            print(f"  {BOLD}{c}{RESET}")
        print("-" * 50)
        
        if len(cards) > 1:
            save = input(f"\n¿Desea guardar estas tarjetas en un archivo? (s/n): ").strip().lower()
            if save == 's':
                filename = input("Nombre del archivo [tarjetas_generadas.txt]: ").strip() or "tarjetas_generadas.txt"
                try:
                    with open(filename, "w") as f:
                        for c in cards:
                            f.write(f"{c}\n")
                    print(f"{GREEN}[+] Guardado en {filename} con éxito.{RESET}")
                except Exception as e:
                    print(f"{RED}[!] Error al guardar el archivo: {e}{RESET}")
        else:
            # Para 1 tarjeta, validación Luhn local automática como detalle informativo
            is_luhn = Luhn.validate(cards[0].split('|')[0])
            print(f"Validación Luhn Local: {'Válida (Check Digit correcto)' if is_luhn else 'Inválida'}")
            
    pause()

def menu_validar_tarjetas():
    print_header("VALIDADOR UNIFICADO DE TARJETAS")
    print("Seleccione la fuente de entrada:")
    print(f"  {CYAN}1.{RESET} Ingresar manualmente en consola (individual o separadas por coma/espacios)")
    print(f"  {CYAN}2.{RESET} Cargar desde un archivo de texto")
    print(f"  {CYAN}3.{RESET} Volver al menú principal")
    
    opc = input(f"\n{BOLD}Seleccione una opción [1-3]: {RESET}").strip()
    if opc == "3" or not opc:
        return
        
    raw_entries = []
    if opc == "1":
        entrada = input("\nIngrese la tarjeta o lista de tarjetas:\n").strip()
        if not entrada:
            print(f"{RED}[!] Entrada vacía.{RESET}")
            pause()
            return
        # Aceptar múltiples formatos (separados por coma, espacio o nuevas líneas)
        raw_entries = [c.strip() for c in re.split(r'[,\s]+', entrada) if c.strip()]
    elif opc == "2":
        filename = input("\nIngrese el nombre/ruta del archivo: ").strip()
        if not os.path.exists(filename):
            print(f"{RED}[!] El archivo '{filename}' no existe.{RESET}")
            pause()
            return
        try:
            with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                raw_entries = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"{RED}[!] Error al leer el archivo: {e}{RESET}")
            pause()
            return
    else:
        print(f"{RED}[!] Opción no válida.{RESET}")
        pause()
        return

    # Normalizar con el DataParser
    print(f"\n[*] Procesando y normalizando {len(raw_entries)} entradas...")
    cards = []
    for entry in raw_entries:
        try:
            parsed = DataParser.parse_entry(entry)
            cards.append(parsed)
        except Exception:
            # Si no se puede parsear, limpiar básico e incluirlo de todas formas
            clean_num = entry.replace(" ", "").replace("-", "")
            if clean_num.isdigit() and len(clean_num) >= 12:
                cards.append({
                    "number": clean_num,
                    "month": "12",
                    "year": "2028",
                    "cvv": "123",
                    "formatted": f"{clean_num}|12|2028|123"
                })

    if not cards:
        print(f"{RED}[!] No se pudieron procesar tarjetas válidas a partir de la entrada.{RESET}")
        pause()
        return

    # Validación local automática (Luhn) para todos
    print(f"\n[*] Realizando pre-validación de Algoritmo de Luhn (Local)...")
    luhn_passed = []
    luhn_failed = []
    for c in cards:
        if Luhn.validate(c["number"]):
            luhn_passed.append(c)
        else:
            luhn_failed.append(c)
            
    print(f"    Total tarjetas procesadas: {len(cards)}")
    print(f"    Pasaron Luhn:   {GREEN}{len(luhn_passed)}{RESET}")
    print(f"    Fallaron Luhn:  {RED}{len(luhn_failed)}{RESET}")
    
    if not luhn_passed:
        print(f"\n{RED}[!] Ninguna de las tarjetas ingresadas pasó la prueba de Luhn local.{RESET}")
        pause()
        return

    # Preguntar si desea validación Web/API
    web_check = input(f"\n¿Desea realizar validación en línea (API / Web Scraper)? (s/n): ").strip().lower()
    if web_check != 's':
        # Mostrar resumen simple de Luhn local
        print(f"\n{BOLD}=== RESULTADOS LOCALES (LUHN) ==={RESET}")
        for c in luhn_passed:
            print(f"[{GREEN}LUHN PASSED{RESET}] {c['number']}")
        for c in luhn_failed:
            print(f"[{RED}LUHN FAILED{RESET}] {c['number']}")
        pause()
        return

    # Validación en línea
    print(f"\nSeleccione el motor de validación:")
    print(f"  {CYAN}1.{RESET} API chkr.cc (Recomendada - Rápida, Banco/País)")
    print(f"  {CYAN}2.{RESET} Formulario Web Personalizado (Scrapeo HTML)")
    motor = input(f"Seleccione opción [1-2, por defecto 1]: ").strip()
    
    try:
        limit_str = input("Límite de conexiones concurrentes [Por defecto: 5]: ").strip()
        limit = int(limit_str) if limit_str else 5
    except ValueError:
        limit = 5

    bar = ProgressBar(total=len(luhn_passed), prefix="Progreso", length=40)
    
    if motor == "2":
        url = input(f"URL del validador [Por defecto: https://www.creditcardvalidator.net/validate/]: ").strip()
        url = url or "https://www.creditcardvalidator.net/validate/"
        checker = AsyncCardChecker(url, concurrency_limit=limit)
        print(f"\n{BLUE}[*] Iniciando validación asíncrona en {url} de {len(luhn_passed)} tarjetas...{RESET}")
        input_list = [c["number"] for c in luhn_passed]
        api_mode = False
    else:
        checker = ChkrApiChecker(concurrency_limit=limit)
        print(f"\n{BLUE}[*] Iniciando validación asíncrona en API chkr.cc de {len(luhn_passed)} tarjetas...{RESET}")
        input_list = [c["formatted"] for c in luhn_passed]
        api_mode = True
        
    results = asyncio.run(checker.check_batch(input_list, progress_callback=bar.update))
    
    # Imprimir resultados consolidados
    print(f"\n{BOLD}=== RESULTADOS DE LA VALIDACIÓN WEB ==={RESET}")
    validas = []
    invalidas = []
    errores = []
    
    for r in results:
        card = r["card"]
        status = r["status"]
        msg = r["message"]
        
        if status == "valid":
            print(f"[{GREEN}LIVE{RESET}] {card} - {msg}")
            validas.append(card)
        elif status == "invalid":
            print(f"[{RED}DIE{RESET}] {card} - {msg}")
            invalidas.append(card)
        else:
            print(f"[{YELLOW}ERROR{RESET}] {card} - {msg}")
            errores.append(card)
            
    print(f"\n{BOLD}Resumen Web:{RESET}")
    print(f"  Válidas (LIVE):  {GREEN}{len(validas)}{RESET}")
    print(f"  Inválidas (DIE): {RED}{len(invalidas)}{RESET}")
    print(f"  Errores/Red:     {YELLOW}{len(errores)}{RESET}")
    
    if validas:
        save = input(f"\n¿Desea guardar las tarjetas válidas en un archivo? (s/n): ").strip().lower()
        if save == 's':
            filename = input("Nombre del archivo [validas.txt]: ").strip() or "validas.txt"
            try:
                with open(filename, "w") as f:
                    for c in validas:
                        f.write(f"{c}\n")
                print(f"{GREEN}[+] Guardado con éxito en {filename}.{RESET}")
            except Exception as e:
                print(f"{RED}[!] Error al guardar el archivo: {e}{RESET}")
                
    pause()

def main():
    while True:
        clear_screen()
        print_banner()
        print(" Seleccione la operación que desea realizar:")
        print(f"  {CYAN}1.{RESET} Generar tarjetas (Individual / Lote / BIN / Patrón)")
        print(f"  {CYAN}2.{RESET} Validar tarjetas (Individual / Lote / Archivo - Local y Web)")
        print(f"  {CYAN}3.{RESET} Salir")
        print(f"{CYAN}  ----------------------------------------------------------{RESET}")
        
        opc = input(f"{BOLD}Ingrese una opción [1-3]: {RESET}").strip()
        
        if opc == "1":
            menu_generar_tarjetas()
        elif opc == "2":
            menu_validar_tarjetas()
        elif opc == "3":
            print(f"\n{GREEN}[+] Saliendo de la herramienta de manera segura. ¡Hasta luego!{RESET}\n")
            break
        else:
            print(f"{RED}[!] Opción no reconocida.{RESET}")
            pause()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{RED}[!] Ejecución interrumpida por el usuario. Saliendo...{RESET}\n")
        sys.exit(0)
