# Project Guidelines

## Project Structure

- Application code lives in `src/django_wee/`.
- Tests live in `tests/` and use the Django project in `testproj/`.
- Public shortcuts and redirect behavior have synchronous and asynchronous variants; keep both paths aligned when changing shared behavior.
- Database schema changes require a new migration under `src/django_wee/migrations/`.

## Development Commands

- Run the full test matrix with `hatch test`.
- Run focused tests with `hatch run pytest tests/<test_file>.py`.
- Run code quality checks with `hatch check code`.
- Verify formatting with `hatch check fmt`.
- Run strict type checks with `hatch check types`.
- Generate migrations with `hatch run ./manage.py makemigrations django_wee -n "friendly_name"`; never hand-write migrations.

## Python and Django Conventions

- Support the Python and Django versions declared in `pyproject.toml`.
- Preserve strict typing and existing type annotations; production code is checked with mypy and Pyrefly.
- Follow the existing Ruff configuration, including a 120-character line limit.
- Use Django ORM and cache APIs rather than duplicating persistence or cache logic.
- Use timezone-aware datetimes through `django.utils.timezone` for expiration behavior.
- Keep sync and async public APIs behaviorally equivalent.

## Testing Expectations

- Add or update focused tests for every behavior change.
- Include both synchronous and asynchronous coverage when changing a paired API.
- For expiration changes, cover unexpired, expired, and non-expiring records where applicable.
- Run the focused test file first, then the full suite before finishing.
- Group tests for a class or module in a single `Test<Name>` class and prefix each test with `test_<method>_` (e.g. `test_alive_...` for the `alive` queryset method).
- Order test classes and methods to match the definition order in the corresponding source file.

## Change Scope

- Keep changes minimal and consistent with neighboring code.
- Do not modify generated migration history or unrelated user changes.
- Use Conventional Commits for commit messages, such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, or `chore:`.
- Update `README.md` when a change affects documented behavior, public APIs, configuration, installation, or usage.
- Update `CHANGELOG.md` for user-visible changes that are not yet part of a published release.
