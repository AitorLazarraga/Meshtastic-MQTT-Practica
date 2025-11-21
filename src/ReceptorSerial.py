#!/usr/bin/env python3
"""
Script para RECIBIR mensajes por puerto serial desde dispositivo LoRa
"""

import serial
import time
from datetime import datetime
import re

class ReceptorSerial:
    def __init__(self, connector=None):
        """Inicializa el receptor serial"""
        self.connector = connector
        self.puerto = connector.portS if connector else '/dev/ttyUSB0'
        self.baudrate = connector.baudrateS if connector else 115200
        self.serial = None
        self.conectado = False
        
        # Listas para GUI (similar a MqttRecibo)
        self.mensajes = {}
        self.n_mensaje = 0
        self.ultimo_mensaje = None
        self.nuevos_mensajes = []
        
    def ParseText(self, payload_str):
        """
        Parsea mensajes tipo key=value o key: value separados por comas.
        """
        pattern = r'(\w+)\s*(?:=|:)\s*([^,]+)'
        matches = re.findall(pattern, payload_str)
        data = {}

        for k, v in matches:
            v = v.strip()

            # Hexadecimal (0x1234abcd)
            if re.fullmatch(r"0x[0-9A-Fa-f]+", v):
                data[k] = int(v, 16)
                continue

            # Int (positivos o negativos)
            if re.fullmatch(r"-?\d+", v):
                data[k] = int(v)
                continue

            # Float (incluye - y .)
            if re.fullmatch(r"-?\d+\.\d+", v):
                data[k] = float(v)
                continue

            # Valor texto
            data[k] = v

        return data

    def conectar(self):
        """Abre la conexión serial"""
        try:
            self.serial = serial.Serial(
                port=self.puerto,
                baudrate=self.baudrate,
                timeout=1,
                rtscts=True
            )
            '''
            parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,'''
            
            # Limpiar buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            self.conectado = True
            print(f"✓ Conectado a {self.puerto} @ {self.baudrate} baudios")
            print(f"  Esperando mensajes...\n")
            print("=" * 60)
            return True
            
        except serial.SerialException as e:
            print(f"✗ Error abriendo puerto: {e}")
            print("\n💡 Soluciones:")
            print("   - Verifica que el puerto sea correcto")
            print("   - Asegúrate de tener permisos: sudo usermod -a -G dialout $USER")
            print("   - O usa: sudo chmod 666 " + self.puerto)
            self.conectado = False
            return False
            
        except Exception as e:
            print(f"✗ Error inesperado: {e}")
            self.conectado = False
            return False
    
    def leer_linea(self):
        """Lee una línea del puerto serial"""
        if not self.conectado or not self.serial:
            return None
        
        try:
            if self.serial.in_waiting > 0:
                linea = self.serial.readline()
                return linea
            return None
            
        except Exception as e:
            print(f"✗ Error leyendo: {e}")
            return None
    
    def procesar_mensaje_serial(self, texto_limpio, timestamp):
        """
        Procesa un mensaje serial y lo agrega a las listas para la GUI
        Similar a como lo hace ProcesarTexto
        """
        try:
            datos_parseados = self.ParseText(texto_limpio)
            
            if 'msg' in datos_parseados:
                texto_msg = datos_parseados['msg']
                
                # Extraer remitente si existe
                remitente = datos_parseados.get('from', 'Desconocido')
                
                # Construir mensaje formateado
                self.n_mensaje += 1
                mensaje_formateado = f"[{timestamp}] Serial - {remitente}: {texto_msg}"
                
                # Guardar en diccionario y listas
                self.mensajes[self.n_mensaje] = mensaje_formateado
                self.ultimo_mensaje = mensaje_formateado
                self.nuevos_mensajes.append(mensaje_formateado)
                
                print(f"✉️  Mensaje procesado: {mensaje_formateado}")
                
                # Si hay callback de GUI, llamarlo
                if self.connector and hasattr(self.connector, 'gui_callback'):
                    self.connector.gui_callback()
                    
        except Exception as e:
            print(f"Error procesando mensaje serial: {e}")
    
    def escuchar_continuo(self, mostrar_hex=False, mostrar_raw=False):
        """
        Escucha continuamente el puerto serial
        """
        print("🎧 Escuchando puerto serial...")
        print("   Presiona Ctrl+C para detener\n")
        
        try:
            while True:
                linea = self.leer_linea()
                
                if linea:
                    # Datos en formato raw
                    if mostrar_raw:
                        print(f"  RAW: {linea}")
                    
                    # Datos en hexadecimal
                    if mostrar_hex:
                        hex_str = ' '.join([f'{b:02X}' for b in linea])
                        print(f"  HEX: {hex_str}")
                    
                    # Intentar decodificar como texto
                    try:
                        texto = linea.decode('utf-8').strip()

                        if 'INFO' in texto and '|' in texto:
                            # Extraer parte después del pipe
                            texto = texto[texto.find('|') + 1:]
                            
                            # Extraer parte después del corchete
                            if ']' in texto:
                                texto_limpio = texto[texto.find(']') + 1:].strip()
                            else:
                                texto_limpio = texto.strip()
                            
                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            
                            # Procesar el mensaje (lo agrega a nuevos_mensajes)
                            self.procesar_mensaje_serial(texto_limpio, timestamp)
                            
                            print(f"  TXT: {texto}")
                            print("-" * 60)

                    except UnicodeDecodeError:
                        if mostrar_raw:
                            print(f"  TXT: [No se pudo decodificar como UTF-8]")
                            print("-" * 60)
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\n👋 Deteniendo receptor serial...")
        except Exception as e:
            print(f"\n✗ Error durante escucha: {e}")
    
    def enviar_mensaje(self, mensaje):
        """Envía un mensaje por el puerto serial"""
        if not self.conectado or not self.serial:
            print("✗ Puerto serial no conectado")
            return False
        
        try:
            time.sleep(1)
            self.serial.write((mensaje + '\r\n').encode('utf-8'))
            print(f"✓ Mensaje enviado por serial: {mensaje}")
            return True
        except serial.SerialException as e:
            print(f"✗ Error al enviar mensaje por serial: {e}")
            return False
    
    def desconectar(self):
        """Cierra la conexión serial"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("✓ Puerto serial cerrado")
        self.conectado = False
    
    def is_connected(self):
        """Verifica si el puerto serial está conectado"""
        return self.conectado and self.serial and self.serial.is_open


def main():
    """Función de prueba standalone"""
    receptor = ReceptorSerial()
    
    if receptor.conectar():
        try:
            receptor.escuchar_continuo(False, False)
        finally:
            receptor.desconectar()
    else:
        print("\n✗ No se pudo establecer conexión")

if __name__ == "__main__":
    main()