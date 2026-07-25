import { cancelBooking, checkInBooking, checkOutBooking, fetchMyBookings } from "../api.js";
import { qs, renderBookingsList, showToast } from "../dom.js";
import { initNav, requireAuth } from "../auth.js";

initNav();

if (requireAuth()) {
  const list = qs("#bookings-list");

  async function loadBookings() {
    list.innerHTML = `<p class="empty-state">Loading your bookings…</p>`;
    try {
      const data = await fetchMyBookings();
      renderBookingsList(list, data.results ?? data, {
        onCancel: handleCancel,
        onCheckIn: handleCheckIn,
        onCheckOut: handleCheckOut,
      });
    } catch (error) {
      list.innerHTML = "";
      showToast(error.message, "error");
    }
  }

  async function handleCancel(id) {
    if (!confirm("Cancel this booking?")) return;
    try {
      await cancelBooking(id);
      showToast("Booking cancelled.", "success");
      loadBookings();
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function handleCheckIn(id) {
    try {
      await checkInBooking(id);
      showToast("Checked in. Enjoy your space!", "success");
      loadBookings();
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function handleCheckOut(id, paymentMethod) {
    try {
      await checkOutBooking(id, paymentMethod);
      showToast("Checked out and payment recorded.", "success");
      loadBookings();
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  loadBookings();
}
