import os
from app import create_app

# Detectar si estamos en Lambda
# En Lambda, Zappa detecta automáticamente y usa la app
# create_app detectará el entorno automáticamente
app = create_app()

if __name__ == '__main__':
    # Solo se ejecuta en desarrollo local
    app.run(debug=True, host='0.0.0.0', port=5000)
