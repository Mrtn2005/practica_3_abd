import os
from dotenv import load_dotenv

load_dotenv(override=True)


class ConfiguracionFlask:
    """
    Clase con todas las variables de configuracion de Flask
    """

    # Secret key: string largo para configurar la proteccion CSRF y sesiones
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Si ponemos el flag DEBUG a true, Flask se ejecutara en modo 'debug'.
    # NO USAR EN PRODUCCION
    DEBUG = True

    # URI de conexion al servidor Neo4j (formato bolt)
    NEO4J_URI = f'neo4j://{os.getenv("HOST")}:{os.getenv("PORT")}'

    # Credenciales de Neo4j
    NEO4J_USER = os.getenv('USER')
    NEO4J_PASSWORD = os.getenv('PASSWORD')

    # Bases de datos
    NEO4J_DATABASE = os.getenv('DATABASE')