"""Practical localized FastAPI and Django REST Framework lessons."""

# Russian lesson prose intentionally contains Cyrillic letters.
# ruff: noqa: RUF001

from typing import Final

from bot.lesson_models import LessonLevel, LessonPage, LessonTopic, LocalizedPage, localize_pages

_FASTAPI = (
    LocalizedPage(
        title=(
            "Роутеры и зависимости",
            "Routers and dependencies",
            "Routers y dependencias",
        ),
        level=LessonLevel.INTERMEDIATE,
        explanation=(
            "APIRouter группирует маршруты и добавляет общий префикс и теги OpenAPI. "
            "Depends вызывает существующую зависимость, а Annotated связывает её с типом "
            "аргумента. Здесь одна зависимость проверяет параметры пагинации.",
            "APIRouter groups routes under a shared prefix and OpenAPI tags. Depends "
            "calls a reusable dependency, and Annotated pairs it with an argument type. "
            "Here one dependency validates the pagination parameters.",
            "APIRouter agrupa rutas con un prefijo y etiquetas de OpenAPI. Depends "
            "invoca una dependencia reutilizable y Annotated la asocia con un tipo. "
            "Aquí una dependencia valida los parámetros de paginación.",
        ),
        example_code="""# api.py
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Query


@dataclass(frozen=True)
class Window:
    offset: Annotated[int, Query(ge=0)] = 0
    limit: Annotated[int, Query(ge=1, le=100)] = 20


WindowDep = Annotated[Window, Depends(Window)]
router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/products")
def list_products(window: WindowDep) -> list[str]:
    products = ["Notebook", "Pen", "Pencil"]
    return products[window.offset : window.offset + window.limit]


app = FastAPI()
app.include_router(router)""",
        steps=(
            (
                "Запустите fastapi dev api.py и сравните limit=1 и limit=0 в /docs.",
                "Run fastapi dev api.py and compare limit=1 and limit=0 in /docs.",
                "Ejecuta fastapi dev api.py y compara limit=1 y limit=0 en /docs.",
            ),
        ),
    ),
    LocalizedPage(
        title=(
            "Lifespan и асинхронный HTTP",
            "Lifespan and asynchronous HTTP",
            "Lifespan y HTTP asíncrono",
        ),
        level=LessonLevel.INTERMEDIATE,
        explanation=(
            "Lifespan открывает один HTTP-клиент с пулом соединений на процесс и закрывает "
            "его при остановке. await освобождает цикл событий на время ожидания сети. "
            "Тайм-аут даёт 504, а невалидный ответ сервиса или другая сетевая ошибка — 502.",
            "Lifespan opens one HTTP client with a connection pool per process and closes "
            "it on shutdown. await yields the event loop while waiting for the network. "
            "A timeout gives 504. Invalid upstream data or another network error gives 502.",
            "Lifespan abre un cliente HTTP con un pool de conexiones por proceso y lo cierra "
            "al apagar. await cede el bucle de eventos durante la espera de red. Un timeout "
            "produce 504. Los datos inválidos del servicio u otro error de red producen 502.",
        ),
        install_code="""# Terminal 1
uvicorn upstream:app --port 9001
# Terminal 2
fastapi dev api.py""",
        example_code="""# api.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError


class Quote(BaseModel):
    price_cents: Annotated[int, Field(strict=True, ge=0)]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:9001", timeout=2.0,
    ) as client:
        app.state.upstream = client
        yield


async def upstream_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.upstream


app = FastAPI(lifespan=lifespan)


@app.get("/quote")
async def get_quote(
    client: Annotated[httpx.AsyncClient, Depends(upstream_client)],
) -> Quote:
    try:
        response = await client.get("/quote")
        response.raise_for_status()
        return Quote.model_validate_json(response.content)
    except httpx.TimeoutException:
        raise HTTPException(504, "Upstream timeout") from None
    except (httpx.HTTPError, ValidationError):
        raise HTTPException(502, "Invalid upstream response") from None


# upstream.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/quote")
def quote() -> dict[str, int]:
    return {"price_cents": 1299}""",
        steps=(
            (
                "Разделите код на api.py и upstream.py. Проверьте /quote на порту 8000.",
                "Split the code into api.py and upstream.py. Check /quote on port 8000.",
                "Divide el código en api.py y upstream.py. Prueba /quote en el puerto 8000.",
            ),
            (
                "Остановите upstream и проверьте обработку ошибки.",
                "Stop the upstream app and check the error response.",
                "Detén el servicio upstream y comprueba la respuesta de error.",
            ),
        ),
    ),
    LocalizedPage(
        title=(
            "Аутентификация сервиса",
            "Service authentication",
            "Autenticación de servicios",
        ),
        level=LessonLevel.PROFESSIONAL,
        explanation=(
            "HTTPBearer извлекает токен запроса и объявляет схему в OpenAPI. "
            "В учебном сервисе токен сверяется с секретом из среды через compare_digest. "
            "В развёрнутом сервисе передавайте его по HTTPS, храните и ротируйте в менеджере "
            "секретов. Для доступа от имени пользователя проверяйте его идентичность и права.",
            "HTTPBearer extracts a request token and declares its scheme in OpenAPI. "
            "For this exercise, compare_digest matches it against an environment secret. "
            "In deployment, transmit it over HTTPS and store and rotate it in a secret manager. "
            "For user access, verify the user's identity and permissions.",
            "HTTPBearer extrae el token y declara el esquema en OpenAPI. En el ejercicio, "
            "compare_digest lo compara con un secreto del entorno. En producción, usa HTTPS, "
            "un gestor de secretos y rotación. Para el acceso de usuarios, verifica su "
            "identidad y sus permisos.",
        ),
        example_code="""# api.py
import os
from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

token = os.environ.get("CATALOG_TOKEN", "").encode()
if len(token) < 32:
    raise RuntimeError("Set CATALOG_TOKEN to a random secret")

bearer = HTTPBearer(auto_error=False)
app = FastAPI()


async def require_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> None:
    if credentials is None or not compare_digest(credentials.credentials.encode(), token):
        raise HTTPException(401, "Unauthorized", headers={"WWW-Authenticate": "Bearer"})


@app.get("/private", dependencies=[Depends(require_token)])
def private_data() -> dict[str, str]:
    return {"status": "authenticated"}""",
        steps=(
            (
                "Задайте CATALOG_TOKEN случайным секретом и запустите fastapi dev api.py.",
                "Set CATALOG_TOKEN to a random secret and run fastapi dev api.py.",
                "Define CATALOG_TOKEN con un secreto aleatorio y ejecuta fastapi dev api.py.",
            ),
            (
                "В /docs сравните запросы к /private без токена и после Authorize.",
                "In /docs, compare requests to /private before and after Authorize.",
                "En /docs, compara las solicitudes a /private antes y después de Authorize.",
            ),
        ),
    ),
    LocalizedPage(
        title=(
            "Уникальность и транзакция",
            "Uniqueness and transactions",
            "Unicidad y transacciones",
        ),
        level=LessonLevel.PROFESSIONAL,
        explanation=(
            "Уникальность SKU гарантирует ограничение SQLite. Конкурентные записи с одним "
            "SKU могут создать только одну строку. Для дублей маршрут возвращает 409. "
            "Параметры передаются "
            "отдельно от SQL. Синхронный маршрут def FastAPI выполняет в пуле потоков, "
            "а соединение открывается в том же потоке и закрывается по выходу.",
            "A SQLite constraint enforces SKU uniqueness. Concurrent writes for the same SKU "
            "can create just one record. The handler answers 409 for a duplicate. "
            "Parameters stay separate from SQL. "
            "FastAPI runs the synchronous def route in a thread pool. The connection opens "
            "in that thread and closes on exit.",
            "Una restricción de SQLite garantiza la unicidad del SKU. Las escrituras "
            "simultáneas solo pueden crear un registro. La ruta devuelve 409 si se repite. "
            "Los parámetros van separados "
            "del SQL. FastAPI ejecuta la ruta síncrona def en un pool de hilos y la conexión "
            "se abre en ese hilo y se cierra al salir.",
        ),
        install_code="""python -c "from api import init_db; init_db()"
fastapi dev api.py""",
        example_code="""# api.py
import sqlite3
from contextlib import closing
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()
DB = "catalog.db"


class ProductIn(BaseModel):
    sku: Annotated[str, Field(pattern=r"^[A-Z0-9-]{1,20}$")]


class ProductOut(ProductIn):
    id: int


def init_db() -> None:
    with closing(sqlite3.connect(DB)) as db, db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS product "
            "(id INTEGER PRIMARY KEY, sku TEXT NOT NULL UNIQUE)"
        )


@app.post("/products", status_code=201)
def create_product(product: ProductIn) -> ProductOut:
    with closing(sqlite3.connect(DB)) as db, db:
        row = db.execute(
            "INSERT INTO product (sku) VALUES (?) "
            "ON CONFLICT(sku) DO NOTHING RETURNING id",
            (product.sku,),
        ).fetchone()
        if row is None:
            raise HTTPException(409, "SKU already exists")
        return ProductOut(id=row[0], sku=product.sku)""",
        steps=(
            (
                'Отправьте {"sku":"NOTE-1"} дважды на POST /products.',
                'Send {"sku":"NOTE-1"} twice to POST /products.',
                'Envía {"sku":"NOTE-1"} dos veces a POST /products.',
            ),
            (
                "В растущем проекте изменяйте схему версионируемыми миграциями.",
                "As the project grows, change the schema with versioned migrations.",
                "A medida que crezca el proyecto, cambia el esquema con migraciones versionadas.",
            ),
        ),
    ),
    LocalizedPage(
        title=(
            "Тестирование с подменой зависимостей",
            "Testing with dependency overrides",
            "Pruebas con sustitución de dependencias",
        ),
        level=LessonLevel.PROFESSIONAL,
        explanation=(
            "TestClient запускает lifespan при входе в контекст. dependency_overrides "
            "заменяет зависимость в тесте, а MockTransport имитирует внешний HTTP-сервис. "
            "Проверяйте контракт ответа, ошибки и тайм-аут. После теста убирайте подмену.",
            "TestClient starts lifespan when used as a context manager. dependency_overrides "
            "replaces a dependency, and MockTransport simulates an external HTTP service. "
            "Assert the response contract, errors and timeouts. Remove the override afterward.",
            "TestClient inicia lifespan al entrar en el contexto. dependency_overrides "
            "sustituye una dependencia y MockTransport simula un servicio HTTP externo. "
            "Comprueba el contrato, errores y timeouts. Retira la sustitución al final.",
        ),
        install_code="""python -m pip install pytest httpx httpx2
python -m pytest -q test_quote.py""",
        example_code="""# test_quote.py — use api.py from the lifespan lesson
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi.testclient import TestClient

from api import app, upstream_client


@pytest.mark.parametrize(
    ("upstream_status", "body", "expected"),
    [
        (200, {"price_cents": 1299}, 200),
        (200, {"price_cents": "not a number"}, 502),
        (503, {}, 502),
        (None, {}, 504),
    ],
)
def test_quote(
    upstream_status: int | None, body: dict[str, object], expected: int,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if upstream_status is None:
            raise httpx.ReadTimeout("simulated timeout", request=request)
        return httpx.Response(upstream_status, json=body)

    async def fake_client() -> AsyncIterator[httpx.AsyncClient]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(respond), base_url="http://upstream.test",
        ) as client:
            yield client

    app.dependency_overrides[upstream_client] = fake_client
    try:
        with TestClient(app) as client:
            response = client.get("/quote")
            assert response.status_code == expected
            if expected == 200:
                assert response.json() == body
    finally:
        del app.dependency_overrides[upstream_client]""",
    ),
)

_DRF = (
    LocalizedPage(
        title=(
            "Запись и изоляция владельцев",
            "Writable resources and owner isolation",
            "Escritura y aislamiento por propietario",
        ),
        level=LessonLevel.INTERMEDIATE,
        explanation=(
            "ModelViewSet объединяет чтение и запись. get_queryset ограничивает список и "
            "доступ по ID своими записями. perform_create назначает владельца из "
            "аутентифицированного запроса. Входные данные не могут выбрать владельца: "
            "поле owner доступно только для чтения.",
            "ModelViewSet groups reads and writes. get_queryset scopes list and detail "
            "operations to records owned by the caller. perform_create assigns the "
            "authenticated user. The owner field is read-only in the serializer.",
            "ModelViewSet reúne lecturas y escrituras. get_queryset limita la lista y "
            "las operaciones por ID a registros del usuario. perform_create asigna al "
            "usuario autenticado. El campo owner es de solo lectura en el serializador.",
        ),
        install_code="""python manage.py makemigrations catalog
python manage.py migrate
python manage.py runserver""",
        example_code="""# catalog/models.py — add to the existing module
from django.conf import settings
from django.db import models


class Listing(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    stock = models.PositiveIntegerField(default=0)


# config/urls.py
from django.urls import include, path
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter

from catalog.models import Listing


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ("id", "name", "owner", "stock")
        read_only_fields = ("owner", "stock")


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Listing.objects.filter(owner_id=self.request.user.pk).order_by("id")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


router = DefaultRouter()
router.register("listings", ListingViewSet, basename="listing")
urlpatterns = [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]""",
        steps=(
            (
                "Добавьте Listing в catalog/models.py и примените миграции.",
                "Add Listing to catalog/models.py and apply the migrations.",
                "Añade Listing a catalog/models.py y aplica las migraciones.",
            ),
            (
                "Зайдите в /api/listings/ под разными пользователями и проверьте их списки.",
                "Log in to /api/listings/ as different users and compare their lists.",
                "Entra en /api/listings/ con distintos usuarios y compara las listas.",
            ),
        ),
    ),
    LocalizedPage(
        title=(
            "Пагинация и поиск",
            "Pagination and search",
            "Paginación y búsqueda",
        ),
        level=LessonLevel.INTERMEDIATE,
        explanation=(
            "PageNumberPagination возвращает count, next, previous и results. "
            "Ограничение размера страницы защищает сервер от больших ответов. "
            "Порядок name, id определён даже для одинаковых имён. При частых вставках "
            "рассмотрите CursorPagination с уникальным неизменяемым ключом.",
            "PageNumberPagination returns count, next, previous and results. "
            "A maximum page size limits response volume. Ordering by name and id "
            "breaks ties for equal names. For frequent inserts, consider CursorPagination "
            "with a unique immutable ordering key.",
            "PageNumberPagination devuelve count, next, previous y results. "
            "Un máximo de elementos limita la respuesta. El orden por name e id "
            "desempata nombres iguales. Si hay inserciones frecuentes, considera "
            "CursorPagination con una clave única e inmutable.",
        ),
        example_code="""# catalog/views.py — uses Product from the Django models lesson
from rest_framework import filters, pagination, serializers, viewsets
from rest_framework.permissions import IsAdminUser

from catalog.models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "available")


class ProductPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 50


class ProductSearchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(available=True).order_by("name", "id")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]
    pagination_class = ProductPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["^name"]  # case-insensitive prefix


# config/urls.py — before using router.urls
from catalog.views import ProductSearchViewSet

router.register("products", ProductSearchViewSet, basename="product")""",
        steps=(
            (
                "В существующем роутере зарегистрируйте путь products один раз.",
                "Register the products path once on the existing router.",
                "Registra la ruta products una sola vez en el router existente.",
            ),
            (
                "Проверьте /api/products/?search=Note&size=2 и перейдите по next.",
                "Check /api/products/?search=Note&size=2 and follow next.",
                "Prueba /api/products/?search=Note&size=2 y sigue el enlace next.",
            ),
        ),
    ),
    LocalizedPage(
        title=(
            "Сессии браузера и CSRF",
            "Browser sessions and CSRF",
            "Sesiones del navegador y CSRF",
        ),
        level=LessonLevel.PROFESSIONAL,
        explanation=(
            "SessionAuthentication использует сессию Django. IsAuthenticated запрещает "
            "анонимные запросы. Для POST, PUT, PATCH и DELETE с сессионной аутентификацией "
            "браузер должен передать CSRF-токен. При развёртывании используйте HTTPS и "
            "Secure cookies. Используйте защищённое представление входа Django.",
            "SessionAuthentication uses a Django session. IsAuthenticated rejects "
            "anonymous requests. Session-authenticated POST, PUT, PATCH and DELETE calls "
            "require a valid CSRF token. Deploy over HTTPS with secure cookies and use "
            "Django's protected login view.",
            "SessionAuthentication usa una sesión de Django. IsAuthenticated rechaza "
            "solicitudes anónimas. POST, PUT, PATCH y DELETE con sesión requieren un token "
            "CSRF válido. Despliega con HTTPS y cookies seguras, y usa la vista de inicio "
            "de sesión protegida de Django.",
        ),
        example_code="""# config/urls.py — add after defining urlpatterns
from django.urls import path
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class DisplayName(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)


class ProfileView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response({"first_name": request.user.first_name})

    def post(self, request: Request) -> Response:
        serializer = DisplayName(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.first_name = serializer.validated_data["first_name"]
        request.user.save(update_fields=["first_name"])
        return Response(serializer.validated_data)


urlpatterns += [path("api/profile/", ProfileView.as_view())]""",
        steps=(
            (
                "В примере используется стандартная модель User. Зайдите через /api-auth/login/.",
                "This uses Django's default User model. Log in at /api-auth/login/.",
                "El ejemplo usa el modelo User de Django. Entra en /api-auth/login/.",
            ),
            (
                "Проверьте POST в браузере DRF. Для fetch добавьте заголовок X-CSRFToken.",
                "Try POST in the browsable API. For fetch, add the X-CSRFToken header.",
                "Prueba POST en la interfaz de DRF. Con fetch, añade la cabecera X-CSRFToken.",
            ),
        ),
    ),
    LocalizedPage(
        title=(
            "Атомарные изменения запасов",
            "Atomic inventory writes",
            "Cambios atómicos de inventario",
        ),
        level=LessonLevel.PROFESSIONAL,
        explanation=(
            "UPDATE с условием stock__gte и выражением F поручает проверку и списание "
            "базе данных. transaction.atomic объединяет списание и запись о резерве. "
            "При сбое второй записи первая откатывается. Чужая запись возвращает 404, "
            "а недостаточный остаток — 409.",
            "A conditional UPDATE with stock__gte and an F expression checks and decrements "
            "stock in the database. transaction.atomic groups the decrement and the "
            "reservation record. Failure in the second write rolls back the first. "
            "A foreign record returns 404 and insufficient stock returns 409.",
            "Un UPDATE condicional con stock__gte y una expresión F comprueba y reduce "
            "el stock en la base de datos. transaction.atomic agrupa la reducción y el "
            "registro de la reserva. Si falla la segunda escritura, se revierte la "
            "primera. Un registro ajeno devuelve 404 y un stock insuficiente, 409.",
        ),
        install_code="""python manage.py makemigrations catalog
python manage.py migrate""",
        example_code="""# catalog/models.py — add below Listing
class Reservation(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


# config/urls.py — add after defining urlpatterns
from django.db import transaction
from django.db.models import F
from django.urls import path
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Listing, Reservation


class ReserveInput(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=1000)


class ReserveView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, pk: int) -> Response:
        serializer = ReserveInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]
        listing = Listing.objects.filter(pk=pk, owner_id=request.user.pk)
        updated = listing.filter(stock__gte=quantity).update(stock=F("stock") - quantity)
        if not updated:
            if not listing.exists():
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"detail": "Insufficient stock"}, status=status.HTTP_409_CONFLICT)
        reservation = Reservation.objects.create(listing_id=pk, quantity=quantity)
        return Response({"id": reservation.pk}, status=status.HTTP_201_CREATED)


urlpatterns += [path("api/listings/<int:pk>/reserve/", ReserveView.as_view())]""",
        steps=(
            (
                "Создайте свою запись через /api/listings/ и задайте ей stock=3 в Django shell.",
                "Create your listing at /api/listings/ and set its stock to 3 in Django shell.",
                "Crea tu anuncio en /api/listings/ y asigna stock=3 en la shell de Django.",
            ),
            (
                'Дважды отправьте {"quantity":2} на /api/listings/{id}/reserve/.',
                'POST {"quantity":2} twice to /api/listings/{id}/reserve/.',
                'Envía {"quantity":2} dos veces a /api/listings/{id}/reserve/.',
            ),
        ),
    ),
    LocalizedPage(
        title=(
            "Тестирование прав и границ API",
            "Testing permissions and API boundaries",
            "Pruebas de permisos y límites de la API",
        ),
        level=LessonLevel.PROFESSIONAL,
        explanation=(
            "APITestCase использует тестовую БД. force_authenticate подставляет "
            "пользователя в проверках авторизации. Отдельно проверяйте реальный вход и "
            "CSRF через APIClient(enforce_csrf_checks=True): force_authenticate пропускает "
            "механизм аутентификации.",
            "APITestCase uses a test database. force_authenticate supplies a user for "
            "authorization tests. Test actual login and CSRF separately with "
            "APIClient(enforce_csrf_checks=True). force_authenticate bypasses authentication.",
            "APITestCase usa una base de datos de prueba. force_authenticate proporciona "
            "un usuario para las pruebas de autorización. Prueba el inicio de sesión y CSRF "
            "con APIClient(enforce_csrf_checks=True) por separado: force_authenticate "
            "omite la autenticación.",
        ),
        install_code="""python manage.py test catalog""",
        example_code="""# catalog/tests.py — uses ListingViewSet and its router
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from catalog.models import Listing


class ListingTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        user = get_user_model()
        cls.alice = user.objects.create_user(username="alice")
        cls.bob = user.objects.create_user(username="bob")
        cls.foreign = Listing.objects.create(name="Private", owner=cls.bob)

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.alice)
        self.list_url = reverse("listing-list")

    def test_foreign_record_is_inaccessible(self) -> None:
        detail = reverse("listing-detail", args=[self.foreign.pk])
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.delete(detail).status_code, 404)
        self.assertEqual(self.client.get(self.list_url).json(), [])

    def test_create_uses_authenticated_owner(self) -> None:
        response = self.client.post(
            self.list_url, {"name": "Notebook", "owner": self.bob.pk, "stock": 99}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        listing = Listing.objects.get(pk=response.data["id"])
        self.assertEqual((listing.owner_id, listing.stock), (self.alice.pk, 0))

    def test_blank_name_is_rejected(self) -> None:
        response = self.client.post(self.list_url, {"name": ""}, format="json")
        self.assertEqual(response.status_code, 400)""",
    ),
)

API_LESSON_PAGES: Final[dict[LessonTopic, dict[str, tuple[LessonPage, ...]]]] = {
    LessonTopic.FASTAPI: localize_pages(*_FASTAPI),
    LessonTopic.DRF: localize_pages(*_DRF),
}
