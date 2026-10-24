import os

import ollama
from dotenv import load_dotenv

from modulos.configuracion import cargar_configuracion

load_dotenv()

class Cerebro:
    def __init__(self):
        configuracion = cargar_configuracion()["configuracion"]
        configuracion_ollama = configuracion["ollama"]
        asistente = configuracion["asistente"]
        contexto_usuario = configuracion["contexto_usuario"]

        self.modelo = os.getenv("OLLAMA_MODEL", configuracion_ollama["modelo"])
        self.cliente = ollama.Client(
            host=os.getenv("OLLAMA_HOST", configuracion_ollama["host"])
        )

        contexto_personal = "\n\n".join(
            [
                f"Eres {asistente['nombre']}, {asistente['personalidad']}",
                "Contexto del usuario:\n"
                + "\n".join(
                    f"- {seccion.replace('_', ' ').capitalize()}: {detalle}"
                    for seccion, detalle in contexto_usuario.items()
                ),
                "Directrices de comportamiento:\n"
                + "\n".join(f"- {directriz}" for directriz in asistente["directrices"]),
            ]
        )
        self.mensajes = [{"role": "system", "content": contexto_personal}]

    def generar_respuesta(self, texto_usuario, al_recibir=None):
        """Envía el texto a la API y devuelve la respuesta completa."""
        try:
            self.mensajes.append({"role": "user", "content": texto_usuario})
            fragmentos = []
            for fragmento in self.cliente.chat(
                model=self.modelo,
                messages=self.mensajes,
                stream=True,
                options={"num_predict": -1},
            ):
                texto = fragmento["message"].get("content", "")
                fragmentos.append(texto)
                if al_recibir:
                    al_recibir(texto)
            respuesta = "".join(fragmentos)
            self.mensajes.append({"role": "assistant", "content": respuesta})
            return respuesta
        except Exception as e:
            return f"Señor, no puedo conectar con Ollama: {e}"

# Código de prueba (solo se ejecuta si corres este archivo directamente)
if __name__ == "__main__":
    jarvis_cerebro = Cerebro()
    print("Prueba del cerebro iniciada. Escribe 'salir' para terminar.")
    while True:
        entrada = input("Tú: ")
        if entrada.lower() == 'salir':
            break
        print(f"J.A.R.V.I.S.: {jarvis_cerebro.generar_respuesta(entrada)}")