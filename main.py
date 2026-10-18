import connexion
from flask import request

from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager

api = connexion.FlaskApp(__name__)


@api.route("/api/get_report", methods=["GET"])
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

    entity, error, status = storage.find_entity(requested_type, requested_code)
    if error is not None:
        return {"error": error}, status

    report = factory.create(report_type)
    result = report.build(entity)
    return report.create_response(result)


@api.route("/api/get_default_report", methods=["GET"])
def get_default_report():
    """Формирует отчёт сущности в формате из настроек приложения."""
    requested_type = request.args.get("type", "").strip().lower()
    requested_code = request.args.get("code", "").strip()
    if not requested_type or not requested_code:
        return {"error": "Необходимо указать type и code"}, 400

    entity, error, status = storage.find_entity(requested_type, requested_code)
    if error is not None:
        return {"error": error}, status

    report = factory.create_default()
    result = report.build(entity)
    return report.create_response(result)


# Инициализация приложения
settings = settings_manager()
settings.load("settings.json")

storage = storage_manager()
storage.convert(settings.settings)

factory = report_factory(settings.settings)

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8000)
