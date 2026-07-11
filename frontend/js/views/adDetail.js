import { api, mediaUrl } from "../api.js";
import { getCurrentUser, isAuthenticated } from "../auth.js";
import { COMPLAINT_REASONS } from "../config.js";
import { navigate } from "../router.js";
import {
  categoryLabel,
  cityLabel,
  escapeHtml,
  formatDateTime,
  formatPrice,
  showToast,
  statusLabel,
} from "../utils.js";

export async function renderAdDetail(params) {
  const app = document.getElementById("app");
  app.innerHTML = `<p class="loading">Загружаем объявление…</p>`;

  let ad;
  try {
    ad = await api.get(`/api/ads/${params.id}`);
  } catch (e) {
    app.innerHTML = `<p class="empty-state">Объявление не найдено или было удалено.</p>`;
    return;
  }

  const me = getCurrentUser();
  const isOwner = me && me.id === ad.owner.id;
  const images = ad.images.length ? ad.images : [{ url: null, id: 0 }];

  app.innerHTML = `
    <div class="ad-detail">
      <a href="#/" class="back-link">← Ко всем объявлениям</a>

      ${
        ad.status !== "active"
          ? `<div class="notice notice--${ad.status}">Статус объявления: ${statusLabel(ad.status)}${isOwner ? "" : " — видно только вам и модераторам"}</div>`
          : ""
      }

      <div class="ad-detail__grid">
        <div class="ad-detail__gallery">
          <div class="gallery-main" id="gallery-main">
            ${
              images[0].url
                ? `<img src="${mediaUrl(images[0].url)}" alt="${escapeHtml(ad.title)}" id="gallery-main-img">`
                : `<div class="ad-card__placeholder ad-card__placeholder--big">${categoryLabel(ad.category)}</div>`
            }
          </div>
          ${
            ad.images.length > 1
              ? `<div class="gallery-thumbs">
                  ${ad.images
                    .map(
                      (img, i) =>
                        `<img src="${mediaUrl(img.url)}" data-full="${mediaUrl(img.url)}" class="gallery-thumb ${i === 0 ? "is-active" : ""}" alt="">`
                    )
                    .join("")}
                </div>`
              : ""
          }
        </div>

        <div class="ad-detail__info">
          <h1>${escapeHtml(ad.title)}</h1>
          <div class="ad-detail__price">${formatPrice(ad.price)}</div>
          <div class="ad-detail__meta">
            ${cityLabel(ad.city)} · ${categoryLabel(ad.category)} · ${ad.views} просмотров
          </div>
          <div class="ad-detail__meta ad-detail__meta--muted">
            Опубликовано ${formatDateTime(ad.created_at)}
          </div>

          <div class="ad-detail__actions" id="ad-actions"></div>

          <div class="seller-box">
            <div class="seller-box__name">
              <a href="#/seller/${ad.owner.id}">${escapeHtml(ad.owner.name)}</a>
            </div>
            <button class="btn btn--secondary" id="show-phone-btn">Показать телефон</button>
            <div id="phone-holder"></div>
          </div>
        </div>
      </div>

      <div class="ad-detail__description">
        <h2>Описание</h2>
        <p>${escapeHtml(ad.description).replaceAll("\n", "<br>")}</p>
      </div>

      <div id="complaint-section"></div>
    </div>
  `;

  wireGallery();
  renderActions(ad, isOwner);
  wirePhoneReveal(ad);
  renderComplaintSection(ad, isOwner);
}

function wireGallery() {
  const thumbs = document.querySelectorAll(".gallery-thumb");
  thumbs.forEach((thumb) => {
    thumb.addEventListener("click", () => {
      document.getElementById("gallery-main").innerHTML = `<img src="${thumb.dataset.full}" alt="">`;
      thumbs.forEach((t) => t.classList.remove("is-active"));
      thumb.classList.add("is-active");
    });
  });
}

function wirePhoneReveal(ad) {
  const btn = document.getElementById("show-phone-btn");
  btn.addEventListener("click", () => {
    const holder = document.getElementById("phone-holder");
    holder.innerHTML = ad.owner.phone
      ? `<div class="seller-box__phone">${escapeHtml(ad.owner.phone)}</div>`
      : `<div class="seller-box__phone seller-box__phone--muted">Продавец не указал телефон — напишите через профиль.</div>`;
    btn.remove();
  });
}

function renderActions(ad, isOwner) {
  const holder = document.getElementById("ad-actions");

  if (isOwner) {
    holder.innerHTML = `
      <a href="#/edit/${ad.id}" class="btn btn--secondary">Редактировать</a>
      ${
        ad.status === "active"
          ? `<button class="btn btn--secondary" id="unpublish-btn">Снять с публикации</button>`
          : ad.status === "draft"
            ? `<button class="btn btn--primary" id="publish-btn">Опубликовать</button>`
            : ""
      }
      <button class="btn btn--danger" id="delete-btn">Удалить</button>
    `;
    document.getElementById("delete-btn").addEventListener("click", async () => {
      if (!confirm("Удалить объявление? Это действие нельзя отменить.")) return;
      try {
        await api.delete(`/api/ads/${ad.id}`);
        showToast("Объявление удалено");
        navigate("/profile");
      } catch (e) {
        showToast(e.message, "error");
      }
    });
    const unpublishBtn = document.getElementById("unpublish-btn");
    if (unpublishBtn)
      unpublishBtn.addEventListener("click", async () => {
        try {
          await api.post(`/api/ads/${ad.id}/publish`, { is_draft: true });
          showToast("Объявление снято с публикации");
          location.reload();
        } catch (e) {
          showToast(e.message, "error");
        }
      });
    const publishBtn = document.getElementById("publish-btn");
    if (publishBtn)
      publishBtn.addEventListener("click", async () => {
        try {
          await api.post(`/api/ads/${ad.id}/publish`, { is_draft: false });
          showToast("Объявление опубликовано");
          location.reload();
        } catch (e) {
          showToast(e.message, "error");
        }
      });
    return;
  }

  if (!isAuthenticated()) {
    holder.innerHTML = `<a href="#/login" class="btn btn--secondary">Войдите, чтобы добавить в избранное</a>`;
    return;
  }

  holder.innerHTML = `
    <button class="btn ${ad.is_favorited ? "btn--danger" : "btn--secondary"}" id="fav-btn">
      ${ad.is_favorited ? "♥ Убрать из избранного" : "♡ В избранное"}
    </button>
  `;
  document.getElementById("fav-btn").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    try {
      if (ad.is_favorited) {
        await api.delete(`/api/favorites/${ad.id}`);
        ad.is_favorited = false;
      } else {
        await api.post(`/api/favorites/${ad.id}`);
        ad.is_favorited = true;
      }
      btn.className = `btn ${ad.is_favorited ? "btn--danger" : "btn--secondary"}`;
      btn.textContent = ad.is_favorited ? "♥ Убрать из избранного" : "♡ В избранное";
    } catch (e2) {
      showToast(e2.message, "error");
    }
  });
}

function renderComplaintSection(ad, isOwner) {
  const holder = document.getElementById("complaint-section");
  if (isOwner) return;

  if (!isAuthenticated()) {
    holder.innerHTML = `<p class="muted-note"><a href="#/login">Войдите</a>, чтобы пожаловаться на объявление.</p>`;
    return;
  }

  holder.innerHTML = `
    <button class="link-btn" id="toggle-complaint">Пожаловаться на объявление</button>
    <form id="complaint-form" class="complaint-form hidden">
      <select id="complaint-reason">
        ${COMPLAINT_REASONS.map((r) => `<option value="${r.slug}">${r.label}</option>`).join("")}
      </select>
      <textarea id="complaint-text" placeholder="Комментарий (необязательно)" maxlength="2000"></textarea>
      <button type="submit" class="btn btn--secondary">Отправить жалобу</button>
    </form>
  `;

  document.getElementById("toggle-complaint").addEventListener("click", () => {
    document.getElementById("complaint-form").classList.toggle("hidden");
  });

  document.getElementById("complaint-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const reason = document.getElementById("complaint-reason").value;
    const text = document.getElementById("complaint-text").value.trim();
    try {
      await api.post("/api/complaints", { ad_id: ad.id, reason, text: text || null });
      showToast("Жалоба отправлена, спасибо!");
      document.getElementById("complaint-form").classList.add("hidden");
    } catch (e2) {
      showToast(e2.message, "error");
    }
  });
}
