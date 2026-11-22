"""Localized Django, FastAPI, DRF and Pydantic v2 lessons."""

from typing import Final

from bot.lesson_models import Lesson, LessonTopic
from bot.lesson_models import LocalizedPage as _Page
from bot.lesson_models import localize_lesson as _localize

ADVANCED_LESSONS: Final[dict[LessonTopic, dict[str, Lesson]]] = {
    LessonTopic.FASTAPI: _localize(
        ("⚡ FastAPI", "⚡ FastAPI", "⚡ FastAPI"),
        _Page(
            title=(
                "Маршруты и валидация параметров",
                "Routes and parameter validation",
                "Rutas y validación de parámetros",
            ),
            explanation=(
                "Аннотации FastAPI задают типы и ограничения пути и query-параметров. "
                "Запрос без подходящих значений получает HTTP 422. OpenAPI описывает "
                "формат запроса и ответа.",
                "FastAPI uses type annotations to validate path and query parameters. "
                "Invalid values return HTTP 422. OpenAPI describes the request and response.",
                "FastAPI usa las anotaciones para validar parámetros de ruta y consulta. "
                "Los valores inválidos devuelven HTTP 422. OpenAPI describe ambos formatos.",
            ),
            install_code="""python -m pip install "fastapi[standard]>=0.165,<1"
fastapi dev api.py""",
            example_code="""# api.py
from typing import Annotated

from fastapi import FastAPI, Path, Query

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(gt=0)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict[str, int]:
    return {"item_id": item_id, "limit": limit}""",
            steps=(
                (
                    "Откройте /docs и сравните ответы /items/1?limit=5 и /items/0.",
                    "Open /docs and compare /items/1?limit=5 with /items/0.",
                    "Abre /docs y compara /items/1?limit=5 con /items/0.",
                ),
            ),
        ),
        _Page(
            title=(
                "Тело запроса, ответ и тест",
                "Request bodies, responses and tests",
                "Cuerpo de solicitud, respuestas y pruebas",
            ),
            explanation=(
                "Модель входных данных проверяет JSON. response_model документирует "
                "и ограничивает поля ответа. TestClient проверяет ASGI-приложение напрямую.",
                "An input model validates JSON. response_model documents and limits "
                "response fields. TestClient calls the ASGI app directly.",
                "Un modelo de entrada valida JSON. response_model documenta y limita "
                "los campos de salida. TestClient llama directamente a la aplicación ASGI.",
            ),
            install_code="""python -m pip install pytest httpx2
python -m pytest -q test_api.py""",
            example_code="""# api.py
from typing import Annotated

from fastapi import FastAPI, status
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI()


class ItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(min_length=1, max_length=120)]


class ItemOut(ItemIn):
    id: int


@app.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemIn) -> ItemOut:
    return ItemOut(id=1, name=item.name)


# test_api.py
from fastapi.testclient import TestClient

from api import app


def test_create_item() -> None:
    with TestClient(app) as client:
        response = client.post("/items", json={"name": "Notebook"})
        assert response.status_code == 201
        assert response.json() == {"id": 1, "name": "Notebook"}
        assert client.post("/items", json={"name": ""}).status_code == 422""",
        ),
    ),
    LessonTopic.DRF: _localize(
        ("🌐 Django REST Framework", "🌐 Django REST Framework", "🌐 Django REST Framework"),
        _Page(
            title=(
                "Сериализатор и APIView",
                "Serializers and APIView",
                "Serializadores y APIView",
            ),
            explanation=(
                "Сериализатор DRF проверяет request.data. is_valid(raise_exception=True) "
                "даёт ответ HTTP 400 при ошибке. validated_data содержит проверенные поля. "
                "Используйте отдельный проект Django или проект из предыдущего урока.",
                "A DRF serializer validates request.data. is_valid(raise_exception=True) "
                "returns HTTP 400 on invalid input. validated_data contains the parsed fields. "
                "Use a new Django project or continue from the Django lesson.",
                "Un serializador de DRF valida request.data. is_valid(raise_exception=True) "
                "devuelve HTTP 400 con datos inválidos. validated_data contiene los campos "
                "validados. Usa un proyecto nuevo o el del tema de Django.",
            ),
            install_code="""python -m pip install "djangorestframework>=3.18.3,<4"
python manage.py runserver""",
            example_code="""# config/urls.py
from django.urls import path
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class ItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    quantity = serializers.IntegerField(min_value=1)


class ItemPreview(APIView):
    def post(self, request: Request) -> Response:
        serializer = ItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


urlpatterns = [path("api/preview/", ItemPreview.as_view())]""",
            steps=(
                (
                    'Добавьте "rest_framework" в INSTALLED_APPS в config/settings.py.',
                    'Add "rest_framework" to INSTALLED_APPS in config/settings.py.',
                    'Añade "rest_framework" a INSTALLED_APPS en config/settings.py.',
                ),
                (
                    'Отправьте JSON {"name": "Notebook", "quantity": 2} на /api/preview/.',
                    'POST JSON {"name": "Notebook", "quantity": 2} to /api/preview/.',
                    'Envía por POST {"name": "Notebook", "quantity": 2} a /api/preview/.',
                ),
            ),
        ),
        _Page(
            title=(
                "ViewSet, роутер и права доступа",
                "ViewSets, routers and permissions",
                "ViewSets, routers y permisos",
            ),
            explanation=(
                "ModelSerializer явным списком задаёт доступные поля. "
                "ReadOnlyModelViewSet предоставляет чтение, DefaultRouter создаёт URL. "
                "IsAdminUser проверяет флаг is_staff.",
                "ModelSerializer exposes an explicit list of fields. A ReadOnlyModelViewSet "
                "serves reads and DefaultRouter creates URLs. IsAdminUser requires is_staff.",
                "ModelSerializer expone una lista explícita de campos. ReadOnlyModelViewSet "
                "permite lecturas, DefaultRouter crea rutas e IsAdminUser exige is_staff.",
            ),
            example_code="""# config/urls.py — uses Product from the Django models lesson
from django.urls import include, path
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.routers import DefaultRouter

from catalog.models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "available")


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]


router = DefaultRouter()
router.register("products", ProductViewSet)
urlpatterns = [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]""",
            steps=(
                (
                    "Примените миграции и создайте сотрудника через createsuperuser.",
                    "Apply migrations and create a staff user with createsuperuser.",
                    "Aplica las migraciones y crea un usuario con createsuperuser.",
                ),
                (
                    "Откройте /api/products/ и сравните запросы до входа и после него.",
                    "Open /api/products/ and compare unauthenticated and staff requests.",
                    "Abre /api/products/ y compara el acceso anónimo y el del personal.",
                ),
            ),
        ),
    ),
    LessonTopic.PYDANTIC: _localize(
        ("🔎 Pydantic v2", "🔎 Pydantic v2", "🔎 Pydantic v2"),
        _Page(
            title=(
                "Строгие поля и валидатор",
                "Strict fields and a validator",
                "Campos estrictos y un validador",
            ),
            explanation=(
                "Annotated описывает ограничения полей. ConfigDict(strict=True) "
                "запрещает обычное приведение строки к числу. field_validator проверяет "
                "правила конкретного поля после базовой валидации.",
                "Annotated adds field constraints. ConfigDict(strict=True) rejects ordinary "
                "string-to-number coercion. field_validator adds a rule after type validation.",
                "Annotated añade restricciones. ConfigDict(strict=True) evita convertir "
                "cadenas en números. field_validator añade una regla después de validar tipos.",
            ),
            install_code='python -m pip install "pydantic>=2.11,<3"',
            example_code="""from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class OrderLine(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    sku: Annotated[str, Field(min_length=3, max_length=30)]
    quantity: Annotated[int, Field(ge=1, le=100)]

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, value: str) -> str:
        if not value.isascii() or not value.isalnum():
            raise ValueError("SKU must contain only ASCII letters and digits")
        return value


print(OrderLine(sku="ABC123", quantity=2).model_dump())
try:
    OrderLine.model_validate({"sku": "ABC123", "quantity": "2"})
except ValidationError as exc:
    print(exc.errors(include_input=False))""",
        ),
        _Page(
            title=(
                "Связанные поля и JSON",
                "Cross-field validation and JSON",
                "Validación cruzada y JSON",
            ),
            explanation=(
                "model_validator(mode='after') проверяет связь между полями "
                "после их валидации. model_validate_json загружает JSON, "
                "model_dump_json сохраняет результат. AwareDatetime требует часовой пояс.",
                "model_validator(mode='after') checks relationships across validated "
                "fields. model_validate_json reads JSON and model_dump_json writes it. "
                "AwareDatetime requires timezone information.",
                "model_validator(mode='after') comprueba la relación entre campos ya "
                "validados. model_validate_json lee JSON y model_dump_json lo genera. "
                "AwareDatetime exige información de zona horaria.",
            ),
            example_code="""from typing import Self

from pydantic import AwareDatetime, BaseModel, model_validator


class Window(BaseModel):
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


window = Window.model_validate_json(
    '{"starts_at":"2026-01-01T10:00:00Z","ends_at":"2026-01-01T12:00:00Z"}'
)
print(window.model_dump_json())""",
        ),
    ),
}
