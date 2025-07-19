# TestProject

A test project for verification

## Features

-   Modern Python project structure with uv and nox
-   Comprehensive code quality tools (Ruff, Black, isort, Pyright)
-   Security scanning (Bandit, pip-audit, Safety)
-   Automated testing with pytest and coverage
-   Documentation with MkDocs Material
-   Pre-commit hooks for code quality
-   Conventional commits with Commitizen
-   GitHub Actions CI/CD pipeline
-   Docker support
-   Structured logging with OpenTelemetry support

## Quick Start

### Prerequisites

-   Python 3.12+
-   uv (Python package manager)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd testproject

# Install dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Development Commands

| Command              | Description                    |
| -------------------- | ------------------------------ |
| `nox -s lint`        | Run linting with Ruff          |
| `nox -s format_code` | Format code with Ruff          |
| `nox -s typing`      | Run type checking with Pyright |
| `nox -s test`        | Run tests with coverage        |
| `nox -s security`    | Run security checks            |
| `nox -s docs`        | Build documentation            |
| `nox -s ci`          | Run all CI checks              |
| `nox -s all_checks`  | Run all quality checks         |

### Testing

```bash
# Run tests with coverage
nox -s test

# Run tests in parallel
pytest -n auto

# Run specific test markers
pytest -m "not slow"
```

### Logging Configuration

The project includes structured logging with OpenTelemetry support. Configure logging behavior using environment variables:

#### Environment Variables

| Variable | Description | Default | Options |
| -------- | ----------- | ------- | ------- |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT` | Log output format | `json` | `json`, `console`, `plain` |
| `LOG_FILE_PATH` | Path to log file (optional) | None | Any valid file path |
| `OTEL_LOGS_EXPORT_MODE` | OpenTelemetry export mode | `file` | `file`, `otlp`, `both` |
| `OTEL_ENDPOINT` | OpenTelemetry collector endpoint | `http://localhost:4317` | Any valid URL |
| `OTEL_SERVICE_NAME` | Service name for OpenTelemetry | `python-app` | Any string |
| `OTEL_EXPORT_TIMEOUT` | Export timeout in milliseconds | `30000` | Any positive integer |

#### Usage Examples

```bash
# Local file logging only
export LOG_FILE_PATH="/var/log/myapp.log"
export OTEL_LOGS_EXPORT_MODE="file"

# OTLP export only
export OTEL_LOGS_EXPORT_MODE="otlp"
export OTEL_ENDPOINT="http://otel-collector:4317"
export OTEL_SERVICE_NAME="my-service"

# Both file and OTLP export
export OTEL_LOGS_EXPORT_MODE="both"
export LOG_FILE_PATH="/var/log/myapp.log"
export OTEL_ENDPOINT="http://otel-collector:4317"

# Development mode with console output
export LOG_LEVEL="DEBUG"
export LOG_FORMAT="console"
```

#### Code Example

```python
from test_project.utils.logger import get_logger, setup_application_logging

# Basic usage
logger = get_logger("my_module")
logger.info("Application started", version="1.0.0")

# With application setup
app_logger = setup_application_logging("my_app", environment="production")
app_logger.error("Error occurred", error_code="E001")

# Context binding
user_logger = logger.bind(user_id="user123", request_id="req456")
user_logger.info("User action", action="login")
```

### Documentation

```bash
# Build documentation
nox -s docs

# Serve documentation locally
mkdocs serve
```

### Docker

```bash
# Build Docker image
docker build -t testproject .

# Run Docker container
docker run testproject
```

## Project Structure

```
testproject/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Documentation
├── .github/                # GitHub configuration
├── .vscode/                # VS Code settings
├── constraints/            # Dependency constraints
├── pyproject.toml          # Project configuration
├── noxfile.py              # Nox tasks
├── mkdocs.yml              # Documentation configuration
├── Dockerfile              # Docker configuration
└── README.md               # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks: `nox -s all_checks`
5. Commit using conventional commits: `cz commit`
6. Create a pull request

## Development Workflow

### Code Quality

The project uses several tools to maintain code quality:

-   **Ruff**: Fast Python linter and formatter
-   **Black**: Uncompromising code formatter
-   **isort**: Import sorting
-   **Pyright**: Type checking
-   **Bandit**: Security linting
-   **pip-audit**: Dependency vulnerability scanning
-   **Safety**: Commercial-grade security scanning

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit:

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

### Conventional Commits

The project uses conventional commits for versioning:

```bash
# Use Commitizen for commits
cz commit

# Bump version
cz bump
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# 開発環境セットアップ手順

## 手動セットアップ

### pipx のインストール（入っていない場合）

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```

詳細は[pipx の公式ドキュメント](https://pipx.pypa.io/stable/installation/)を参照してください。

### uv のインストール

```bash
pipx install uv
```

詳細は[uv の公式ドキュメント](https://docs.astral.sh/uv/getting-started/installation/#configuring-installation)を参照してください。

### 対象の Python バージョンのインストール

```bash
uv python install [TARGET_PYTHON_VERSION]
```

### 仮想環境の作成

```bash
uv venv
```

### ライブラリのインストール

```bash
uv sync
```

### pre-commit の設定

```bash
uv run pre-commit install
```

ここまでは`setup.sh`で実行できます

### nox の実行

```bash
uv run nox
```

### 仮想環境の有効化

```bash
source .venv/bin/activate
```

### 仮想環境の終了

```bash
deactivate
```

## 自動セットアップスクリプト

環境のセットアップを自動化するために、`setup.sh`スクリプトを用意しています。

### setup.sh の使用方法

このスクリプトを使用することで、開発環境のセットアップを簡単に行うことができます。

1. `setup.sh`ファイルをプロジェクトのルートディレクトリに配置します。

2. スクリプトに実行権限を付与します：

    ```bash
    chmod +x setup.sh
    ```

3. スクリプトを実行します：

    ```bash
    ./setup.sh
    ```

注意事項：

-   スクリプトは sudo コマンドを使用するため、実行時にパスワードの入力を求められる場合があります。
-   Python のバージョンインストール行はデフォルトでコメントアウトされています。使用する場合は、スクリプトを編集し、適切なバージョン番号を指定してください。
-   仮想環境の有効化と終了は、スクリプト実行後に手動で行う必要があります。
