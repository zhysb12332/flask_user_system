#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/flask_user_system"

if [ ! -d "$APP_DIR" ]; then
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
git fetch --all
git reset --hard "origin/${DEPLOY_BRANCH:-main}"

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD down
$COMPOSE_CMD up -d --build

sleep 3
curl -fsS http://127.0.0.1:5000/api/v1/health >/dev/null
echo "Deploy success: app is healthy."
