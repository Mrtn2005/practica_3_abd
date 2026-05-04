"""
Modulo de Python que contiene el enrutado de Fdinder
"""
import os
import uuid
from flask import current_app as app, render_template, redirect, url_for, flash, abort, request, make_response, \
    send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from . import query, login_manager
from .modelos import Persona
from .formularios import SignInForm, SignupForm, MensajeForm, ConfirmarMatchForm, DEFAULT_FOTO_URL


# NOTA: todas las consultas a Neo4j se realizan a traves de la funcion query() definida
# en app/__init__.py. Dicha funcion envuelve driver.execute_query fijando siempre la base
# de datos configurada en NEO4J_DATABASE, de forma que no es necesario pasarla aqui.
# Cada llamada abre y cierra su propia transaccion automaticamente (sin session explicita).


@app.route('/profiles/<path:filename>')
@login_required
def foto_perfil(filename: str):
    """
    NO HAY QUE MODIFICAR.

    Sirve fotos de perfil almacenadas fuera de "static/" (requiere autenticacion).
    """
    return send_from_directory(
        os.path.join(app.root_path, 'profiles'),
        filename
    )


@login_manager.user_loader
def carga_usuario(id_usuario: str):
    """
    Tal y como indican los apuntes, debe cargar el objeto Persona asociado
    a id_usuario si existe, o devolver None en caso contrario. Para ello, utiliza
    el metodo Persona.from_node().
    """

    cypher = "MATCH (p:Persona {id: $id_usuario}) RETURN p" #La consulta

    records, _, _ = query(cypher, id_usuario=id_usuario) #Solo necesito records por eso las demas pongo un guion
    if records:

        nodo_persona = records[0]["p"] #Solo hay una cosa y esta dentro de p
        return Persona.from_node(nodo_persona)

    return None


@app.route('/')
@app.route('/log_in', methods=['GET', 'POST'])
def log_in():
    """
    Acceso de un usuario ya registrado.
    Acepta tanto peticiones GET como POST.

    En esta funcion de vista se renderiza el formulario de acceso (SignInForm) con el
    template 'log_in.html'. Una vez el usuario introduzca datos correctamente,
    se comprueba si hay un nodo Persona con ese email en Neo4j.
    - Si no existe: mensaje flash "El email introducido no tiene un usuario asociado".
    - Si existe pero la contrasena es incorrecta: mensaje flash "Contraseña incorrecta".
    - Si las credenciales son correctas: login y redireccion a 'explorar'.
    """
    formulario = SignInForm()

    if formulario.validate_on_submit(): #Q los datos no estén vacíos y por seguridad
        email = formulario.email.data
        contrasena = formulario.password.data

        cypher = "MATCH (p:Persona {email: $email}) RETURN p"
        records, _, _ = query(cypher, email=email)

        if not records: #Si no existe
            flash("El email introducido no tiene un usuario asociado")
        else:
            nodo_persona = records[0]["p"]
            usuario = Persona.from_node(nodo_persona)

            if not usuario.check_password(contrasena): #Si la contraseña es incprrecta
                flash("La contrasena es incorrecta")
            else:
                login_user(usuario)
                return redirect(url_for('explorar'))

    return render_template('log_in.html', form=formulario)


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    """
    Registro completo de un usuario. Acepta GET y POST.
    Para ello, se utiliza el formulario SignupForm.

    En esta funcion de vista renderiza el formulario de acceso (SignupForm) con el
    template 'sign_up.html'.

    - Para peticiones GET o si el formulario no se valida correctamente, se renderiza este template.

    - Si el formulario se valida correctamente, se debe comprobar si existe ya un usuario con ese email.
      En tal caso, se lanza el mensaje flash "Ya existe un usuario con este email" y se renderiza el template.

        Si no existe, se guarda la foto en la carpeta "profiles/" con el siguiente codigo:

        nuevo_id = str(uuid.uuid4())
        archivo = form.data["foto"]
        if archivo and archivo.filename:
            ext = archivo.filename.rsplit('.', 1)[-1].lower()
            archivo.save(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'profiles', f'{nuevo_id}.{ext}'))
            foto_url = f'/profiles/{nuevo_id}.{ext}'
        else:
            foto_url = DEFAULT_FOTO_URL

        y se crean los siguientes nodos y relaciones:

        * Nodo Persona con toda la informacion, incluyendo la variable foto_url del codigo anterior. Utiliza como id la
          variable "nuevo_id" anterior.
        * Informacion para denotar la edad (nodo Edad y relacion TIENE_EDAD).
        * Informacion para denotar las preferencias de edad (nodo Edad y relacion BUSCA_EDAD). Recuerda el operador UNWIND.

      Finalmente hace login y redirige a explorar.
    """
    formulario = SignupForm()

    if formulario.validate_on_submit():
        email = formulario.email.data

        cypher = "MATCH (p:Persona {email: $email}) RETURN p"
        records, _, _ = query(cypher, email=email)

        if records:
            flash("Ya existe un usuario con este email")
            return render_template('sign_up.html', form=formulario)

        nuevo_id = str(uuid.uuid4())
        archivo = formulario.data["foto"]
        if archivo and archivo.filename:
            ext = archivo.filename.rsplit('.', 1)[-1].lower()
            archivo.save(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'profiles', f'{nuevo_id}.{ext}'))
            foto_url = f'/profiles/{nuevo_id}.{ext}'
        else:
            foto_url = DEFAULT_FOTO_URL

        nombre = formulario.nombre.data
        password = formulario.password.data
        edad = formulario.edad.data
        edad_min = formulario.busca_edad_min.data
        edad_max = formulario.busca_edad_max.data

        cypher = """
        CREATE (p:Persona {id: $id_nuevo, nombre: $nombre, email: $email, password_hash: $password. foto_url: $foto_url})
        
        MERGE (e1:Edad {valor: $edad})
        CREATE (p)-[:TIENE_EDAD]->(e1)
        
        WITH p
        UNWIND $rango_edades AS edad_buscada
        MERGE (e2:Edad {valor: edad_buscada})
        CREATE (p)-[:BUSCA_EDAD]->(e2)
        """







@app.route('/log_out')
@login_required
def log_out():
    """
    Desconexion de un usuario. Requiere estar autenticado.
    Hace logout, manda un mensaje flash y redirige al login.
    """
    logout_user()
    flash("usuario logout")
    return redirect(url_for('login_in'))


@app.route('/explorar')
@login_required
def explorar():
    """
    Ruta que muestra 100 candidatos compatibles con el usuario actual.

    Los candidatos a mostrar deben cumplir las siguientes restricciones:

    * Los candidatos compatibles tienen que tener la edad de acuerdo con las
    edades que busca el usuario actual (BUSCA_EDAD) y viceversa.

    * El usuario actual no ha intentado hacer match o ha rechazado previamente al candidato
      (relaciones QUIERE_MATCH y HA_RECHAZADO).

    * El usuario actual no esta actualmente en un MatchActivo (con la relacion :ACEPTA) con el candidato.

    Además, los candidatos se deben ordenar por el numero de personas
    'personas en comun' de forma descendente. Las personas comunes son aquellas
    que estan conectadas a traves de a lo sumo 4 relaciones :QUIERE_MATCH del candidato,
    y a otras cuatro relaciones a lo sumo del usuario actual (da igual el orden de las relaciones).

    Como resultado, se renderiza el template "explorar.html". Si el campo 'foto_url' es None, entonces
    se debe asignar el valor DEFAULT_FOTO_URL.
    """
    abort(404)


@app.route('/aceptar/<id_persona>', methods=['POST'])
@login_required
def aceptar(id_persona: str):
    """
    Swipe right sobre una Persona.

    Se siguen los siguientes pasos:
      1. Si la persona no existe, se aborta con un error 404.

      2. Se debe detectar si se ha formado un ciclo con la persona con la que se quiere hacer match.
         Aqui distinguimos varios casos:

        2.1 Sin ciclo: Se crea la relacion (yo)-[:QUIERE_MATCH]->(candidato) con MERGE a la espera de que
                       la otra persona tambien acepte (o no).
        2.2 Si hay un ciclo de longitud 1 (el candidato tambien ha hecho Swipe y es mutuo): match directo entre
                                  dos personas, se crea MatchActivo{estado:"activo"} con ACEPTA con confirmado:true.
        2.3 Si todos los ciclos son de longitud > 1: match poliamoroso, se crea MatchActivo con {estado:"pendiente"}
                                  y todos los participantes del ciclo reciben ACEPTA con confirmado:false.

      En los casos 2.2 y 2.3 se eliminan todos los QUIERE_MATCH entre participantes.

      Como resultado, la funcion devuelve una respuesta 204 con make_response('', 204)
    """
    abort(404)


@app.route('/rechazar/<id_persona>', methods=['POST'])
@login_required
def rechazar(id_persona: str):
    """
    Swipe left sobre una Persona. Solo acepta POST.
    Registra la relacion HA_RECHAZADO con MERGE para que ese
    candidato no vuelva a aparecer en /explorar. No hace falta gestionar el caso de que
    el usuario ya haya rechazado previamente a la persona (MERGE repite la creacion).

    Como resultado, la funcion devuelve una respuesta 204 con make_response('', 204)
    """
    cypher = """
            MATCH (yo:Persona {id: $mi_id})
            MATCH (candidato:Persona {id: $su_id})
            MERGE (yo)-[:HA_RECHAZADO]->(candidato)
            """
    query(cypher, mi_id=current_user.id, su_id=id_persona)
    return make_response('', 204)



@app.route('/matches')
@login_required
def matches():
    """
    Lista los matches del usuario actual. Solo acepta GET.
    Muestra tanto los matches activos como los pendientes de confirmar.
    Para cada match se carga: resto de participantes, numero de mensajes
    y fecha del ultimo mensaje. Los resultados se deben ordenar por la fecha
    del ultimo mensaje de forma descendente (la funcion max sobre fechas devuelve la
    fecha mas reciente).

    Como resultado, se debe renderizar el template "matches.html".
    """
    abort(404)


@app.route('/match/<id_match>', methods=['GET', 'POST'])
@login_required
def match(id_match: str):
    """
    Ruta que explora un match concreto. Acepta tanto metodos GET como POST porque permite visualizar
    participantes y mensajes (GET) o enviar mensajes utilizando el formulario MensajeForm (POST).

    Devuelve 404 si el match no existe o el usuario no participa.


    * Si se manda una peticion POST, el formulario se valida correctamente y el estado del match es activo (y no pendiente),
      se debe crear un mensaje por parte del usuario actual a ese match. Como resultado, se redirige a la ruta "math/<id-match>"
      con el match actual.

    * En caso contrario, se renderiza el template "match_detalle.html". Para ello, hay que cargar los mensajes
      cronologicamente de forma ascendente (del mas antiguo al mas nuevo).
    """
    abort(404)


@app.route('/confirmar_match/<id_match>', methods=['GET', 'POST'])
@login_required
def confirmar_match(id_match: str):
    """
    Confirmacion o rechazo de un match poliamoroso pendiente. Acepta GET y POST.
    Si no existe un MatchActivo entre el usuario actual y el id del match, entonces
    se aborta con un error 404. Hay que gestionar 3 casos:

    -> GET: muestra el template "confirmar_match.html" con los participantes
            del match pendiente y los botones para aceptar o rechazar. Para ello,
            utilizar el formulario ConfirmarMatchForm.

    -> Con POST, hay dos variantes en funcion del valor del campo 'accion' del formulario:
      * Si el formulario tiene accion='aceptar':
        - Se marca la relacion ACEPTA del usuario actual como confirmado=true.
        - Si todos los participantes han confirmado, el match pasa a estado 'activo'
          y se redirige a la ruta asociada a ese match.
        - Si hay algun participante que no haya confirmado, se redirige a la lista de matches.

      * Si el formulario tiene accion='rechazar':
        - Se crean relaciones HA_RECHAZADO entre todos los participantes para que no
          vuelvan a aparecer entre si en /explorar, y se elimina el MatchActivo directamente.
          Se redirige a la lista de matches.
    """
    abort(404)
