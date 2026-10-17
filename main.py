import connexion
from flask import Response

from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager

api = connexion.FlaskApp(__name__)

@api.route("/api/get_report", methods=["GET"])
def get_report():
    if not storage.recipes:
        return {"error": "Рецепты отсутствуют"}, 404

    reports = []
    for recipe in storage.recipes:
        report = factory.create(report_type_enum.TXT)
        result = report.build(recipe)
        reports.append(f"Рецепт: {recipe.name}\n{result.text}")

    return Response(
        "\n\n".join(reports),
        content_type="text/plain; charset=utf-8",
    )

# Инициализация приложения
settings = settings_manager()
settings.load("settings.json")

storage = storage_manager()
storage.convert(settings.settings)

factory = report_factory()

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8000)
