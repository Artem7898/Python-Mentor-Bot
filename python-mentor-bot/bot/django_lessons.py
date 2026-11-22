"""A version-aware, localized Django workshop built around one sample project."""

# ruff: noqa: RUF001
# The catalogue contains intentionally Cyrillic lesson text.

from typing import Final

from bot.lesson_models import Lesson, LessonLevel, LocalizedPage, localize_lesson

_PAGES = (
    LocalizedPage(
        level=LessonLevel.BEGINNER,
        title=(
            "Первый проект и HTTP-маршрут",
            "First project and HTTP route",
            "Proyecto y ruta HTTP",
        ),
        explanation=(
            "Создадим каталог товаров. Проект config хранит настройки и таблицу маршрутов, "
            "а приложение catalog будет содержать модели и формы. Запустите упражнения под "
            "Python 3.14 на Django 5.2 LTS, начиная с 5.2.8. Для 6.0 и 6.1 есть "
            "отдельное практическое задание в конце.",
            "Build a product catalogue. The config project holds settings and routing. "
            "The catalog application will hold models and forms. Use Python 3.14 with "
            "Django 5.2 LTS, starting from 5.2.8. A separate lab covers Django 6.0 and 6.1.",
            "Crea un catálogo de productos. El proyecto config contiene la configuración "
            "y las rutas. La aplicación catalog tendrá modelos y formularios. Usa Python "
            "3.14 con Django 5.2 LTS desde la versión 5.2.8. El último ejercicio usa 6.0 y 6.1.",
        ),
        install_code="""python -m venv .venv
# Activate .venv first.
python -m pip install "Django~=5.2.8"
python -m django startproject config .
python manage.py migrate
python manage.py runserver""",
        example_code="""# config/urls.py
from django.contrib import admin
from django.http import HttpRequest, JsonResponse
from django.urls import path


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
]""",
        steps=(
            (
                "Создайте пустую папку. Активируйте .venv: source .venv/bin/activate "
                "(POSIX) или .venv/Scripts/Activate.ps1 (PowerShell).",
                "Use an empty directory. Activate .venv with source .venv/bin/activate "
                "(POSIX) or .venv/Scripts/Activate.ps1 (PowerShell).",
                "Usa una carpeta vacía. Activa .venv con source .venv/bin/activate "
                "(POSIX) o .venv/Scripts/Activate.ps1 (PowerShell).",
            ),
            (
                "Замените config/urls.py после startproject и до запуска runserver. "
                "Откройте http://127.0.0.1:8000/health/ и проверьте JSON.",
                "Replace config/urls.py after startproject and before running the server. "
                "Open http://127.0.0.1:8000/health/ and check its JSON.",
                "Reemplaza config/urls.py después de startproject y antes de iniciar el servidor. "
                "Abre http://127.0.0.1:8000/health/ y comprueba el JSON.",
            ),
        ),
    ),
    LocalizedPage(
        level=LessonLevel.BEGINNER,
        title=(
            "Модели, миграции и админка",
            "Models, migrations and admin",
            "Modelos, migraciones y admin",
        ),
        explanation=(
            "Category и Product образуют связь «один ко многим». PROTECT не позволяет "
            "удалить категорию, пока она используется. makemigrations записывает "
            "изменения модели в файл, migrate применяет их к базе. Храните миграции в Git.",
            "Category and Product form a one-to-many relation. PROTECT blocks removal of "
            "a category still in use. makemigrations creates migration files and migrate "
            "applies them to the database. Commit migration files to version control.",
            "Category y Product forman una relación de uno a muchos. PROTECT bloquea el "
            "borrado de una categoría en uso. makemigrations crea archivos de migración "
            "y migrate los aplica a la base. Guarda esas migraciones en el control de versiones.",
        ),
        install_code="""python manage.py startapp catalog
# Add catalog to INSTALLED_APPS and save the example files.
python manage.py makemigrations catalog
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver""",
        example_code="""# catalog/models.py
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=120)
    available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, null=True, blank=True
    )


class StockReservation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()


# catalog/admin.py
from django.contrib import admin

from .models import Category, Product

admin.site.register(Category)
admin.site.register(Product)""",
        steps=(
            (
                'Добавьте "catalog" в INSTALLED_APPS и разделите пример на два файла.',
                'Add "catalog" to INSTALLED_APPS and split the example into two files.',
                'Añade "catalog" a INSTALLED_APPS y divide el ejemplo en dos archivos.',
            ),
            (
                "В /admin/ создайте категорию Stationery и товар Notebook с запасом 3.",
                "In /admin/, create a Stationery category and a Notebook product with stock 3.",
                "En /admin/, crea la categoría Stationery y el producto Notebook con stock 3.",
            ),
        ),
    ),
    LocalizedPage(
        level=LessonLevel.BEGINNER,
        title=("Формы, шаблоны и доступ", "Forms, templates and access", "Formularios y permisos"),
        explanation=(
            "ModelForm проверяет поля до сохранения. Явный список полей защищает служебные "
            "атрибуты, permission_required проверяет право, а CSRF-токен защищает POST "
            "от подделки. После успешной записи перенаправьте браузер.",
            "A ModelForm validates fields before saving. An explicit field list protects "
            "internal attributes, permission_required checks access, and a CSRF token "
            "protects POST requests. Redirect the browser after a successful save.",
            "ModelForm valida los campos antes de guardar. La lista explícita protege "
            "atributos internos, permission_required comprueba el acceso y el token CSRF "
            "protege las solicitudes POST. Tras guardar, redirige el navegador.",
        ),
        example_code="""# catalog/forms.py
from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "category", "available", "stock")


# catalog/views.py
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render

from .forms import ProductForm


@permission_required("catalog.add_product", raise_exception=True)
def add_product(request):
    form = ProductForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("health")
    return render(request, "catalog/product_form.html", {"form": form})


# config/urls.py (append after urlpatterns)
from catalog.views import add_product

urlpatterns += [path("products/new/", add_product, name="product-add")]

# catalog/templates/catalog/product_form.html
<form method="post">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Save</button>
</form>""",
        steps=(
            (
                "Разнесите четыре части по указанным файлам. Войдите через /admin/, "
                "затем откройте /products/new/. В другом браузере проверьте 403.",
                "Split the example into the four marked files. Sign in via /admin/, "
                "then open /products/new/. Check for HTTP 403 in a separate browser.",
                "Divide el ejemplo en los cuatro archivos. Inicia sesión en /admin/ "
                "y abre /products/new/. Comprueba el HTTP 403 en otro navegador.",
            ),
        ),
    ),
    LocalizedPage(
        level=LessonLevel.INTERMEDIATE,
        title=(
            "Запросы ORM и проблема N+1",
            "ORM queries and the N+1 problem",
            "ORM y el problema N+1",
        ),
        explanation=(
            "QuerySet ленивый. Без select_related обращение к category может вызвать ещё "
            "один запрос для каждого товара. select_related подходит для внешних ключей, "
            "prefetch_related — для связей со многими объектами. Измерьте число запросов.",
            "A QuerySet is lazy. Accessing category without select_related can add one query "
            "per product. Use select_related for foreign keys and prefetch_related for "
            "collections. Measure the number of queries before and after.",
            "QuerySet es perezoso. Acceder a category sin select_related puede añadir una "
            "consulta por producto. Usa select_related para claves foráneas y prefetch_related "
            "para colecciones. Mide el número de consultas antes y después.",
        ),
        install_code="python manage.py shell",
        example_code="""# Paste this block in the Django shell.
from django.db import connection
from django.test.utils import CaptureQueriesContext

from catalog.models import Product


def names(queryset):
    return [(product.name, product.category.name) for product in queryset]


products = Product.objects.filter(category__isnull=False).order_by("id")
with CaptureQueriesContext(connection) as plain:
    original = names(products.all())
with CaptureQueriesContext(connection) as joined:
    optimized = names(products.select_related("category"))

assert original == optimized
print(len(plain), len(joined))""",
        steps=(
            (
                "Создайте минимум два товара с категориями. Проверьте результат 3 1 "
                "для двух товаров. Для обратной связи попробуйте "
                'Category.objects.prefetch_related("product_set").',
                "Create at least two products with categories. Expect 3 1 for two products. "
                'For the reverse relation, try Category.objects.prefetch_related("product_set").',
                "Crea al menos dos productos con categorías. Con dos productos espera 3 1. "
                'Para la relación inversa prueba Category.objects.prefetch_related("product_set").',
            ),
        ),
    ),
    LocalizedPage(
        level=LessonLevel.INTERMEDIATE,
        title=(
            "Транзакции и конкурентные изменения",
            "Transactions and concurrent updates",
            "Transacciones y concurrencia",
        ),
        explanation=(
            "Обычное чтение остатка перед записью создаёт гонку. Условный UPDATE проверяет "
            "остаток и уменьшает его в одном запросе. atomic связывает изменение остатка "
            "и запись брони. При ошибке обе операции откатываются.",
            "Reading stock and then saving can race. A conditional UPDATE checks and "
            "decrements stock in one query. atomic groups the decrement and reservation "
            "insertion, so an error rolls back both.",
            "Leer el stock y luego guardarlo puede causar una carrera. Un UPDATE condicional "
            "comprueba y reduce el stock en una consulta. atomic agrupa la reducción y la "
            "inserción de la reserva para revertir ambas si hay un error.",
        ),
        example_code="""# catalog/services.py
from django.db import transaction
from django.db.models import F

from .models import Product, StockReservation


class NotEnoughStock(Exception):
    pass


@transaction.atomic
def reserve(product_id: int, quantity: int) -> StockReservation:
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    updated = Product.objects.filter(
        id=product_id, available=True, stock__gte=quantity
    ).update(stock=F("stock") - quantity)
    if updated != 1:
        raise NotEnoughStock("Product is unavailable or out of stock")
    return StockReservation.objects.create(product_id=product_id, quantity=quantity)""",
        steps=(
            (
                "В production используйте PostgreSQL для проверки параллельных транзакций. "
                "Для безопасного повтора HTTP-запроса добавьте уникальный ключ идемпотентности.",
                "Use PostgreSQL to test parallel transactions for production. "
                "Add a unique idempotency key before allowing HTTP requests to be retried.",
                "Usa PostgreSQL para probar transacciones en paralelo antes de producción. "
                "Añade una clave de idempotencia única antes de permitir reintentos HTTP.",
            ),
        ),
    ),
    LocalizedPage(
        level=LessonLevel.INTERMEDIATE,
        title=(
            "Тесты HTTP, прав и остатков",
            "Testing HTTP, permissions and stock",
            "Pruebas HTTP, permisos y stock",
        ),
        explanation=(
            "TestCase изолирует тесты в отдельной базе. Проверьте HTTP-ответ и отсутствие "
            "записи при нехватке остатка. Django Client по умолчанию пропускает CSRF. "
            "Для проверки защиты включите enforce_csrf_checks.",
            "TestCase isolates tests in a separate database. Verify the HTTP response "
            "and that insufficient stock never creates a reservation. Django Client skips "
            "CSRF by default. Enable enforce_csrf_checks to test that protection.",
            "TestCase aísla las pruebas en una base separada. Comprueba la respuesta HTTP "
            "y que el stock insuficiente no crea reservas. Django Client omite CSRF por "
            "defecto. Activa enforce_csrf_checks para probar esa protección.",
        ),
        install_code="""python manage.py test catalog
python manage.py makemigrations --check --dry-run""",
        example_code="""# catalog/tests.py
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Product, StockReservation
from .services import NotEnoughStock, reserve


class CatalogueTests(TestCase):
    def test_health(self):
        self.assertEqual(self.client.get(reverse("health")).json(), {"status": "ok"})

    def test_create_requires_permission_and_csrf(self):
        url = reverse("product-add")
        self.assertEqual(self.client.get(url).status_code, 403)
        admin = get_user_model().objects.create_superuser("test-admin")
        client = Client(enforce_csrf_checks=True)
        client.force_login(admin)
        self.assertEqual(client.get(url).status_code, 200)
        self.assertEqual(client.post(url, {"name": "Notebook"}).status_code, 403)

    def test_cannot_oversell(self):
        product = Product.objects.create(name="Notebook", stock=3)
        reserve(product.pk, 2)
        with self.assertRaises(NotEnoughStock):
            reserve(product.pk, 2)
        product.refresh_from_db()
        self.assertEqual(product.stock, 1)
        self.assertEqual(StockReservation.objects.count(), 1)""",
        steps=(
            (
                "Добавьте тест успешного POST с cookie CSRF и валидной формой. Для проверки "
                "реального конкурентного доступа используйте TransactionTestCase и PostgreSQL.",
                "Add a successful POST test with a CSRF cookie and valid form. Use "
                "TransactionTestCase and PostgreSQL for real concurrent access tests.",
                "Añade una prueba POST válida con cookie CSRF. Para acceso concurrente real usa "
                "TransactionTestCase y PostgreSQL.",
            ),
        ),
    ),
    LocalizedPage(
        level=LessonLevel.PROFESSIONAL,
        title=("ASGI и подготовка к production", "ASGI and deployment", "ASGI y despliegue"),
        explanation=(
            "ASGI позволяет использовать async-представления и await для ORM-операций. "
            "Транзакцию из предыдущего урока оставьте синхронной и вызывайте через "
            "sync_to_async, если входная точка асинхронная. Для production нужны "
            "ASGI-сервер, TLS, управляемые секреты и отдельное обслуживание статики.",
            "ASGI supports async views and awaitable ORM calls. Keep the transaction "
            "from the previous lesson synchronous and wrap it in sync_to_async from "
            "async code. Production needs an ASGI server, TLS, managed secrets and "
            "separate static-file serving.",
            "ASGI admite vistas asíncronas y operaciones ORM con await. Mantén síncrona "
            "la transacción anterior y llámala con sync_to_async desde código asíncrono. "
            "Producción necesita servidor ASGI, TLS, secretos gestionados y servicio de estáticos.",
        ),
        install_code="""python -m pip install uvicorn
python manage.py check --deploy --settings=config.production
python manage.py collectstatic --no-input --settings=config.production
python -m uvicorn config.asgi:application --host 127.0.0.1 --port 8000""",
        example_code="""# config/production.py
import os

from .settings import *  # Load the generated project's base settings.

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = [os.environ["DJANGO_HOST"]]
STATIC_ROOT = BASE_DIR / "staticfiles"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# catalog/views.py (add a separate read-only view)
from django.http import JsonResponse

from .models import Product


async def availability(request):
    in_stock = await Product.objects.filter(available=True, stock__gt=0).aexists()
    return JsonResponse({"products_in_stock": in_stock})

# config/urls.py (append after urlpatterns)
from catalog.views import availability

urlpatterns += [path("availability/", availability, name="availability")]""",
        steps=(
            (
                "Экспортируйте DJANGO_SETTINGS_MODULE=config.production, DJANGO_HOST "
                "и секрет DJANGO_SECRET_KEY через платформу развёртывания.",
                "Set DJANGO_SETTINGS_MODULE=config.production and DJANGO_HOST, and inject "
                "DJANGO_SECRET_KEY through the deployment platform.",
                "Configura DJANGO_SETTINGS_MODULE=config.production y DJANGO_HOST. Inyecta "
                "DJANGO_SECRET_KEY desde la plataforma de despliegue.",
            ),
            (
                "Настройте HTTPS на прокси, доверие к его заголовкам и PostgreSQL. "
                "Выполните миграции до запуска и разберите предупреждения check --deploy.",
                "Configure HTTPS at the proxy, trusted proxy headers and PostgreSQL. "
                "Run migrations before starting and resolve the check --deploy warnings.",
                "Configura HTTPS en el proxy, las cabeceras de confianza y PostgreSQL. "
                "Ejecuta las migraciones antes de iniciar y revisa los avisos de check --deploy.",
            ),
        ),
    ),
    LocalizedPage(
        level=LessonLevel.PROFESSIONAL,
        title=(
            "Карта версий и подготовка обновления",
            "Version map and upgrade practice",
            "Mapa de versiones y actualización",
        ),
        explanation=(
            "<b>Состояние на ноябрь 2026.</b>\n"
            "4.1: async-методы QuerySet и async-обработчики классов.\n"
            "4.2 LTS: STORAGES и psycopg 3.\n"
            "5.0: db_default и GeneratedField.\n"
            "5.1: пулы PostgreSQL и LoginRequiredMiddleware.\n"
            "5.2 LTS: составные первичные ключи и автоимпорт моделей в shell.\n"
            "6.0: CSP, частичные шаблоны и API задач.\n"
            "6.1: режимы загрузки полей ORM, DB_CASCADE и MAILERS.\n\n"
            "4.1, 4.2, 5.0 и 5.1 вышли из поддержки. Разбирайте их при чтении старого кода. "
            "Выбирайте свежий патч 5.2 LTS или 6.1. В 6.x нужен Python ≥ 3.12.",
            "<b>Status as of November 2026.</b>\n"
            "4.1: async QuerySet methods and async class-based view handlers.\n"
            "4.2 LTS: STORAGES and psycopg 3.\n"
            "5.0: db_default and GeneratedField.\n"
            "5.1: PostgreSQL connection pooling and LoginRequiredMiddleware.\n"
            "5.2 LTS: composite primary keys and automatic shell imports.\n"
            "6.0: CSP, template partials and the Tasks API.\n"
            "6.1: ORM field fetch modes, DB_CASCADE and MAILERS.\n\n"
            "4.1, 4.2, 5.0 and 5.1 are end of life. Use their documentation to read "
            "legacy projects. Install the latest 5.2 LTS or 6.1 patch. 6.x requires Python ≥ 3.12.",
            "<b>Estado en noviembre de 2026.</b>\n"
            "4.1: métodos async de QuerySet y vistas de clase asíncronas.\n"
            "4.2 LTS: STORAGES y psycopg 3.\n"
            "5.0: db_default y GeneratedField.\n"
            "5.1: pool de conexiones PostgreSQL y LoginRequiredMiddleware.\n"
            "5.2 LTS: claves primarias compuestas e importaciones automáticas en shell.\n"
            "6.0: CSP, parciales de plantilla y API de tareas.\n"
            "6.1: modos de carga en el ORM, DB_CASCADE y MAILERS.\n\n"
            "4.1, 4.2, 5.0 y 5.1 ya no tienen soporte. Consulta sus notas para proyectos "
            "heredados. Instala el último parche de 5.2 LTS o 6.1. "
            "La rama 6.x requiere Python ≥ 3.12.",
        ),
        install_code="""python -Wa manage.py test
python manage.py showmigrations
python manage.py migrate --plan
python manage.py check""",
        steps=(
            (
                "Сделайте резервную копию и проверьте её восстановление. Изучите "
                "несовместимые изменения каждой промежуточной версии и поддержку зависимостей.",
                "Back up the database and verify recovery. Read the incompatible changes "
                "for each intervening release and check dependency support.",
                "Haz una copia de la base y prueba su restauración. Revisa los cambios "
                "incompatibles de cada versión intermedia y el soporte de las dependencias.",
            ),
            (
                "Обновляйте копию приложения по одному релизу, исправляя предупреждения "
                "устаревания. Проверяйте миграции и полный набор тестов до production.",
                "Upgrade an isolated copy one feature release at a time and resolve "
                "deprecation warnings. Test migrations and the full suite before production.",
                "Actualiza una copia aislada versión por versión y resuelve los avisos "
                "de obsolescencia. Prueba migraciones y la suite antes de producción.",
            ),
            (
                "Официальные заметки: https://docs.djangoproject.com/en/6.1/releases/",
                "Official release notes: https://docs.djangoproject.com/en/6.1/releases/",
                "Notas oficiales: https://docs.djangoproject.com/en/6.1/releases/",
            ),
        ),
    ),
    LocalizedPage(
        level=LessonLevel.PROFESSIONAL,
        title=(
            "Практикум 6.0–6.1: задачи и ORM",
            "Django 6.0–6.1 lab: tasks and ORM",
            "Laboratorio 6.0–6.1: tareas y ORM",
        ),
        explanation=(
            "Django 6.0 добавил @task. ImmediateBackend выполняет задачу синхронно для "
            "разработки. В production нужен backend с очередью и независимым воркером. "
            "В 6.1 FETCH_PEERS загружает связи пачкой при первом обращении, а FETCH_RAISE "
            "отклоняет неожиданные ленивые запросы.",
            "Django 6.0 added @task. ImmediateBackend executes tasks synchronously for "
            "development. Production needs a queue backend and a separate worker. "
            "In 6.1 FETCH_PEERS batches related fields on access, while FETCH_RAISE "
            "blocks unexpected missing-field fetches.",
            "Django 6.0 añadió @task. ImmediateBackend ejecuta tareas de forma síncrona "
            "para desarrollo. Producción necesita un backend de cola y un proceso separado. "
            "En 6.1 FETCH_PEERS agrupa relaciones al acceder y FETCH_RAISE bloquea "
            "cargas inesperadas de campos.",
        ),
        install_code="""# Use a separate project copy and virtual environment.
python -m pip install "Django~=6.1.0"
python manage.py test catalog
python manage.py migrate
python manage.py shell""",
        example_code="""# catalog/tasks.py (Django >= 6.0)
from django.tasks import task

from .models import Product


@task
def count_available_products() -> int:
    return Product.objects.filter(available=True).count()


# Django shell
from django.db import models

from catalog.models import Product
from catalog.tasks import count_available_products

result = count_available_products.enqueue()
print(result.status)  # SUCCESSFUL with the default ImmediateBackend

# Django 6.1+
products = Product.objects.filter(category__isnull=False).fetch_mode(models.FETCH_PEERS)
assert all(product.category.name for product in products)""",
        steps=(
            (
                "Сравните FETCH_PEERS с select_related через CaptureQueriesContext. "
                "Наблюдайте запрос при первом доступе к category.",
                "Compare FETCH_PEERS with select_related using CaptureQueriesContext. "
                "Observe the query on the first access to category.",
                "Compara FETCH_PEERS con select_related usando CaptureQueriesContext. "
                "Observa la consulta en el primer acceso a category.",
            ),
            (
                "Проверьте рабочие примеры на свежем патче 6.1. Он пришёл после релиза "
                "6.1 от 5 августа 2026. Задачи 6.0 и режимы 6.1 — разные возможности.",
                "Try the examples on the latest 6.1 patch. The 6.1 series launched "
                "on August 5, 2026. Tasks arrived in 6.0 and fetch modes in 6.1.",
                "Prueba los ejemplos con el último parche de 6.1. La serie 6.1 se publicó "
                "el 5 de agosto de 2026. Las tareas llegaron en 6.0 y los modos de carga en 6.1.",
            ),
        ),
    ),
)

DJANGO_LESSONS: Final[dict[str, Lesson]] = localize_lesson(
    ("🎸 Django", "🎸 Django", "🎸 Django"),
    *_PAGES,
)
