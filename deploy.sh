#!/bin/bash
# JobsBot — Deploy rápido no Fly.io
set -e

echo "🚀 JobsBot — Deploy Fly.io"
echo "============================"

# Verifica flyctl
if ! command -v flyctl &>/dev/null; then
    echo "❌ flyctl não encontrado."
    echo "   Instale com: brew install flyctl"
    echo "   Depois faça login: flyctl auth signup"
    exit 1
fi

# Verifica .env
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado."
    echo "   Copie .env.example e configure seu TELEGRAM_BOT_TOKEN."
    exit 1
fi

# Carrega token
source <(grep -v '^#' .env | grep TELEGRAM_BOT_TOKEN | sed 's/^/export /')
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN não configurado no .env."
    exit 1
fi

echo "✅ flyctl encontrado"
echo "✅ TELEGRAM_BOT_TOKEN configurado"

# Seta secrets
echo ""
echo "🔐 Configurando secrets..."
flyctl secrets set TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" 2>/dev/null || true
grep TELEGRAM_CHAT_ID .env | grep -qv '^#' && flyctl secrets set TELEGRAM_CHAT_ID="$(grep TELEGRAM_CHAT_ID .env | cut -d= -f2-)" 2>/dev/null || true

# Deploy
echo ""
echo "📦 Fazendo deploy..."
flyctl deploy

echo ""
echo "============================"
echo "✅ Deploy concluído!"
echo "   Verifique: flyctl status"
echo "   Logs:      flyctl logs"