import { register } from "../auth.js";
import { navigate } from "../router.js";
import { escapeHtml } from "../utils.js";

export async function renderRegister() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="auth-page">
      <h1>Регистрация</h1>
      <form id="register-form" class="auth-form">
        <label>Имя
          <input type="text" id="reg-name" required autofocus maxlength="120">
        </label>
        <label>Email
          <input type="email" id="reg-email" required>
        </label>
        <label>Пароль <span class="hint">(минимум 6 символов)</span>
          <input type="password" id="reg-password" required minlength="6">
        </label>
        <div class="form-error hidden" id="reg-error"></div>
        <button type="submit" class="btn btn--primary">Зарегистрироваться</button>
      </form>
      <p class="auth-switch">Уже есть аккаунт? <a href="#/login">Войдите</a></p>
    </div>
  `;

  document.getElementById("register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("reg-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const errorBox = document.getElementById("reg-error");
    errorBox.classList.add("hidden");

    try {
      await register(email, password, name);
      navigate("/");
    } catch (err) {
      errorBox.textContent = escapeHtml(err.message);
      errorBox.classList.remove("hidden");
    }
  });
}
