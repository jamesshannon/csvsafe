# Development

## Setup

```bash
make install
```

`make install` creates `.venv` automatically (if missing) and installs runtime + dev dependencies into it.

If you want an interactive shell in that environment:

```bash
source .venv/bin/activate
```

## Commands

- `make lint`
- `make test`
- `make test-integration`
- `make build`
- `make package`

## Integration Test Note

`make test-integration` exercises LaunchServices with `open -a dist/CSVSafe.app <file>`.
On some macOS setups this may also show an Open dialog as a side effect during the test run.
The test is still valid if conversion succeeds and the expected `.xlsx` is created.
