# Práctica 1 – POO  
## Comunicación al fin del mundo  

**Autor:** Aitor Lazárraga  
**Asignatura:** Programación Orientada a Objetos  
**Fecha:** 10/10/2025  

---

## 🧭 Índice

- [Introducción y Objetivos](#introducción-y-objetivos)
- [Desarrollo](#desarrollo)
  - [MqttCliente.py](#mqttclientepy)
  - [MqttDispositivo.py](#mqttdispositivopy)
  - [MqttEnvio.py](#mqttenviopy)
  - [MqttRecibo.py](#mqttrecibopy)
  - [Interfaz](#interfaz)
- [Conclusiones](#conclusiones)
- [Anexo: Librerías Usadas](#anexo-librerías-usadas)

---

## 🧩 Introducción y Objetivos

El objetivo de esta práctica es aprender a usar el protocolo de comunicación industrial **MQTT**, y para ello usar el formato de comunicación **mesh de Meshtastic**.

En esta práctica se refactoriza un código secuencial en una forma **modular y orientada a objetos**, con el objetivo de unirse a esa red mesh y poder enviar mensajes y datos posicionales o sensóricos entre nodos.

Tras refactorizar el código, se implementan clases cuyo objetivo es crear **interfaces de usuario por terminal** para la modificación de mensajes, lectura de los recibidos y almacenamiento persistente de los datos.

Finalmente, se ha implementado una clase adicional para **enviar y recibir imágenes** en formato base64. Esta clase no está completamente finalizada y se completará en la segunda parte de la práctica.

---

## ⚙️ Desarrollo

El primer objetivo era refactorizar el código en objetos.  
El programa original se ha dividido en cuatro módulos principales:

- **MqttCliente:** Encargado de crear las interfaces entre los demás módulos e iniciar el programa.  
- **MqttDispositivo:** Encargado de crear las conexiones, desconexiones, datos del dispositivo, suscripción a tópicos, etc.  
- **MqttRecibo:** Encargado de recibir los mensajes y tratarlos dependiendo del tipo de payload.  
- **MqttEnvio:** Encargado de crear, codificar y mandar los mensajes.

A mayores, se han implementado dos clases extra:

- **Interfaz:** Maneja la interacción con el usuario mediante línea de comandos.  
- **ImageEncoder:** Codifica y decodifica imágenes en base64, dividiendo las tramas en paquetes de 200 bytes para su envío.

---

## 🧠 MqttCliente.py

Este módulo inicia el programa y los demás módulos, además de crear el cliente y la conexión a la red.

Después de crear las conexiones, el callback y el cliente, espera a que esté conectado y llama a la interfaz que controla el programa.

El cliente está en la carpeta raíz (programa principal), y al importar el resto de módulos lo hace desde el paquete `src`.

---

## 🔌 MqttDispositivo.py

Es el módulo con más carga lógica. Se encarga de realizar el **setup inicial**, proporcionar datos del dispositivo y conectarse a la red mesh.

Entre sus atributos están el broker, el canal y los tópicos a suscribirse y publicar.

Crea un cliente MQTT con la key indicada, se suscribe a los tópicos necesarios y define un **callback** para tratar los mensajes entrantes.

Incluye métodos auxiliares que mejoran la legibilidad del código, como `is_connected()` o `create_client_and_callbacks()`, que centraliza la creación de los callbacks de mensajes.

---

## 📤 MqttEnvio.py

Se encarga de enviar mensajes, datos del nodo, acknowledgments y mensajes de tipo **trazarutas**, además de codificarlos.

Usa como atributo principal el cliente creado en `MqttDispositivo`, permitiendo enviar mensajes globales por el canal o mensajes directos a un nodo específico (indicando su ID).

También puede enviar información del dispositivo y coordenadas GPS, publicándolas en el tópico correspondiente.

Las funciones internas encargadas de generar la **encriptación y los paquetes mesh** son privadas, ya que solo deben usarse por otras funciones internas.

---

## 📥 MqttRecibo.py

Este módulo recibe los mensajes, los muestra en terminal y los guarda dependiendo del tipo de dato recibido.

Dispone de listas y diccionarios para almacenar temporalmente los datos antes de guardarlos en archivos persistentes.

### Flujo de funcionamiento:

1. Recepción del mensaje  
2. Decodificación  
3. Si el mensaje proviene de tópicos MQTT, se procesa como dato recibido  
   - **sensorGas:** se guarda en JSON y CSV  
   - **Sen55:** igual que el anterior, para facilitar tratamiento posterior  
4. Si no es sensórico, se trata como texto JSON y se almacena dependiendo del tipo:
   - **POSITION_APP:** parseado en diccionario → dataframe → CSV  
   - **TEXT_MESSAGE_APP:** texto con hora de recepción  
   - **NODEINFO_APP:** diccionario con hora añadida

### Función `ParseText()`

Transforma la payload (string) en un diccionario clave-valor mediante:
```python
matches = re.findall(r'(\w+):\s*([-\w.]+)', payload_str)
```
Luego convierte los valores a `int` o `float` si es posible, manteniendo el resto como texto.

Los datos recibidos se guardan en CSV usando `pandas`, y las rutas de guardado se obtienen dinámicamente con `pathlib` para evitar problemas de rutas absolutas.

---

## 💬 Interfaz

La clase **Interfaz** gestiona la interacción con el usuario desde terminal, actuando como puente entre los demás módulos.

- Si no detecta cliente o conexión, la inicia automáticamente.  
- Sus métodos principales son:
  - `mostrar_menu()`: muestra las opciones disponibles.
  - `elegir_opcion()`: ejecuta la opción seleccionada.
  - `run()`: mantiene el ciclo del menú activo.

Una de las funciones más destacadas es el cambio de **broker Meshtastic ↔ EMQX**.  
Cuando se cambia, la interfaz desconecta el cliente, limpia los tópicos y reconecta usando el nuevo broker.

Mientras se usa EMQX, la interfaz solo permite volver a modo Meshtastic.

Además, usa `pathlib` para encontrar las carpetas `datos` e `imagenes` desde cualquier ubicación del proyecto.

---

## 🧾 Conclusiones

- Se ha aprendido la importancia de la **refactorización de código**, clave para mantener proyectos grandes.  
- El protocolo **MQTT** puede ser muy útil para enviar datos sensóricos ligeros en entornos industriales sin cableado.  
- La parte más compleja fue entender código ajeno con tecnologías nuevas, lo que impulsó la investigación sobre los métodos y protocolos usados.

---

## 📚 Anexo: Librerías Usadas

- Meshtastic  
- Time  
- Pathlib  
- Paho.mqtt  
- Random  
- Base64  
- Cryptography  
- Re  
- Json  
- Os  
- Pandas

---

📅 **Fecha:** 10/10/2025  
✍️ **Autor:** Aitor Lazárraga  
🎓 **Asignatura:** Programación Orientada a Objetos
