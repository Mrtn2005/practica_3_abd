from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from neo4j import GraphDatabase
from config import ConfiguracionFlask

# Los distintos objetos de la aplicacion se crean fuera del metodo create_app, para que esten
# disponibles para importar del resto de paquetes.

driver = None
_database = None
bootstrap = Bootstrap5()
csrf = CSRFProtect()
login_manager = LoginManager()


def query(cypher: str, **params):
    """
    Ejecuta una query Cypher contra la base de datos configurada en NEO4J_DATABASE.
    Envuelve driver.execute_query fijando siempre database_ al valor de la config,
    de forma que no se necesite pasar database_ en cada llamada.

    Devuelve todas las componentes de la llamada a execute_query (records, resumen y keys).
    """
    return driver.execute_query(cypher, database_=_database, **params)


def create_app() -> Flask:
    """
    Funcion que crea la instancia de la aplicacion de Flask
    """
    # Declaramos la instancia de la app de Flask
    app = Flask(__name__)

    # Configuramos la app utilizando el objeto que hemos declarado previamente
    app.config.from_object(ConfiguracionFlask())

    # Inicializamos el driver (unico por servidor Neo4j) y fijamos la base de datos
    global driver, _database
    driver = GraphDatabase.driver(
        app.config['NEO4J_URI'],
        auth=(app.config['NEO4J_USER'], app.config['NEO4J_PASSWORD'])
    )
    _database = app.config['NEO4J_DATABASE']

    # Inicializamos los distintos componentes de la app
    bootstrap.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Ruta a la que redirige Flask-Login cuando se requiere autenticacion
    login_manager.login_view = 'log_in'
    login_manager.login_message = 'Debes iniciar sesion para acceder a esta pagina.'

    # Vinculamos las rutas del modulo "rutas"
    with app.app_context():
        from . import rutas

    return app
