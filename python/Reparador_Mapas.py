import os
import json

# ========================================================
# CONFIGURAÇÃO DOS CAMINHOS
# ========================================================
# Pega a pasta onde este script está e sobe um nível para achar a 'dados'
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(DIRETORIO_ATUAL, "..", "dados")

# Lista de conversão: (Arquivo Original TXT, Arquivo Final JS, Variável JS)
ARQUIVOS = [
    {
        "origem": "Dados_Geojson_Municípios.txt",
        "destino": "municipios.js",
        "variavel": "geoMunicipios"
    },
    {
        "origem": "Dados_Geojson_Estado.txt",
        "destino": "estado.js",
        "variavel": "geoEstado"
    }
]

def converter_txt_para_js(config):
    caminho_origem = os.path.join(PASTA_DADOS, config["origem"])
    caminho_destino = os.path.join(PASTA_DADOS, config["destino"])

    print(f"🔄 Processando: {config['origem']}...")

    if not os.path.exists(caminho_origem):
        print(f"   [ERRO] Arquivo original não encontrado: {caminho_origem}")
        print(f"   Certifique-se de colocar o '{config['origem']}' na pasta 'dados'.")
        return

    try:
        # 1. Ler o conteúdo bruto
        with open(caminho_origem, 'r', encoding='utf-8') as f:
            conteudo = f.read().strip()

        # 2. Tentar limpar lixo no início/fim (caso tenha sobrado de edições manuais)
        # Procura o primeiro '{' e o último '}'
        inicio = conteudo.find('{')
        fim = conteudo.rfind('}')

        if inicio == -1 or fim == -1:
            print("   [ERRO] Não parece ser um JSON válido (faltam chaves).")
            return

        json_limpo = conteudo[inicio : fim + 1]

        # 3. Testar se o JSON é válido
        try:
            dados = json.loads(json_limpo)
            print("   [OK] JSON validado com sucesso.")
        except json.JSONDecodeError as e:
            print(f"   [ERRO] JSON inválido: {e}")
            return

        # 4. Salvar como JS
        # Usamos json.dumps para garantir que o formato no arquivo final seja perfeito
        conteudo_js = f"const {config['variavel']} = {json.dumps(dados)};\n"

        with open(caminho_destino, 'w', encoding='utf-8') as f:
            f.write(conteudo_js)
        
        print(f"   [SUCESSO] Criado: {config['destino']}")

    except Exception as e:
        print(f"   [CRÍTICO] Erro inesperado: {e}")

if __name__ == "__main__":
    print("=== REPARADOR DE MAPAS ===")
    # Verifica se a pasta dados existe
    if not os.path.exists(PASTA_DADOS):
        print(f"[ERRO] Pasta de dados não encontrada: {PASTA_DADOS}")
    else:
        for item in ARQUIVOS:
            converter_txt_para_js(item)
    
    print("\n=== FIM ===")
    input("Pressione ENTER para sair...")