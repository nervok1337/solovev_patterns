import connexion
from connexion.options import SwaggerUIOptions
from flask import jsonify, make_response, request, send_from_directory

from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager
from Src.Logics.convert_factory import convert_factory
from Src.Logics.deserialize_factory import deserialize_factory
from Src.Logics.entity_mapper import entity_mapper
from Src.Logics.storage_adapter import storage_adapter
from Src.Logics.crud_service import crud_service
from Src.Core.validator import argument_exception, operation_exception

api = connexion.FlaskApp(__name__)


@api.route("/api-spec.yaml", methods=["GET"])
def get_openapi_spec():
    """Отдаёт Swagger исходную спецификацию с сохранением адресов серверов."""
    return send_from_directory(api.app.root_path, "openapi.yaml", mimetype="application/yaml")


def get_entities():
    """Возвращает типы сущностей, доступные для получения отчётов."""
    return jsonify(crud.types()), 200


def get_report():
    """Формирует отчёт сущности в явно указанном формате."""
    requested_format = request.args.get("format", "").strip().upper()
    requested_type = request.args.get("type", "").strip().lower()
    requested_code = request.args.get("code", "").strip()
    if not requested_format or not requested_type or not requested_code:
        return {"error": "Необходимо указать format, type и code"}, 400

    try:
        report_type = report_type_enum[requested_format]
    except KeyError:
        return {"error": f"Неподдерживаемый формат: {requested_format}"}, 400

    entity, error, status = crud.find_entity(requested_type, requested_code)
    if error is not None:
        return {"error": error}, status

    report = factory.create(report_type)
    result = report.build(entity)
    return report.create_response(result)


def get_default_report(type: str = "", code: str = ""):
    """Формирует отчёт сущности в формате из настроек приложения."""
    requested_type = (type or request.args.get("type", "")).strip().lower()
    requested_code = (code or request.args.get("code", "")).strip()
    if not requested_type or not requested_code:
        return make_response(jsonify({"error": "Необходимо указать type и code"}), 400)

    entity, error, status = crud.find_entity(requested_type, requested_code)
    if error is not None:
        return make_response(jsonify({"error": error}), status)

    report = factory.create_default()
    result = report.build(entity)
    return report.create_response(result)


def get_report_formats():
    """Возвращает допустимые форматы отчётов в JSON."""
    return jsonify([item.value for item in report_type_enum]), 200


def list_entities(entity_type):
    """Передаёт получение коллекции CRUD-сервису."""
    return jsonify([mapper.encode(item) for item in crud.list(entity_type)]), 200


def get_entity(entity_type, code):
    """Получает сущность по индексу и преобразует её в ответ API."""
    return jsonify(mapper.encode(crud.get(entity_type, code))), 200


def create_entity(entity_type, body):
    """Создаёт доменную сущность через отдельную прослойку."""
    return jsonify(mapper.encode(crud.create(entity_type, body))), 201


def replace_entity(entity_type, code, body):
    """Заменяет данные сущности после проверки модели и связей."""
    return jsonify(mapper.encode(crud.update(entity_type, code, body))), 200


def delete_entity(entity_type, code):
    """Удаляет свободную сущность через CRUD-сервис."""
    crud.delete(entity_type, code)
    return "", 204


def invalid_data(error):
    """Преобразует ошибку входных данных в HTTP 400."""
    return jsonify(error=str(error)), 400


def missing_entity(error):
    """Преобразует отсутствие сущности в HTTP 404."""
    return jsonify(error=str(error)), 404


def conflicting_entity(error):
    """Преобразует нарушение уникальности или связей в HTTP 409."""
    return jsonify(error=str(error)), 409


# Сборка приложения: прежнее хранилище остаётся источником начальных данных.
settings = settings_manager()
settings.load("settings.json")

storage = storage_manager()
storage.convert(settings.settings)

factory = report_factory(settings.settings)
mapper = entity_mapper(deserialize_factory(), convert_factory())
crud = crud_service(storage_adapter(storage, mapper, settings.settings))

for error_type in (ValueError, argument_exception):
    api.app.register_error_handler(error_type, invalid_data)
api.app.register_error_handler(KeyError, missing_entity)
api.app.register_error_handler(operation_exception, conflicting_entity)

api.add_api(
    "openapi.yaml",
    strict_validation=True,
    validate_responses=True,
    swagger_ui_options=SwaggerUIOptions(
        swagger_ui_template_arguments={"openapi_spec_url": "/api-spec.yaml"},
    ),
)

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8000)
