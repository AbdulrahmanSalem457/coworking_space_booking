/**
 * dom.js — every direct DOM read/write lives here so page scripts stay
 * declarative (fetch data, then hand it to a render function).
 */

import { PAYMENT_METHODS } from "./api.js";

export const qs = (selector, scope = document) => scope.querySelector(selector);
export const qsa = (selector, scope = document) => [...scope.querySelectorAll(selector)];

export function formatMoney(value) {
  return `$${Number(value).toFixed(2)}`;
}

export function formatTime(value) {
  const [hours, minutes] = value.split(":");
  const date = new Date();
  date.setHours(Number(hours), Number(minutes));
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function formatDate(value) {
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ---------------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------------

export function showToast(message, type = "info") {
  let container = qs("#toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add("toast--visible"));
  setTimeout(() => {
    toast.classList.remove("toast--visible");
    toast.addEventListener("transitionend", () => toast.remove(), { once: true });
  }, 4000);
}

// ---------------------------------------------------------------------------
// Navbar (shared across every page)
// ---------------------------------------------------------------------------

export function renderNavAuthState(isLoggedIn, username) {
  const guestLinks = qs("#nav-guest-links");
  const userLinks = qs("#nav-user-links");
  if (!guestLinks || !userLinks) return;

  guestLinks.hidden = isLoggedIn;
  userLinks.hidden = !isLoggedIn;

  const greeting = qs("#nav-username", userLinks);
  if (greeting && username) greeting.textContent = `Hi, ${username}`;
}

// ---------------------------------------------------------------------------
// Space cards / grid
// ---------------------------------------------------------------------------

export function renderSpaceGrid(container, spaces) {
  container.innerHTML = "";

  if (spaces.length === 0) {
    container.innerHTML = `<p class="empty-state">No spaces match your search just yet. Try widening your filters.</p>`;
    return;
  }

  for (const space of spaces) {
    const card = document.createElement("article");
    card.className = "space-card";
    card.innerHTML = `
      <div class="space-card__image" ${space.image ? `style="background-image:url('${space.image}')"` : ""}>
        ${space.image ? "" : `<span class="space-card__placeholder">🌿</span>`}
      </div>
      <div class="space-card__body">
        <h3 class="space-card__title">${space.name}</h3>
        <p class="space-card__meta">Seats up to ${space.capacity} · ${formatMoney(space.price_per_hour)}/hr</p>
        <p class="space-card__desc">${space.description || "A calm, well-lit space ready to book."}</p>
        <a class="btn btn--primary" href="space.html?slug=${encodeURIComponent(space.slug)}">View &amp; Book</a>
      </div>
    `;
    container.appendChild(card);
  }
}

// ---------------------------------------------------------------------------
// Space detail
// ---------------------------------------------------------------------------

export function renderSpaceDetail(container, space) {
  container.innerHTML = `
    <div class="space-detail__image" ${space.image ? `style="background-image:url('${space.image}')"` : ""}>
      ${space.image ? "" : `<span class="space-card__placeholder">🌿</span>`}
    </div>
    <div class="space-detail__info">
      <h1>${space.name}</h1>
      <p class="space-detail__meta">Seats up to ${space.capacity} people · ${formatMoney(space.price_per_hour)} / hour</p>
      <p class="space-detail__desc">${space.description || "A calm, well-lit space ready to book."}</p>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Bookings list
// ---------------------------------------------------------------------------

const STATUS_LABELS = {
  pending: "Pending",
  confirmed: "Confirmed",
  checked_in: "Checked In",
  checked_out: "Checked Out",
  cancelled: "Cancelled",
};

const PAYMENT_METHOD_LABELS = Object.fromEntries(PAYMENT_METHODS.map((m) => [m.value, m.label]));

function paymentMethodOptionsHtml() {
  return PAYMENT_METHODS.map((m) => `<option value="${m.value}">${m.label}</option>`).join("");
}

/**
 * onCancel(id), onCheckIn(id), onCheckOut(id, paymentMethod) are called with
 * the booking id (and, for check-out, the chosen payment method value).
 */
export function renderBookingsList(container, bookings, { onCancel, onCheckIn, onCheckOut }) {
  container.innerHTML = "";

  if (bookings.length === 0) {
    container.innerHTML = `<p class="empty-state">You haven't booked a space yet — go find one you like.</p>`;
    return;
  }

  for (const booking of bookings) {
    const row = document.createElement("article");
    row.className = "booking-card";

    let actionsHtml = "";
    if (booking.status === "pending" || booking.status === "confirmed") {
      actionsHtml = `
        <button class="btn btn--primary btn--small" data-action="check-in">Check In</button>
        <button class="btn btn--ghost btn--small" data-action="cancel">Cancel</button>
      `;
    } else if (booking.status === "checked_in") {
      actionsHtml = `
        <select class="payment-method-select" aria-label="Payment method">
          ${paymentMethodOptionsHtml()}
        </select>
        <button class="btn btn--primary btn--small" data-action="check-out">Check Out</button>
      `;
    } else if (booking.status === "checked_out" && booking.payment) {
      actionsHtml = `
        <span class="payment-summary">
          Paid ${formatMoney(booking.payment.amount)} via ${PAYMENT_METHOD_LABELS[booking.payment.method] ?? booking.payment.method}
        </span>
      `;
    }

    row.innerHTML = `
      <div class="booking-card__info">
        <h3>${booking.space_detail?.name ?? "Space"}</h3>
        <p>${formatDate(booking.date)} · ${formatTime(booking.start_time)} – ${formatTime(booking.end_time)}</p>
      </div>
      <div class="booking-card__actions">
        <span class="badge badge--${booking.status}">${STATUS_LABELS[booking.status] ?? booking.status}</span>
        ${actionsHtml}
      </div>
    `;

    row.querySelector('[data-action="cancel"]')?.addEventListener("click", () => onCancel(booking.id));
    row.querySelector('[data-action="check-in"]')?.addEventListener("click", () => onCheckIn(booking.id));
    row.querySelector('[data-action="check-out"]')?.addEventListener("click", () => {
      const method = row.querySelector(".payment-method-select").value;
      onCheckOut(booking.id, method);
    });

    container.appendChild(row);
  }
}

// ---------------------------------------------------------------------------
// Form helpers
// ---------------------------------------------------------------------------

export function showFieldError(form, message) {
  let errorEl = qs(".form-error", form);
  if (!errorEl) {
    errorEl = document.createElement("p");
    errorEl.className = "form-error";
    form.prepend(errorEl);
  }
  errorEl.textContent = message;
}

export function clearFieldError(form) {
  qs(".form-error", form)?.remove();
}

export function setButtonLoading(button, isLoading, loadingText = "Please wait…") {
  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.textContent = loadingText;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
  }
}
