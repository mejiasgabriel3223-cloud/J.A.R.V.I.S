import asyncio
import os
import queue
import re
import tempfile
import threading

import edge_tts
import pygame

from modulos.configuracion import cargar_configuracion


class Voz:
    def __init__(self):
        configuracion_voz = cargar_configuracion()["configuracion"]["voz"]
        self.nombre_voz = configuracion_voz["voz_edge"]
        self.velocidad = configuracion_voz["velocidad_edge"]
        self.usar_respaldo_local = configuracion_voz["usar_respaldo_local"]
        self.idioma_respaldo_local = configuracion_voz["idioma_respaldo_local"]
        self.idioma_gtts = configuracion_voz["idioma_gtts"]
        self.region_gtts = configuracion_voz["region_gtts"]
        self.cola_audio = queue.Queue()
        self.hilo_audio = None
        self.texto_pendiente = ""

        pygame.mixer.init()

    async def _generar_audio(self, texto, ruta):
        comunicador = edge_tts.Communicate(
            texto,
            voice=self.nombre_voz,
            rate=self.velocidad,
        )
        await comunicador.save(ruta)

    def _generar_audio_gtts(self, texto, ruta):
        from gtts import gTTS

        gTTS(
            text=texto,
            lang=self.idioma_gtts,
            tld=self.region_gtts,
        ).save(ruta)

    def _reproducir_local(self, texto):
        import pyttsx3

        motor = pyttsx3.init(driverName="sapi5")
        try:
            voces = motor.getProperty("voices")
            idioma = self.idioma_respaldo_local.lower()

            def coincide_idioma(voz):
                for etiqueta in getattr(voz, "languages", []):
                    if isinstance(etiqueta, bytes):
                        etiqueta = etiqueta.decode(errors="ignore")
                    etiqueta_normalizada = str(etiqueta).lower().replace("_", "-")
                    if (
                        etiqueta_normalizada == idioma
                        or etiqueta_normalizada.startswith(f"{idioma}-")
                    ):
                        return True
                return False

            voz_local = next(
                (voz for voz in voces if coincide_idioma(voz)),
                None,
            )
            if voz_local:
                motor.setProperty("voice", voz_local.id)
            else:
                print(
                    f"[Sistema]: No encontré una voz local para '{idioma}'; "
                    "usaré la voz predeterminada de Windows."
                )
            motor.setProperty("rate", int(motor.getProperty("rate") * 1.15))
            motor.say(texto)
            motor.runAndWait()
        finally:
            motor.stop()

    def _reproducir(self, texto):
        ruta_audio = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as archivo:
                ruta_audio = archivo.name

            try:
                asyncio.run(self._generar_audio(texto, ruta_audio))
            except Exception as error:
                estado = getattr(error, "status", None)
                detalle = f"HTTP {estado}" if estado else type(error).__name__
                print(
                    f"\n[Sistema]: Edge TTS no está disponible ({detalle}). "
                    "Usando la voz española de Google TTS."
                )
                try:
                    self._generar_audio_gtts(texto, ruta_audio)
                except Exception as error_gtts:
                    print(
                        "\n[Sistema]: Google TTS tampoco está disponible: "
                        f"{type(error_gtts).__name__}: {error_gtts}"
                    )
                    if not self.usar_respaldo_local:
                        return
                    try:
                        self._reproducir_local(texto)
                    except Exception as error_local:
                        print(
                            "\n[Sistema]: También falló la voz local de Windows: "
                            f"{type(error_local).__name__}: {error_local}"
                        )
                    return

            pygame.mixer.music.load(ruta_audio)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as error:
            print(
                "\n[Sistema]: No se pudo reproducir el audio: "
                f"{type(error).__name__}: {error}"
            )
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
        frases = [frase.strip() for frase in frases if frase.strip()]
        while len(frases) >= 2:
            self.cola_audio.put(" ".join(frases[:2]))
            frases = frases[2:]
        if frases:
            self.texto_pendiente = f"{frases[0]} {self.texto_pendiente}"

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
