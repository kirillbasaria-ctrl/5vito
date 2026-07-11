// Хранение JWT-токенов и данных текущего пользователя в localStorage,
// плюс сами вызовы /api/auth/*. Другие модули (api.js) переиспользуют
// getAccessToken/getRefreshToken/setTokens/clearTokens для авто-обновления
// access-токена при 401.
import { API_BASE_URL } from "./config.js";

const ACCESS_KEY = "va_access_token";
const REFRESH_KEY = "va_refresh_token";
const USER_KEY = "va_user";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function getCurrentUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function isAuthenticated() {
  return !!getAccessToken();
}

export function hasRole(...roles) {
  const user = getCurrentUser();
  return !!user && roles.includes(user.role);
}

export function setTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(ACCESS_KEY, access_token);
  if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
}

export function setCurrentUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

function notifyAuthChanged() {
  window.dispatchEvent(new Event("auth-changed"));
}

async function parseErrorDetail(res) {
  try {
    const data = await res.json();
    return data.detail || "Что-то пошло не так";
  } catch {
    return "Что-то пошло не так";
  }
}

export async function loadAndStoreCurrentUser() {
  const token = getAccessToken();
  if (!token) return null;
  const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    clearTokens();
    return null;
  }
  const user = await res.json();
  setCurrentUser(user);
  return user;
}

export async function register(email, password, name) {
  const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  const tokens = await res.json();
  setTokens(tokens);
  await loadAndStoreCurrentUser();
  notifyAuthChanged();
}

export async function login(email, password) {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  const tokens = await res.json();
  setTokens(tokens);
  await loadAndStoreCurrentUser();
  notifyAuthChanged();
}

export function logout() {
  clearTokens();
  notifyAuthChanged();
}

/** Пытается обновить access-токен через refresh. Возвращает true/false. */
export async function tryRefreshAccessToken() {
  const refresh_token = getRefreshToken();
  if (!refresh_token) return false;
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    });
    if (!res.ok) {
      clearTokens();
      return false;
    }
    const tokens = await res.json();
    setTokens(tokens);
    return true;
  } catch {
    return false;
  }
}
