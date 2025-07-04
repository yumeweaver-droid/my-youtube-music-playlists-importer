# Importador de Playlists para YouTube Music

Importa tus listas de reproducción desde archivos JSON (exportados desde otras plataformas) a YouTube Music para
migración, restauración de backups o sincronización multiplataforma.

---

## Descripción

`my_youtube_music_playlists_importer.py` es un script de línea de comandos en Python diseñado para importar tus
playlists a YouTube Music desde archivos JSON generados por herramientas
como [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader).

Este script se conecta a tu cuenta de YouTube Music mediante `ytmusicapi` y realiza:

- Creación de playlists (o uso de las existentes)
- Búsqueda y agregado de canciones por nombre e intérprete
- Prevención de duplicados (opcional)
- Reintentos automáticos para errores API transitorios (por ejemplo, HTTP 409 Conflict)

Este script es ideal para:

- Migrar tu biblioteca musical desde Spotify a YouTube Music
- Reconstruir playlists tras cambiar de plataforma
- Mantener backups sincronizados entre múltiples servicios
- Aprender sobre automatización con la API de YouTube Music usando Python

El proyecto se publica bajo la licencia MIT y está destinado a uso educativo y personal.

---

## Funcionalidades

- Importa playlists desde un **archivo JSON exportado por scripts de Spotify**
- Opcionalmente **elimina playlists existentes** con el mismo nombre antes de importar
- **Prevención de duplicados** (comportamiento por defecto)
- Flag opcional para **permitir duplicados** en las playlists importadas
- Implementa **reintentos con backoff exponencial** para errores transitorios 409 Conflict
- Delay configurable entre llamadas a la API para evitar límites de tasa
- **Logs** tanto en consola como en archivo para auditoría y depuración
- **Portable** – funciona en Windows, macOS y Linux

---

## Requisitos

- Python 3.9 o superior
- [ytmusicapi](https://ytmusicapi.readthedocs.io/)
- Una **cuenta de YouTube Music** (no requiere Premium)
- Tus **headers de autenticación** exportados desde el navegador para autenticar `ytmusicapi`

Instala las dependencias con:

```shell
pip install -r requirements.txt
````

---

## Configuración

1. **Clona este repositorio**

    ```shell
    git clone https://github.com/yourusername/my_youtube_music_playlists_importer.git
    cd my_youtube_music_playlists_importer
    ```

2. **Crea tu archivo `.env`**

   Copia el ejemplo provisto:

    ```shell
    cp .env.example .env
    ```

3. **Edita `.env` y define tus variables**

   **Obligatorias:**

    - `HEADERS_RAW_FILE`: Ruta al archivo de texto con tus headers exportados desde las DevTools del navegador.

   **Opcionales:**

    - `AUTH_GENERATED_FILE`: Ruta al archivo de autenticación generado (por defecto: ./browser.json)
    - `YT_API_DELAY_SECONDS`: Delay entre adiciones de canciones (por defecto: 1)
    - `YT_API_MAX_RETRIES`: Número máximo de reintentos para errores 409 Conflict (por defecto: 3)
    - `LOG_DIR`: Directorio para guardar logs (por defecto: ubicación del script)
    - `LOG_LEVEL`: Nivel de logs (por defecto: INFO)

### Autenticación de navegador con `ytmusicapi`

Este script usa **autenticación basada en navegador** con `ytmusicapi`, lo cual requiere copiar los headers de tus
requests de YouTube Music después de iniciar sesión exitosamente en [music.youtube.com](https://music.youtube.com).

#### ¿Por qué es necesario?

A diferencia de APIs oficiales, YouTube Music no ofrece un método directo de autenticación para desarrolladores.
`ytmusicapi` funciona simulando tu sesión de navegador, permitiéndole realizar acciones como si fueras tú, usando tus
cookies y headers de sesión.

#### Cómo extraer tus headers de YouTube Music

1. **Inicia sesión** en tu cuenta de YouTube Music en el navegador (Chrome o Firefox recomendados).
2. Abre las **DevTools (F12)**.
3. Ve a la pestaña **Network**.
4. Recarga la página para capturar requests.
5. Busca un request **POST** a `music.youtube.com` y revisa sus headers. Lo más sencillo es filtrar por `browse`.
6. Copia todos los **Request Headers** (en Firefox: clic derecho > copy > copy request headers).

Para un paso a paso detallado, consulta
la [guía de configuración de ytmusicapi](https://ytmusicapi.readthedocs.io/en/latest/setup/browser.html).

#### Guardando tus headers

Una vez copiados correctamente:

- Crea un archivo llamado `headers_raw.txt` en el directorio del proyecto.
- Pega allí los headers y guarda el archivo.

> ⚠️ **Nota de seguridad importante:**
> Este archivo contiene información de autenticación vinculada a tu cuenta de Google. Mantenlo **privado**, no lo subas
> a control de versiones y almacénalo de forma segura.

---

## Ejemplo de estructura del archivo JSON

El archivo JSON de entrada debe contener una lista de playlists, cada una con la siguiente estructura mínima:

```json
[
  {
    "playlist_name": "Mis canciones favoritas",
    "description": "Descripción opcional de esta playlist",
    "tracks": [
      {
        "name": "Título de la canción",
        "artist": "Nombre del artista"
      },
      {
        "name": "Otra canción",
        "artist": "Otro artista"
      }
    ]
  },
  {
    "playlist_name": "Chill Vibes",
    "description": "",
    "tracks": [
      {
        "name": "Chill Song 1",
        "artist": "Chill Artist"
      }
    ]
  }
]
````

### ✅ **Campos requeridos**

- `playlist_name`: Nombre de la playlist a crear o actualizar
- Cada objeto track debe incluir:

  - `name`: Título de la canción
  - `artist`: Artista de la canción

### ℹ️ **Campos opcionales**

- `description`: Descripción de la playlist (puede ser vacío)

> ⚠️ **Nota:**
> El archivo exportado por [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader)
> es compatible por defecto.
> Si usas tu propio exportador, asegúrate de que genere JSON con esta estructura.

---

## Uso

### Importar playlists a YouTube Music

```shell
python my_youtube_music_playlists_importer.py --playlists_file /ruta/a/playlists.json
```

### Permitir canciones duplicadas en las playlists

```shell
python my_youtube_music_playlists_importer.py --playlists_file /ruta/a/playlists.json --allow_duplicates
```

### Eliminar playlists existentes con el mismo nombre antes de importar

```shell
python my_youtube_music_playlists_importer.py --playlists_file /ruta/a/playlists.json --delete_if_exists
```

---

## Resumen de salida

Al finalizar, el script registrará:

- Total de playlists creadas
- Total de playlists eliminadas
- Total de playlists existentes (no eliminadas)
- Total de canciones agregadas exitosamente
- Total de canciones omitidas por prevención de duplicados
- Total de canciones que no pudieron agregarse (no encontradas o error API)
- Tiempo total de ejecución

---

## Descargo de Responsabilidad

Este script se proporciona únicamente con fines educativos.
Úsalo responsablemente con tu cuenta de YouTube Music.
El autor no asume ninguna responsabilidad por su uso indebido o por pérdida de datos causada por su utilización.
El código es limpio y no contiene componentes maliciosos.

## Descargo de Responsabilidad de Marca Registrada

YouTube y YouTube Music son marcas registradas de Google LLC.
Este proyecto **no está afiliado, patrocinado ni respaldado por Google** de ninguna manera.
Todas las referencias a YouTube Music se realizan únicamente con fines informativos y educativos.

---

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](../../LICENSE).
