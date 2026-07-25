# API Catalog — Coworking Space Booking Platform

Complete reference for every endpoint the backend exposes.

- **Base URL:** `http://127.0.0.1:8000/api` locally, or `https://<username>.pythonanywhere.com/api` once deployed — see [Hosting it online](README.md#hosting-it-online)
- **Interactive docs:** `/swagger/` · `/redoc/`
- **Raw schema:** `GET /swagger.json` (or `/swagger.yaml`)
- **Format:** JSON in, JSON out (the one exception is uploading a space image — see [Spaces](#3-spaces))

Every path below is relative to the base URL. `GET /spaces/` means
`GET http://127.0.0.1:8000/api/spaces/` locally.

---

## Table of contents

1. [Authentication](#1-authentication)
2. [Conventions](#2-conventions) — pagination, errors, date/time formats
3. [Spaces](#3-spaces)
4. [Bookings](#4-bookings)
5. [Payments](#5-payments)
6. [Booking lifecycle](#6-booking-lifecycle)
7. [Business rules](#7-business-rules)
8. [Reference tables](#8-reference-tables)

---

## 1. Authentication

The API is **JWT-only** — there is no session or cookie auth. Send the access
token on every protected request:

```
Authorization: Bearer <access_token>
```

Token lifetimes: **access = 60 minutes**, **refresh = 7 days**. Refresh tokens
rotate, so `/auth/refresh/` returns a *new* refresh token alongside the access
token — store both.

> **In Swagger UI:** click **Authorize** 🔒 and type the word `Bearer`, a space,
> then the token. The `Bearer` prefix is part of the value.

### `POST /auth/register/`

Create a new account. Public.

**Request**
```json
{
  "username": "sara",
  "email": "sara@example.com",
  "phone_number": "+201234567890",
  "password": "StrongPass123",
  "password_confirm": "StrongPass123"
}
```

`phone_number` is optional. Password must be at least 8 characters and pass
Django's validators (not too common, not all-numeric, not similar to the
username).

**Response `201`**
```json
{ "id": 3, "username": "sara", "email": "sara@example.com", "phone_number": "+201234567890" }
```

**Errors** — `400` if the username or email is taken, the passwords differ
(`password_confirm`), or the password is too weak.

New accounts are regular members: `is_staff = false`, `is_space_owner = false`.

---

### `POST /auth/login/`

Exchange credentials for a token pair. Public.

**Request**
```json
{ "username": "sara", "password": "StrongPass123" }
```

**Response `200`**
```json
{ "refresh": "eyJhbGciOi...", "access": "eyJhbGciOi..." }
```

**Errors** — `401 {"detail": "No active account found with the given credentials"}`
for a wrong username/password, or for a deactivated account.

---

### `POST /auth/refresh/`

Trade a valid refresh token for a fresh pair. Public.

**Request**
```json
{ "refresh": "eyJhbGciOi..." }
```

**Response `200`**
```json
{ "access": "eyJhbGciOi...", "refresh": "eyJhbGciOi..." }
```

**Errors** — `401` if the refresh token is expired, malformed, or already
rotated out.

---

### `GET /auth/me/`

The authenticated user's own profile. Requires a token.

**Response `200`**
```json
{
  "id": 1,
  "username": "Abdulrahman_Salem",
  "email": "admin@example.com",
  "phone_number": "",
  "is_space_owner": true,
  "date_joined": "2026-07-19T13:51:12+03:00"
}
```

Every field is read-only — this endpoint does not update the profile.

---

## 2. Conventions

### Pagination

List endpoints return **12 items per page**, wrapped like this:

```json
{
  "count": 37,
  "next": "http://127.0.0.1:8000/api/spaces/?page=2",
  "previous": null,
  "results": [ … ]
}
```

Move between pages with `?page=2`. Two endpoints are **not** paginated and
return a bare array: `GET /spaces/choices/` and `GET /auth/me/`.

### Errors

Field-level problems come back keyed by field name:

```json
{ "end_time": ["End time must be after start time."] }
```

Rule violations that aren't tied to one field use `non_field_errors`:

```json
{ "non_field_errors": ["This space is already booked for an overlapping time slot on that date."] }
```

Auth and permission failures use `detail`:

```json
{ "detail": "Authentication credentials were not provided." }
```

| Code | Meaning |
|---|---|
| `200` | OK |
| `201` | Created |
| `204` | Deleted — empty body |
| `400` | Validation failed |
| `401` | Missing, malformed, or expired token |
| `403` | Authenticated, but not allowed to do this |
| `404` | Doesn't exist — **or** exists but isn't yours (see note below) |

> A booking you don't own returns `404`, not `403`. The queryset is filtered per
> user before permissions run, so other people's bookings are invisible rather
> than forbidden.

### CORS — using this API from your own project

The API accepts browser requests from **any origin**. Drop it straight into
your own frontend on any host or port — no backend of your own needed:

```js
const API = "https://username.pythonanywhere.com/api";   // the deployed URL

const res = await fetch(`${API}/spaces/`);
const data = await res.json();
```

> A locally-run API lives at `http://127.0.0.1:8000` — an address that only
> exists on the machine running it. For other people to reach it, it has to be
> deployed; see [Hosting it online](README.md#hosting-it-online).
>
> Call the API over **https** from an https page — browsers block an https page
> from calling a plain http endpoint.

Authenticated calls work the same way — the token goes in a header:

```js
const res = await fetch(`${API}/bookings/`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${accessToken}`,
  },
  body: JSON.stringify({
    space: "space-1",
    date: "2026-07-26",
    start_time: "09:00",
    end_time: "11:00",
  }),
});
```

Do **not** set `credentials: "include"` — this API never uses cookies, and
credentialed mode is incompatible with the wildcard origin. The bearer token is
all the auth it needs.

CORS restricts browsers only. Server-side clients — `curl`, Postman, Python,
another backend — were never affected by it.

To restrict origins later, set `CORS_ALLOWED_ORIGINS` in `backend/.env` to a
comma-separated list; leaving it empty keeps the API open.

### Dates and times

| Field | Format | Example |
|---|---|---|
| `date` | `YYYY-MM-DD` | `2026-07-26` |
| `start_time` / `end_time` | send `HH:MM` (24-hour); returned as `HH:MM:SS` | send `09:00` → read back `09:00:00` |
| `created_at` / `paid_at` | ISO 8601 with offset | `2026-07-26T00:32:13+03:00` |

Times are **wall-clock at the venue** — they carry no timezone and are compared
against the server's `TIME_ZONE` (set in `backend/.env`, defaults to
`Africa/Cairo`). Midnight is `00:00`, noon is `12:00`.

---

## 3. Spaces

A bookable room or desk. Reading is public; writing requires **staff** or an
account with `is_space_owner = true`.

### `GET /spaces/`

Browse active spaces. Public. Paginated.

| Query param | Effect |
|---|---|
| `search` | Matches `name` or `description` |
| `capacity` | Exact seat count |
| `ordering` | `price_per_hour`, `capacity`, `created_at` — prefix with `-` to reverse |
| `page` | Page number |

**Example** — cheapest 6-seaters first:
```
GET /spaces/?capacity=6&ordering=price_per_hour
```

**Response `200`**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Space 1",
      "slug": "space-1",
      "description": "A calm, well-lit room.",
      "capacity": 8,
      "price_per_hour": "50.00",
      "image": "http://127.0.0.1:8000/media/spaces/images.jpeg",
      "is_active": true,
      "created_at": "2026-07-20T00:56:09.721514+03:00"
    }
  ]
}
```

Inactive spaces (`is_active = false`) never appear in this list and cannot be
booked.

---

### `GET /spaces/choices/`

Every active space as `{slug, name}` — no pagination, no auth. Built for filling
a dropdown or for looking up the slug you need when creating a booking.

**Response `200`**
```json
[
  { "slug": "space-1", "name": "Space 1" },
  { "slug": "space-2", "name": "Space 2" }
]
```

---

### `GET /spaces/{slug}/`

One space by slug. Public.

**Example** — `GET /spaces/space-1/`. Returns the same object shape as a row in
the list above. `404` if the slug doesn't exist or the space is inactive.

---

### `POST /spaces/`

Create a space. **Staff or space owner only.**

**Request**
```json
{
  "name": "Creative Hub",
  "description": "Corner room with a whiteboard wall.",
  "capacity": 6,
  "price_per_hour": "40.00",
  "is_active": true
}
```

`slug` is generated from `name` automatically — don't send it.

To attach an image, send the request as `multipart/form-data` with an `image`
file part instead of JSON.

**Response `201`** — the created space, including its generated `slug`.

**Errors** — `403` for regular members. `400` if `capacity < 1` or
`price_per_hour < 0`.

---

### `PUT /spaces/{slug}/` · `PATCH /spaces/{slug}/`

Update a space. **Staff or space owner only.** `PUT` replaces every writable
field; `PATCH` updates only what you send.

**Example** — take a space offline without deleting it:
```json
PATCH /spaces/space-2/
{ "is_active": false }
```

> Renaming a space does **not** regenerate its slug — the slug is only derived
> on first save, so existing links and bookings keep working.

---

### `DELETE /spaces/{slug}/`

Permanently delete a space. **Staff or space owner only.** Response `204`.

> **This cascades.** Every booking for that space — and every payment attached
> to those bookings — is deleted with it. To retire a space while keeping its
> history, `PATCH` it to `is_active: false` instead.

---

## 4. Bookings

A reservation of one space for a date and time window. **All booking endpoints
require authentication.** Members see only their own bookings; staff see
everyone's.

### `GET /bookings/`

List bookings. Paginated.

| Query param | Effect |
|---|---|
| `status` | `pending`, `confirmed`, `checked_in`, `checked_out`, `cancelled` |
| `space` | Space **numeric ID** — note this differs from creation, which takes the slug. Passing a slug here returns `400` |
| `date` | Exact date, `YYYY-MM-DD` |
| `page` | Page number |

**Response `200`**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 11,
      "space": "space-2",
      "space_detail": {
        "id": 2,
        "name": "Space 2",
        "slug": "space-2",
        "description": "",
        "capacity": 4,
        "price_per_hour": "20.00",
        "image": null,
        "is_active": true,
        "created_at": "2026-07-20T01:10:00+03:00"
      },
      "user": 1,
      "date": "2026-07-26",
      "start_time": "00:24:00",
      "end_time": "01:00:00",
      "status": "checked_out",
      "payment": {
        "id": 4,
        "booking": 11,
        "method": "credit_card",
        "amount": "12.00",
        "paid_at": "2026-07-26T00:32:13.081Z"
      },
      "created_at": "2026-07-26T00:24:51+03:00"
    }
  ]
}
```

`space_detail` is the full nested space, so listing bookings needs no follow-up
request. `payment` is `null` until check-out.

---

### `POST /bookings/`

Reserve a space.

**Request** — only these four fields; everything else is derived:
```json
{
  "space": "space-1",
  "date": "2026-07-26",
  "start_time": "09:00",
  "end_time": "11:00"
}
```

`space` is the **slug**, not the numeric ID — get it from
[`GET /spaces/choices/`](#get-spaceschoices).

**Response `201`** — the full booking object. Take `id` from it; you'll need it
for check-in and check-out.

The new booking starts as `pending`, owned by whoever's token you sent. You
cannot book on another user's behalf.

**Errors `400`**

| Message | Cause |
|---|---|
| `"This space is already booked for an overlapping time slot on that date."` | Clashes with a non-cancelled booking |
| `"End time must be after start time."` | `end_time` ≤ `start_time` |
| `"You cannot book a date in the past."` | `date` is before today |
| `"Object with slug=… does not exist."` | Unknown slug, or the space is inactive |

---

### `GET /bookings/{id}/`

One booking, same shape as a list row. `404` if it isn't yours (unless you're
staff).

---

### `PUT /bookings/{id}/` · `PATCH /bookings/{id}/`

Reschedule a booking you own. Accepts the same four writable fields as creation
and re-runs every validation, including the overlap check — which correctly
ignores the booking being edited.

```json
PATCH /bookings/11/
{ "start_time": "10:00", "end_time": "12:00" }
```

`status` cannot be changed here — it's read-only on this serializer. Use
[`/status/`](#patch-bookingsidstatus), [`/check-in/`](#post-bookingsidcheck-in)
or [`/check-out/`](#post-bookingsidcheck-out).

---

### `DELETE /bookings/{id}/`

Response `204`.

> **This deletes the row outright** — it does not set the status to `cancelled`.
> The booking disappears from history, and its payment (if any) goes with it. To
> keep the record and just free the slot, have an admin
> `PATCH /bookings/{id}/status/` to `cancelled` instead.

---

### `PATCH /bookings/{id}/status/`

**Admin only** (`is_staff`). Confirm or cancel a booking.

**Request**
```json
{ "status": "confirmed" }
```

Accepts `pending`, `confirmed`, `cancelled` only.

**Errors** — `403` for non-admins. `400` if you pass `checked_in` or
`checked_out`: *"Use the check-in/check-out endpoints to move a booking to that
status."* Those two transitions enforce timing and payment rules that a plain
status write would bypass.

---

### `POST /bookings/{id}/check-in/`

Mark arrival. **No request body** — the booking ID in the path is the whole
request.

**Response `200`** — the booking, now `checked_in`.

**Errors `400`**

| Message | Cause |
|---|---|
| `"Check-in isn't open yet — it becomes available at the booking's start time."` | You're early |
| `"Cannot check in a booking with status 'checked_out'."` | Only `pending` or `confirmed` can check in |

The gate compares *now* against the booking's `date` + `start_time` interpreted
in the server's `TIME_ZONE`. If check-in seems to open at the wrong hour, that
setting is pointing at the wrong zone.

---

### `POST /bookings/{id}/check-out/`

End the session and record payment. The booking must be `checked_in`.

**Request**
```json
{ "payment_method": "credit_card" }
```

Valid values: `cash`, `credit_card`, `debit_card`, `wallet`, `bank_transfer`.

**Response `200`** — the booking, now `checked_out`, with `payment` populated.

**The amount is calculated server-side and cannot be set by the client:**

```
amount = space.price_per_hour × booked_hours
```

where `booked_hours = end_time − start_time`. A 2-hour booking of a $50/hr space
is `$100.00`. Rounded to 2 decimal places.

**Errors** — `400 "Cannot check out a booking with status 'pending'. It must be
checked in first."`, or `400` on `payment_method` if the value isn't one of the
five.

---

## 5. Payments

Created automatically at check-out. There is no endpoint to create, edit or
delete a payment — the record is immutable once written.

### `GET /payments/`

Your payment history. Staff see every payment. Paginated.

**Response `200`**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    { "id": 4, "booking": 11, "method": "credit_card", "amount": "12.00", "paid_at": "2026-07-26T00:32:13.081Z" }
  ]
}
```

### `GET /payments/{id}/`

A single payment. `404` if it belongs to someone else's booking.

---

## 6. Booking lifecycle

```
      POST /bookings/
            │
            ▼
        ┌─────────┐   PATCH /status/    ┌───────────┐
        │ pending │ ──────────────────► │ confirmed │
        └────┬────┘                     └─────┬─────┘
             │                                │
             └────────────┬───────────────────┘
                          │  POST /check-in/
                          │  (only once start_time has passed)
                          ▼
                   ┌────────────┐
                   │ checked_in │
                   └──────┬─────┘
                          │  POST /check-out/  {payment_method}
                          │  → creates the Payment
                          ▼
                  ┌─────────────┐
                  │ checked_out │   terminal
                  └─────────────┘

  pending / confirmed ──PATCH /status/──► cancelled   (frees the time slot)
```

Every status except `cancelled` holds the time slot against other bookings.

---

## 7. Business rules

**Double-booking is impossible.** Two bookings clash when they share a space and
date and their time ranges overlap (`start < other_end` and `end > other_start`).
The check runs twice — once in the serializer, then again in the model's
`clean()` at save time — so a race between two simultaneous requests still can't
produce an overlap. A `cancelled` booking releases its slot; every other status
holds it.

**Amounts are never client-supplied.** The check-out endpoint accepts only the
payment *method*. The figure charged is computed from the space's rate and the
booked duration, so a client cannot underpay by sending its own number.

**Check-in can't be early.** The endpoint compares the current time to the
booking's start. This is the one piece of behaviour that depends on `TIME_ZONE`
being correct for the venue's actual location.

**Ownership is enforced by filtering, not just by permission checks.** The
booking queryset is narrowed to `request.user` before object permissions are
consulted, which is why someone else's booking reads as `404`.

**Writing spaces is gated on a role, not on ownership.** `is_staff` or
`is_space_owner` may create and edit *any* space — there's no per-space owner
column.

---

## 8. Reference tables

### Booking statuses

| Value | Meaning | Holds the slot? |
|---|---|---|
| `pending` | Created, not yet confirmed | Yes |
| `confirmed` | Approved by an admin | Yes |
| `checked_in` | Member has arrived | Yes |
| `checked_out` | Session finished and paid | Yes |
| `cancelled` | Called off | **No** |

### Payment methods

| Value | Label |
|---|---|
| `cash` | Cash |
| `credit_card` | Credit Card |
| `debit_card` | Debit Card |
| `wallet` | Digital Wallet |
| `bank_transfer` | Bank Transfer |

Always send the left-hand value — `credit_card`, never `Credit Card`.

### Permissions at a glance

| Endpoint | Anonymous | Member | Space owner | Staff |
|---|:--:|:--:|:--:|:--:|
| `POST /auth/register/`, `/login/`, `/refresh/` | ✅ | ✅ | ✅ | ✅ |
| `GET /auth/me/` | ❌ | ✅ | ✅ | ✅ |
| `GET /spaces/`, `/spaces/{slug}/`, `/spaces/choices/` | ✅ | ✅ | ✅ | ✅ |
| `POST` `PUT` `PATCH` `DELETE /spaces/` | ❌ | ❌ | ✅ | ✅ |
| `GET` `POST /bookings/` | ❌ | own | own | all |
| `PUT` `PATCH` `DELETE /bookings/{id}/` | ❌ | own | own | all |
| `PATCH /bookings/{id}/status/` | ❌ | ❌ | ❌ | ✅ |
| `POST /bookings/{id}/check-in/`, `/check-out/` | ❌ | own | own | all |
| `GET /payments/`, `/payments/{id}/` | ❌ | own | own | all |

"own" = limited to the requester's own records.

---

## Worked example — booking to payment

```bash
# 1. Log in
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"sara","password":"StrongPass123"}'
# → {"refresh":"…","access":"eyJhbGci…"}

TOKEN="eyJhbGci…"

# 2. Find a space
curl http://127.0.0.1:8000/api/spaces/choices/
# → [{"slug":"space-1","name":"Space 1"}]

# 3. Book it
curl -X POST http://127.0.0.1:8000/api/bookings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"space":"space-1","date":"2026-07-26","start_time":"09:00","end_time":"11:00"}'
# → {"id":12, "status":"pending", …}   ← keep the id

# 4. Check in (only works from 09:00 onward)
curl -X POST http://127.0.0.1:8000/api/bookings/12/check-in/ \
  -H "Authorization: Bearer $TOKEN"
# → {"id":12, "status":"checked_in", …}

# 5. Check out and pay — 2 hours × $50/hr = $100.00
curl -X POST http://127.0.0.1:8000/api/bookings/12/check-out/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"payment_method":"cash"}'
# → {"id":12, "status":"checked_out", "payment":{"amount":"100.00","method":"cash", …}}
```
