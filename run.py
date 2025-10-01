import os
from app import create_app

# Detectar si estamos en Lambda
if os.environ.get('LAMBDA_TASK_ROOT'):
    # Producción en Lambda
    app = create_app('production')
else:
    # Desarrollo local
    app = create_app('development')

if __name__ == '__main__':
    app.run(debug=True)
