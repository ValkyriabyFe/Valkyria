#!/bin/bash

cd /home/felipe_weissmann_93

echo "Iniciando ValKyria com monitoramento..."

# Função para reiniciar se algum processo cair
while true; do
    echo "Reiniciando módulos em $(date)"

    # Executa todos os scripts
    python3 valkyriabot.py &          
    BOT_PID=$!

    python3 telegram_listener.py &    
    LISTENER_PID=$!

    python3 main.py                   
    MAIN_PID=$!

    # Espera o processo principal terminar
    wait $MAIN_PID

    echo "Algum processo caiu. Reiniciando todos os módulos em 5 segundos..."
    kill $BOT_PID $LISTENER_PID 2>/dev/null
    sleep 5
done
