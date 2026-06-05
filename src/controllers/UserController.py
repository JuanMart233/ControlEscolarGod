from src.models.UserModel import (
    login, registrar, get_especialidades, get_perfil, guardar_perfil,
    get_materias, agregar_materia, get_calificaciones,
    guardar_calificacion, get_promedio_general
)


def autenticar(nombre_usuario, contrasenia):
    return login(nombre_usuario, contrasenia)

def crear_usuario(nombre_usuario, contrasenia, id_especialidad):
    return registrar(nombre_usuario, contrasenia, id_especialidad)

def obtener_especialidades():
    return get_especialidades()

def obtener_perfil(id_usuario):
    return get_perfil(id_usuario)

def actualizar_perfil(id_usuario, datos):
    return guardar_perfil(id_usuario, datos)

def obtener_materias(id_especialidad, semestre):
    return get_materias(id_especialidad, semestre)

def nueva_materia(nombre, semestre, id_especialidad):
    return agregar_materia(nombre, semestre, id_especialidad)

def obtener_calificaciones(id_alumno, semestre):
    return get_calificaciones(id_alumno, semestre)

def guardar_calif(id_alumno, id_materia, semestre, u1, u2, u3):
    return guardar_calificacion(id_alumno, id_materia, semestre, u1, u2, u3)

def promedio_general(id_alumno):
    return get_promedio_general(id_alumno)
