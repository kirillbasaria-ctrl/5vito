import { login } from "../auth.js";
import { navigate } from "../router.js";
import { escapeHtml } from "../utils.js";

export async function renderLogin() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="auth-page">
      <h1>Вход</h1>
      <form id="login-form" class="auth-form">
        <label>Email
          <input type="email" id="login-email" required autofocus>
        </label>
        <label>Пароль
          <input type="password" id="login-password" required minlength="6">
        </label>
        <div class="form-error hidden" id="login-error"></div>
        <button type="submit" class="btn btn--primary">Войти</button>
      </form>
      <p class="auth-switch">Нет аккаунта? <a href="#/register">Зарегистрируйтесь</a></p>
    </div>
  `;

  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const errorBox = document.getElementById("login-error");
    errorBox.classList.add("hidden");

    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      errorBox.textContent = escapeHtml(err.message);
      errorBox.classList.remove("hidden");
    }
  });
}
