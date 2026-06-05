import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import bcrypt
from Database.database import get_connection


# ── AUTH ──────────────────────────────────────────────────────────────────────
def login(nombre_usuario: str, contrasenia: str):
    db = get_connection()
    if not db:
        return None
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s", (nombre_usuario,))
    usuario = cursor.fetchone()
    cursor.close(); db.close()
    if usuario and bcrypt.checkpw(contrasenia.encode(), usuario["contrasenia"].encode()):
        return usuario
    return None


def registrar(nombre_usuario: str, contrasenia: str, id_especialidad: int):
    db = get_connection()
    if not db:
        return False, "No se pudo conectar a la base de datos"
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id_usuario FROM usuarios WHERE nombre_usuario = %s", (nombre_usuario,))
        if cursor.fetchone():
            cursor.close(); db.close()
            return False, "El usuario ya existe"
        hashed = bcrypt.hashpw(contrasenia.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO usuarios (nombre_usuario, contrasenia, id_especialidad) VALUES (%s, %s, %s)",
            (nombre_usuario, hashed, id_especialidad)
        )
        db.commit()
        id_usuario = cursor.lastrowid
        cursor.close(); db.close()
        return True, id_usuario
    except Exception as ex:
        db.rollback()
        db.close()
        return False, str(ex)


# ── ESPECIALIDADES ────────────────────────────────────────────────────────────
def get_especialidades():
    db = get_connection()
    if not db:
        return []
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM especialidades")
    rows = cursor.fetchall()
    cursor.close(); db.close()
    return rows


# ── PERFIL ALUMNO ─────────────────────────────────────────────────────────────
def get_perfil(id_usuario: int):
    db = get_connection()
    if not db:
        return None
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, u.nombre_usuario, u.id_especialidad, e.nombre_especialidad
        FROM alumnos a
        JOIN usuarios u ON a.id_usuario = u.id_usuario
        JOIN especialidades e ON u.id_especialidad = e.id_especialidad
        WHERE a.id_usuario = %s
    """, (id_usuario,))
    perfil = cursor.fetchone()
    cursor.close(); db.close()
    return perfil


def guardar_perfil(id_usuario: int, datos: dict):
    db = get_connection()
    if not db:
        return False
    cursor = db.cursor()
    cursor.execute("SELECT id_alumno FROM alumnos WHERE id_usuario = %s", (id_usuario,))
    existe = cursor.fetchone()
    if existe:
        cursor.execute("""
            UPDATE alumnos SET nombre_completo=%s, curp=%s, matricula=%s,
            correo=%s, celular=%s, foto_path=%s WHERE id_usuario=%s
        """, (datos["nombre_completo"], datos["curp"], datos["matricula"],
              datos["correo"], datos["celular"], datos.get("foto_path"), id_usuario))
    else:
        cursor.execute("""
            INSERT INTO alumnos (id_usuario, nombre_completo, curp, matricula, correo, celular, foto_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id_usuario, datos["nombre_completo"], datos["curp"], datos["matricula"],
              datos["correo"], datos["celular"], datos.get("foto_path")))
    db.commit()
    cursor.close(); db.close()
    return True


# ── MATERIAS ──────────────────────────────────────────────────────────────────
def get_materias(id_especialidad: int, semestre: int):
    db = get_connection()
    if not db:
        return []
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM materias WHERE id_especialidad = %s AND semestre = %s",
        (id_especialidad, semestre)
    )
    rows = cursor.fetchall()
    cursor.close(); db.close()
    return rows


def agregar_materia(nombre: str, semestre: int, id_especialidad: int):
    db = get_connection()
    if not db:
        return False
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO materias (nombre_materia, semestre, id_especialidad) VALUES (%s, %s, %s)",
        (nombre, semestre, id_especialidad)
    )
    db.commit()
    cursor.close(); db.close()
    return True


# ── CALIFICACIONES ────────────────────────────────────────────────────────────
def get_calificaciones(id_alumno: int, semestre: int):
    db = get_connection()
    if not db:
        return []
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, m.nombre_materia,
               CASE
                   WHEN c.unidad1 IS NULL AND c.unidad2 IS NULL AND c.unidad3 IS NULL THEN NULL
                   ELSE ROUND(
                       (COALESCE(c.unidad1,0) + COALESCE(c.unidad2,0) + COALESCE(c.unidad3,0)) /
                       NULLIF((c.unidad1 IS NOT NULL) + (c.unidad2 IS NOT NULL) + (c.unidad3 IS NOT NULL), 0),
                       2
                   )
               END AS promedio
        FROM calificaciones c
        JOIN materias m ON c.id_materia = m.id_materia
        WHERE c.id_alumno = %s AND c.semestre = %s
    """, (id_alumno, semestre))
    rows = cursor.fetchall()
    cursor.close(); db.close()
    return rows


def guardar_calificacion(id_alumno: int, id_materia: int, semestre: int,
                         u1: float, u2: float, u3: float):
    db = get_connection()
    if not db:
        return False
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO calificaciones (id_alumno, id_materia, semestre, unidad1, unidad2, unidad3)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE unidad1=%s, unidad2=%s, unidad3=%s
    """, (id_alumno, id_materia, semestre, u1, u2, u3, u1, u2, u3))
    db.commit()
    cursor.close(); db.close()
    return True


def get_promedio_general(id_alumno: int):
    db = get_connection()
    if not db:
        return 0
    cursor = db.cursor()
    cursor.execute("""
        SELECT ROUND(AVG(
            CASE
                WHEN unidad1 IS NULL AND unidad2 IS NULL AND unidad3 IS NULL THEN NULL
                ELSE (COALESCE(unidad1,0)+COALESCE(unidad2,0)+COALESCE(unidad3,0)) /
                     NULLIF((unidad1 IS NOT NULL) + (unidad2 IS NOT NULL) + (unidad3 IS NOT NULL), 0)
            END
        ), 2)
        FROM calificaciones WHERE id_alumno = %s
    """, (id_alumno,))
    row = cursor.fetchone()
    cursor.close(); db.close()
    return float(row[0]) if row and row[0] is not None else 0.0
