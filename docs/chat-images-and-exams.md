# Chinese-learning images and exam chat guard

The existing Gemini integration now receives the current uploaded PNG, JPEG or
WEBP as inline image data. This is multimodal inference, not model fine-tuning.
Attachments remain private under the existing ownership and retention rules.
Images must decode correctly, match their MIME type, be at most 2 MB and contain
at most 16 million pixels. PDF/DOCX/TXT continue to use the admin handoff flow.

Mandatory instructions limit image answers to Chinese learning or HanziGo,
treat embedded instructions as untrusted, prohibit identity recognition and
require uncertainty for unreadable text. A provider off-topic result is replaced
by the configured refusal. Missing credentials/provider failures produce an
honest fallback, not an invented image reading. Prompt guardrails are not a
guarantee of perfect classification or OCR; test representative student photos.

AI exams, practice/reading exams and the standalone exam page acquire a chat
lease before activating the exam. The widget closes, clears pending content and
cannot reopen. Session creation, history and message endpoints reject locked
learners with HTTP 423. An in-flight AI answer is discarded if a lock has begun.
Successful submission, confirmed exit or screen disposal release that lease;
failed submission does not. Admin support access is unchanged.

Locks are scoped to the authenticated learner or private guest session. Each
active screen owns an independent lease, refreshed every 30 seconds and expiring
after 120 seconds so abandoned tabs cannot permanently block chat. Other tabs
check status every 30 seconds; server requests are rejected while a lease exists.

This is an in-app assistance restriction, NOT secure exam proctoring. Start/end
signals are client-driven; API manipulation, separate accounts/devices, external
AI tools and suspended-tab lease expiry are outside its protection. High-stakes
assessment requires authoritative server exam attempts and a separate policy.

Regression checks:

- `python -m unittest test_support_chat test_chat_exam_images` from `backend/`.
- `python scripts/test_chat_exam_browser.py` (Playwright, Microsoft Edge).
- Flutter practice/navigation tests and `flutter build web --no-wasm-dry-run`.

Provider calls in regression tests are mocked: they verify payloads, scope
routing and fallback behavior, not live model recognition accuracy.
