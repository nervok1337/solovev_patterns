import connexion
from flask import Response, request

from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager

api = connexion.FlaskApp(__name__)


def create_report_response(result, report_type):
    """Создаёт HTTP-ответ с учётом текстового или бинарного формата."""
    downloadable_formats = {
        report_type_enum.CSV: ("text/csv; charset=utf-8", "report.csv"),
        report_type_enum.MARKDOWN: ("text/markdown; charset=utf-8", "report.md"),
    }
    if report_type in downloadable_formats:
        content_type, file_name = downloadable_formats[report_type]
        return Response(
            bytes(result.binary),
            content_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"',
            },
        )

    content_types = {
        report_type_enum.XML: "application/xml; charset=utf-8",
        report_type_enum.TXT: "text/plain; charset=utf-8",
        report_type_enum.HTML: "text/html; charset=utf-8",
    }
    return Response(result.text, content_type=content_types[report_type])


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

    type_aliases = {
        "nomenclature": "nomenclatures",
        "nomenclatures": "nomenclatures",
        "номенклатура": "nomenclatures",
        "range": "ranges",
        "ranges": "ranges",
        "unit": "ranges",
        "unit_of_measurement": "ranges",
        "единица измерения": "ranges",
        "recipe": "recipes",
        "recipes": "recipes",
        "рецепт": "recipes",
    }
    collection_name = type_aliases.get(requested_type)
    if collection_name is None:
        return {"error": f"Неподдерживаемый тип: {requested_type}"}, 400

    entity = next(
        (
            item
            for item in getattr(storage, collection_name)
            if item.unique_code == requested_code
        ),
        None,
    )
    if entity is None:
        return {"error": f"Сущность с кодом {requested_code} не найдена"}, 404

    report = factory.create(report_type)
    result = report.build(entity)
    return create_report_response(result, report_type)

# Инициализация приложения
settings = settings_manager()
settings.load("settings.json")

storage = storage_manager()
storage.convert(settings.settings)

factory = report_factory(settings.settings)

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8000)
