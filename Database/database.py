import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../controlescolar/.env"))

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME     = os.getenv("DB_NAME")


def _init_db():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
        cursor = conn.cursor()

        # Tabla alumnos (perfil extendido)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alumnos (
                id_alumno     INT AUTO_INCREMENT PRIMARY KEY,
                id_usuario    INT NOT NULL UNIQUE,
                nombre_completo VARCHAR(150),
                curp          VARCHAR(18),
                matricula     VARCHAR(20),
                correo        VARCHAR(100),
                celular       VARCHAR(15),
                foto_path     VARCHAR(255),
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
            )
        """)

        # Tabla materias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materias (
                id_materia    INT AUTO_INCREMENT PRIMARY KEY,
                nombre_materia VARCHAR(100) NOT NULL,
                semestre      INT NOT NULL,
                id_especialidad INT NOT NULL,
                FOREIGN KEY (id_especialidad) REFERENCES especialidades(id_especialidad)
            )
        """)

        # Tabla calificaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calificaciones (
                id_calificacion INT AUTO_INCREMENT PRIMARY KEY,
                id_alumno     INT NOT NULL,
                id_materia    INT NOT NULL,
                semestre      INT NOT NULL,
                unidad1       DECIMAL(4,2),
                unidad2       DECIMAL(4,2),
                unidad3       DECIMAL(4,2),
                UNIQUE KEY uq_alumno_materia (id_alumno, id_materia),
                FOREIGN KEY (id_alumno)  REFERENCES alumnos(id_alumno),
                FOREIGN KEY (id_materia) REFERENCES materias(id_materia)
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print(f"Error al inicializar BD: {e}")


_init_db()


def get_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME
        )
    except Error as e:
        print(f"Error al conectar: {e}")
        return None
