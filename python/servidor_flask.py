import os
import sys
# import webbrowser  <-- Não precisamos mais disso
from threading import Timer
from datetime import datetime

# Tenta importar o Flask
try:
    from flask import Flask, send_from_directory, make_response, request
except ImportError:
    print("❌ A biblioteca 'flask' não está instalada.")
    print("   Por favor, execute: pip install flask")
    sys.exit(1)

# ========================================================
# 🛡️ CONFIGURAÇÃO DE SEGURANÇA
# ========================================================

# MODO_AUDITORIA:
# True  = Apenas avisa no console, mas deixa todo mundo entrar (para testes).
# False = BLOQUEIA quem não estiver na lista (Segurança Ativa).
MODO_AUDITORIA = False

# Lista de IPs ou Prefixos Autorizados
IPS_PERMITIDOS = [
    "127.0.0.1",      # Localhost (Essencial para você acessar do servidor)
    "10.184.40.",     # Rede Cabeada da Empresa (Toda a faixa 40.x)
    "10.184.24.",     # Rede Wi-Fi da Empresa (Toda a faixa 24.x)
    "187.32.5.240",    # IP Extra Autorizado
    "10.184.41.56"
] 

# ========================================================
# CONFIGURAÇÃO DE CAMINHOS
# ========================================================
DIRETORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_SCRIPT, ".."))

app = Flask(__name__, static_folder=DIRETORIO_RAIZ)
PORTA = 8080

# ========================================================
# MIDDLEWARE DE SEGURANÇA
# ========================================================
@app.before_request
def verificar_seguranca():
    # 1. Identifica o IP
    if request.headers.getlist("X-Forwarded-For"):
        ip_visitante = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip_visitante = request.remote_addr

    # 2. Verifica se bate com a lista
    permitido = False
    for prefixo in IPS_PERMITIDOS:
        if ip_visitante.startswith(prefixo):
            permitido = True
            break

    # 3. Logs e Ação
    hora = datetime.now().strftime("%H:%M:%S") 

    if permitido:
        print(f"[{hora}] ✅ Acesso Permitido: {ip_visitante}")
    else:
        if MODO_AUDITORIA:
            print(f"[{hora}] ⚠️  [AUDITORIA] Seria BLOQUEADO: {ip_visitante}")
        else:
            print(f"[{hora}] ❌ BLOQUEADO: {ip_visitante}")
            return f"Acesso Restrito. IP: {ip_visitante}", 403

# ========================================================
# ROTAS
# ========================================================
@app.route('/')
def index():
    return enviar_arquivo_no_cache('Monitoramento.html')

@app.route('/<path:path>')
def serve_static(path):
    return enviar_arquivo_no_cache(path)

def enviar_arquivo_no_cache(caminho_arquivo):
    try:
        response = make_response(send_from_directory(DIRETORIO_RAIZ, caminho_arquivo))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    except Exception:
        return "Arquivo não encontrado", 404

# Função removida pois não será mais usada
# def abrir_navegador():
#     webbrowser.open_new(f"http://127.0.0.1:{PORTA}/")

if __name__ == "__main__":
    print("="*60)
    print(f"🌍 SERVIDOR DE MONITORAMENTO (SECURE)")
    print(f"🛡️  Segurança: {'SOMENTE AUDITORIA' if MODO_AUDITORIA else 'BLOQUEIO ATIVO'}")
    print(f"📋 IPs Permitidos: {len(IPS_PERMITIDOS)} regras ativas")
    print(f"🚀 Rodando em: http://0.0.0.0:{PORTA}")
    print("="*60)
    
    # Comentei a linha abaixo para não abrir o navegador sozinho
    # Timer(1, abrir_navegador).start()
    
    app.run(host='0.0.0.0', port=PORTA, debug=False)