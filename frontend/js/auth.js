/**
 * auth.js — wires the shared navbar (login/register vs. greeting/logout)
 * and guards pages that require a session. Every page imports this.
 */

import { getUsername, isLoggedIn, logoutUser } from "./api.js";
import { qs, renderNavAuthState } from "./dom.js";

export function initNav() {
  renderNavAuthState(isLoggedIn(), getUsername());

  qs("#nav-logout")?.addEventListener("click", (event) => {
    event.preventDefault();
    logoutUser();
    window.location.href = "index.html";
  });
}

/** Redirects to the login page (preserving the current URL) if no session exists. */
export function requireAuth() {
  if (isLoggedIn()) return true;
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  window.location.href = `login.html?next=${next}`;
  return false;
}
