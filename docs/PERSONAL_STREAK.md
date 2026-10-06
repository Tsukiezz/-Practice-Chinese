# Personal learning streak

The Personal (Cá nhân) page shows a compact row that opens a separate screen with current and
longest chain, distinct learning-day count, next milestone, 28-day rolling
calendar, today's activity, and Premium freeze allowance. All dates use UTC+7.

The header flame next to the theme button shows the server streak count; zero is
neutral, positive counts are orange, with brighter milestone colors at 7/30 days.
It also opens the detail screen. Refresh occurs on tab changes, return from detail,
and once per minute while mounted. A failed fetch shows an unknown count, not zero.
The home clock updates every second in UTC+7. Greeting is morning from 06:00 to
17:59 and evening from 18:00 to 05:59, independent of the device timezone.

Pronunciation reading now uses the same `/reading` UI for HSK 1–9. Advanced levels
require active server-verified Premium. Each currently has six words and two
example sentences from the original advanced lesson catalog, not a full HSK
vocabulary corpus. The 22-topic filter applies to the existing HSK 1–6 corpus.

`GET /api/me/dashboard` returns `streak_details` for the authenticated user only.
Existing `streak` remains compatible. Learned and protected days are separate;
freeze days sustain chains without increasing real learning-day totals. Opening
the profile never records learning. Yesterday's chain remains valid until today
ends. Existing monthly Premium protection limits remain unchanged.

Dictionary lookups preserve previous lookup dates before updating the per-word
history entry. Historical activity no longer available in the database cannot be
reconstructed; the card reports retained evidence, not invented study days.

Validation: backend tests cover UTC+7 dates, duplicate days, empty histories,
freeze separation, dictionary repeat lookups, private dashboard access, and AI
support knowledge. Widget tests cover mobile rendering, refresh and free state.
`smoke_premium_benefits.py` checks the real web dashboard response after navigating
to Personal and captures desktop/mobile screenshots under ignored test-results.
