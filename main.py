import threading
import time
import keyboard

# Importamos nuestros tres módulos independientes
from modulos.cerebro import Cerebro
from modulos.oidos import Oidos
from modulos.voz import Voz

class JarvisSystem:
    def __init__(self):
        print("[Sistema]: Inicializando protocolos de J.A.R.V.I.S...")
        self.cerebro = Cerebro()
        self.oidos = Oidos()
        self.voz = Voz()
        self._bloqueo_despertar = threading.Lock()
        print("[Sistema]: Todos los subsistemas en línea.")

    def despertar(self):
        """Rutina que se ejecuta al presionar la combinacion de teclas"""
        if not self._bloqueo_despertar.acquire(blocking=False):
            print("[Sistema]: Ya estoy atendiendo otra solicitud.")
            return

        try:
            print("\n[Escuchando...]")

            # 1. Capturamos tu voz y la convertimos a texto
            texto_usuario = self.oidos.grabar_y_transcribir()

            if texto_usuario:
                print(f"[Tú]: {texto_usuario}")

                # 2. El cerebro procesa el texto usando el contexto de tu vida
                self.voz.iniciar_stream()
                respuesta_ia = self.cerebro.generar_respuesta(
                    texto_usuario,
                    al_recibir=self.voz.agregar_fragmento,
                )
                print(f"[J.A.R.V.I.S.]: {respuesta_ia}")

                # La voz termina de reproducir los fragmentos recibidos.
                self.voz.finalizar_stream()

            print("\n[Sistema]: En espera. Presiona [Ctrl + Alt + J] para hablar.")
        finally:
            self._bloqueo_despertar.release()

    def iniciar_demonio(self):
        """Mantiene el sistema corriendo de forma silenciosa en segundo plano"""
        # Configuramos el atajo de teclado global (puedes cambiarlo si prefieres otros botones)
        keyboard.add_hotkey('ctrl+alt+j', self.despertar)
        
        # Bucle pasivo que consume 0% de CPU
        while True:
            time.sleep(1)

if __name__ == "__main__":
    jarvis = JarvisSystem()
    print("\n----------------------------------------------------")
    print(" J.A.R.V.I.S. oculto en segundo plano.")
    print(" Atajo activo: Presiona [Ctrl + Alt + J] para hablar.")
    print("----------------------------------------------------")
    
    # Lanzamos el proceso en un hilo secundario tipo "Demón" (como un servicio de Discord)
    hilo_escucha = threading.Thread(target=jarvis.iniciar_demonio, daemon=True)
    hilo_escucha.start()
    
    # Mantiene la consola principal viva
    try:
        hilo_escucha.join()
    except KeyboardInterrupt:
        print("\n[Sistema]: Apagando J.A.R.V.I.S. Hasta luego, señor.")