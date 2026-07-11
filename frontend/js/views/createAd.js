import { api, mediaUrl } from "../api.js";
import { CATEGORIES, CITIES } from "../config.js";
import { navigate } from "../router.js";
import { escapeHtml, showToast } from "../utils.js";

export async function renderAdForm(params) {
  const app = document.getElementById("app");
  const isEdit = !!params.id;

  let ad = null;
  if (isEdit) {
    app.innerHTML = `<p class="loading">Загружаем объявление…</p>`;
    try {
      ad = await api.get(`/api/ads/${params.id}`);
    } catch (e) {
      app.innerHTML = `<p class="empty-state">Не удалось загрузить объявление: ${escapeHtml(e.message)}</p>`;
      return;
    }
  }

  app.innerHTML = `
    <div class="ad-form-page">
      <h1>${isEdit ? "Редактирование объявления" : "Новое объявление"}</h1>

      <form id="ad-form" class="ad-form">
        <label>Заголовок
          <input type="text" id="f-title" required minlength="3" maxlength="150" value="${escapeHtml(ad?.title || "")}">
        </label>

        <label>Описание
          <textarea id="f-description" required minlength="10" maxlength="5000" rows="6">${escapeHtml(ad?.description || "")}</textarea>
        </label>

        <div class="ad-form__row">
          <label>Категория
            <select id="f-category">
              ${CATEGORIES.map(
                (c) => `<option value="${c.slug}" ${ad?.category === c.slug ? "selected" : ""}>${c.label}</option>`
              ).join("")}
            </select>
          </label>
          <label>Город
            <select id="f-city">
              ${CITIES.map(
                (c) => `<option value="${c.slug}" ${ad?.city === c.slug ? "selected" : ""}>${c.label}</option>`
              ).join("")}
            </select>
          </label>
        </div>

        <div class="ad-form__row">
          <label class="price-label">Цена, ₽
            <input type="number" id="f-price" min="0" step="1" value="${ad?.price ?? ""}" ${ad && ad.price === null ? "disabled" : ""}>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="f-negotiable" ${ad && ad.price === null ? "checked" : ""}>
            Цена договорная
          </label>
        </div>

        ${
          !isEdit
            ? `<label class="checkbox-label">
                 <input type="checkbox" id="f-draft">
                 Сохранить как черновик (не публиковать сразу)
               </label>`
            : ""
        }

        <div class="form-error hidden" id="form-error"></div>
        <button type="submit" class="btn btn--primary">${isEdit ? "Сохранить изменения" : "Создать объявление"}</button>
      </form>

      ${isEdit ? `<div class="photos-section" id="photos-section"></div>` : `<p class="hint">Фото можно будет добавить сразу после создания объявления.</p>`}
    </div>
  `;

  document.getElementById("f-negotiable").addEventListener("change", (e) => {
    document.getElementById("f-price").disabled = e.target.checked;
  });

  if (isEdit) renderPhotosSection(ad);

  document.getElementById("ad-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("form-error");
    errorBox.classList.add("hidden");

    const negotiable = document.getElementById("f-negotiable").checked;
    const priceRaw = document.getElementById("f-price").value;

    const payload = {
      title: document.getElementById("f-title").value.trim(),
      description: document.getElementById("f-description").value.trim(),
      price: negotiable || priceRaw === "" ? null : Number(priceRaw),
      category: document.getElementById("f-category").value,
      city: document.getElementById("f-city").value,
    };

    try {
      if (isEdit) {
        await api.patch(`/api/ads/${ad.id}`, payload);
        showToast("Изменения сохранены");
        navigate(`/ad/${ad.id}`);
      } else {
        payload.is_draft = document.getElementById("f-draft").checked;
        const created = await api.post("/api/ads", payload);
        showToast(payload.is_draft ? "Черновик сохранён" : "Объявление опубликовано");
        navigate(`/edit/${created.id}`);
      }
    } catch (err) {
      errorBox.textContent = escapeHtml(err.message);
      errorBox.classList.remove("hidden");
    }
  });
}

function renderPhotosSection(ad) {
  const section = document.getElementById("photos-section");
  const maxImages = 6;

  function draw() {
    section.innerHTML = `
      <h2>Фото (${ad.images.length}/${maxImages})</h2>
      <div class="photo-grid">
        ${ad.images
          .map(
            (img) => `
          <div class="photo-item">
            <img src="${mediaUrl(img.url)}" alt="">
            <button type="button" class="photo-item__remove" data-remove-image="${img.id}" title="Удалить фото">✕</button>
          </div>`
          )
          .join("")}
      </div>
      ${
        ad.images.length < maxImages
          ? `<label class="btn btn--secondary photo-upload-btn">
               Добавить фото
               <input type="file" id="photo-input" accept="image/jpeg,image/png,image/webp" hidden>
             </label>`
          : `<p class="hint">Достигнут лимит фото для одного объявления.</p>`
      }
    `;

    const input = document.getElementById("photo-input");
    if (input) {
      input.addEventListener("change", async () => {
        const file = input.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);
        try {
          const uploaded = await api.uploadFile(`/api/ads/${ad.id}/images`, formData);
          ad.images.push(uploaded);
          draw();
        } catch (e) {
          showToast(e.message, "error");
        }
      });
    }

    section.querySelectorAll("[data-remove-image]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const imageId = btn.dataset.removeImage;
        try {
          await api.delete(`/api/ads/${ad.id}/images/${imageId}`);
          ad.images = ad.images.filter((img) => String(img.id) !== String(imageId));
          draw();
        } catch (e) {
          showToast(e.message, "error");
        }
      });
    });
  }

  draw();
}
