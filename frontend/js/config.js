// ВАЖНО: после деплоя бэкенда на Render замените адрес ниже на реальный,
// например "https://vologda-ads-backend.onrender.com".
// Для локальной разработки (uvicorn на 127.0.0.1:8000) значение по умолчанию
// уже подходит.
export const API_BASE_URL = "http://127.0.0.1:8000";

// Категории и города — фиксированные списки (совпадают с backend/app/constants.py).
// Меняются редко, поэтому хранятся здесь напрямую, без похода в /api/meta.
export const CATEGORIES = [
  { slug: "services", label: "Услуги" },
  { slug: "job", label: "Работа" },
  { slug: "clothing", label: "Одежда" },
  { slug: "realty", label: "Недвижимость" },
  { slug: "auto", label: "Автомобили" },
];

export const CITIES = [
  { slug: "vologda", label: "Вологда" },
  { slug: "cherepovets", label: "Череповец" },
  { slug: "sokol", label: "Сокол" },
  { slug: "velikiy_ustyug", label: "Великий Устюг" },
  { slug: "gryazovets", label: "Грязовец" },
  { slug: "sheksna", label: "Шексна" },
  { slug: "babaevo", label: "Бабаево" },
  { slug: "totma", label: "Тотьма" },
  { slug: "ustyuzhna", label: "Устюжна" },
  { slug: "kirillov", label: "Кириллов" },
  { slug: "belozersk", label: "Белозерск" },
  { slug: "vytegra", label: "Вытегра" },
];

export const CATEGORY_LABELS = Object.fromEntries(CATEGORIES.map((c) => [c.slug, c.label]));
export const CITY_LABELS = Object.fromEntries(CITIES.map((c) => [c.slug, c.label]));

export const COMPLAINT_REASONS = [
  { slug: "spam", label: "Спам / реклама" },
  { slug: "fraud", label: "Мошенничество" },
  { slug: "prohibited", label: "Запрещённый товар/услуга" },
  { slug: "duplicate", label: "Дубликат объявления" },
  { slug: "other", label: "Другое" },
];
