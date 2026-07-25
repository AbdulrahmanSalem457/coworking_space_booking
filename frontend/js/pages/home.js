import { fetchSpaces } from "../api.js";
import { qs, renderSpaceGrid, showToast } from "../dom.js";
import { initNav } from "../auth.js";

initNav();

const grid = qs("#space-grid");
const filterForm = qs("#filter-form");

async function loadSpaces(params = {}) {
  grid.innerHTML = `<p class="empty-state">Loading spaces…</p>`;
  try {
    const data = await fetchSpaces(params);
    renderSpaceGrid(grid, data.results ?? data);
  } catch (error) {
    grid.innerHTML = "";
    showToast(error.message, "error");
  }
}

filterForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(filterForm);
  loadSpaces({
    search: formData.get("search")?.trim() ?? "",
    capacity: formData.get("capacity") ?? "",
  });
});

loadSpaces();
