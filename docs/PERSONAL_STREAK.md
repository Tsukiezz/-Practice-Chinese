# Personal learning streak

The Personal (Cá nhân) page shows a server-derived streak card with current and
longest chain, distinct learning-day count, next milestone, 28-day rolling
calendar, today's activity, and Premium freeze allowance. All dates use UTC+7.

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
