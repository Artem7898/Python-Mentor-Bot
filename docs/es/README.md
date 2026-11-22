# Guía de Python Mentor Bot

[English](../en/README.md) · [Русский](../ru/README.md) · [Descripción del proyecto](../../README-es.md)

## Qué hace el bot

Abre un chat privado con el bot y envía `/start`. El **Dashboard** de Telegram da acceso al temario, los ejemplos de código, la instalación de Python, las preguntas, el progreso y los ajustes.

Abre el selector de idioma en el Dashboard o usa `/language`. La elección de español, inglés o ruso se guarda por cuenta de Telegram y se conserva al reiniciar. Antes de elegir, el bot usa el idioma de Telegram si es compatible y el ruso en los demás casos. El progreso se comparte entre idiomas.

| Comando | Acción |
| --- | --- |
| `/start` | Abrir el Dashboard. |
| `/help` | Mostrar los comandos y su uso. |
| `/language` | Elegir el idioma del bot. |
| `/cancel` | Salir del diálogo para enviar una pregunta. |
| `/questions` | Consultar tus preguntas y respuestas en un chat privado. |
| `/privacy` | Consultar los datos guardados y solicitar su eliminación en un chat privado. |
| `/run (2 + 3) ** 2` | Calcular la expresión y devolver `25`. |

El evaluador admite números enteros y reales finitos con las operaciones `+ - * / // % **`. Limita la longitud de la entrada, el tamaño y la profundidad del árbol, los exponentes y la magnitud de los números. Su gramática excluye nombres, llamadas, atributos, importaciones y sentencias.

### Privacidad y preguntas

Los grupos permiten consultar el catálogo de lecciones. Usa un chat privado para acceder a tu perfil, el progreso guardado, los ajustes, las preguntas y la eliminación de datos. El bot vincula el perfil al identificador de tu cuenta de Telegram y guarda tu nombre de usuario, el idioma, la actividad de aprendizaje y las preguntas enviadas.

Puedes tener hasta cinco preguntas abiertas. Evita incluir tokens y datos personales. Las preguntas nuevas y las que están en revisión cuentan como abiertas. El mentor puede marcar una pregunta como en revisión y guardar una respuesta en el panel privado. Abre `/questions` para leer la respuesta o borrar una pregunta tras confirmar. Al iniciar y cada hora mientras está en marcha, el bot elimina las preguntas de más de 90 días, incluidas las respondidas.

Para eliminar el perfil, el progreso, los marcadores, las lecciones completadas y las preguntas de la base de datos del bot, usa `/privacy` en un chat privado y confirma la acción. Gestiona el historial del chat desde Telegram. El operador gestiona por separado la caducidad de las copias de seguridad.

## Instalación y arranque

Necesitas Python 3.14 o posterior, SQLite 3.35 o posterior y un token de bot de Telegram. Para desarrollar, crea un bot independiente para pruebas. [@BotFather](https://t.me/BotFather)

En Linux o macOS, ejecuta estos comandos desde la raíz del repositorio.

```bash
python3.14 -m venv python-mentor-bot/.venv
python-mentor-bot/.venv/bin/python -m pip install --require-hashes -r python-mentor-bot/requirements.lock
python-mentor-bot/.venv/bin/python -c 'import sqlite3; print(sqlite3.sqlite_version)'
```

En Windows con PowerShell, ejecuta estos comandos desde la raíz del repositorio.

```powershell
py -3.14 -m venv .\python-mentor-bot\.venv
.\python-mentor-bot\.venv\Scripts\python.exe -m pip install --require-hashes -r .\python-mentor-bot\requirements.lock
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
| `BOT_OWNER_IDS` | Identificadores opcionales de propietarios en Telegram, separados por comas. |
| `BOT_MENTOR_IDS` | Identificadores opcionales de mentores en Telegram, separados por comas. |
| `BOT_EDITOR_IDS` | Identificadores opcionales de editores en Telegram, separados por comas. |
| `LOG_LEVEL` | Nivel de registro de la aplicación. El valor predeterminado es `INFO`. |
| `DEBUG` | Activa los registros de depuración cuando `LOG_LEVEL` no está definido. |
| `HTTPS_PROXY` | Variable del proceso para configurar un proxy hacia la API de Telegram cuando sea necesario. |

El bot necesita acceso HTTPS saliente a `api.telegram.org`. Si utilizas un entorno en la nube con red restringida, permite ese dominio y configura el token en la administración de secretos del entorno. Un error de conexión con el proxy apunta a la red o a la configuración del proxy. Un error de autenticación devuelto por Telegram apunta al token del bot. [API de bots de Telegram](https://core.telegram.org/bots/api)

### Acceso del personal

Usa identificadores numéricos de cuentas de Telegram. Una lista vacía deja el rol sin asignar. Concede a cada cuenta los roles que necesita y reinicia el proceso del bot tras cambiar la configuración.

Los propietarios y mentores pueden usar `/mentor` en un chat privado para revisar las preguntas. Los propietarios y editores pueden usar `/editor` en privado para consultar cómo contribuir al temario. Envía los cambios a Git para que pasen la revisión y las comprobaciones de CI antes de desplegarlos. Conserva los identificadores de las lecciones publicadas, actualiza las tres traducciones y ejecuta cada ejemplo modificado con su intérprete y dependencias.

## Temario

El catálogo tiene 81 páginas de lecciones en 16 temas. Elige un capítulo o una ruta de aprendizaje desde el Dashboard, filtra por nivel o busca títulos de lecciones y capítulos en un chat privado. Cada página indica su nivel, Principiante, Intermedio o Profesional. Los títulos, las explicaciones y las instrucciones siguen el idioma elegido. Todos los idiomas comparten los ejemplos de código.

Desde el Dashboard puedes retomar la última lección abierta. El modo compacto muestra primero la explicación y permite abrir el código por separado. Puedes cambiar el modo en los ajustes. Guarda páginas en los marcadores, marca las lecciones completadas y comprueba lo aprendido con pruebas breves sobre algunos temas.

| Capítulo | Contenidos |
| --- | --- |
| Python 3.14 | Verificación del intérprete, cadenas de plantilla, anotaciones diferidas, Zstandard y grupos de intérpretes. [Novedades de Python 3.14](https://docs.python.org/3.14/whatsnew/3.14.html) |
| Novedades de Python 3.15 | UTF-8 por defecto, desempaquetado en comprensiones, frozendict, valores centinela, importaciones diferidas y profiling. [Novedades de Python 3.15](https://docs.python.org/3.15/whatsnew/3.15.html) |
| Django | Proyecto con 5.2 LTS, modelos, formularios, permisos, transacciones, optimización del ORM y ASGI. Otros ejercicios cubren las novedades de 6.0 y 6.1. La guía de actualización parte de proyectos anteriores con 4.1–5.1. [Notas de Django](https://docs.djangoproject.com/en/6.1/releases/) |
| FastAPI | Validación de peticiones, dependencias, lifespan y pruebas de autorización, transacciones y llamadas HTTP salientes. [Documentación de FastAPI](https://fastapi.tiangolo.com/) |
| Django REST Framework | Serializadores, viewsets, permisos y consultas restringidas al propietario, paginación y pruebas de autenticación, CSRF y operaciones concurrentes. [Documentación de DRF](https://www.django-rest-framework.org/) |
| Pydantic v2 | Validación de campos y lotes, uniones discriminadas y serialización para respuestas públicas. [Documentación de Pydantic](https://docs.pydantic.dev/latest/) |
| Práctica de Python | Funciones, tipos, POO, archivos, herramientas de desarrollo, ciencia de datos, tareas asíncronas y plazos, y pruebas con unittest y pytest. |

Los ejercicios principales usan Python 3.14. Utiliza Python 3.15 para los ejemplos propios de esa versión, estable desde el 9 de octubre de 2026. Django 5.2 LTS admite hasta Python 3.14. Para los ejercicios de Django en Python 3.15, instala Django 6.1.3 o un parche posterior de la serie 6.1. Django 4.1 se estudia como punto de partida para una migración. [Calendario de Python 3.15](https://peps.python.org/pep-0790/) · [Compatibilidad de Django](https://docs.djangoproject.com/en/6.1/faq/install/#what-python-version-can-i-use-with-django)

Ejecuta los ejemplos en proyectos de práctica e instala las dependencias del capítulo en un entorno virtual independiente. Django, DRF, FastAPI y las bibliotecas de datos son dependencias didácticas. El bot también usa Pydantic v2.

## Arquitectura y datos

Python Mentor Bot funciona como un proceso asíncrono con long polling mediante aiogram. `main.py` gestiona el arranque y los ciclos de vida de la sesión HTTP y la base de datos. `bot/handlers.py` dirige los comandos y las pulsaciones de botones. `bot/i18n.py` selecciona y aplica el idioma de la interfaz. El catálogo suministra las páginas de las lecciones a los controladores. Pydantic v2 valida la configuración y los registros persistentes. `bot/storage.py` reutiliza una conexión aiosqlite y vincula los datos como parámetros de SQL.

SQLite conserva los perfiles, las preferencias, el progreso, los marcadores, las lecciones completadas y las preguntas enviadas. Los estados temporales de conversación, como la espera de una pregunta, se guardan en memoria y caducan. Se pierden al reiniciar el proceso.

El bot crea el esquema al arrancar. Para trasladar una base anterior `python_mentor.db` o `bot_data.db`, detén los procesos que escriben en ella y crea una copia de seguridad de SQLite. Indica en `DATABASE_PATH` una copia de trabajo con permisos de escritura. La inicialización añade las columnas de progreso o idioma necesarias a los esquemas anteriores compatibles y conserva los registros existentes. Tras la migración, las preguntas nuevas se guardan en `user_questions`.

Puedes inicializar una copia sin un token de Telegram. Sustituye la ruta absoluta por la de tu copia de trabajo y ejecuta desde la raíz del repositorio.

```bash
(cd python-mentor-bot && .venv/bin/python create_db.py /absolute/path/to/working.db)
```

Puedes repetir la inicialización. Guarda la base de `DATABASE_PATH` y las copias fuera del repositorio y en un directorio accesible solo a la cuenta del servicio y al personal autorizado. Usa un archivo normal en un directorio que pertenezca al servicio y carezca de permisos de escritura compartidos. En POSIX usa permisos `0700` para el directorio y `0600` para los archivos de base de datos y las copias. En Windows, restringe el acceso mediante ACL. Aplica la misma política a los archivos auxiliares de SQLite. Prueba la restauración en una copia privada y elimina las copias según la política de retención. [Documentación de copias de seguridad de SQLite](https://sqlite.org/backup.html)

Se retiró la base de datos histórica de la copia de trabajo tras verificar un archivo local de acceso restringido. El archivo se conserva en los commits anteriores. Se mantuvo el historial de Git. Restringe el acceso al repositorio y a las copias hasta que el responsable de los datos revise las versiones anteriores.

## Comprobaciones de desarrollo

Ejecuta estos comandos con Bash desde la raíz del repositorio.

```bash
python-mentor-bot/.venv/bin/python -m pip install --require-hashes -r python-mentor-bot/requirements-dev.lock
(cd python-mentor-bot && .venv/bin/ruff check .)
(cd python-mentor-bot && .venv/bin/ruff format --check .)
(cd python-mentor-bot && .venv/bin/python -B -m pytest -p no:cacheprovider)
```

En PowerShell, entra en el directorio de la aplicación y usa `.\.venv\Scripts\python.exe` y `.\.venv\Scripts\ruff.exe` con los mismos argumentos de pytest y Ruff.

Cuando cambien las dependencias, vuelve a generar ambos archivos de bloqueo con uv desde el directorio de la aplicación.

```bash
uv pip compile --universal --python-version 3.14 --generate-hashes --no-annotate --output-file requirements.lock requirements.txt
uv pip compile --universal --python-version 3.14 --generate-hashes --no-annotate --constraint requirements.lock --output-file requirements-dev.lock requirements-dev.txt
```

CI ejecuta Ruff y pytest en Python 3.14 y 3.15, audita las dependencias del bot con pip-audit, analiza el historial Git con Gitleaks y oculta los valores detectados. También rechaza bases de despliegue y archivos dotenv rastreados, salvo la plantilla de ejemplo. Los archivos de bloqueo con hashes fijan las versiones de las dependencias de ejecución y desarrollo. Revisa y prueba sus actualizaciones junto con los cambios en los manifiestos.

Las pruebas automatizadas usan actualizaciones de Telegram simuladas y bases temporales. Para una prueba manual, abre el Dashboard de un bot de pruebas en un chat privado. Cambia el idioma, recorre una ruta, prueba el modo compacto, guarda un marcador, completa una lección y responde a una prueba breve. Reinicia el bot y comprueba el progreso de dos cuentas. Envía una pregunta y comprueba el acceso con un mentor autorizado y con una cuenta sin ese rol. En un grupo, verifica que es posible consultar el catálogo y que las acciones personales remiten a un chat privado. Confirma la eliminación de un perfil de prueba con `/privacy`.

Si cambias los controladores o el almacenamiento, prueba los botones antiguos, los mensajes no disponibles, las preguntas vacías y las actualizaciones simultáneas de una cuenta. Si cambias la validación, prueba la ausencia del token, la omisión de secretos en los mensajes de error, las expresiones inválidas y los límites numéricos. Si cambias las lecciones o las traducciones, verifica la navegación, el escapado del código y la longitud de los mensajes de Telegram.
