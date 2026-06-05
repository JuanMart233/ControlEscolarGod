import re, sys, os, base64
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import flet as ft
import bcrypt
from Database.database import get_connection

# Cargar imagen en base64 una sola vez
_IMG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "../../controlescolar/assest/pibemotocierra.webp")
BG_B64 = ""
BG_PATH = _IMG_PATH if os.path.exists(_IMG_PATH) else ""
try:
    with open(_IMG_PATH, "rb") as f:
        BG_B64 = base64.b64encode(f.read()).decode()
except Exception as ex:
    print(f"No se pudo cargar imagen de fondo: {ex}")


def _fondo(page: ft.Page, content: ft.Control) -> ft.Container:
    return ft.Container(
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
        content=content
    )


def build_login(page: ft.Page, on_success, on_registro):
    txt_user = ft.TextField(label="Usuario", width=320, prefix_icon=ft.Icons.PERSON,
                            color=ft.Colors.WHITE,
                            label_style=ft.TextStyle(color=ft.Colors.WHITE70),
                            border_color=ft.Colors.WHITE54,
                            focused_border_color=ft.Colors.WHITE)
    txt_pass = ft.TextField(label="Contraseña", password=True, can_reveal_password=True,
                            width=320, prefix_icon=ft.Icons.LOCK,
                            color=ft.Colors.WHITE,
                            label_style=ft.TextStyle(color=ft.Colors.WHITE70),
                            border_color=ft.Colors.WHITE54,
                            focused_border_color=ft.Colors.WHITE)
    err_msg = ft.Text("", color=ft.Colors.RED_300, size=13)

    def on_login(e):
        txt_user.error_text = None
        txt_pass.error_text = None
        err_msg.value = ""
        if not txt_user.value.strip():
            txt_user.error_text = "Requerido"
        if not txt_pass.value:
            txt_pass.error_text = "Requerido"
        if txt_user.error_text or txt_pass.error_text:
            page.update(); return
        try:
            db = get_connection()
            if not db:
                err_msg.value = "No se pudo conectar a la base de datos"
                page.update(); return
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s",
                           (txt_user.value.strip(),))
            usuario = cursor.fetchone()
            cursor.close(); db.close()
            if usuario and bcrypt.checkpw(txt_pass.value.encode(),
                                          usuario["contrasenia"].encode()):
                on_success(usuario)
            else:
                err_msg.value = "Usuario o contraseña incorrectos"
                page.update()
        except Exception as ex:
            err_msg.value = f"Error: {ex}"
            page.update()

    contenido = ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.SCHOOL, size=64, color=ft.Colors.WHITE),
            ft.Text("Control Escolar", size=26, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE),
            ft.Text("Inicia sesión para continuar", color=ft.Colors.WHITE70),
            ft.Container(height=10),
            txt_user, txt_pass, err_msg,
            ft.ElevatedButton("Ingresar", on_click=on_login, width=320,
                              bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            ft.TextButton("¿No tienes cuenta? Regístrate",
                          on_click=lambda _: on_registro(),
                          style=ft.ButtonStyle(color=ft.Colors.WHITE70)),
        ]
    )
    return _fondo(page, contenido)


def build_registro(page: ft.Page, on_success, on_login):
    especialidades = []
    try:
        db = get_connection()
        if db:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM especialidades")
            especialidades = cursor.fetchall()
            cursor.close(); db.close()
    except Exception as ex:
        print(f"Error cargando especialidades: {ex}")

    def campo(label, icon, password=False, reveal=False):
        return ft.TextField(label=label, width=320, prefix_icon=icon,
                            password=password, can_reveal_password=reveal,
                            color=ft.Colors.WHITE,
                            label_style=ft.TextStyle(color=ft.Colors.WHITE70),
                            border_color=ft.Colors.WHITE54,
                            focused_border_color=ft.Colors.WHITE)

    txt_user  = campo("Nombre de usuario",    ft.Icons.PERSON)
    txt_pass  = campo("Contraseña",           ft.Icons.LOCK,         password=True, reveal=True)
    txt_pass2 = campo("Confirmar contraseña", ft.Icons.LOCK_OUTLINE,  password=True, reveal=True)
    dd_esp = ft.Dropdown(
        label="Especialidad", width=320,
        color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color=ft.Colors.WHITE70),
        border_color=ft.Colors.WHITE54,
        focused_border_color=ft.Colors.WHITE,
        options=[ft.dropdown.Option(key=str(e["id_especialidad"]),
                                    text=e["nombre_especialidad"])
                 for e in especialidades]
    )
    err_msg = ft.Text("", color=ft.Colors.RED_300, size=13)

    def on_registrar(e):
        txt_user.error_text = txt_pass.error_text = None
        txt_pass2.error_text = dd_esp.error_text = None
        err_msg.value = ""
        hay_error = False

        if not (txt_user.value or "").strip():
            txt_user.error_text = "Requerido"; hay_error = True
        elif not re.match(r'^[a-zA-Z0-9_]{4,30}$', txt_user.value.strip()):
            txt_user.error_text = "4-30 caracteres: letras, números y _"; hay_error = True

        if not txt_pass.value:
            txt_pass.error_text = "Requerido"; hay_error = True
        elif len(txt_pass.value) < 6:
            txt_pass.error_text = "Mínimo 6 caracteres"; hay_error = True

        if not txt_pass2.value:
            txt_pass2.error_text = "Requerido"; hay_error = True
        elif txt_pass.value != txt_pass2.value:
            txt_pass2.error_text = "Las contraseñas no coinciden"; hay_error = True

        if not dd_esp.value:
            dd_esp.error_text = "Selecciona una especialidad"; hay_error = True

        page.update()
        if hay_error: return

        try:
            db = get_connection()
            if not db:
                err_msg.value = "Sin conexión"; page.update(); return
            cursor = db.cursor()
            cursor.execute("SELECT id_usuario FROM usuarios WHERE nombre_usuario = %s",
                           (txt_user.value.strip(),))
            if cursor.fetchone():
                cursor.close(); db.close()
                err_msg.value = "El usuario ya existe"; page.update(); return
            hashed = bcrypt.hashpw(txt_pass.value.encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                "INSERT INTO usuarios (nombre_usuario, contrasenia, id_especialidad) VALUES (%s,%s,%s)",
                (txt_user.value.strip(), hashed, int(dd_esp.value))
            )
            db.commit(); cursor.close(); db.close()
            on_success()
        except Exception as ex:
            err_msg.value = f"Error al registrar: {ex}"; page.update()

    contenido = ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Icon(ft.Icons.PERSON_ADD, size=56, color=ft.Colors.WHITE),
            ft.Text("Crear cuenta", size=22, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE),
            ft.Container(height=8),
            txt_user, txt_pass, txt_pass2, dd_esp, err_msg,
            ft.ElevatedButton("Registrar", on_click=on_registrar, width=320,
                              bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            ft.TextButton("¿Ya tienes cuenta? Inicia sesión",
                          on_click=lambda _: on_login(),
                          style=ft.ButtonStyle(color=ft.Colors.WHITE70)),
        ]
    )
    return _fondo(page, contenido)
