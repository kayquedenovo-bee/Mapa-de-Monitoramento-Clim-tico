import time
import datetime
import subprocess
import os
import sys

# ========================================================
# CONFIGURAÇÃO
# ========================================================
USUARIO_ATUAL = os.environ['USERPROFILE']
CAMINHO_PYTHON = sys.executable

# Caminho absoluto (seguro para inicialização automática)
PASTA_DO_SCRIPT = r"C:\Users\A21057766\Documents\Documentos\Mapa de Monitoramento climático\python"
NOME_SCRIPT_EXTRATOR = "Extrator_Dados.py"

# Horários de Execução
HORARIOS_EXECUCAO = ["08:00", "10:00"]

# ========================================================
# FUNÇÕES
# ========================================================
def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def executar_tarefa():
    log(f"⏰ Iniciando atualização...")
    
    # Validações de caminho
    if not os.path.exists(PASTA_DO_SCRIPT):
        log(f"[ERRO] Pasta não existe: {PASTA_DO_SCRIPT}")
        return
    
    script = os.path.join(PASTA_DO_SCRIPT, NOME_SCRIPT_EXTRATOR)
    if not os.path.exists(script):
        log(f"[ERRO] Script não encontrado: {script}")
        return

    try:
        # Executa o extrator
        res = subprocess.run(
            [CAMINHO_PYTHON, script], 
            cwd=PASTA_DO_SCRIPT, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='ignore'
        )
        
        # Logs de Saída
        if res.stdout: 
            print("--- SAÍDA ---\n" + res.stdout.strip())
            
        if res.returncode == 0: 
            log("✅ Sucesso!")
        else: 
            log("❌ Erro.")
            if res.stderr: 
                print("--- ERROS ---\n" + res.stderr)
                
    except Exception as e:
        log(f"[CRÍTICO] {e}")

# ========================================================
# LOOP PRINCIPAL
# ========================================================
if __name__ == "__main__":
    print(f"--- ROBÔ ATIVO ---")
    print(f"Pasta: {PASTA_DO_SCRIPT}")
    print(f"Horários: {HORARIOS_EXECUCAO}")
    
    print("Teste inicial de boot...")
    executar_tarefa()
    
    print("A aguardar horários...")

    while True:
        agora = datetime.datetime.now().strftime("%H:%M")
        
        if agora in HORARIOS_EXECUCAO:
            executar_tarefa()
            # Espera 61 segundos para não repetir no mesmo minuto
            time.sleep(61)
        else:
            # Verifica novamente em 30 segundos
            time.sleep(30)