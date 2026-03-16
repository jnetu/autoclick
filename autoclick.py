from pynput.mouse import Listener, Button, Controller
import threading
import time
import sys
from collections import deque

mouse = Controller()

def click_mouse():
    mouse.press(Button.left)
    mouse.release(Button.left)

class Cores:
    VERDE = '\033[92m'
    VERMELHO = '\033[91m'
    AZUL_MARINHO = '\033[34m'
    AMARELO = '\033[93m'
    RESET = '\033[0m'
    BRANCO = '\033[97m'
    CIANO = '\033[36m'

running = False
click_interval = 1
clicks_per_second = 0
num_threads = 6

click_history = deque(maxlen=120)
history_lock = threading.Lock()
state_lock = threading.Lock()

def auto_click_worker(thread_id):
    global running, click_interval, clicks_per_second
    
    while True:
        with state_lock:
            interval = click_interval
            should_run = running
        
        if should_run:
            try:
                click_mouse()
                
                current_time = time.time()
                with history_lock:
                    click_history.append(current_time)
                    
                    if click_history and len(click_history) > 1:
                        time_span = current_time - click_history[0]
                        if time_span > 0.05:
                            clicks_per_second = len(click_history) / time_span
            except Exception as e:
                pass
            
            if interval > 0:
                time.sleep(interval)
        else:
            time.sleep(0.01)


def toggle_auto_click():
    global running
    with state_lock:
        running = not running
        if running:
            print(f"{Cores.VERDE}✓ AUTO CLICK ATIVADO ({num_threads} threads - pynput){Cores.RESET}")
        else:
            print(f"{Cores.VERMELHO}✗ AUTO CLICK DESATIVADO{Cores.RESET}")

def on_click(x, y, button, pressed):
    if button == Button.x2 and pressed:
        toggle_auto_click()

def read_user_input():
    global click_interval, clicks_per_second
    while True:
        try:
            user_input = input().strip()
            if user_input:
                try:
                    novo_intervalo = float(user_input)
                    if novo_intervalo >= 0:
                        with state_lock:
                            click_interval = novo_intervalo
                        with history_lock:
                            cps = clicks_per_second
                        print(f"{Cores.AZUL_MARINHO}INTERVALO ATUALIZADO: {novo_intervalo} segundos{Cores.RESET}")
                        with state_lock:
                            status = "ATIVADO" if running else "DESATIVADO"
                        cor = Cores.VERDE if running else Cores.VERMELHO
                        if running:
                            print(f"Status: {cor}{status}{Cores.RESET} | Intervalo: {novo_intervalo}s | {Cores.CIANO}CPS: {cps:.1f}{Cores.RESET}")
                        else:
                            print(f"Status: {cor}{status}{Cores.RESET} | Intervalo: {novo_intervalo}s")
                    else:
                        print(f"{Cores.VERMELHO}✗ Erro: O intervalo não pode ser negativo!{Cores.RESET}")
                except ValueError:
                    print(f"{Cores.VERMELHO}✗ Erro: Digite um número válido (ex: 1, 0.5, 0.0001, 0){Cores.RESET}")
        except EOFError:
            break
        except Exception as e:
            print(f"{Cores.VERMELHO}✗ Erro: {e}{Cores.RESET}")

def monitor_cps():
    global clicks_per_second
    while True:
        time.sleep(0.3)
        with state_lock:
            is_running = running
        with history_lock:
            cps = clicks_per_second
        if is_running and cps > 0:
            sys.stdout.write(f"\r{Cores.CIANO}[CPS: {cps:.1f}]{Cores.RESET}  ")
            sys.stdout.flush()

# Inicia as threads
print(f"{Cores.AMARELO}{'='*70}{Cores.RESET}")
print(f"{Cores.BRANCO}AUTO CLICK ULTRA-RÁPIDO COM PYNPUT (15+ CPS){Cores.RESET}")
print(f"{Cores.AMARELO}{'='*70}{Cores.RESET}")
print(f"\n{Cores.BRANCO}Instruções:{Cores.RESET}")
print(f"  • Pressione o botão thumb do mouse (lateral) para {Cores.VERDE}ATIVAR/DESATIVAR{Cores.RESET}")
print(f"  • Digite um número e pressione ENTER para alterar velocidade:")
print(f"    - {Cores.VERDE}0{Cores.RESET} = máxima velocidade (recomendado para 15+ CPS)")
print(f"    - {Cores.VERDE}0.0001{Cores.RESET} = ultra rápido com pequeno controle")
print(f"    - {Cores.VERDE}1{Cores.RESET} = 1 clique por segundo")
print(f"  • {Cores.VERDE}Verde{Cores.RESET} = ativado | {Cores.VERMELHO}Vermelho{Cores.RESET} = desativado")
print(f"  • {Cores.AZUL_MARINHO}Azul marinho{Cores.RESET} = configuração atualizada")
print(f"  • {Cores.CIANO}Ciano{Cores.RESET} = cliques por segundo (CPS) em tempo real")
print(f"  • Usa {num_threads} threads paralelas + pynput para máxima velocidade\n")

input_thread = threading.Thread(target=read_user_input, daemon=True)
input_thread.start()
monitor_thread = threading.Thread(target=monitor_cps, daemon=True)
monitor_thread.start()
for i in range(num_threads):
    threading.Thread(target=auto_click_worker, args=(i,), daemon=True).start()

try:
    with Listener(on_click=on_click) as listener:
        listener.join()
except KeyboardInterrupt:
    print(f"\n{Cores.AMARELO}Encerrando...{Cores.RESET}")
    sys.exit(0)
