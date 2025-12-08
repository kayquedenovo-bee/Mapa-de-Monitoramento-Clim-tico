import pandas as pd
import pdfplumber
import re
import os
import json
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
BASE_USER = os.environ['USERPROFILE']
# Caminho do OneDrive (Entrada)
PASTA_PDFS = os.path.join(BASE_USER, "OneDrive - GRUPO EQUATORIAL ENERGIA", "Arquivos de Derivan Oliveira Silva Filho - BOT ClimaTempo")
# Caminho do Projeto (Saída)
PASTA_PROJETO = os.path.join(BASE_USER, "Documents", "Documentos", "Mapa de Monitoramento climático")
# Arquivo JS Final
ARQUIVO_JS_SAIDA = os.path.join(PASTA_PROJETO, "js", "climaticos.js")

# Data Automática (Hoje)
DATA_HOJE = datetime.now().strftime("%Y_%m_%d")

NOME_ARQUIVO_PDF = os.path.join(PASTA_PDFS, f"Equatorial GO_{DATA_HOJE}.pdf")

# REGEX GERAIS
REGEX_CHUVA = re.compile(r'(\d+[\.,]?\d*)\s*mm|mm\s*(\d+[\.,]?\d*)', re.IGNORECASE)
REGEX_VENTO = re.compile(r'Ventos:.*?\s*(\d+)', re.IGNORECASE)
REGEX_DATA = re.compile(r'(\d{2}/\d{2}/\d{4})')

# --- REGEX DE CABEÇALHO (SUPER FLEXÍVEL) ---
# Agora aceita:
# 1. Dias com ou sem "-feira" (Ex: "Domingo (07):", "Sábado (06):")
# 2. Apenas o dia entre parênteses (Ex: "(07):")
REGEX_CABECALHO_AVISO = re.compile(
    r'((?:(?:Segunda|Terça|Quarta|Quinta|Sexta|S[aá]bado|Domingo)(?:-feira)?|\(\d{2}\)).*?):', 
    re.IGNORECASE | re.DOTALL
)

# Regex para pegar os números (dias) dentro do cabeçalho que foi encontrado acima
REGEX_NUMEROS_DIA = re.compile(r'\((\d{2})\)')

def extrair_dados_celula(texto):
    """Extrai chuva e vento de uma célula da tabela."""
    if texto is None: return None, None
    t = texto.replace("\n", " ")
    c, v = None, None
    
    m_c = REGEX_CHUVA.search(t)
    if m_c: c = float((m_c.group(1) or m_c.group(2)).replace(",", "."))
    
    m_v = REGEX_VENTO.search(t)
    if m_v: v = int(m_v.group(1))
    
    return c, v

def extrair_avisos_por_dia(pdf, datas_encontradas):
    """
    Lê o texto do cabeçalho, lida com dias agrupados e dias isolados.
    """
    print("Processando avisos diários...")
    avisos_map = {} 
    
    try:
        # Extrai texto da primeira página
        texto_completo = pdf.pages[0].extract_text()
        
        # Limpeza bruta: Remove a parte da tabela para baixo
        if "Regional" in texto_completo:
            texto_bruto_topo = texto_completo.split("Regional")[0]
        else:
            texto_bruto_topo = texto_completo

        # Busca todos os cabeçalhos flexíveis
        matches = list(REGEX_CABECALHO_AVISO.finditer(texto_bruto_topo))
        
        if not matches:
            print("[AVISO] Nenhum aviso textual identificado no topo do PDF.")
            return {d: "Consulte o relatório completo." for d in datas_encontradas}

        for i, match in enumerate(matches):
            cabecalho_texto = match.group(1) # Ex: "Domingo (07)"
            inicio_msg = match.end() # Onde termina o ":"
            
            # O fim da mensagem é o início do próximo cabeçalho ou o fim do texto
            fim_msg = matches[i+1].start() if i + 1 < len(matches) else len(texto_bruto_topo)
            
            mensagem = texto_bruto_topo[inicio_msg:fim_msg].strip().replace('\n', ' ')
            
            # Procura TODOS os dias mencionados neste cabeçalho (Ex: "05", "06", "07")
            dias_no_cabecalho = REGEX_NUMEROS_DIA.findall(cabecalho_texto)
            
            for dia_num in dias_no_cabecalho:
                # Associa o dia "07" à data completa "07/12/2025"
                data_completa = next((d for d in datas_encontradas if d.startswith(dia_num)), None)
                
                if data_completa:
                    avisos_map[data_completa] = mensagem
                    print(f"   -> Aviso encontrado para {data_completa}")

    except Exception as e:
        print(f"[ERRO] Falha ao processar avisos de texto: {e}")
    
    # Preenche dias vazios
    for d in datas_encontradas:
        if d not in avisos_map:
            avisos_map[d] = "Sem avisos de destaque para este dia."
            
    return avisos_map

def processar_pdf(caminho):
    print(f"Lendo: {caminho}")
    if not os.path.exists(caminho):
        print("[ERRO] PDF não encontrado.")
        return None, None

    dados = []
    dias_globais = [] 
    ts = { "vertical_strategy": "lines", "horizontal_strategy": "lines", "snap_tolerance": 3, "text_tolerance": 3 }
    
    try:
        with pdfplumber.open(caminho) as pdf:
            # 1. Extrair Tabelas (Prioridade para pegar as datas primeiro)
            for p in pdf.pages:
                tabs = p.extract_tables(ts)
                for tab in tabs:
                    reg = None
                    for lin in tab:
                        if not lin or len(lin)<7: continue
                        
                        # Cabeçalho de datas
                        if "feira" in (lin[2] or "").lower() and not dias_globais:
                            temp = []
                            for cel in lin[2:]:
                                m = REGEX_DATA.search(cel or "")
                                if m: temp.append(m.group(1))
                            if len(temp)>=5: dias_globais = temp
                            continue
                        
                        if not dias_globais: continue
                        
                        # Extração de linhas
                        if lin[0] and "Regional" in lin[0]: reg = lin[0].replace("\n", " ").strip()
                        mun = lin[1].replace("\n", " ").strip() if lin[1] else None
                        if not mun: continue
                        
                        for i, cel in enumerate(lin[2:7]):
                            if i < len(dias_globais):
                                c, v = extrair_dados_celula(cel)
                                dados.append({ "Regional": reg, "Municipio": mun, "Data": dias_globais[i], "Chuva_mm": c, "Vento_KmH": v })
            
            # 2. Extrair avisos textuais
            if dias_globais:
                avisos_dict = extrair_avisos_por_dia(pdf, dias_globais)
            else:
                avisos_dict = {}
        
        return pd.DataFrame(dados).drop_duplicates(), avisos_dict

    except Exception as e:
        print(f"[ERRO] {e}")
        return None, None

def gerar_js(df, avisos_map, saida):
    if df is None or df.empty: return False
    
    lista = []
    for (reg, mun), d in df.groupby(["Regional", "Municipio"]):
        entry = { "regional": reg, "municipio": mun.upper(), "dados": [] }
        try: d = d.sort_values("Data", key=lambda x: pd.to_datetime(x, format="%d/%m/%Y"))
        except: pass
        for _, r in d.iterrows():
            entry["dados"].append({ "data": r["Data"], "chuva_mm": r["Chuva_mm"] or 0.0, "vento_kmh": r["Vento_KmH"] or 0 })
        lista.append(entry)
    
    json_dados = json.dumps(lista, indent=4, ensure_ascii=False)
    json_avisos = json.dumps(avisos_map, indent=4, ensure_ascii=False)
    
    conteudo = f"const previsaoCompleta = {json_dados};\nconst avisosPorDia = {json_avisos};"
    
    try:
        os.makedirs(os.path.dirname(saida), exist_ok=True)
        with open(saida, "w", encoding="utf-8") as f: f.write(conteudo)
        print(f"[SUCESSO] JS salvo em: {saida}")
        return True
    except Exception as e:
        print(f"[ERRO] Salvar JS: {e}")
        return False

if __name__ == "__main__":
    df_res, avisos_res = processar_pdf(NOME_ARQUIVO_PDF)
    if df_res is not None: 
        gerar_js(df_res, avisos_res, ARQUIVO_JS_SAIDA)