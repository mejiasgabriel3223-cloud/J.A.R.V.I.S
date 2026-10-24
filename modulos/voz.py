import asyncio
import os
import queue
import re
import tempfile
import threading

import edge_tts
import pygame


class Voz:
    def __init__(self):
        self.nombre_voz = "es-MX-JorgeNeural"
        self.cola_audio = queue.Queue()
        self.hilo_audio = None
        self.texto_pendiente = ""

        pygame.mixer.init()

    async def _generar_audio(self, texto, ruta):
        comunicador = edge_tts.Communicate(
            texto,
            voice=self.nombre_voz,
            rate="+25%",
        )
        await comunicador.save(ruta)

    def _reproducir(self, texto):
        ruta_audio = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as archivo:
                ruta_audio = archivo.name

            asyncio.run(self._generar_audio(texto, ruta_audio))
            pygame.mixer.music.load(ruta_audio)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as error:
            print(f"\n[Sistema]: Error en el sintetizador de voz: {error}")
        finally:
            if ruta_audio:
                try:
                    os.remove(ruta_audio)
                except OSError:
                    pass

    def iniciar_stream(self):
        """Prepara la reproducción mientras Gemini sigue generando texto."""
        self.texto_pendiente = ""
        self.hilo_audio = threading.Thread(target=self._procesar_cola, daemon=True)
        self.hilo_audio.start()

    def agregar_fragmento(self, fragmento):
        """Encola cada frase completa que llega desde Gemini."""
        self.texto_pendiente += fragmento
        frases = re.split(r"(?<=[.!?])\s+", self.texto_pendiente)
        self.texto_pendiente = frases.pop()
        for frase in frases:
            if frase.strip():
                self.cola_audio.put(frase.strip())

    def finalizar_stream(self):
        """Encola el texto restante y espera a que termine el audio."""
        if self.texto_pendiente.strip():
            self.cola_audio.put(self.texto_pendiente.strip())
        self.cola_audio.put(None)
        if self.hilo_audio:
            self.hilo_audio.join()
            self.hilo_audio = None

    def _procesar_cola(self):
        while True:
            texto = self.cola_audio.get()
            if texto is None:
                return
            print(f"[Sintetizando voz: {self.nombre_voz}...]")
            self._reproducir(texto)

    def hablar(self, texto):
        """Convierte un texto completo a voz masculina mexicana."""
        if not texto:
            return
        self.iniciar_stream()
        self.agregar_fragmento(texto)
        self.finalizar_stream()


if __name__ == "__main__":
    Voz().hablar("Sistemas en línea. Voz masculina mexicana activada, señor.")
