#!/bin/bash

cd /home/felipe_weissmann_93/Valkyria

echo "Iniciando Valkyria com monitoramento..."

# Loop infinito para reiniciar caso algum processo caia
while true; do
    echo "Reiniciando módulos em $(date)"

    # Inicia valkyriabot.py em segundo plano
    python3 valkyriabot.py &
    BOT_PID=$!

    # Inicia telegram_listener.py em segundo plano
    python3 telegram_listener.py &
    LISTENER_PID=$!

    # Inicia main.py em segundo plano
    python3 main.py &
    MAIN_PID=$!

    # Aguarda o main.py finalizar
    wait $MAIN_PID

    # Quando algum cair, reinicia todos
    echo "Algum processo caiu. Reiniciando todos os módulos em 5 segundos..."
    kill $BOT_PID $LISTENER_PID 2>/dev/null
    sleep 5
done
