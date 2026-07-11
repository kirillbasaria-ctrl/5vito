"""
Справочники проекта. Категории и города — фиксированные списки (без БД),
как и требует ТЗ. slug используется в API и в БД, label — для отображения
(в т.ч. в админ-панели на Jinja2).
"""
from enum import Enum


class RoleEnum(str, Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class CategoryEnum(str, Enum):
    services = "services"
    job = "job"
    clothing = "clothing"
    realty = "realty"
    auto = "auto"


CATEGORY_LABELS: dict[str, str] = {
    CategoryEnum.services.value: "Услуги",
    CategoryEnum.job.value: "Работа",
    CategoryEnum.clothing.value: "Одежда",
    CategoryEnum.realty.value: "Недвижимость",
    CategoryEnum.auto.value: "Автомобили",
}


class CityEnum(str, Enum):
    vologda = "vologda"
    cherepovets = "cherepovets"
    sokol = "sokol"
    velikiy_ustyug = "velikiy_ustyug"
    gryazovets = "gryazovets"
    sheksna = "sheksna"
    babaevo = "babaevo"
    totma = "totma"
    ustyuzhna = "ustyuzhna"
    kirillov = "kirillov"
    belozersk = "belozersk"
    vytegra = "vytegra"


CITY_LABELS: dict[str, str] = {
    CityEnum.vologda.value: "Вологда",
    CityEnum.cherepovets.value: "Череповец",
    CityEnum.sokol.value: "Сокол",
    CityEnum.velikiy_ustyug.value: "Великий Устюг",
    CityEnum.gryazovets.value: "Грязовец",
    CityEnum.sheksna.value: "Шексна",
    CityEnum.babaevo.value: "Бабаево",
    CityEnum.totma.value: "Тотьма",
    CityEnum.ustyuzhna.value: "Устюжна",
    CityEnum.kirillov.value: "Кириллов",
    CityEnum.belozersk.value: "Белозерск",
    CityEnum.vytegra.value: "Вытегра",
}


class AdStatusEnum(str, Enum):
    draft = "draft"        # черновик, виден только автору
    active = "active"      # опубликовано, видно всем
    hidden = "hidden"      # скрыто модератором/админом
    deleted = "deleted"    # удалено (мягкое удаление), не видно никому кроме админки


class ComplaintReasonEnum(str, Enum):
    spam = "spam"
    fraud = "fraud"
    prohibited = "prohibited"
    duplicate = "duplicate"
    other = "other"


class ComplaintStatusEnum(str, Enum):
    new = "new"
    resolved = "resolved"
    rejected = "rejected"


# --- Подписи для отображения в админ-панели ---

ROLE_LABELS: dict[str, str] = {
    RoleEnum.user.value: "Пользователь",
    RoleEnum.moderator.value: "Модератор",
    RoleEnum.admin.value: "Админ",
}

AD_STATUS_LABELS: dict[str, str] = {
    AdStatusEnum.draft.value: "Черновик",
    AdStatusEnum.active.value: "Активно",
    AdStatusEnum.hidden.value: "Скрыто модератором",
    AdStatusEnum.deleted.value: "Удалено",
}

COMPLAINT_REASON_LABELS: dict[str, str] = {
    ComplaintReasonEnum.spam.value: "Спам / реклама",
    ComplaintReasonEnum.fraud.value: "Мошенничество",
    ComplaintReasonEnum.prohibited.value: "Запрещённый товар/услуга",
    ComplaintReasonEnum.duplicate.value: "Дубликат объявления",
    ComplaintReasonEnum.other.value: "Другое",
}

COMPLAINT_STATUS_LABELS: dict[str, str] = {
    ComplaintStatusEnum.new.value: "Новая",
    ComplaintStatusEnum.resolved.value: "Решена",
    ComplaintStatusEnum.rejected.value: "Отклонена",
}
