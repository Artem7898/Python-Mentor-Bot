# Python Mentor Bot

Python Mentor Bot te ayuda a aprender Python en Telegram. Abre **DASHBOARD** con `/start` para elegir una lección, ver ejemplos, enviar una pregunta, consultar tu progreso o cambiar el idioma de la interfaz.

[English](README.md) · [Русский](README-ru.md) · [Documentación](docs/README.md)

## Inicio rápido

Necesitas Python 3.14+, SQLite 3.35+ y un token para un bot de pruebas. [@BotFather](https://t.me/BotFather)

Desde la raíz del repositorio, crea un entorno e instala las dependencias.

```bash
python3.14 -m venv python-mentor-bot/.venv
python-mentor-bot/.venv/bin/python -m pip install -r python-mentor-bot/requirements.txt
```

Configura `BOT_TOKEN` en el entorno del proceso o en un archivo privado `python-mentor-bot/.env`. Arranca el bot desde el directorio de la aplicación.

```bash
(cd python-mentor-bot && .venv/bin/python main.py)
```

Abre el bot en Telegram y envía `/start`. El botón de idioma y el comando `/language` permiten elegir entre inglés, ruso y español. El bot guarda el idioma y tu progreso en SQLite.

El temario incluye fundamentos de Python y capítulos independientes sobre Django, FastAPI, Django REST Framework y Pydantic. El comando `/run (2 + 3) ** 2` evalúa una expresión aritmética con límites de complejidad.

La guía completa incluye los comandos para Windows, la configuración, la arquitectura, el temario y las pruebas. [Documentación en español](docs/es/README.md)
