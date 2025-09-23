#!/bin/bash

set -e

# --- Messaging helpers ---
error() {
  echo "❌ エラー: $1" >&2
}

success() {
  echo "✅ 成功: $1"
}

info() {
  echo "ℹ️ 情報: $1"
}

# --- Checks ---
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    GitHub CLI Setup Script                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Ensure gh CLI is installed
if ! command_exists gh; then
  error "gh CLI が見つかりません。'gh' をインストールして PATH に追加してください。"
  echo "   インストール: https://cli.github.com/"
  exit 1
fi

info "gh CLI はインストールされています"

# Ensure authenticated to GitHub
if ! gh auth status >/dev/null 2>&1; then
  echo "🔐 GitHub CLI にログインしていません。これから 'gh auth login' を実行します。"
  echo "   画面の指示に従って認証を完了してください。"
  # Run interactive login; returns control to this script after completion
  if ! gh auth login; then
    error "'gh auth login' に失敗しました。もう一度お試しください。"
    exit 1
  fi

  # Re-verify
  if ! gh auth status >/dev/null 2>&1; then
    error "GitHub CLI のログインが完了しませんでした。"
    exit 1
  fi
  success "GitHub CLI にログインしました"
else
  info "GitHub CLI は認証済みです"
fi

# Ensure global git identity (user.name, user.email)
need_set_name=false
need_set_email=false

current_name=$(git config --global user.name || true)
current_email=$(git config --global user.email || true)

if [ -z "$current_name" ]; then
  need_set_name=true
fi
if [ -z "$current_email" ]; then
  need_set_email=true
fi

if [ "$need_set_name" = true ]; then
  echo "🪪 Git のグローバル user.name が未設定です。"
  while true; do
    read -p "👤 Git のユーザー名 (user.name) を入力してください: " input_name
    if [ -n "$input_name" ]; then
      git config --global user.name "$input_name"
      success "git config --global user.name を設定しました: $input_name"
      break
    else
      echo "❌ 空の値は設定できません。"
    fi
  done
else
  info "Git のグローバル user.name は既に設定されています: $current_name"
fi

if [ "$need_set_email" = true ]; then
  echo "✉️  Git のグローバル user.email が未設定です。"
  while true; do
    read -p "📧 Git のメールアドレス (user.email) を入力してください: " input_email
    if [[ -n "$input_email" && "$input_email" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
      git config --global user.email "$input_email"
      success "git config --global user.email を設定しました: $input_email"
      break
    else
      echo "❌ メールアドレスの形式が正しくありません。例: name@example.com"
    fi
  done
else
  info "Git のグローバル user.email は既に設定されています: $current_email"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     ✅ 前提条件チェック完了                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
success "GitHub CLI ログインおよび Git グローバル設定が整いました"

exit 0

