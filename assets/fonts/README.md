# HanziGo HSK font

Derived from Noto Sans SC, Google Fonts / the Noto project:
https://github.com/google/fonts/tree/main/ofl/notosanssc

License: SIL Open Font License 1.1, see OFL.txt (also bundled as an application asset).
Modified for HanziGo: instantiated at weight 400, subset to the bundled HSK corpus,
UI/source text and Latin/Vietnamese/punctuation ranges, renamed HanziGo HSK.
The 1.2 MB font contains 4,236 mapped characters, covering every Hanzi in the
bundled 5,000-entry corpus. Characters outside this subset still use platform fallback.
This avoids fetching external CJK fonts just to read the bundled HSK words.

Rebuild with optional authoring dependency fonttools:
`python backend/tools/build_hsk_font.py path/to/NotoSansSC[wght].ttf`
Keep the upstream OFL.txt alongside the derivative.
