import { api } from "../api.js";
import { getCurrentUser, isAuthenticated } from "../auth.js";
import { cityLabel, escapeHtml, formatDate, renderAdCard, renderStars, showToast } from "../utils.js";

export async function renderSellerProfile(params) {
  const app = document.getElementById("app");
  app.innerHTML = `<p class="loading">Загружаем профиль…</p>`;

  const userId = params.id;
  let profile, reviews, adsPage;
  try {
    [profile, reviews, adsPage] = await Promise.all([
      api.get(`/api/users/${userId}`),
      api.get(`/api/reviews/user/${userId}`),
      api.get(`/api/ads?owner_id=${userId}&page_size=50`),
    ]);
  } catch (e) {
    app.innerHTML = `<p class="empty-state">Не удалось загрузить профиль: ${escapeHtml(e.message)}</p>`;
    return;
  }

  const me = getCurrentUser();
  const isSelf = me && me.id === Number(userId);

  app.innerHTML = `
    <div class="seller-page">
      <h1>${escapeHtml(profile.user.name)}</h1>
      <div class="seller-page__meta">
        ${profile.user.city ? cityLabel(profile.user.city) + " · " : ""}на сайте с ${formatDate(profile.user.created_at)}
      </div>
      <div class="seller-page__rating">
        ${
          profile.reviews_count
            ? `<span class="stars">${renderStars(profile.average_rating)}</span> ${profile.average_rating} (${profile.reviews_count} отзывов)`
            : "Пока нет отзывов"
        }
        · ${profile.active_ads_count} активных объявлений
      </div>

      <h2>Объявления продавца</h2>
      <div class="ads-grid">
        ${
          adsPage.items.length
            ? adsPage.items.map((ad) => renderAdCard(ad)).join("")
            : `<p class="empty-state">Сейчас нет активных объявлений.</p>`
        }
      </div>

      <h2>Отзывы</h2>
      <div id="reviews-list">
        ${
          reviews.length
            ? reviews
                .map(
                  (r) => `
              <div class="review-item">
                <div class="review-item__head">
                  <strong>${escapeHtml(r.author.name)}</strong>
                  <span class="stars">${renderStars(r.rating)}</span>
                  <span class="review-item__date">${formatDate(r.created_at)}</span>
                </div>
                <p>${escapeHtml(r.text)}</p>
              </div>`
                )
                .join("")
            : `<p class="empty-state">Отзывов пока нет.</p>`
        }
      </div>

      <div id="review-form-holder"></div>
    </div>
  `;

  if (!isSelf) renderReviewForm(userId);
}

function renderReviewForm(targetUserId) {
  const holder = document.getElementById("review-form-holder");

  if (!isAuthenticated()) {
    holder.innerHTML = `<p class="muted-note"><a href="#/login">Войдите</a>, чтобы оставить отзыв.</p>`;
    return;
  }

  holder.innerHTML = `
    <h2>Оставить отзыв</h2>
    <form id="review-form" class="ad-form">
      <label>Оценка
        <select id="review-rating">
          <option value="5">5 — отлично</option>
          <option value="4">4 — хорошо</option>
          <option value="3">3 — нормально</option>
          <option value="2">2 — плохо</option>
          <option value="1">1 — очень плохо</option>
        </select>
      </label>
      <label>Текст отзыва
        <textarea id="review-text" required minlength="1" maxlength="2000" rows="3"></textarea>
      </label>
      <div class="form-error hidden" id="review-error"></div>
      <button type="submit" class="btn btn--primary">Отправить отзыв</button>
    </form>
  `;

  document.getElementById("review-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("review-error");
    errorBox.classList.add("hidden");
    try {
      await api.post("/api/reviews", {
        target_user_id: Number(targetUserId),
        rating: Number(document.getElementById("review-rating").value),
        text: document.getElementById("review-text").value.trim(),
      });
      showToast("Отзыв опубликован");
      location.reload();
    } catch (err) {
      errorBox.textContent = escapeHtml(err.message);
      errorBox.classList.remove("hidden");
    }
  });
}
