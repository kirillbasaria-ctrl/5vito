import { api } from "../api.js";
import { escapeHtml, renderAdCard, showToast } from "../utils.js";

export async function renderFavorites() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="favorites-page">
      <h1>Избранное</h1>
      <div id="favorites-grid" class="ads-grid">
        <p class="loading">Загружаем избранное…</p>
      </div>
    </div>
  `;

  await loadFavorites();
}

async function loadFavorites() {
  const grid = document.getElementById("favorites-grid");
  try {
    const ads = await api.get("/api/favorites");
    if (!ads.length) {
      grid.innerHTML = `<p class="empty-state">Пока ничего не добавлено в избранное.</p>`;
      return;
    }
    grid.innerHTML = ads.map((ad) => renderAdCard(ad, { favorite: true })).join("");

    grid.querySelectorAll("[data-fav-toggle]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        const adId = btn.dataset.favToggle;
        try {
          await api.delete(`/api/favorites/${adId}`);
          showToast("Убрано из избранного");
          await loadFavorites();
        } catch (err) {
          showToast(err.message, "error");
        }
      });
    });
  } catch (e) {
    grid.innerHTML = `<p class="empty-state">Не удалось загрузить избранное: ${escapeHtml(e.message)}</p>`;
  }
}
