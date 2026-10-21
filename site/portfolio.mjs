/** BELENTANI • PRIVATE PORTFOLIO
 * Pure validation, filtering and statistics. No network, storage or telemetry.
 * Never treat file names or imported claims as completed-release evidence.
 */
export const MAX_FILE_BYTES = 8 * 1024 * 1024;
export const MAX_REPOSITORIES = 2000;
const KNOWN_CATEGORIES = new Set(["education", "music_art", "ai_tools", "unclassified"]);
const norm = value => String(value ?? "").trim();
const bool = value => value === true;
const isObject = value => value !== null && typeof value === "object" && !Array.isArray(value);

export function parsePortfolio(input) {
  if (!isObject(input) || !Array.isArray(input.repositories)) {
    throw new Error("Archivo inválido: falta la lista repositories.");
  }
  if (input.repositories.length > MAX_REPOSITORIES) {
    throw new Error("El inventario supera el límite de seguridad de 2.000 repositorios.");
  }
  const owner = norm(input.owner || "belentani7");
  if (!/^[A-Za-z0-9-]{1,39}$/.test(owner)) {
    throw new Error("Propietario inválido en el inventario.");
  }
  const mode = input.live_authenticated === true &&
    input.inventory_scope === "authenticated_live_github" ? "live" : "snapshot";
  const seen = new Set();
  const rows = input.repositories.map((entry, index) => {
    if (!isObject(entry)) throw new Error(`Fila ${index + 1}: objeto inválido.`);
    const fullName = norm(entry.full_name);
    const pieces = fullName.split("/");
    if (pieces.length !== 2 || pieces[0].toLowerCase() !== owner.toLowerCase() ||
        !/^[\w.-]{1,100}$/.test(pieces[1])) {
      throw new Error(`Fila ${index + 1}: nombre de repositorio inválido.`);
    }
    const key = fullName.toLowerCase();
    if (seen.has(key)) throw new Error(`Repositorio duplicado: ${fullName}.`);
    seen.add(key);
    const category = norm(entry.category_hint);
    const status = norm(entry.status) || (bool(entry.archived) ? "archived_in_snapshot" : "unverified_snapshot");
    const checked = mode === "live" && status === "manual_product_validation_required";
    return {
      name: pieces[1], full_name: fullName, archived: bool(entry.archived),
      private: entry.private !== false, branch: norm(entry.default_branch) || "desconocida",
      category: KNOWN_CATEGORIES.has(category) ? category : "unclassified",
      status, checked, missing: checked && Array.isArray(entry.missing)
        ? entry.missing.filter(x => typeof x === "string").slice(0, 25) : [],
      ready: false, // A file cannot authorize production or prove full completeness.
      declared_authorized: bool(entry.release_authorized),
      purpose_verified: mode === "live" && bool(entry.purpose_verified),
      content_verified: mode === "live" && bool(entry.content_verified),
      deployed_verified: mode === "live" && bool(entry.deployed_verified),
    };
  });
  const total = input.total_visible ?? input.total;
  if (total !== undefined && total !== rows.length) {
    throw new Error("El total declarado no coincide con las filas.");
  }
  return { owner, mode, rows, generated: norm(input.generated_at || input.source),
    scope: mode === "live" ? "Inventario autenticado · no certifica productos" :
      "Instantánea histórica · sin verificación en vivo" };
}
export function summarize(rows) {
  return {
    total: rows.length,
    active: rows.filter(x => !x.archived).length,
    archived: rows.filter(x => x.archived).length,
    private: rows.filter(x => x.private).length,
    public: rows.filter(x => !x.private).length,
    codeChecked: rows.filter(x => x.checked).length,
    fullyReleased: 0,
  };
}
export function selectRows(rows, {query = "", state = "all", category = "all", order = "name"} = {}) {
  const q = norm(query).toLocaleLowerCase();
  const filtered = rows.filter(r => (
    (!q || r.full_name.toLocaleLowerCase().includes(q)) &&
    (state === "all" || (state === "active" ? !r.archived : r.archived)) &&
    (category === "all" || r.category === category)
  ));
  return filtered.sort((a,b) => {
    if (order === "status") return Number(a.archived) - Number(b.archived) || a.name.localeCompare(b.name);
    if (order === "category") return a.category.localeCompare(b.category) || a.name.localeCompare(b.name);
    return a.name.localeCompare(b.name);
  });
}
