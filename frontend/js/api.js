// Единая точка обращения к бэкенду. Автоматически подставляет
// Authorization: Bearer <access_token> и, если он истёк (401), один раз
// пробует обновить его через refresh-токен и повторяет запрос.
import { API_BASE_URL } from "./config.js";
import { clearTokens, getAccessToken, tryRefreshAccessToken } from "./auth.js";

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function parseBody(res) {
  if (res.status === 204) return null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  return res.text();
}

async function request(path, { method = "GET", body, isFormData = false, auth = true } = {}, isRetry = false) {
  const headers = {};
  if (auth) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  if (body !== undefined && !isFormData) {
    headers["Content-Type"] = "application/json";
  }

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
    });
  } catch (e) {
    throw new ApiError(0, "Не удалось связаться с сервером. Проверьте подключение к интернету.");
  }

  if (res.status === 401 && auth && !isRetry) {
    const refreshed = await tryRefreshAccessToken();
    if (refreshed) return request(path, { method, body, isFormData, auth }, true);
    clearTokens();
  }

  if (!res.ok) {
    let detail = `Ошибка запроса (${res.status})`;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* тело не JSON — оставляем дефолтный текст */
    }
    throw new ApiError(res.status, detail);
  }

  return parseBody(res);
}

export const api = {
  get: (path, opts) => request(path, { ...opts, method: "GET" }),
  post: (path, body, opts) => request(path, { ...opts, method: "POST", body }),
  patch: (path, body, opts) => request(path, { ...opts, method: "PATCH", body }),
  delete: (path, opts) => request(path, { ...opts, method: "DELETE" }),
  uploadFile: (path, formData, opts) =>
    request(path, { ...opts, method: "POST", body: formData, isFormData: true }),
};

/** Полный URL для отображения фото (бэкенд отдаёт относительные пути вида /uploads/xxx.jpg) */
export function mediaUrl(path) {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${API_BASE_URL}${path}`;
}
