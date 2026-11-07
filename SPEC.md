# StudioFlow specification

StudioFlow serves students and developers managing personal projects. The Creator archetype guides a clear, encouraging voice and the promise to organize projects with clarity, simplicity, and security. The design uses dark navy surfaces, electric blue accents, a custom SVG mark, and a responsive layout.

## APP-001 · Branded homepage

- Scope and files — `app/brand.json`, `app/templates/home.html`, `app/templates/base.html`, `app/static/logo.svg`, and `app/static/site.css` supply the brand, shared navigation, and responsive homepage.
- Acceptance — The homepage renders the brand and SVG, the primary action reaches the next section, and keyboard navigation and the 390 px layout work in Chromium. Account routes are outside this lesson.
- Local evidence — Both `python studio.py check --lesson APP-001` and `python studio.py check` passed with Black, Pylint, 96 foundation tests, two contract tests, and two real Chromium tests. Two foundation cases were skipped by the instructor suite on Windows.
- [Issue #1](https://github.com/yungjorge/my-app-studio/issues/1) · Branch `app-001-studioflow-homepage`.
- [Pull request #2](https://github.com/yungjorge/my-app-studio/pull/2).

## APP-002 · Secure accounts

- Scope and files — `app/features/accounts.py` connects the shared security and SQLite helpers to the REST endpoints and to `app/templates/account.html` and `app/templates/dashboard.html`.
- Acceptance — Signup creates a member with an Argon2id hash. A live signed, expiring session in an HttpOnly cookie unlocks the dashboard and changes `GET /api/me` from 401 to 200. CSRF checks guard mutations. Logout revokes the server session and rejects replay.
- Local evidence — Both `python studio.py check --lesson APP-002` and `python studio.py check` passed with Black, Pylint, 96 foundation tests, 14 cumulative contracts, and two real Chromium tests. Coverage includes wrong passwords, duplicate and invalid signup, role injection, CSRF rejection, and copied-cookie replay.
- [Issue #3](https://github.com/yungjorge/my-app-studio/issues/3) · Branch `app-002-secure-accounts`.
