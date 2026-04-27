"""
Modulo en el que definimos los formularios de la aplicacion Fdinder
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField,
                     IntegerField, TextAreaField, HiddenField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

DEFAULT_FOTO_URL = '/static/default_avatar.svg'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}


class SignInForm(FlaskForm):
    """Formulario de inicio de sesion"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Entrar')


class SignupForm(FlaskForm):
    """Formulario de registro: crea la Persona y todo su perfil en un solo paso"""
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repite la contraseña',
        validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden')]
    )
    foto = FileField(
        'Foto de perfil (opcional)',
        validators=[Optional(), FileAllowed(ALLOWED_EXTENSIONS, 'Solo imágenes jpg/png/webp')]
    )
    edad = IntegerField('Tu edad', validators=[DataRequired(), NumberRange(min=18, max=99)])
    busca_edad_min = IntegerField(
        'Edad mínima buscada',
        validators=[DataRequired(), NumberRange(min=18, max=99)]
    )
    busca_edad_max = IntegerField(
        'Edad máxima buscada',
        validators=[DataRequired(), NumberRange(min=18, max=99)]
    )
    submit = SubmitField('Crear cuenta')


class MensajeForm(FlaskForm):
    """Formulario para enviar un mensaje en un match"""
    contenido = TextAreaField(
        'Mensaje',
        validators=[DataRequired(), Length(min=1, max=500)]
    )
    submit = SubmitField('Enviar')


class ConfirmarMatchForm(FlaskForm):
    """Formulario para aceptar o rechazar un match poliamoroso pendiente"""
    accion = HiddenField('accion', validators=[DataRequired()])
    submit = SubmitField('Confirmar')
