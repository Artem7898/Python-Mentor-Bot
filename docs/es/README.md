# Guía de Python Mentor Bot

[English](../en/README.md) · [Русский](../ru/README.md) · [Descripción del proyecto](../../README-es.md)

## Qué hace el bot

Abre un chat privado con el bot y envía `/start`. **DASHBOARD** es un menú integrado en Telegram con accesos al temario, los ejemplos de código, la instalación de Python, las preguntas, el progreso y la selección de idioma. Tu cuenta de Telegram identifica tu perfil automáticamente.

Abre el selector de idioma en DASHBOARD o usa `/language`. Puedes elegir español, inglés o ruso. Tu elección se guarda por cuenta de Telegram y se conserva al reiniciar. Antes de elegir, el bot usa el idioma de Telegram si es compatible. En los demás casos usa el ruso. El progreso se comparte entre idiomas.

| Comando | Acción |
| --- | --- |
| `/start` | Abrir DASHBOARD. |
| `/help` | Mostrar los comandos y su uso. |
| `/language` | Elegir el idioma del bot. |
| `/cancel` | Salir del diálogo para enviar una pregunta. |
| `/run (2 + 3) ** 2` | Calcular la expresión y devolver `25`. |

El bot guarda las preguntas para su revisión y confirma la recepción. El evaluador admite números enteros y reales finitos con las operaciones `+ - * / // % **`. Limita la longitud de la entrada, el tamaño y la profundidad del árbol, los exponentes y la magnitud de los números. Su gramática excluye nombres, llamadas, atributos, importaciones y sentencias.

## Instalación y arranque

Necesitas Python 3.14 o posterior, SQLite 3.35 o posterior y un token de bot de Telegram. Para desarrollar, crea un bot independiente para pruebas. [@BotFather](https://t.me/BotFather)

En Linux o macOS, ejecuta estos comandos desde la raíz del repositorio.

```bash
python3.14 -m venv python-mentor-bot/.venv
python-mentor-bot/.venv/bin/python -m pip install -r python-mentor-bot/requirements.txt
python-mentor-bot/.venv/bin/python -c 'import sqlite3; print(sqlite3.sqlite_version)'
```

En Windows con PowerShell, ejecuta estos comandos desde la raíz del repositorio.

```powershell
py -3.14 -m venv .\python-mentor-bot\.venv
.\python-mentor-bot\.venv\Scripts\python.exe -m pip install -r .\python-mentor-bot\requirements.txt
.\python-mentor-bot\.venv\Scripts\python.exe -c "import sqlite3; print(sqlite3.sqlite_version)"
```

Configura `BOT_TOKEN` en el entorno del proceso o en un archivo privado `python-mentor-bot/.env`. Sustituye el marcador por el token de pruebas y mantenlo fuera de Git y de los registros.

```dotenv
BOT_TOKEN=replace_with_your_test_bot_token
```

Arranca el bot desde el directorio de la aplicación. Con Bash, ejecuta desde la raíz del repositorio.

```bash
(cd python-mentor-bot && .venv/bin/python main.py)
```

Con PowerShell, ejecuta desde la raíz del repositorio.

```powershell
Push-Location .\python-mentor-bot
.\.venv\Scripts\python.exe main.py
Pop-Location
```

Espera el mensaje `Run polling` de aiogram y envía `/start` al bot. Usa un único proceso de long polling por token. Si Telegram indica un conflicto, detén la instancia anterior y comprueba si hay un webhook registrado antes de reiniciar.

### Configuración

Las variables del proceso tienen prioridad sobre `.env`. Las rutas relativas se resuelven desde el directorio de trabajo de la aplicación.

| Variable | Propósito |
| --- | --- |
| `BOT_TOKEN` | Token obligatorio de BotFather. El inicio rechaza los formatos incorrectos. |
| `DATABASE_PATH` | Ruta a la base de datos SQLite con permisos de escritura. El valor predeterminado es `data/python_mentor.db`. |
| `LOG_LEVEL` | Nivel de registro de la aplicación. El valor predeterminado es `INFO`. |
| `DEBUG` | Activa los registros de depuración cuando `LOG_LEVEL` no está definido. |
| `HTTPS_PROXY` | Variable del proceso para configurar un proxy hacia la API de Telegram cuando sea necesario. |

El bot necesita acceso HTTPS saliente a `api.telegram.org`. Si utilizas un entorno en la nube con red restringida, permite ese dominio y configura el token en la administración de secretos del entorno. Un error de conexión con el proxy apunta a la red o a la configuración del proxy. Un error de autenticación devuelto por Telegram apunta al token del bot. [API de bots de Telegram](https://core.telegram.org/bots/api)

## Temario

El temario incluye fundamentos y sintaxis moderna de Python, programación orientada a objetos, archivos, herramientas de desarrollo, ciencia de datos y entrada/salida asíncrona. Abre un capítulo desde DASHBOARD para leer sus páginas o ver sus ejemplos.

| Capítulo | Contenidos |
| --- | --- |
| Django | Estructura de proyectos y aplicaciones, modelos, migraciones y ciclo de petición y respuesta. [Documentación de Django](https://docs.djangoproject.com/) |
| FastAPI | Endpoints tipados, validación de peticiones y documentación OpenAPI generada. [Documentación de FastAPI](https://fastapi.tiangolo.com/) |
| Django REST Framework | Serializadores y endpoints REST basados en modelos de Django. [Documentación de Django REST Framework](https://www.django-rest-framework.org/) |
| Pydantic | Modelos de datos, restricciones de campos, validación y serialización. [Documentación de Pydantic](https://docs.pydantic.dev/latest/) |

Ejecuta los fragmentos de las lecciones en proyectos de aprendizaje separados. Instala en un entorno virtual independiente las dependencias indicadas en el capítulo correspondiente. Django, Django REST Framework, FastAPI y Uvicorn son dependencias opcionales para las lecciones. Pydantic v2 es una dependencia del bot y forma parte del temario.

## Arquitectura y datos

Python Mentor Bot funciona como un proceso asíncrono con long polling mediante aiogram. `main.py` gestiona el arranque y los ciclos de vida de la sesión HTTP y la base de datos. `bot/handlers.py` dirige los comandos y las pulsaciones de botones. `bot/i18n.py` selecciona y aplica el idioma de la interfaz. El catálogo suministra las páginas de las lecciones a los controladores. Pydantic v2 valida la configuración y los registros persistentes. `bot/storage.py` reutiliza una conexión aiosqlite y vincula los datos como parámetros de SQL.

SQLite conserva el registro, el idioma elegido, el capítulo y la página actuales, y las preguntas enviadas. Los estados temporales de conversación, como la espera de una pregunta, se guardan en memoria y caducan. Se pierden al reiniciar el proceso.

El bot crea el esquema al arrancar. Para trasladar una base anterior `python_mentor.db` o `bot_data.db`, detén los procesos que escriben en ella y crea una copia de seguridad de SQLite. Indica en `DATABASE_PATH` una copia de trabajo con permisos de escritura. La inicialización añade las columnas de progreso o idioma necesarias a los esquemas anteriores compatibles y conserva los registros existentes. Tras la migración, las preguntas nuevas se guardan en `user_questions`.

Puedes inicializar una copia sin un token de Telegram. Sustituye la ruta absoluta por la de tu copia de trabajo y ejecuta desde la raíz del repositorio.

```bash
(cd python-mentor-bot && .venv/bin/python create_db.py /absolute/path/to/working.db)
```

Puedes repetir la inicialización. Mantén en privado las bases y las copias de seguridad porque contienen identificadores de Telegram, nombres de usuario y preguntas. [Documentación de copias de seguridad de SQLite](https://sqlite.org/backup.html)

## Comprobaciones de desarrollo

Ejecuta estos comandos con Bash desde la raíz del repositorio.

```bash
python-mentor-bot/.venv/bin/python -m pip install -r python-mentor-bot/requirements-dev.txt
(cd python-mentor-bot && .venv/bin/ruff check .)
(cd python-mentor-bot && .venv/bin/ruff format --check .)
(cd python-mentor-bot && .venv/bin/python -B -m pytest -p no:cacheprovider)
```

En PowerShell, entra en el directorio de la aplicación y usa `.\.venv\Scripts\python.exe` y `.\.venv\Scripts\ruff.exe` con los mismos argumentos de pytest y Ruff.

Las pruebas automatizadas usan actualizaciones de Telegram simuladas y bases temporales. Para una prueba manual con un bot de pruebas, abre DASHBOARD, cambia a cada idioma y abre una lección sobre uno de los frameworks. Avanza hasta otra página, envía una pregunta y evalúa `/run 2 ** 3`. Reinicia el bot y comprueba que se conservan el idioma y el progreso. Repite con una segunda cuenta para verificar que las preferencias son independientes.

Si cambias los controladores o el almacenamiento, prueba los botones antiguos, los mensajes no disponibles, las preguntas vacías y las actualizaciones simultáneas de una cuenta. Si cambias la validación, prueba la ausencia del token, la omisión de secretos en los mensajes de error, las expresiones inválidas y los límites numéricos. Si cambias las lecciones o las traducciones, verifica la navegación, el escapado del código y la longitud de los mensajes de Telegram.
