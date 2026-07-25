import { loginUser } from "../api.js";
import { clearFieldError, qs, setButtonLoading, showFieldError } from "../dom.js";
import { initNav } from "../auth.js";

initNav();

const form = qs("#login-form");
const params = new URLSearchParams(window.location.search);
const next = params.get("next") || "index.html";

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearFieldError(form);

  const formData = new FormData(form);
  const submitButton = qs("button[type=submit]", form);
  setButtonLoading(submitButton, true, "Logging in…");

  try {
    await loginUser({
      username: formData.get("username").trim(),
      password: formData.get("password"),
    });
    window.location.href = next;
  } catch (error) {
    showFieldError(form, error.message);
  } finally {
    setButtonLoading(submitButton, false);
  }
});
