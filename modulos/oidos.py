import os

import speech_recognition as sr
from dotenv import load_dotenv

load_dotenv()

class Oidos:
    def __init__(self):
        # Instanciamos el reconocedor, que será el cerebro auditivo
        self.reconocedor = sr.Recognizer()
        self.indice_microfono = self._seleccionar_microfono()
        
        # Habilitamos el ajuste dinámico. Esto ayuda a que el micrófono 
        # se adapte si los ventiladores de la laptop empiezan a sonar más fuerte.
        self.reconocedor.dynamic_energy_threshold = True

    def _seleccionar_microfono(self):
        """Obtiene un índice válido aunque Windows reordene los dispositivos."""
        indice_configurado = os.getenv("MICROPHONE_INDEX")
        nombres = sr.Microphone.list_microphone_names()

        if indice_configurado:
            try:
                indice = int(indice_configurado)
                if 0 <= indice < len(nombres):
                    return indice
            except ValueError:
                pass

        preferencias = ("microphone array", "frontmic", "microphone", "headset")
        for preferencia in preferencias:
            for indice, nombre in enumerate(nombres):
                if preferencia in nombre.lower():
                    return indice

        raise RuntimeError("No se encontró ningún micrófono de entrada")

    def grabar_y_transcribir(self):
        """Abre el micrófono, captura el audio y lo convierte a texto."""
        try:
            # Usamos un micrófono de entrada explícito para evitar el dispositivo predeterminado defectuoso.
            with sr.Microphone(device_index=self.indice_microfono) as origen:
                # Calibra el ruido de fondo durante 1 segundo antes de empezar a grabar
                self.reconocedor.adjust_for_ambient_noise(origen, duration=1)
                print(f"[Escuchando... Habla ahora] Micrófono: {self.indice_microfono}")

                # timeout=15: Da más tiempo para empezar a hablar después del atajo.
                # phrase_time_limit=15: Corta la grabación a los 15 segundos máximo para evitar que se quede pegado.
                audio = self.reconocedor.listen(origen, timeout=15, phrase_time_limit=15)
                print("[Procesando audio...]")
                
                # Para empezar sin configurar nada extra, usamos la API gratuita de Google.
                # (Nota: más adelante puedes cambiar 'recognize_google' por 'recognize_whisper' 
                # para usar tu GPU y procesarlo localmente).
                texto = self.reconocedor.recognize_google(audio, language="es-VE")
                return texto
                
        except sr.WaitTimeoutError:
            # Esto evita que el programa colapse si presionas la tecla y no dices nada
            print("[Sistema]: Tiempo de espera agotado.")
        except sr.UnknownValueError:
            # Si balbuceas o hay mucho ruido y la IA no entiende qué dijiste
            print("[Sistema]: Audio incomprensible.")
        except sr.RequestError as e:
            print(f"[Sistema]: Error de conexión con el servicio de transcripción: {e}")
        except (OSError, AssertionError, AttributeError) as e:
            print(f"[Sistema]: No se pudo abrir el micrófono {self.indice_microfono}: {e}")
        return None

# Código de prueba (solo se ejecuta si corres este archivo directamente)
if __name__ == "__main__":
    jarvis_oidos = Oidos()
    texto_detectado = jarvis_oidos.grabar_y_transcribir()
    if texto_detectado:
        print(f"Detectado: {texto_detectado}")