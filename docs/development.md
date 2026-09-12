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
uv run python -m pytest tests/ -v
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
├── builder.py     # build_schema(), SchemaType
├── config.py      # SchemaConfig dataclass
├── decorator.py   # @auto_schema decorator
├── py.typed       # PEP 561 type marker
├── types.py       # Type extraction utilities
├── mixins/        # Built-in reusable mixins
└── utils/         # Internal utilities
```

## Contributing

- Open an issue for bugs or feature requests.
- Pull requests should include tests.
- Run `uv run python -m pytest tests/ -v` before committing.
