# Development

## Setup

```bash
git clone https://github.com/emiliano-go/schemap
cd schemap
uv venv
uv sync
```

## Running tests

```bash
uv run pytest
```

Tests use SQLite in-memory databases. No external database needed.

## Building docs

```bash
pip install zensical
zensical build --clean
```

Output goes to `site/`. Add `site/` to your `.gitignore`.

## Project structure

```
src/schemap/
├── __init__.py    # Public API exports
├── base.py        # AutoBase, SchemaMixin
├── builder.py     # build_schema()
├── config.py      # SchemaConfig dataclass
├── decorator.py   # @auto_schema decorator
├── methods.py     # from_schema / to_schema helpers
├── types.py       # Type extraction utilities
├── mixins/        # Built-in reusable mixins
└── utils/         # Internal utilities
```

## Contributing

- Open an issue for bugs or feature requests.
- Pull requests should include tests.
- Run `ruff check src/` before committing.
