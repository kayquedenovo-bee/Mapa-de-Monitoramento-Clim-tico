@echo off
TITLE Inicializador Monitoramento
echo ======================================================
echo      INICIANDO SISTEMA COMPLETO (PYTHON + NGROK)
echo ======================================================

:: 1. Navega para a pasta do projeto
cd /d "C:\Users\A21057766\Documents\Documentos\Mapa de Monitoramento climático\python"

:: 2. Abre o Servidor Python em uma NOVA janela independente
start "Servidor Flask (Local)" python servidor_flask.py

:: 3. Abre o Robô Agendador (Que lê o PDF e atualiza os dados)
:: Ele roda uma vez agora e depois fica aguardando os horarios agendados.
start "Robo Extrator (Agendador)" python agendador.py

:: 4. Abre o Ngrok em OUTRA janela independente
:: (Certifique-se de ter copiado o ngrok.exe para esta pasta 'python')
start "Link Publico Ngrok" ngrok http 5000

echo.
echo ---------------------------------------------------
echo  SISTEMA INICIADO!
echo  1. Janela 'Servidor Flask': Mantem o site no ar.
echo  2. Janela 'Robo Extrator': Atualiza os dados do PDF.
echo  3. Janela 'Link Ngrok': Gera o link para celular.
echo ---------------------------------------------------
echo.
pause