import { api } from "../api.js";
import { CATEGORIES, CITIES } from "../config.js";
import { navigate } from "../router.js";
import { debounce, escapeHtml, qs, renderAdCard, renderPagination } from "../utils.js";

export async function renderHome(params, query) {
  const app = document.getElementById("app");

  const state = {
    category: query.get("category") || "",
    city: query.get("city") || "",
    search: query.get("search") || "",
    min_price: query.get("min_price") || "",
    max_price: query.get("max_price") || "",
    sort: query.get("sort") || "new",
    page: parseInt(query.get("page") || "1", 10),
  };

  const sidebarHref = (categorySlug) => "#" + qs({ ...state, category: categorySlug, page: undefined });

  app.innerHTML = `
    <div class="home-layout">
      <aside class="category-sidebar">
        <h2 class="sidebar-title">Категории</h2>
        <nav class="category-list">
          <a href="${sidebarHref("")}" class="category-link ${!state.category ? "category-link--active" : ""}">Все категории</a>
          ${CATEGORIES.map(
            (c) =>
              `<a href="${sidebarHref(c.slug)}" class="category-link ${state.category === c.slug ? "category-link--active" : ""}">${c.label}</a>`
          ).join("")}
        </nav>
      </aside>

      <div class="home-content">
        <section class="hero">
          <h1>Доска объявлений Вологодской области</h1>
          <p class="hero__sub">Услуги, работа, одежда, недвижимость и автомобили — во всех городах региона</p>

          <div class="search-bar">
            <input type="text" id="search-input" placeholder="Что вы ищете?" value="${escapeHtml(state.search)}">
            <select id="city-select" aria-label="Город">
              <option value="">Весь регион</option>
              ${CITIES.map(
                (c) => `<option value="${c.slug}" ${state.city === c.slug ? "selected" : ""}>${c.label}</option>`
              ).join("")}
            </select>
            <button id="search-btn" class="btn btn--primary">Найти</button>
          </div>
        </section>

        <section class="listing">
          <div class="listing__toolbar">
            <div class="price-filter">
              <label>Цена от <input type="number" id="min-price" min="0" value="${escapeHtml(state.min_price)}"></label>
              <label>до <input type="number" id="max-price" min="0" value="${escapeHtml(state.max_price)}"></label>
            </div>
            <select id="sort-select" aria-label="Сортировка">
              <option value="new" ${state.sort === "new" ? "selected" : ""}>Сначала новые</option>
              <option value="price_asc" ${state.sort === "price_asc" ? "selected" : ""}>Сначала дешевле</option>
              <option value="price_desc" ${state.sort === "price_desc" ? "selected" : ""}>Сначала дороже</option>
            </select>
          </div>

          <div id="ads-grid" class="ads-grid">
            <p class="loading">Загружаем объявления…</p>
          </div>
          <div id="pagination-holder"></div>
        </section>
      </div>
    </div>
  `;

  function applyFilter(patch) {
    navigate("/" + qs({ ...state, ...patch, page: undefined }));
  }

  document.getElementById("search-btn").addEventListener("click", () => {
    applyFilter({ search: document.getElementById("search-input").value.trim() });
  });
  document.getElementById("search-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") applyFilter({ search: e.target.value.trim() });
  });
  document.getElementById("city-select").addEventListener("change", (e) => applyFilter({ city: e.target.value }));
  document.getElementById("sort-select").addEventListener("change", (e) => applyFilter({ sort: e.target.value }));
  document
    .getElementById("min-price")
    .addEventListener("input", debounce((e) => applyFilter({ min_price: e.target.value }), 600));
  document
    .getElementById("max-price")
    .addEventListener("input", debounce((e) => applyFilter({ max_price: e.target.value }), 600));

  await loadAds(state);
}

async function loadAds(state) {
  const grid = document.getElementById("ads-grid");
  const pager = document.getElementById("pagination-holder");
  try {
    const data = await api.get(
      "/api/ads" +
        qs({
          category: state.category,
          city: state.city,
          search: state.search,
          min_price: state.min_price,
          max_price: state.max_price,
          sort: state.sort,
          page: state.page,
          page_size: 12,
        })
    );

    if (!data.items.length) {
      grid.innerHTML = `<p class="empty-state">Ничего не найдено. Попробуйте изменить фильтры или город.</p>`;
    } else {
      grid.innerHTML = data.items.map((ad) => renderAdCard(ad)).join("");
    }

    pager.innerHTML = renderPagination(data.page, data.pages, (p) => "#" + qs({ ...state, page: p }));
  } catch (e) {
    grid.innerHTML = `<p class="empty-state">Не удалось загрузить объявления: ${escapeHtml(e.message)}</p>`;
  }
}
