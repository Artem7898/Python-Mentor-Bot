"""English and Spanish copy for the shared Python lesson catalog."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class PageTranslation:
    """Localized prose and optional overrides for instructional console examples."""

    title: str
    explanation: str
    steps: tuple[str, ...] | None = None
    windows_code: str | None = None
    linux_code: str | None = None
    windows_install: str | None = None
    linux_install: str | None = None
    install_code: str | None = None


type TopicTranslation = tuple[str, tuple[PageTranslation, ...]]

TRANSLATIONS: Final[dict[str, dict[str, TopicTranslation]]] = {
    "en": {
        "basics": (
            "📚 Python basics",
            (
                PageTranslation(
                    "Introduction to Python",
                    "Python is a high-level, interpreted programming language. "
                    "It is used for web development, data analysis, machine learning, "
                    "automation, and much more.\n\n"
                    "<b>Key features:</b>\n"
                    "• Clear, readable syntax\n"
                    "• Dynamic typing\n"
                    "• An extensive standard library\n"
                    "• Runs on Windows, Linux, and macOS\n\n"
                    "<b>Running Python for the first time:</b>",
                    windows_code="# Python Install Manager (Windows):\n"
                    "py -3.14 --version\npy -3.14",
                    linux_code="# Linux/macOS:\npython3.14 --version\npython3.14",
                ),
                PageTranslation(
                    "Control flow and functions",
                    "Conditionals and loops are fundamental programming tools.",
                ),
            ),
        ),
        "syntax": (
            "🧠 Python syntax",
            (
                PageTranslation(
                    "Modern syntax",
                    "Python continues to evolve as new language features are added.",
                ),
            ),
        ),
        "oop": (
            "🏛️ Object-oriented programming",
            (
                PageTranslation(
                    "OOP basics",
                    "Object-oriented programming organizes code into objects that combine data "
                    "and the methods that work with it.\n\n"
                    "<b>Four principles of OOP:</b>\n"
                    "1. <b>Encapsulation</b> hides implementation details.\n"
                    "2. <b>Inheritance</b> builds new classes from existing classes.\n"
                    "3. <b>Polymorphism</b> lets objects use the same interface with "
                    "different implementations.\n"
                    "4. <b>Abstraction</b> exposes the concepts a caller needs.",
                ),
            ),
        ),
        "files": (
            "📁 Working with files",
            (
                PageTranslation(
                    "Reading and writing files",
                    "Programs use files to:\n"
                    "• Keep data between runs\n"
                    "• Store application settings\n"
                    "• Process large datasets\n"
                    "• Log events",
                ),
            ),
        ),
        "frameworks": (
            "🚀 Web frameworks",
            (
                PageTranslation(
                    "Flask: a microframework",
                    "Flask is a lightweight framework for building web applications.",
                    windows_install=(
                        "# Install Flask on Windows:\n"
                        "1. Open Command Prompt (cmd)\n"
                        "2. Create a virtual environment:\n"
                        "   python -m venv venv\n"
                        "3. Activate it:\n"
                        "   venv\\Scripts\\activate\n"
                        "4. Install Flask:\n"
                        "   python -m pip install flask\n"
                        "5. Check the installation:\n"
                        "   python -m flask --version"
                    ),
                    linux_install=(
                        "# Install Flask on Linux:\n"
                        "1. Open a terminal\n"
                        "2. Create a virtual environment:\n"
                        "   python3 -m venv venv\n"
                        "3. Activate it:\n"
                        "   source venv/bin/activate\n"
                        "4. Install Flask:\n"
                        "   python -m pip install flask\n"
                        "5. Check the installation:\n"
                        "   python3 -m flask --version"
                    ),
                ),
                PageTranslation(
                    "Django: a full-featured framework",
                    "Django is a framework for building complex web applications.",
                    windows_install=(
                        "# Install Django on Windows:\n"
                        "1. python -m venv venv\n"
                        "2. venv\\Scripts\\activate\n"
                        '3. python -m pip install "Django>=5.2.8,<5.3"\n'
                        "4. django-admin --version"
                    ),
                    linux_install=(
                        "# Install Django on Linux:\n"
                        "1. python3 -m venv venv\n"
                        "2. source venv/bin/activate\n"
                        '3. python -m pip install "Django>=5.2.8,<5.3"\n'
                        "4. django-admin --version"
                    ),
                ),
            ),
        ),
        "tools": (
            "🛠️ Developer tools",
            (
                PageTranslation(
                    "pip: the package installer",
                    "python -m pip installs and manages Python packages.",
                    windows_code=(
                        "# Common pip commands on Windows:\n\n"
                        "# Install a package\n"
                        "python -m pip install requests\n\n"
                        "# Require a compatible Django version\n"
                        'python -m pip install "Django~=5.2.8"\n\n'
                        "# Install packages listed in requirements.txt\n"
                        "python -m pip install -r requirements.txt\n\n"
                        "# Upgrade, list, or remove packages\n"
                        "python -m pip install --upgrade package_name\n"
                        "python -m pip list\n"
                        "python -m pip uninstall package_name\n\n"
                        "# Find packages at https://pypi.org/search/"
                    ),
                    linux_code=(
                        "# Use pip3 on Linux:\n\n"
                        "python3 -m pip install requests\n"
                        "python3 -m pip list\n"
                        "python3 -m pip uninstall package_name"
                    ),
                ),
                PageTranslation(
                    "Git: version control",
                    "Git tracks changes to code and helps teams collaborate.",
                    windows_install=(
                        "# Install Git on Windows:\n"
                        "1. Download it from git-scm.com\n"
                        "2. Run the installer\n"
                        "3. Use Git Bash or Command Prompt"
                    ),
                    linux_install=(
                        "# Install Git on Ubuntu or Debian:\n"
                        "sudo apt update\n"
                        "sudo apt install git\n"
                        "git --version"
                    ),
                ),
            ),
        ),
        "datascience": (
            "📊 Data science",
            (
                PageTranslation(
                    "NumPy and pandas",
                    "Libraries for scientific computing and data analysis.",
                    install_code=(
                        "# Install libraries for data science\n"
                        "python -m pip install numpy pandas scikit-learn"
                    ),
                ),
                PageTranslation(
                    "Machine learning",
                    "A basic machine learning example using scikit-learn.",
                ),
            ),
        ),
        "async": (
            "⚡ Asynchronous programming",
            (
                PageTranslation(
                    "async/await",
                    "Asynchronous programming helps applications handle I/O efficiently:\n"
                    "• Network requests\n"
                    "• Database access\n"
                    "• File operations\n"
                    "• Web servers",
                ),
            ),
        ),
        "install": (
            "📥 Python installation",
            (
                PageTranslation(
                    "Windows",
                    "Install Python 3.14 using the official Python Install Manager.",
                    steps=(
                        "Get Python Install Manager from python.org/downloads/windows.",
                        "Open PowerShell and run py install 3.14.",
                        "Check the version with py -3.14 --version.",
                        "Create your project environment with py -3.14 -m venv .venv.",
                    ),
                ),
                PageTranslation(
                    "Linux and macOS",
                    "Install Python 3.14 alongside your system interpreter.",
                    steps=(
                        "Install Python 3.14 from a trusted source or use uv python install 3.14.",
                        "Check the interpreter with python3.14 --version.",
                        "Create an environment with python3.14 -m venv .venv.",
                        "Run .venv/bin/python -m pip --version to check pip.",
                    ),
                ),
            ),
        ),
    },
    "es": {
        "basics": (
            "📚 Fundamentos de Python",
            (
                PageTranslation(
                    "Introducción a Python",
                    "Python es un lenguaje de programación interpretado y de alto nivel. "
                    "Se utiliza para el desarrollo web, el análisis de datos, el aprendizaje "
                    "automático, la automatización y mucho más.\n\n"
                    "<b>Características:</b>\n"
                    "• Sintaxis clara y legible\n"
                    "• Tipado dinámico\n"
                    "• Amplia biblioteca estándar\n"
                    "• Compatible con Windows, Linux y macOS\n\n"
                    "<b>Cómo iniciar Python por primera vez:</b>",
                    windows_code="# Python Install Manager (Windows):\n"
                    "py -3.14 --version\npy -3.14",
                    linux_code="# Linux/macOS:\npython3.14 --version\npython3.14",
                ),
                PageTranslation(
                    "Estructuras de control y funciones",
                    "Las condiciones y los bucles son herramientas básicas de programación.",
                ),
            ),
        ),
        "syntax": (
            "🧠 Sintaxis de Python",
            (
                PageTranslation(
                    "Sintaxis moderna",
                    "Python evoluciona con nuevas características del lenguaje.",
                ),
            ),
        ),
        "oop": (
            "🏛️ Programación orientada a objetos",
            (
                PageTranslation(
                    "Fundamentos de la POO",
                    "La programación orientada a objetos organiza el código en objetos que "
                    "combinan datos y métodos para operar sobre ellos.\n\n"
                    "<b>Cuatro principios de la POO:</b>\n"
                    "1. <b>Encapsulación</b>: oculta los detalles de implementación.\n"
                    "2. <b>Herencia</b>: crea clases a partir de otras clases.\n"
                    "3. <b>Polimorfismo</b>: permite que varios objetos compartan una interfaz "
                    "con distintas implementaciones.\n"
                    "4. <b>Abstracción</b>: expone los conceptos necesarios para usar un objeto.",
                ),
            ),
        ),
        "files": (
            "📁 Manejo de archivos",
            (
                PageTranslation(
                    "Lectura y escritura de archivos",
                    "Los programas usan archivos para:\n"
                    "• Conservar datos entre ejecuciones\n"
                    "• Almacenar la configuración de aplicaciones\n"
                    "• Procesar grandes conjuntos de datos\n"
                    "• Registrar eventos",
                ),
            ),
        ),
        "frameworks": (
            "🚀 Frameworks web",
            (
                PageTranslation(
                    "Flask: un microframework",
                    "Flask es un framework ligero para desarrollar aplicaciones web.",
                    windows_install=(
                        "# Instala Flask en Windows:\n"
                        "1. Abre el símbolo del sistema (cmd)\n"
                        "2. Crea un entorno virtual:\n"
                        "   python -m venv venv\n"
                        "3. Actívalo:\n"
                        "   venv\\Scripts\\activate\n"
                        "4. Instala Flask:\n"
                        "   python -m pip install flask\n"
                        "5. Comprueba la instalación:\n"
                        "   python -m flask --version"
                    ),
                    linux_install=(
                        "# Instala Flask en Linux:\n"
                        "1. Abre una terminal\n"
                        "2. Crea un entorno virtual:\n"
                        "   python3 -m venv venv\n"
                        "3. Actívalo:\n"
                        "   source venv/bin/activate\n"
                        "4. Instala Flask:\n"
                        "   python -m pip install flask\n"
                        "5. Comprueba la instalación:\n"
                        "   python3 -m flask --version"
                    ),
                ),
                PageTranslation(
                    "Django: un framework completo",
                    "Django es un framework para desarrollar aplicaciones web complejas.",
                    windows_install=(
                        "# Instala Django en Windows:\n"
                        "1. python -m venv venv\n"
                        "2. venv\\Scripts\\activate\n"
                        '3. python -m pip install "Django>=5.2.8,<5.3"\n'
                        "4. django-admin --version"
                    ),
                    linux_install=(
                        "# Instala Django en Linux:\n"
                        "1. python3 -m venv venv\n"
                        "2. source venv/bin/activate\n"
                        '3. python -m pip install "Django>=5.2.8,<5.3"\n'
                        "4. django-admin --version"
                    ),
                ),
            ),
        ),
        "tools": (
            "🛠️ Herramientas de desarrollo",
            (
                PageTranslation(
                    "pip: el instalador de paquetes",
                    "pip instala y administra paquetes de Python.",
                    windows_code=(
                        "# Comandos habituales de pip en Windows:\n\n"
                        "# Instala un paquete\n"
                        "python -m pip install requests\n\n"
                        "# Requiere una versión compatible de Django\n"
                        'python -m pip install "Django~=5.2.8"\n\n'
                        "# Instala los paquetes de requirements.txt\n"
                        "python -m pip install -r requirements.txt\n\n"
                        "# Actualiza, enumera o elimina paquetes\n"
                        "python -m pip install --upgrade package_name\n"
                        "python -m pip list\n"
                        "python -m pip uninstall package_name\n\n"
                        "# Busca paquetes en https://pypi.org/search/"
                    ),
                    linux_code=(
                        "# Usa pip3 en Linux:\n\n"
                        "python3 -m pip install requests\n"
                        "python3 -m pip list\n"
                        "python3 -m pip uninstall package_name"
                    ),
                ),
                PageTranslation(
                    "Git: control de versiones",
                    "Git registra los cambios en el código y facilita el trabajo en equipo.",
                    windows_install=(
                        "# Instala Git en Windows:\n"
                        "1. Descárgalo desde git-scm.com\n"
                        "2. Ejecuta el instalador\n"
                        "3. Usa Git Bash o el símbolo del sistema"
                    ),
                    linux_install=(
                        "# Instala Git en Ubuntu o Debian:\n"
                        "sudo apt update\n"
                        "sudo apt install git\n"
                        "git --version"
                    ),
                ),
            ),
        ),
        "datascience": (
            "📊 Ciencia de datos",
            (
                PageTranslation(
                    "NumPy y pandas",
                    "Bibliotecas para el cálculo científico y el análisis de datos.",
                    install_code=(
                        "# Instala bibliotecas de ciencia de datos\n"
                        "python -m pip install numpy pandas scikit-learn"
                    ),
                ),
                PageTranslation(
                    "Aprendizaje automático",
                    "Un ejemplo básico de aprendizaje automático con scikit-learn.",
                ),
            ),
        ),
        "async": (
            "⚡ Programación asíncrona",
            (
                PageTranslation(
                    "async/await",
                    "La programación asíncrona facilita las operaciones de entrada y salida:\n"
                    "• Solicitudes de red\n"
                    "• Acceso a bases de datos\n"
                    "• Operaciones con archivos\n"
                    "• Servidores web",
                ),
            ),
        ),
        "install": (
            "📥 Instalación de Python",
            (
                PageTranslation(
                    "Windows",
                    "Instala Python 3.14 con el gestor oficial Python Install Manager.",
                    steps=(
                        "Obtén Python Install Manager en python.org/downloads/windows.",
                        "Abre PowerShell y ejecuta py install 3.14.",
                        "Comprueba la versión con py -3.14 --version.",
                        "Crea el entorno del proyecto con py -3.14 -m venv .venv.",
                    ),
                ),
                PageTranslation(
                    "Linux y macOS",
                    "Instala Python 3.14 junto al intérprete del sistema.",
                    steps=(
                        "Instala Python 3.14 de una fuente fiable o usa uv python install 3.14.",
                        "Comprueba la versión con python3.14 --version.",
                        "Crea un entorno con python3.14 -m venv .venv.",
                        "Ejecuta .venv/bin/python -m pip --version para comprobar pip.",
                    ),
                ),
            ),
        ),
    },
}
