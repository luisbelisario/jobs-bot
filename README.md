# 🤖 JobsBot

Assistente de busca de vagas via Telegram.  
Envie seu currículo, e o bot busca vagas alinhadas ao seu perfil em múltiplas fontes — automaticamente, 24/7.

## 🚀 Funcionalidades

- 📎 **Upload de currículo**: PDF, DOCX ou TXT — extração automática de skills
- 🔍 **Busca multi-fonte**: 8 fontes — Remotive, Remote OK, Himalayas, We Work Remotely, Wellfound, GitHub, Programathor, GeekHunter
- 🎯 **Matching inteligente**: cruza skills, cargo desejado e senioridade
- ⏰ **Agendamento 24/7**: busca automática a cada X horas e notifica vagas novas
- 💾 **Persistência**: SQLite — não repete vagas já notificadas
- 🆓 **Free tier**: feito para rodar em Fly.io, Railway ou Oracle Cloud de graça

## 📦 Stack

- Python 3.9+ com `asyncio`
- `python-telegram-bot` v21 (JobQueue para agendamento)
- `httpx` (HTTP assíncrono)
- `beautifulsoup4` + `lxml` (scraping)
- `pypdf` + `python-docx` (parsing de currículo)
- `aiosqlite` (banco de dados)

## 🔧 Instalação

```bash
# Clone
git clone <repo-url> jobs-bot
cd jobs-bot

# Ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Dependências
pip install -r requirements.txt

# Configuração
cp .env.example .env
# Edite .env com seu TELEGRAM_BOT_TOKEN (fale com @BotFather)
```

## ▶️ Uso

```bash
python main.py
```

### Comandos no Telegram

| Comando | Descrição |
|---------|-----------|
| `/start` | Boas-vindas e instruções |
| `/help` | Ajuda detalhada |
| `/upload` | Enviar currículo |
| `/profile` | Ver perfil salvo |
| `/search` | Buscar vagas agora |
| `/config` | Instruções de configuração |
| `/setrole` | Definir cargos desejados |
| `/setlocation` | Definir localizações |

## 🌐 Deploy

### Fly.io (recomendado — free tier generoso)

```bash
fly launch --no-deploy
fly secrets set TELEGRAM_BOT_TOKEN=seu_token
fly secrets set TELEGRAM_CHAT_ID=seu_chat_id
fly deploy
```

### Railway

1. Conecte o repositório no Railway
2. Adicione as variáveis de ambiente no dashboard
3. Deploy automático no push

## 📝 Variáveis de ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `TELEGRAM_BOT_TOKEN` | Sim | — | Token do bot (@BotFather) |
| `TELEGRAM_CHAT_ID` | Não | — | Chat ID para notificações agendadas |
| `SEARCH_INTERVAL_HOURS` | Não | 6 | Intervalo entre buscas automáticas |
| `MIN_MATCH_SCORE` | Não | 0.3 | Score mínimo de match (0 a 1) |
| `ENABLED_SOURCES` | Não | remotive,github,programathor | Fontes habilitadas |
| `GITHUB_TOKEN` | Não | — | Token GitHub (aumenta limite de API) |

## 🗺️ Roadmap

- [ ] Scraper LinkedIn (via Google dorks)
- [ ] Scraper Gupy / Vagas.com.br / InfoJobs
- [ ] Embeddings + vector search para matching mais preciso
- [ ] Dashboard web simples
- [ ] Suporte a múltiplos usuários
- [ ] Notificações de freelance (Upwork, Workana)