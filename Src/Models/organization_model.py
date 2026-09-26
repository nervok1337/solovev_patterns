from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception


class organization_model(entity_model):
    """Организация с банковскими реквизитами и формой собственности."""

    __inn: str
    __bik: str
    __account: str
    __ownership_form: str

    def __init__(
        self,
        name: str,
        inn: str,
        bik: str,
        account: str,
        ownership_form: str,
    ) -> None:
        """Создаёт организацию с обязательными реквизитами."""
        super().__init__()
        self.name = name
        self.inn = inn
        self.bik = bik
        self.account = account
        self.ownership_form = ownership_form

    @staticmethod
    def __validate_text(field: str, value: str) -> str:
        """Проверяет, что текстовый реквизит заполнен."""
        if not isinstance(value, str) or value.strip() == "":
            raise arguments_exception(field, "Значение не может быть пустым!")

        return value.strip()

    @property
    def inn(self) -> str:
        """Возвращает ИНН организации."""
        return self.__inn

    @inn.setter
    def inn(self, value: str) -> None:
        """Устанавливает ИНН организации."""
        self.__inn = self.__validate_text("inn", value)

    @property
    def bik(self) -> str:
        """Возвращает БИК банка."""
        return self.__bik

    @bik.setter
    def bik(self, value: str) -> None:
        """Устанавливает БИК банка."""
        self.__bik = self.__validate_text("bik", value)

    @property
    def account(self) -> str:
        """Возвращает расчётный счёт организации."""
        return self.__account

    @account.setter
    def account(self, value: str) -> None:
        """Устанавливает расчётный счёт организации."""
        self.__account = self.__validate_text("account", value)

    @property
    def ownership_form(self) -> str:
        """Возвращает форму собственности."""
        return self.__ownership_form

    @ownership_form.setter
    def ownership_form(self, value: str) -> None:
        """Устанавливает форму собственности."""
        self.__ownership_form = self.__validate_text("ownership_form", value)
