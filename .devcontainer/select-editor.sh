#!/usr/bin/env bash
set -euo pipefail

workspace="${PWD}"

detect_editor_flavor() {
  # Allow manual override
  if [[ "${EDITOR_FLAVOR:-}" =~ ^(vscode|cursor)$ ]]; then
    echo "${EDITOR_FLAVOR}"
    return
  fi

  # VS Code/ Cursor remote server folder hint
  if [[ -n "${VSCODE_AGENT_FOLDER:-}" ]]; then
    if [[ "${VSCODE_AGENT_FOLDER}" == *".cursor-server"* ]]; then
      echo "cursor"; return
    fi
    if [[ "${VSCODE_AGENT_FOLDER}" == *".vscode-server"* ]]; then
      echo "vscode"; return
    fi
  fi

  # Server installation directories
  if [[ -d "${HOME}/.cursor-server" ]]; then
    echo "cursor"; return
  fi
  if [[ -d "${HOME}/.vscode-server" ]]; then
    echo "vscode"; return
  fi

  # Terminal program hint
  case "${TERM_PROGRAM:-}" in
    cursor|*Cursor*) echo "cursor"; return ;;
    vscode|*VSCode*) echo "vscode"; return ;;
  esac

  # Default
  echo "vscode"
}

flavor="$(detect_editor_flavor)"
echo "[devcontainer] Detected editor flavor: ${flavor}"

mkdir -p "${workspace}/.vscode"

pushd "${workspace}/.vscode" >/dev/null

# Link editor-specific settings
if [[ -f "settings.${flavor}.json" ]]; then
  ln -sf "settings.${flavor}.json" "settings.json"
elif [[ -f "settings.vscode.json" ]]; then
  ln -sf "settings.vscode.json" "settings.json"
fi

# Link editor-specific extension recommendations
if [[ -f "extensions.${flavor}.json" ]]; then
  ln -sf "extensions.${flavor}.json" "extensions.json"
elif [[ -f "extensions.vscode.json" ]]; then
  ln -sf "extensions.vscode.json" "extensions.json"
fi

popd >/dev/null

# Ensure venv exists and install dev deps
if [[ ! -d "${workspace}/.venv" ]]; then
  echo "[devcontainer] Creating Python venv with uv..."
  uv venv "${workspace}/.venv"
  source "${workspace}/.venv/bin/activate"
  uv pip install -e "${workspace}.[dev]"
fi

echo "[devcontainer] Editor-specific settings linked: ${flavor}"

