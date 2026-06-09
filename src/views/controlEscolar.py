import sys, os, re, base64
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

import flet as ft
from src.views.base import build_login, build_registro, BG_B64, BG_PATH
from src.controllers.UserController import (
    obtener_perfil, obtener_materias, nueva_materia,
    obtener_calificaciones, guardar_calif, promedio_general
)
from Database.database import get_connection

SEMESTRES = [str(i) for i in range(1, 7)]

_APP_IMG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "../../controlescolar/assest/capitanotieso.jpeg")


def main(page: ft.Page):
    page.title = "Control Escolar"
    page.window_width  = 500
    page.window_height = 720
    page.bgcolor = ft.Colors.TRANSPARENT

    session = {"usuario": None, "alumno": None, "semestre": "1"}

    def snack(msg, color=ft.Colors.GREEN_700):
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def bg_wrap(content):
        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
            content=content
        )

    def set_view(content, appbar=None):
        if os.path.exists(_APP_IMG_PATH):
            page.decoration = ft.BoxDecoration(
                image=ft.DecorationImage(src=_APP_IMG_PATH, fit=ft.BoxFit.COVER)
            )
        page.clean()
        page.appbar = appbar
        page.drawer = make_drawer()
        page.add(bg_wrap(content))
        page.update()

    #DRAWER
    def make_appbar(titulo, back=None):
        def abrir(e):
            if page.drawer:
                page.drawer.open = True
                page.update()
        title_text = "Control Escolar" if titulo == "Dashboard" else titulo
        if back:
            leading = ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: back())
            return ft.AppBar(leading=leading, title=ft.Text(title_text),
                             bgcolor=ft.Colors.BLUE_800, color=ft.Colors.WHITE)
        else:
            return ft.AppBar(
                leading=ft.IconButton(ft.Icons.MENU, on_click=abrir,
                                      icon_color=ft.Colors.WHITE),
                title=ft.Text(title_text),
                bgcolor=ft.Colors.BLUE_800,
                color=ft.Colors.WHITE,
                actions=[
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        icon_color=ft.Colors.WHITE,
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.RED_400),
                                    ft.Text("Cerrar sesión", color=ft.Colors.RED_400),
                                ]),
                                on_click=lambda _: confirmar_logout(),
                            ),
                        ],
                    )
                ],
            )

    def confirmar_logout():
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cerrar sesión"),
            content=ft.Text("¿Estás seguro que deseas cerrar sesión?"),
            actions_alignment=ft.MainAxisAlignment.END,
        )
        def cerrar(e):
            dlg.open = False
            page.update()
        def hacer_logout(e):
            dlg.open = False
            page.update()
            mostrar_login()
        dlg.actions = [
            ft.TextButton("Cancelar", on_click=cerrar),
            ft.ElevatedButton("Cerrar sesión", on_click=hacer_logout,
                              bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        ]
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def make_drawer():
        usuario = session["usuario"] or {}
        alumno  = session["alumno"]  or {}
        nombre  = alumno.get("nombre_completo") or usuario.get("nombre_usuario", "")
        esp     = alumno.get("nombre_especialidad", "")

        def nav(dest):
            if page.drawer:
                page.drawer.open = False
                page.update()
            if dest == "perfil":  mostrar_perfil()
            elif dest == "califs": mostrar_calificaciones()
            elif dest == "logout": confirmar_logout()

        return ft.NavigationDrawer(controls=[
            ft.Container(
                padding=ft.Padding(left=20, right=20, top=24, bottom=24),
                bgcolor=ft.Colors.BLUE_800,
                content=ft.Row([
                    ft.CircleAvatar(
                        content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=30),
                        bgcolor=ft.Colors.BLUE_400,
                        radius=28,
                    ),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(nombre, color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD, size=15),
                        ft.Text(esp, color=ft.Colors.BLUE_100, size=12),
                    ], spacing=2, tight=True)
                ])
            ),
            ft.Divider(height=1),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.EDIT, color=ft.Colors.BLUE_400),
                title=ft.Text("Editar Perfil"),
                on_click=lambda _: nav("perfil"),
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.ADD_CIRCLE, color=ft.Colors.GREEN_400),
                title=ft.Text("Añadir Materia"),
                on_click=lambda _: nav("califs"),
            ),
            ft.Divider(),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.RED_400),
                title=ft.Text("Cerrar sesión", color=ft.Colors.RED_400),
                on_click=lambda _: nav("logout"),
            ),
        ])

    #El inicio de sesion o el loging
    def mostrar_login():
        session["usuario"] = None
        session["alumno"]  = None
        page.appbar = None
        page.drawer = None
        if BG_PATH and os.path.exists(BG_PATH):
            page.decoration = ft.BoxDecoration(
                image=ft.DecorationImage(src=BG_PATH, fit=ft.BoxFit.COVER)
            )
        page.clean()
        page.add(build_login(page, on_success=on_login_ok, on_registro=mostrar_registro))

    def on_login_ok(usuario):
        session["usuario"] = usuario
        alumno = obtener_perfil(usuario["id_usuario"])
        if not alumno:
            try:
                db = get_connection()
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT u.id_especialidad, e.nombre_especialidad
                    FROM usuarios u
                    JOIN especialidades e ON u.id_especialidad = e.id_especialidad
                    WHERE u.id_usuario = %s
                """, (usuario["id_usuario"],))
                session["alumno"] = cursor.fetchone()
                cursor.close(); db.close()
            except:
                session["alumno"] = None
        else:
            session["alumno"] = alumno
        mostrar_dashboard()

    #REGISTRO
    def mostrar_registro():
        page.drawer = None
        if BG_PATH and os.path.exists(BG_PATH):
            page.decoration = ft.BoxDecoration(
                image=ft.DecorationImage(src=BG_PATH, fit=ft.BoxFit.COVER)
            )
        page.appbar = ft.AppBar(
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: mostrar_login()),
            title=ft.Text("Registro"), bgcolor=ft.Colors.BLUE_800, color=ft.Colors.WHITE,
        )
        page.clean()
        def on_ok():
            mostrar_login()
            snack("Usuario registrado. Inicia sesión")
        page.add(build_registro(page, on_success=on_ok, on_login=mostrar_login))

    #DASHBOARD god
    def mostrar_dashboard():
        alumno  = session["alumno"]
        usuario = session["usuario"]
        nombre  = (alumno or {}).get("nombre_completo") or usuario["nombre_usuario"]
        esp     = (alumno or {}).get("nombre_especialidad", "Sin especialidad")
        mat     = (alumno or {}).get("matricula", "—")

        selected_sem = session.get("semestre", "1")
        if selected_sem not in SEMESTRES:
            selected_sem = "1"
            session["semestre"] = selected_sem

        prom_txt = ft.Text("—", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        lista    = ft.Column()

        def cargar(e=None):
            if not alumno or not alumno.get("id_alumno"): return
            selected_sem = sem_dd.value or "1"
            if selected_sem not in SEMESTRES:
                selected_sem = "1"
            session["semestre"] = selected_sem
            califs = obtener_calificaciones(alumno["id_alumno"], int(selected_sem))
            lista.controls.clear()
            for c in califs:
                p   = float(c["promedio"])
                col = ft.Colors.GREEN_400 if p >= 6 else ft.Colors.RED_400
                lista.controls.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.CIRCLE, color=col, size=12),
                    title=ft.Text(c["nombre_materia"], color=ft.Colors.WHITE),
                    trailing=ft.Text(f"{p:.2f}", weight=ft.FontWeight.BOLD, color=col),
                ))
            prom_txt.value = f"{promedio_general(alumno['id_alumno']):.2f}"
            page.update()

        sem_dd = ft.Dropdown(
            label="Semestre",
            width=160,
            value=selected_sem,
            options=[ft.dropdown.Option(key=s, text=s) for s in SEMESTRES],
        )

        btn_actualizar = ft.ElevatedButton(
            "Actualizar",
            icon=ft.Icons.REFRESH,
            on_click=cargar,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )

        content = ft.Column(scroll=ft.ScrollMode.AUTO, controls=[
            ft.Container(padding=16, content=ft.Column([
                ft.Row([
                    ft.CircleAvatar(
                        content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=28),
                        bgcolor=ft.Colors.BLUE_400, radius=26,
                    ),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(nombre, size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(f"Especialidad: {esp}", color=ft.Colors.WHITE70, size=13),
                        ft.Text(f"Matrícula: {mat}", color=ft.Colors.WHITE70, size=13),
                    ], spacing=2, tight=True)
                ]),
                ft.Divider(color=ft.Colors.WHITE24),
                ft.Text("Promedio General", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE70),
                prom_txt,
                ft.Divider(color=ft.Colors.WHITE24),
                ft.Row([
                    ft.Text("Por semestre:", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Row([
                        sem_dd,
                        btn_actualizar
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                lista,
                ft.Container(height=8),
                ft.ElevatedButton("Calificaciones", icon=ft.Icons.GRADE,
                                  on_click=lambda _: mostrar_calificaciones(),
                                  bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                ft.ElevatedButton("Editar Perfil", icon=ft.Icons.EDIT,
                                  on_click=lambda _: mostrar_perfil(),
                                  bgcolor=ft.Colors.GREY_700, color=ft.Colors.WHITE),
            ]))
        ])
        set_view(content, make_appbar("Dashboard"))
        cargar()

    # ── PERFIL 
    def mostrar_perfil():
        alumno = session["alumno"] or {}

        def tf(label, key, icon):
            return ft.TextField(label=label, width=320, prefix_icon=icon,
                                value=str(alumno.get(key) or ""))

        txt_nombre = tf("Nombre completo",      "nombre_completo", ft.Icons.BADGE)
        txt_curp   = tf("CURP",                 "curp",            ft.Icons.FINGERPRINT)
        txt_mat    = tf("Matrícula",            "matricula",       ft.Icons.NUMBERS)
        txt_correo = tf("Correo institucional", "correo",          ft.Icons.EMAIL)
        txt_cel    = tf("Celular",              "celular",         ft.Icons.PHONE)
        err_msg    = ft.Text("", color=ft.Colors.RED_300, size=13)

        def on_guardar(e):
            for c in [txt_nombre, txt_curp, txt_mat, txt_correo, txt_cel]:
                c.error_text = None
            err_msg.value = ""
            hay_error = False
            for c in [txt_nombre, txt_mat, txt_correo, txt_cel]:
                if not c.value.strip():
                    c.error_text = "Requerido"; hay_error = True
            if txt_correo.value.strip() and not re.match(r'^[^@]+@[^@]+\.[^@]+$', txt_correo.value.strip()):
                txt_correo.error_text = "Correo inválido"; hay_error = True
            if txt_cel.value.strip() and not re.match(r'^\d{10}$', txt_cel.value.strip()):
                txt_cel.error_text = "10 dígitos requeridos"; hay_error = True
            if hay_error:
                page.update(); return
            try:
                db = get_connection()
                cursor = db.cursor()
                id_u = session["usuario"]["id_usuario"]
                cursor.execute("SELECT id_alumno FROM alumnos WHERE id_usuario = %s", (id_u,))
                if cursor.fetchone():
                    cursor.execute("""UPDATE alumnos SET nombre_completo=%s, curp=%s,
                        matricula=%s, correo=%s, celular=%s WHERE id_usuario=%s""",
                        (txt_nombre.value.strip(), txt_curp.value.strip().upper(),
                         txt_mat.value.strip(), txt_correo.value.strip(),
                         txt_cel.value.strip(), id_u))
                else:
                    cursor.execute("""INSERT INTO alumnos
                        (id_usuario,nombre_completo,curp,matricula,correo,celular)
                        VALUES(%s,%s,%s,%s,%s,%s)""",
                        (id_u, txt_nombre.value.strip(), txt_curp.value.strip().upper(),
                         txt_mat.value.strip(), txt_correo.value.strip(), txt_cel.value.strip()))
                db.commit(); cursor.close(); db.close()
                session["alumno"] = obtener_perfil(id_u) or session["alumno"]
                snack("Perfil guardado correctamente")
                mostrar_dashboard()
            except Exception as ex:
                err_msg.value = f"Error: {ex}"; page.update()

        content = ft.Column(expand=True, alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=64, color=ft.Colors.WHITE),
                ft.Text("Mi Perfil", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(height=8),
                txt_nombre, txt_curp, txt_mat, txt_correo, txt_cel, err_msg,
                ft.ElevatedButton("Guardar", on_click=on_guardar, width=320,
                                  bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            ])
        set_view(content, ft.AppBar(
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: mostrar_dashboard()),
            title=ft.Text("Mi Perfil"), bgcolor=ft.Colors.BLUE_800, color=ft.Colors.WHITE,
        ))

    # ── CALIFICACIONES
    def mostrar_calificaciones():
        alumno  = session["alumno"]
        usuario = session["usuario"]

        if not alumno or not alumno.get("id_alumno"):
            snack("Completa tu perfil primero", ft.Colors.ORANGE_700)
            mostrar_perfil(); return

        selected_sem = session.get("semestre", "1")
        if selected_sem not in SEMESTRES:
            selected_sem = "1"
            session["semestre"] = selected_sem

        barra_sem = ft.ProgressBar(width=360, height=8, value=0.0,
                                   bgcolor=ft.Colors.WHITE24, color=ft.Colors.GREEN_400)
        progreso_txt = ft.Text(f"Semestre {selected_sem} de 6", size=13, color=ft.Colors.WHITE70)
        tabla     = ft.Column()
        prom_lbl  = ft.Text("Promedio del semestre: —", weight=ft.FontWeight.BOLD,
                            size=15, color=ft.Colors.WHITE)
        txt_nueva = ft.TextField(label="Nueva materia", width=200)
        err_mat   = ft.Text("", color=ft.Colors.RED_300, size=12)

        def parse_nota(v):
            try:
                n = float(v)
                return n if 0.0 <= n <= 10.0 else None
            except:
                return None

        def validar_nota_campo(campo):
            """Recorta el valor a máximo 10.0 al perder foco."""
            v = campo.value.strip()
            if not v:
                return
            try:
                n = float(v)
                if n > 10.0:
                    campo.value = "10"
                    campo.update()
            except:
                campo.value = ""
                campo.update()

        def cargar(e=None):
            sem_str = sem_dd.value or session.get("semestre", "1")
            if sem_str not in SEMESTRES:
                sem_str = "1"
            sem = int(sem_str)
            session["semestre"] = sem_str
            materias = obtener_materias(usuario["id_especialidad"], sem)
            califs   = {c["id_materia"]: c
                        for c in obtener_calificaciones(alumno["id_alumno"], sem)}
            barra_sem.value = (sem - 1) / 5 if 1 <= sem <= 6 else 0.0
            progress_percent = round(barra_sem.value * 100)
            progreso_txt.value = f"Semestre {sem} de 6 ({progress_percent}%)"
            tabla.controls.clear()
            tabla.controls.append(ft.Row([
                ft.Text("Materia", width=115, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("U1",  width=62, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("U2",  width=62, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("U3",  width=62, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("Prom",width=52, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ]))
            for m in materias:
                mid = m["id_materia"]
                cal = califs.get(mid, {})
                p   = float(cal["promedio"]) if cal.get("promedio") is not None else None
                def make_nota_field(val):
                    f = ft.TextField(
                        value=str(val or ""),
                        width=62,
                        text_align=ft.TextAlign.CENTER,
                        max_length=4,
                        input_filter=ft.InputFilter(regex_string=r'[0-9.]'),
                    )
                    f.on_blur = lambda e, campo=f: validar_nota_campo(campo)
                    return f
                u1f = make_nota_field(cal.get("unidad1") if cal.get("unidad1") is not None else "")
                u2f = make_nota_field(cal.get("unidad2") if cal.get("unidad2") is not None else "")
                u3f = make_nota_field(cal.get("unidad3") if cal.get("unidad3") is not None else "")
                prom_cell = ft.Text(
                    f"{p:.2f}" if p is not None else "—", width=52,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.GREEN_400 if p is not None and p >= 6 else ft.Colors.RED_400
                )

                def guardar_fila(e, mid=mid, u1f=u1f, u2f=u2f, u3f=u3f):
                    raw_vals = [u1f.value.strip(), u2f.value.strip(), u3f.value.strip()]
                    vals = []
                    for v in raw_vals:
                        if v == "":
                            vals.append(None)
                        else:
                            nota = parse_nota(v)
                            if nota is None:
                                snack("Notas deben ser números entre 0.0 y 10.0", ft.Colors.RED_700)
                                return
                            vals.append(nota)
                    guardar_calif(alumno["id_alumno"], mid, int(sem_dd.value), *vals)
                    snack("Guardado"); cargar()

                tabla.controls.append(ft.Row([
                    ft.Text(m["nombre_materia"], width=115, color=ft.Colors.WHITE),
                    u1f, u2f, u3f, prom_cell,
                    ft.IconButton(ft.Icons.SAVE,  tooltip="Guardar",
                                  icon_color=ft.Colors.BLUE_200, on_click=guardar_fila),
                    ft.IconButton(ft.Icons.DELETE, tooltip="Eliminar",
                                  icon_color=ft.Colors.RED_400,
                                  on_click=lambda e, mid=mid: borrar_materia(mid)),
                ]))

            avg_values = [float(c["promedio"]) for c in califs.values() if c.get("promedio") is not None]
            if avg_values:
                ps = sum(avg_values) / len(avg_values)
                prom_lbl.value = f"Promedio del semestre: {ps:.2f}"
                prom_lbl.color = ft.Colors.GREEN_400 if ps >= 6 else ft.Colors.RED_400
            else:
                prom_lbl.value = "Promedio del semestre: —"
                prom_lbl.color = ft.Colors.WHITE
            page.update()

        sem_dd = ft.Dropdown(
            label="Semestre",
            width=140,
            value=selected_sem,
            options=[ft.dropdown.Option(key=s, text=s) for s in SEMESTRES],
        )

        btn_actualizar = ft.ElevatedButton(
            "Actualizar",
            icon=ft.Icons.REFRESH,
            on_click=cargar,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )


        def mostrar_historial(e=None):
            promedio_gral = promedio_general(alumno["id_alumno"])

            contenido = [
                ft.Text(
                    f"Promedio General: {promedio_gral:.2f}",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_400 if promedio_gral >= 6 else ft.Colors.RED_400
                ),
                ft.Divider()
            ]

            for semestre in range(1, 7):
                califs = obtener_calificaciones(alumno["id_alumno"], semestre)

                promedios = [
                    float(c["promedio"])
                    for c in califs
                    if c.get("promedio") is not None
                ]

                promedio_sem = sum(promedios) / len(promedios) if promedios else 0

                contenido.append(
                    ft.Container(
                        padding=10,
                        border=ft.Border(
                            left=ft.BorderSide(1, ft.Colors.WHITE24),
                            top=ft.BorderSide(1, ft.Colors.WHITE24),
                            right=ft.BorderSide(1, ft.Colors.WHITE24),
                            bottom=ft.BorderSide(1, ft.Colors.WHITE24),
                        ),
                        border_radius=10,
                        margin=ft.Margin(left=0, top=0, right=0, bottom=10),
                        content=ft.Column([
                            ft.Row(
                                [
                                    ft.Text(
                                        f"Semestre {semestre}",
                                        weight=ft.FontWeight.BOLD,
                                        size=16,
                                        color=ft.Colors.WHITE
                                    ),
                                    ft.Text(
                                        f"Promedio: {promedio_sem:.2f}",
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREEN_400 if promedio_sem >= 6 else ft.Colors.RED_400
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            *[
                                ft.Row(
                                    [
                                        ft.Text(c["nombre_materia"], expand=True, color=ft.Colors.WHITE),
                                        ft.Text(
                                            f"{float(c['promedio']):.2f}" if c.get("promedio") is not None else "—",
                                            color=ft.Colors.WHITE70
                                        )
                                    ]
                                )
                                for c in califs
                            ]
                        ])
                    )
                )

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Historial Académico"),
                content=ft.Container(
                    width=700,
                    height=500,
                    content=ft.Column(
                        controls=contenido,
                        scroll=ft.ScrollMode.AUTO
                    )
                ),
                actions=[
                    ft.TextButton(
                        "Cerrar",
                        on_click=lambda e: cerrar_historial()
                    )
                ]
            )

            def cerrar_historial():
                dlg.open = False
                page.update()

            page.overlay.append(dlg)
            dlg.open = True
            page.update()


        def borrar_materia(id_materia):
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Eliminar materia"),
                content=ft.Text("¿Seguro que deseas eliminar esta materia y sus calificaciones?"),
                actions_alignment=ft.MainAxisAlignment.END,
            )
            def confirmar(e):
                dlg.open = False
                page.update()
                try:
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("DELETE FROM calificaciones WHERE id_materia = %s", (id_materia,))
                    cursor.execute("DELETE FROM materias WHERE id_materia = %s", (id_materia,))
                    db.commit(); cursor.close(); db.close()
                    snack("Materia eliminada")
                    cargar()
                except Exception as ex:
                    snack(f"Error: {ex}", ft.Colors.RED_700)
            def cancelar(e):
                dlg.open = False
                page.update()
            dlg.actions = [
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Eliminar", on_click=confirmar,
                                  bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
            ]
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        def agregar(e):
            err_mat.value = ""
            if not txt_nueva.value.strip():
                err_mat.value = "Escribe el nombre de la materia"
                page.update(); return
            nueva_materia(txt_nueva.value.strip(), int(sem_dd.value),
                          usuario["id_especialidad"])
            txt_nueva.value = ""
            snack("Materia agregada"); cargar()

        content = ft.Column(scroll=ft.ScrollMode.AUTO, controls=[
            ft.Container(padding=16, content=ft.Column([
                ft.Row([
                    ft.Text("Semestre:", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    sem_dd,
                    btn_actualizar
                ]),
                ft.Container(height=6),
                ft.Row([progreso_txt], alignment=ft.MainAxisAlignment.START),
                barra_sem,
                ft.Divider(color=ft.Colors.WHITE24),
                ft.Row([txt_nueva,
                        ft.IconButton(ft.Icons.ADD_CIRCLE, tooltip="Agregar materia",
                                      icon_color=ft.Colors.GREEN_400, on_click=agregar)]),
                err_mat,
                ft.Divider(color=ft.Colors.WHITE24),
                tabla,
                ft.Divider(color=ft.Colors.WHITE24),
                ft.ElevatedButton(
                    "Historial",
                    icon=ft.Icons.HISTORY,
                    on_click=mostrar_historial,
                    bgcolor=ft.Colors.PURPLE_700,
                    color=ft.Colors.WHITE,
                ),
                prom_lbl,
            ]))
        ])
        set_view(content, make_appbar("Calificaciones", back=mostrar_dashboard))
        cargar()

    mostrar_login()


if __name__ == "__main__":
    ft.run(main)
