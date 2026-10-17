from enum import Enum


class report_type_enum(str, Enum):
    """Допустимые форматы формирования отчёта."""

    CSV = "CSV"
    MARKDOWN = "Markdown"
    XML = "XML"
    TXT = "TXT"
    HTML = "HTML"
