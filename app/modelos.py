"""
Modulo que contiene los modelos de la aplicacion.
La clase Persona implementa UserMixin para integrarse con Flask-Login.
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Persona(UserMixin):
    """
    Clase que representa a un usuario de Fdinder.
    Implementa UserMixin para que Flask-Login pueda gestionarla.
    """

    def __init__(self, id: str, nombre: str, email: str,
                 password_hash: str = None, foto_url: str = None,
                 preferences: dict = None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password_hash = password_hash
        self.foto_url = foto_url
        self.preferences = preferences or {}

    @staticmethod
    def from_node(node) -> 'Persona':
        """
        Construye un objeto Persona a partir de un nodo Neo4j.
        """
        return Persona(
            id=node['id'],
            nombre=node['nombre'],
            email=node['email'],
            password_hash=node.get('password_hash'),
            foto_url=node.get('foto_url'),
            preferences=node.get('preferences', {})
        )

    # Con property, especificamos que password se puede acceder como un atributo,
    # de la forma usuario.password. Es un getter encubierto
    @property
    def password(self):
        raise AttributeError('No se puede leer el atributo password')

    # Especificando `nombre_propiedad.setter`, definimos la función setter. Esta función
    # se invoca siempre que asignemos al atributo un nuevo valor. En este caso, cuando hagamos usuario.password
    @password.setter
    def password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
