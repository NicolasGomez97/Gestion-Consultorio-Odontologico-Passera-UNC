"""
main.py — Punto de entrada del Sistema de Gestión Consultorio Odontológico Passera.
Universidad Nacional de Córdoba — Práctica Profesional
Desarrollado por: Ramiro Nicolas Gomez
David Macías, Matías Rodríguez
"""
import sys
import os

# Asegurarse de que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
from ui.login_ui import LoginWindow
from ui.app import MainApp


def main():
    # Inicializar la base de datos (crea tablas y datos semilla si no existen)
    database.init_db()

    # Mostrar ventana de login
    login = LoginWindow()
    login.mainloop()

    # Si el usuario cerró la ventana sin autenticarse, salir
    if login.current_user is None:
        return

    # Lanzar la aplicación principal con el usuario autenticado
    app = MainApp(current_user=login.current_user)
    app.mainloop()


if __name__ == "__main__":
    main()
