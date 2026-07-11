// Минималистичный роутер на основе location.hash. Паттерны вида
// "/ad/:id" сопоставляются с реальным хэшем "#/ad/42" -> {id: "42"}.
const routes = [];
let notFoundHandler = () => {
  document.getElementById("app").innerHTML = "<p class='empty-state'>Страница не найдена.</p>";
};

export function addRoute(pattern, handler) {
  const paramNames = [];
  const regexStr =
    "^" +
    pattern
      .replace(/\/+$/, "")
      .split("/")
      .map((segment) => {
        if (segment.startsWith(":")) {
          paramNames.push(segment.slice(1));
          return "([^/]+)";
        }
        return segment.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      })
      .join("/") +
    "/?$";
  routes.push({ regex: new RegExp(regexStr), paramNames, handler });
}

export function setNotFoundHandler(handler) {
  notFoundHandler = handler;
}

function currentPath() {
  const hash = window.location.hash.slice(1) || "/";
  const [path, query] = hash.split("?");
  return { path: path || "/", query: new URLSearchParams(query || "") };
}

async function resolve() {
  const { path, query } = currentPath();
  for (const route of routes) {
    const match = path.match(route.regex);
    if (match) {
      const params = {};
      route.paramNames.forEach((name, i) => (params[name] = decodeURIComponent(match[i + 1])));
      window.scrollTo(0, 0);
      await route.handler(params, query);
      return;
    }
  }
  window.scrollTo(0, 0);
  notFoundHandler();
}

export function navigate(path) {
  window.location.hash = path;
}

export function initRouter() {
  window.addEventListener("hashchange", resolve);
  window.addEventListener("load", resolve);
  // На случай если скрипт подключён после события load
  if (document.readyState === "complete") resolve();
}

/** Перехват кликов по ссылкам с data-link — используем обычные <a href="#/..."> */
export function currentQuery() {
  return currentPath().query;
}
