import os
import json

# ========================================================
# CONFIGURAÇÃO
# ========================================================
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(DIRETORIO_ATUAL, "..", "dados")

ARQUIVOS = [
    {"nome": "municipios.js", "variavel": "geoMunicipios"},
    {"nome": "estado.js", "variavel": "geoEstado"}
]

def limpar_e_corrigir(arquivo, nome_variavel):
    caminho = os.path.join(PASTA_DADOS, arquivo)
    print(f"🔧 Processando: {arquivo}...")

    if not os.path.exists(caminho):
        print(f"   [ERRO] Arquivo não encontrado: {caminho}")
        return

    try:
        # 1. Ler o conteúdo bruto
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # 2. Encontrar o início real do JSON
        inicio_json = conteudo.find('{')
        if inicio_json == -1:
            print("   [ERRO] Nenhuma chave '{' encontrada.")
            return

        # Pega tudo do início do JSON para a frente
        texto_para_analise = conteudo[inicio_json:]

        # 3. Decodificação Inteligente (Lê apenas o primeiro objeto válido)
        decoder = json.JSONDecoder()
        try:
            dados, indice_fim = decoder.raw_decode(texto_para_analise)
            print(f"   [OK] JSON válido encontrado e extraído com sucesso.")
            print(f"   (Ignorando {len(texto_para_analise) - indice_fim} caracteres de lixo no final)")
        except json.JSONDecodeError as e:
            print(f"   [ERRO] JSON inválido ou corrompido no início: {e}")
            return

        # 4. Salvar apenas a parte limpa
        # Converte de volta para string para garantir formatação limpa
        json_limpo = json.dumps(dados) 
        novo_conteudo = f"const {nome_variavel} = {json_limpo};\n"

        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(novo_conteudo)
        
        print(f"   [SUCESSO] Arquivo limpo e salvo!")

    except Exception as e:
        print(f"   [CRÍTICO] Erro inesperado: {e}")

if __name__ == "__main__":
    print("--- CIRURGIA DE DADOS GEOJSON ---")
    for item in ARQUIVOS:
        limpar_e_corrigir(item['nome'], item['variavel'])
    print("\n--- FIM ---")
    input("Pressione ENTER para sair...")