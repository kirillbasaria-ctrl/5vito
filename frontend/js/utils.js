import { CATEGORY_LABELS, CITY_LABELS } from "./config.js";
import { mediaUrl } from "./api.js";

export function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function formatPrice(price) {
  if (price === null || price === undefined) return "Договорная";
  const num = Number(price);
  return num.toLocaleString("ru-RU") + " ₽";
}

export function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function formatDateTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function categoryLabel(slug) {
  return CATEGORY_LABELS[slug] || slug;
}

export function cityLabel(slug) {
  return CITY_LABELS[slug] || slug;
}

export function qs(params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") usp.set(k, v);
  });
  const str = usp.toString();
  return str ? `?${str}` : "";
}

/** Карточка объявления — используется в ленте, избранном, "моих объявлениях". */
export function renderAdCard(ad, { showStatus = false, favorite = false } = {}) {
  const img = mediaUrl(ad.cover_image);
  const statusBadge = showStatus
    ? `<span class="status-badge status-${ad.status}">${statusLabel(ad.status)}</span>`
    : "";
  return `
    <a class="ad-card" href="#/ad/${ad.id}">
      <div class="ad-card__image">
        ${img ? `<img src="${img}" alt="${escapeHtml(ad.title)}" loading="lazy">` : `<div class="ad-card__placeholder">${categoryLabel(ad.category)}</div>`}
        ${statusBadge}
        ${favorite ? `<button class="ad-card__fav is-active" data-fav-toggle="${ad.id}" title="Убрать из избранного" aria-label="Убрать из избранного">♥</button>` : ""}
      </div>
      <div class="ad-card__body">
        <div class="ad-card__price">${formatPrice(ad.price)}</div>
        <div class="ad-card__title">${escapeHtml(ad.title)}</div>
        <div class="ad-card__meta">${cityLabel(ad.city)} · ${categoryLabel(ad.category)}</div>
      </div>
    </a>
  `;
}

export function statusLabel(status) {
  return { draft: "Черновик", active: "Активно", hidden: "Скрыто", deleted: "Удалено" }[status] || status;
}

export function renderStars(rating) {
  const r = Math.round(rating || 0);
  return "★".repeat(r) + "☆".repeat(5 - r);
}

export function renderPagination(page, pages, buildHref) {
  if (pages <= 1) return "";
  let html = '<div class="pagination">';
  if (page > 1) html += `<a href="${buildHref(page - 1)}" class="page-btn">← Назад</a>`;
  html += `<span class="page-info">Страница ${page} из ${pages}</span>`;
  if (page < pages) html += `<a href="${buildHref(page + 1)}" class="page-btn">Вперёд →</a>`;
  html += "</div>";
  return html;
}

let toastTimer = null;
export function showToast(message, type = "info") {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.className = `toast toast--${type} toast--visible`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("toast--visible"), 3200);
}

export function debounce(fn, delay = 350) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
}
