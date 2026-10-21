import { parsePortfolio, summarize, selectRows, MAX_FILE_BYTES } from "./portfolio.mjs";

const PAGE_SIZE = 20;
const $ = id => document.getElementById(id);
const state = { inventory: null, query: "", status: "all", category: "all", order: "name", page: 1 };
const filters = ["search", "state", "category", "order"];
const categoryLabel = {
  education: "EDUCACIÓN · ORIENTATIVO",
  music_art: "ARTE / MÚSICA · ORIENTATIVO",
  ai_tools: "IA / SISTEMAS · ORIENTATIVO",
  unclassified: "SIN CLASIFICACIÓN VERIFICADA",
};
function node(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined) element.textContent = String(value);
  return element;
}
function replaceEmpty(text, hint) {
  const container = node("div", "empty");
  container.append(node("span", "empty-glyph", "◌"), node("strong", "", text), node("p", "", hint));
  $("list").replaceChildren(container);
}
function setNotice(message, isError = false) {
  $("message").textContent = message;
  $("source-message").textContent = message;
  $("source-message").style.color = isError ? "#f1b7b7" : "";
}
function clearSelection() {
  $("inspector-title").textContent = "Ninguno seleccionado";
  $("inspector-detail").textContent = "Selecciona un repositorio para inspeccionar su estado.";
  $("inspector-facts").replaceChildren();
}
function reset() {
  state.inventory = null;
  state.query = ""; state.status = "all"; state.category = "all"; state.order = "name"; state.page = 1;
  $("file").value = "";
  $("search").value = "";
  $("state").value = "all";
  $("category").value = "all";
  $("order").value = "name";
  for (const id of filters) $(id).disabled = true;
  $("clear").disabled = true;
  for (const id of ["total","active","archived","checked","ready"]) $("metric-" + id).textContent = "—";
  $("results-summary").textContent = "Importa un archivo para comenzar.";
  $("pagination").hidden = true;
  clearSelection();
  replaceEmpty("Sin inventario. Sin suposiciones.", "Importa el archivo de auditoría o una instantánea local para visualizar los repositorios, sin exponerlos.");
}
function stat(label, value) {
  $("metric-" + label).textContent = new Intl.NumberFormat("es-ES").format(value);
}
function showDetail(row) {
  $("inspector-title").textContent = row.full_name;
  $("inspector-detail").textContent = row.checked
    ? "Se ha inspeccionado la estructura raíz. Todavía falta demostrar que el producto esté completo."
    : "Sin verificación integral del producto. Los nombres de archivos no prueban funcionalidad.";
  const dl = node("dl");
  const fields = [
    ["Estado", row.archived ? "Archivado" : "No archivado"],
    ["Visibilidad", row.private ? "Privado" : "Público"],
    ["Rama principal", row.branch],
    ["Categoría", categoryLabel[row.category]],
    ["Origen", state.inventory.mode === "live" ? "Auditoría autenticada" : "Instantánea histórica"],
    ["Código raíz", row.checked ? "Inspección preliminar" : "No verificado"],
    ["Propósito", row.purpose_verified ? "Verificado en fuente" : "Pendiente"],
    ["Contenido", row.content_verified ? "Declarado verificado" : "Pendiente"],
    ["Despliegue", row.deployed_verified ? "Declarado verificado" : "Pendiente"],
    ["Entrega completa", "NO CERTIFICADA"],
  ];
  for (const [label, value] of fields) {
    const d = node("div");d.append(node("dt", "", label), node("dd", "", value));dl.append(d);
  }
  $("inspector-facts").replaceChildren(dl);
}
function render() {
  if (!state.inventory) return;
  const data = selectRows(state.inventory.rows, {
    query: state.query, state: state.status, category: state.category, order: state.order,
  });
  const pages = Math.max(1, Math.ceil(data.length / PAGE_SIZE));
  state.page = Math.max(1, Math.min(state.page, pages));
  $("results-summary").textContent = data.length + " de " + state.inventory.rows.length + " repositorios";
  const page = data.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE);
  if (!page.length) {
    replaceEmpty("Sin resultados para estos filtros.", "Prueba otra búsqueda o cambia el estado del filtro.");
  } else {
    const fragment = document.createDocumentFragment();
    for (let index = 0; index < page.length; index++) {
      const r = page[index];
      const card = node("article", "repo");
      const idx = (state.page - 1) * PAGE_SIZE + index + 1;
      const content = node("div", "repo-content");
      const heading = node("button", "", r.name);
      heading.type = "button";
      heading.setAttribute("aria-label", "Inspeccionar " + r.name);
      heading.addEventListener("click", () => showDetail(r));
      const sub = node("div", "repo-sub", categoryLabel[r.category] + " · " + r.branch);
      content.append(heading, sub);
      card.append(node("span", "repo-index", String(idx).padStart(3, "0")), content,
        node("span", "repo-status " + (r.archived ? "archived" : "active"),
          r.archived ? "Archivado" : "Sin archivar"));
      fragment.append(card);
    }
    $("list").replaceChildren(fragment);
  }
  $("pagination").hidden = data.length <= PAGE_SIZE;
  $("page-status").textContent = state.page + " / " + pages;
  $("prev").disabled = state.page === 1;
  $("next").disabled = state.page === pages;
}
async function readFile(file) {
  if (!file) return;
  if (file.size > MAX_FILE_BYTES) {
    reset();setNotice("El archivo supera 8 MB y no se ha cargado.", true);return;
  }
  try {
    const raw = JSON.parse(await file.text());
    const inventory = parsePortfolio(raw);
    state.inventory = inventory;
    state.page = 1;
    clearSelection();
    filters.forEach(id => $(id).disabled = false);
    $("clear").disabled = false;
    const metrics = summarize(inventory.rows);
    stat("total", metrics.total);stat("active",metrics.active);stat("archived",metrics.archived);
    stat("checked",metrics.codeChecked);stat("ready",metrics.fullyReleased);
    const freshness = inventory.generated ? " · " + inventory.generated.slice(0, 60) : "";
    setNotice(inventory.scope + freshness);
    render();
  } catch (error) {
    reset();
    setNotice("Importación rechazada: " + (error instanceof Error ? error.message : "error desconocido"), true);
  }
}
$("file").addEventListener("change", event => readFile(event.target.files?.[0]));
$("clear").addEventListener("click", () => {reset();setNotice("Inventario eliminado de esta sesión.");});
$("search").addEventListener("input", event => {state.query = event.target.value;state.page = 1;render();});
$("state").addEventListener("change", event => {state.status = event.target.value;state.page = 1;render();});
$("category").addEventListener("change", event => {state.category = event.target.value;state.page = 1;render();});
$("order").addEventListener("change", event => {state.order = event.target.value;state.page = 1;render();});
$("prev").addEventListener("click", () => {state.page--;render();});
$("next").addEventListener("click", () => {state.page++;render();});
document.querySelector(".filters").addEventListener("submit", event => event.preventDefault());
const heroLabel = document.querySelector(".hero-actions label[for=file]");
heroLabel.addEventListener("keydown", event => {
  if (event.key === "Enter" || event.key === " ") {event.preventDefault();$("file").click();}
});
reset();
