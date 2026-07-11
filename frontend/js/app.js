import { getCurrentUser, isAuthenticated, loadAndStoreCurrentUser, logout } from "./auth.js";
import { addRoute, initRouter, navigate, setNotFoundHandler } from "./router.js";
import { escapeHtml } from "./utils.js";
import { renderAdDetail } from "./views/adDetail.js";
import { renderAdForm } from "./views/createAd.js";
import { renderFavorites } from "./views/favorites.js";
import { renderHome } from "./views/home.js";
import { renderLogin } from "./views/login.js";
import { renderProfile } from "./views/profile.js";
import { renderRegister } from "./views/register.js";
import { renderSellerProfile } from "./views/sellerProfile.js";

function requireAuth(renderFn) {
  return async (params, query) => {
    if (!isAuthenticated()) {
      navigate("/login");
      return;
    }
    await renderFn(params, query);
  };
}

addRoute("/", renderHome);
addRoute("/ad/:id", renderAdDetail);
addRoute("/login", renderLogin);
addRoute("/register", renderRegister);
addRoute("/create", requireAuth(renderAdForm));
addRoute("/edit/:id", requireAuth(renderAdForm));
addRoute("/profile", requireAuth(renderProfile));
addRoute("/favorites", requireAuth(renderFavorites));
addRoute("/seller/:id", renderSellerProfile);

setNotFoundHandler(() => {
  document.getElementById("app").innerHTML = `<p class="empty-state">Страница не найдена. <a href="#/">На главную</a></p>`;
});

function renderHeader() {
  const header = document.getElementById("site-header");
  const user = getCurrentUser();

  header.innerHTML = `
    <div class="header-inner">
      <a href="#/" class="logo">Доска объявлений<span>Вологодской области</span></a>
      <button class="nav-toggle" id="nav-toggle" aria-label="Меню">☰</button>
      <nav class="header-nav" id="header-nav">
        <a href="#/create" class="btn btn--primary btn--small">+ Подать объявление</a>
        ${
          user
            ? `
              <a href="#/favorites">Избранное</a>
              <a href="#/profile">${escapeHtml(user.name)}</a>
              <button id="logout-btn" class="link-btn">Выйти</button>
            `
            : `
              <a href="#/login">Войти</a>
              <a href="#/register">Регистрация</a>
            `
        }
      </nav>
    </div>
  `;

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      logout();
      navigate("/");
    });
  }

  document.getElementById("nav-toggle").addEventListener("click", () => {
    document.getElementById("header-nav").classList.toggle("header-nav--open");
  });
}

window.addEventListener("auth-changed", renderHeader);
window.addEventListener("hashchange", () => {
  document.getElementById("header-nav").classList.remove("header-nav--open");
});

(async function bootstrap() {
  if (isAuthenticated()) {
    await loadAndStoreCurrentUser();
  }
  renderHeader();
  initRouter();
})();
