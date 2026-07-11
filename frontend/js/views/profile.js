import { api } from "../api.js";
import { CITIES } from "../config.js";
import { getCurrentUser, loadAndStoreCurrentUser } from "../auth.js";
import { escapeHtml, renderAdCard, showToast } from "../utils.js";

const TABS = [
  { slug: "", label: "Все" },
  { slug: "active", label: "Активные" },
  { slug: "draft", label: "Черновики" },
  { slug: "hidden", label: "Скрытые модератором" },
  { slug: "deleted", label: "Удалённые" },
];

export async function renderProfile(params, query) {
  const app = document.getElementById("app");
  const user = getCurrentUser();
  if (!user) {
    app.innerHTML = `<p class="empty-state">Нужно <a href="#/login">войти</a>, чтобы открыть личный кабинет.</p>`;
    return;
  }

  const activeTab = query.get("tab") || "";

  app.innerHTML = `
    <div class="profile-page">
      <h1>Личный кабинет</h1>

      <section class="profile-card">
        <h2>Мои данные</h2>
        <form id="profile-form" class="ad-form">
          <label>Имя
            <input type="text" id="p-name" value="${escapeHtml(user.name)}" maxlength="120" required>
          </label>
          <label>Телефон
            <input type="tel" id="p-phone" value="${escapeHtml(user.phone || "")}" maxlength="32" placeholder="+7 900 000-00-00">
          </label>
          <label>Город
            <select id="p-city">
              <option value="">Не указан</option>
              ${CITIES.map(
                (c) => `<option value="${c.slug}" ${user.city === c.slug ? "selected" : ""}>${c.label}</option>`
              ).join("")}
            </select>
          </label>
          <div class="form-error hidden" id="profile-error"></div>
          <button type="submit" class="btn btn--primary">Сохранить</button>
        </form>
      </section>

      <section>
        <h2>Мои объявления</h2>
        <div class="tabs">
          ${TABS.map(
            (t) => `<a href="#/profile?tab=${t.slug}" class="tab ${activeTab === t.slug ? "tab--active" : ""}">${t.label}</a>`
          ).join("")}
        </div>
        <div id="my-ads-grid" class="ads-grid">
          <p class="loading">Загружаем объявления…</p>
        </div>
      </section>
    </div>
  `;

  document.getElementById("profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("profile-error");
    errorBox.classList.add("hidden");
    try {
      const updated = await api.patch("/api/users/me", {
        name: document.getElementById("p-name").value.trim(),
        phone: document.getElementById("p-phone").value.trim() || null,
        city: document.getElementById("p-city").value || null,
      });
      showToast("Данные обновлены");
      // обновляем закешированного пользователя
      await loadAndStoreCurrentUser();
      void updated;
    } catch (err) {
      errorBox.textContent = escapeHtml(err.message);
      errorBox.classList.remove("hidden");
    }
  });

  await loadMyAds(activeTab);
}

async function loadMyAds(status) {
  const grid = document.getElementById("my-ads-grid");
  try {
    const path = status ? `/api/ads/mine?status=${status}` : "/api/ads/mine";
    const ads = await api.get(path);
    grid.innerHTML = ads.length
      ? ads.map((ad) => renderAdCard(ad, { showStatus: true })).join("")
      : `<p class="empty-state">Тут пока пусто. <a href="#/create">Разместить объявление?</a></p>`;
  } catch (e) {
    grid.innerHTML = `<p class="empty-state">Не удалось загрузить: ${escapeHtml(e.message)}</p>`;
  }
}
