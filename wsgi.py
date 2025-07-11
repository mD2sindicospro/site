from app import create_app
import os

# Determina o ambiente
config_name = os.getenv('FLASK_ENV', 'production')
app = create_app(config_name)

if __name__ == '__main__':
    app.run() 