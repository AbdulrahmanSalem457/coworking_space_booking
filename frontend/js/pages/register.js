import { registerUser } from "../api.js";
import { clearFieldError, qs, setButtonLoading, showFieldError } from "../dom.js";
import { initNav } from "../auth.js";

initNav();

const form = qs("#register-form");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearFieldError(form);

  const formData = new FormData(form);
  const password = formData.get("password");
  const passwordConfirm = formData.get("password_confirm");

  if (password !== passwordConfirm) {
    showFieldError(form, "Passwords do not match.");
    return;
  }

  const submitButton = qs("button[type=submit]", form);
  setButtonLoading(submitButton, true, "Creating account…");

  try {
    await registerUser({
      username: formData.get("username").trim(),
      email: formData.get("email").trim(),
      password,
      passwordConfirm,
    });
    window.location.href = "login.html";
  } catch (error) {
    showFieldError(form, error.message);
  } finally {
    setButtonLoading(submitButton, false);
  }
});
