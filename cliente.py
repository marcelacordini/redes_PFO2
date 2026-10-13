"""
Cliente en Consola - PFO2 Programación sobre Redes
Interactúa con la API REST de Gestión de Tareas
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:5000"

class APIClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.usuario_actual = None

    def _request(self, endpoint, method='GET', data=None):
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        body = json.dumps(data).encode('utf-8') if data else None

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode('utf-8')
                return response.status, json.loads(res_body)
        except urllib.error.HTTPError as e:
            res_body = e.read().decode('utf-8')
            try:
                return e.code, json.loads(res_body)
            except Exception:
                return e.code, {"error": res_body}
        except urllib.error.URLError as e:
            return 500, {"error": f"No se pudo conectar al servidor: {e.reason}. ¿Está ejecutándose 'servidor.py'?"}

    def registrar_usuario(self):
        print("\n--- REGISTRO DE USUARIO ---")
        usuario = input("Ingrese nombre de usuario: ").strip()
        password = input("Ingrese contraseña: ").strip()

        if not usuario or not password:
            print("❌ El usuario y la contraseña no pueden estar vacíos.")
            return

        payload = {"usuario": usuario, "contraseña": password}
        status, response = self._request('/registro', method='POST', data=payload)

        if status == 201:
            print(f"✅ {response.get('mensaje')}")
        else:
            print(f"❌ Error ({status}): {response.get('error', 'Error al registrar')}")

    def iniciar_sesion(self):
        print("\n--- INICIO DE SESIÓN ---")
        usuario = input("Ingrese usuario: ").strip()
        password = input("Ingrese contraseña: ").strip()

        if not usuario or not password:
            print("❌ Por favor complete ambos campos.")
            return

        payload = {"usuario": usuario, "contraseña": password}
        status, response = self._request('/login', method='POST', data=payload)

        if status == 200:
            self.usuario_actual = usuario
            print(f"✅ {response.get('mensaje')} ¡Bienvenido/a, {usuario}!")
        else:
            print(f"❌ Error ({status}): {response.get('error', 'Credenciales incorrectas')}")

    def ver_tareas(self):
        print("\n--- MIS TAREAS ---")
        if not self.usuario_actual:
            print("⚠️ Nota: No has iniciado sesión. Mostrando todas las tareas del sistema.")
            endpoint = "/tareas"
        else:
            endpoint = f"/tareas?usuario={self.usuario_actual}"

        status, response = self._request(endpoint, method='GET')

        if status == 200:
            tareas = response.get('tareas', [])
            print(f"📌 {response.get('mensaje')}")
            if not tareas:
                print("   (No hay tareas registradas)")
            else:
                for t in tareas:
                    estado = "✔ [COMPLETADA]" if t['completada'] else "⏳ [PENDIENTE]"
                    print(f"   ID #{t['id']} | {estado} | {t['titulo']}")
        else:
            print(f"❌ Error al obtener tareas: {response.get('error')}")

    def crear_tarea(self):
        print("\n--- CREAR NUEVA TAREA ---")
        if not self.usuario_actual:
            print("⚠️ Debes iniciar sesión primero para asignar la tarea a tu usuario.")
            usuario = input("O ingresa tu usuario manualmente: ").strip()
        else:
            usuario = self.usuario_actual

        titulo = input("Ingrese la descripción o título de la tarea: ").strip()

        if not usuario or not titulo:
            print("❌ El usuario y el título son obligatorios.")
            return

        payload = {"usuario": usuario, "titulo": titulo}
        status, response = self._request('/tareas', method='POST', data=payload)

        if status == 201:
            tarea = response.get('tarea', {})
            print(f"✅ {response.get('mensaje')} (ID #{tarea.get('id')}: {tarea.get('titulo')})")
        else:
            print(f"❌ Error ({status}): {response.get('error')}")

    def marcar_completada(self):
        print("\n--- MARCAR TAREA COMO COMPLETADA ---")
        tarea_id = input("Ingrese el ID de la tarea completada: ").strip()
        if not tarea_id.isdigit():
            print("❌ El ID debe ser un número entero.")
            return

        status, response = self._request(f"/tareas/{tarea_id}", method='PUT')
        if status == 200:
            print(f"✅ {response.get('mensaje')}")
        else:
            print(f"❌ Error ({status}): {response.get('error')}")

    def eliminar_tarea(self):
        print("\n--- ELIMINAR TAREA ---")
        tarea_id = input("Ingrese el ID de la tarea a eliminar: ").strip()
        if not tarea_id.isdigit():
            print("❌ El ID debe ser un número entero.")
            return

        status, response = self._request(f"/tareas/{tarea_id}", method='DELETE')
        if status == 200:
            print(f"✅ {response.get('mensaje')}")
        else:
            print(f"❌ Error ({status}): {response.get('error')}")


def main():
    client = APIClient()

    while True:
        usuario_str = f" ({client.usuario_actual})" if client.usuario_actual else " (Sin sesión)"
        print("\n==========================================")
        print(f"   GESTOR DE TAREAS API REST - PFO2{usuario_str}")
        print("==========================================")
        print("1. Registrar nuevo usuario (POST /registro)")
        print("2. Iniciar sesión (POST /login)")
        print("3. Ver mis tareas (GET /tareas)")
        print("4. Crear nueva tarea (POST /tareas)")
        print("5. Marcar tarea como completada (PUT /tareas/<id>)")
        print("6. Eliminar tarea (DELETE /tareas/<id>)")
        print("0. Salir")
        print("------------------------------------------")

        opcion = input("Seleccione una opción (0-6): ").strip()

        if opcion == '1':
            client.registrar_usuario()
        elif opcion == '2':
            client.iniciar_sesion()
        elif opcion == '3':
            client.ver_tareas()
        elif opcion == '4':
            client.crear_tarea()
        elif opcion == '5':
            client.marcar_completada()
        elif opcion == '6':
            client.eliminar_tarea()
        elif opcion == '0':
            print("¡Gracias por utilizar el cliente de la PFO2! Hasta luego.")
            sys.exit(0)
        else:
            print("❌ Opción inválida. Intente de nuevo.")

if __name__ == '__main__':
    main()
