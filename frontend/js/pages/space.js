import { createBooking, fetchSpace, isLoggedIn } from "../api.js";
import {
  clearFieldError,
  qs,
  renderSpaceDetail,
  setButtonLoading,
  showFieldError,
  showToast,
} from "../dom.js";
import { initNav } from "../auth.js";

initNav();

const params = new URLSearchParams(window.location.search);
const slug = params.get("slug");

const detailContainer = qs("#space-detail");
const bookingForm = qs("#booking-form");
const bookingPrompt = qs("#booking-login-prompt");
const dateInput = qs("#booking-date");

dateInput.min = new Date().toISOString().split("T")[0];

if (!isLoggedIn()) {
  bookingForm.hidden = true;
  bookingPrompt.hidden = false;
}

let currentSpace = null;

async function loadSpace() {
  if (!slug) {
    detailContainer.innerHTML = `<p class="empty-state">No space was specified.</p>`;
    return;
  }
  try {
    currentSpace = await fetchSpace(slug);
    renderSpaceDetail(detailContainer, currentSpace);
  } catch (error) {
    detailContainer.innerHTML = `<p class="empty-state">${error.message}</p>`;
  }
}

bookingForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearFieldError(bookingForm);

  const formData = new FormData(bookingForm);
  const submitButton = qs("button[type=submit]", bookingForm);
  setButtonLoading(submitButton, true, "Booking…");

  try {
    await createBooking({
      spaceSlug: currentSpace.slug,
      date: formData.get("date"),
      startTime: formData.get("start_time"),
      endTime: formData.get("end_time"),
    });
    showToast("Booking confirmed. See you there!", "success");
    window.location.href = "my-bookings.html";
  } catch (error) {
    showFieldError(bookingForm, error.message);
  } finally {
    setButtonLoading(submitButton, false);
  }
});

loadSpace();
