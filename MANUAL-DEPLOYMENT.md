# 🚀 THE OVERMIND PROTOCOL - Manual Deployment Guide

## 📋 **OVERVIEW**

Ten przewodnik opisuje manualny deployment THE OVERMIND PROTOCOL na Contabo VDS (marcin@89.117.53.53) krok po kroku.

**Status:** Ready for manual deployment  
**Target:** Contabo VDS 89.117.53.53  
**User:** marcin

## 🎯 **STEP-BY-STEP DEPLOYMENT**

### **KROK 1: Przygotowanie lokalnego środowiska**

✅ **Już wykonane:**
- Reorganizacja projektu (`./reorganize-project.sh`)
- Setup monitoringu (`./monitoring-setup.sh`)
- Struktura `overmind-protocol/` gotowa

### **KROK 2: Połączenie z serwerem**

```bash
# Połącz się z Contabo VDS
ssh marcin@89.117.53.53
```

### **KROK 3: Przygotowanie serwera**

Na serwerze wykonaj:

```bash
# Update systemu
sudo apt-get update && sudo apt-get upgrade -y

# Instalacja podstawowych pakietów
sudo apt-get install -y \
    curl \
    wget \
    git \
    htop \
    vim \
    ufw \
    fail2ban \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Instalacja Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Instalacja Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Restart sesji żeby docker group działał
exit
```

### **KROK 4: Konfiguracja firewall**

Połącz się ponownie i skonfiguruj firewall:

```bash
ssh marcin@89.117.53.53

# Konfiguracja UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp  # Trading system
sudo ufw allow 3001/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus
sudo ufw allow 8000/tcp  # AI Brain Vector DB
sudo ufw --force enable

# Sprawdź status
sudo ufw status
```

### **KROK 5: Tworzenie katalogów**

```bash
# Utwórz katalogi projektu
mkdir -p /home/marcin/overmind-protocol
mkdir -p /home/marcin/backups/overmind
mkdir -p /home/marcin/logs/overmind

# Sprawdź utworzone katalogi
ls -la /home/marcin/
```

### **KROK 6: Transfer plików**

**Z lokalnego komputera** (nowy terminal):

```bash
# Przejdź do katalogu projektu
cd /home/marcin/windsurf/Projects/LastBot

# Synchronizuj pliki na serwer
rsync -avz --progress \
    --exclude='.git' \
    --exclude='target' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    overmind-protocol/ marcin@89.117.53.53:/home/marcin/overmind-protocol/

# Sprawdź transfer
ssh marcin@89.117.53.53 "ls -la /home/marcin/overmind-protocol/"
```

### **KROK 7: Konfiguracja środowiska**

Na serwerze:

```bash
cd /home/marcin/overmind-protocol

# Skopiuj template środowiska
cp .env.example .env

# Edytuj konfigurację
nano .env
```

**Ustaw przynajmniej:**
```bash
# REQUIRED - Ustaw swój OpenAI API key
OPENAI_API_KEY=sk-your-actual-openai-api-key

# OPTIONAL - Inne API keys
GROQ_API_KEY=your-groq-api-key
MISTRAL_API_KEY=your-mistral-api-key

# Trading mode (zostaw paper dla testów)
SNIPER_TRADING_MODE=paper
```

### **KROK 8: Budowanie Docker images**

```bash
cd /home/marcin/overmind-protocol

# Sprawdź dostępne compose files
ls -la infrastructure/compose/

# Użyj production compose file
COMPOSE_FILE="infrastructure/compose/docker-compose.production.yml"

# Jeśli nie ma production file, użyj overmind
if [[ ! -f "$COMPOSE_FILE" ]]; then
    COMPOSE_FILE="infrastructure/compose/docker-compose.overmind.yml"
fi

echo "Using compose file: $COMPOSE_FILE"

# Buduj images
docker-compose -f "$COMPOSE_FILE" build

# Sprawdź zbudowane images
docker images
```

### **KROK 9: Uruchomienie usług**

```bash
cd /home/marcin/overmind-protocol

# Określ compose file
COMPOSE_FILE="infrastructure/compose/docker-compose.production.yml"
if [[ ! -f "$COMPOSE_FILE" ]]; then
    COMPOSE_FILE="infrastructure/compose/docker-compose.overmind.yml"
fi

# Uruchom infrastrukturę
echo "Starting infrastructure services..."
docker-compose -f "$COMPOSE_FILE" up -d \
    overmind-dragonfly \
    overmind-chroma \
    overmind-postgres \
    tensorzero-clickhouse

# Poczekaj na bazy danych
echo "Waiting for databases to initialize..."
sleep 30

# Uruchom AI services
echo "Starting AI services..."
docker-compose -f "$COMPOSE_FILE" up -d \
    tensorzero-gateway \
    overmind-brain

# Poczekaj na AI services
echo "Waiting for AI services..."
sleep 20

# Uruchom trading system
echo "Starting trading system..."
docker-compose -f "$COMPOSE_FILE" up -d \
    overmind-executor

# Uruchom monitoring
echo "Starting monitoring..."
docker-compose -f "$COMPOSE_FILE" up -d \
    prometheus \
    grafana \
    node-exporter

echo "All services started!"
```

### **KROK 10: Weryfikacja deployment**

```bash
# Sprawdź status kontenerów
docker-compose -f "$COMPOSE_FILE" ps

# Sprawdź logi
docker-compose -f "$COMPOSE_FILE" logs --tail=50

# Test health endpoints
echo "Testing health endpoints..."

# Trading System
curl -f http://localhost:8080/health && echo " ✅ Trading System OK" || echo " ❌ Trading System FAIL"

# Vector Database
curl -f http://localhost:8000/api/v1/heartbeat && echo " ✅ Vector DB OK" || echo " ❌ Vector DB FAIL"

# TensorZero
curl -f http://localhost:3000/health && echo " ✅ TensorZero OK" || echo " ❌ TensorZero FAIL"

# Prometheus
curl -f http://localhost:9090/-/healthy && echo " ✅ Prometheus OK" || echo " ❌ Prometheus FAIL"

# Grafana
curl -f http://localhost:3001/api/health && echo " ✅ Grafana OK" || echo " ❌ Grafana FAIL"
```

### **KROK 11: Sprawdzenie zasobów**

```bash
# Sprawdź użycie pamięci
free -h

# Sprawdź użycie dysku
df -h

# Sprawdź Docker stats
docker stats --no-stream

# Sprawdź system info
docker system df
```

## 🎯 **ACCESS POINTS**

Po udanym deployment:

- **🧠 Trading System:** http://89.117.53.53:8080
- **📊 Grafana Dashboard:** http://89.117.53.53:3001
- **📈 Prometheus:** http://89.117.53.53:9090
- **🤖 AI Vector DB:** http://89.117.53.53:8000

## 🔧 **MANAGEMENT COMMANDS**

```bash
# Sprawdź status
docker-compose -f "$COMPOSE_FILE" ps

# Zobacz logi
docker-compose -f "$COMPOSE_FILE" logs -f

# Restart usług
docker-compose -f "$COMPOSE_FILE" restart

# Stop systemu
docker-compose -f "$COMPOSE_FILE" down

# Update systemu
git pull  # jeśli masz repo na serwerze
docker-compose -f "$COMPOSE_FILE" build
docker-compose -f "$COMPOSE_FILE" up -d
```

## 🚨 **TROUBLESHOOTING**

### Problem: Brak compose file
```bash
# Skopiuj z głównego katalogu
cp docker-compose.overmind.yml infrastructure/compose/
```

### Problem: Błędy budowania
```bash
# Sprawdź logi budowania
docker-compose -f "$COMPOSE_FILE" build --no-cache

# Sprawdź dostępne miejsce
df -h
```

### Problem: Usługi nie startują
```bash
# Sprawdź logi konkretnej usługi
docker-compose -f "$COMPOSE_FILE" logs overmind-executor

# Restart konkretnej usługi
docker-compose -f "$COMPOSE_FILE" restart overmind-executor
```

## ✅ **SUCCESS CRITERIA**

Deployment jest udany gdy:
- [ ] Wszystkie kontenery są w stanie "Up"
- [ ] Health endpoints odpowiadają
- [ ] Grafana dashboard jest dostępny
- [ ] Trading system pokazuje status "healthy"
- [ ] AI Brain łączy się z Vector DB
- [ ] Brak błędów w logach

---

**🧠 THE OVERMIND PROTOCOL - Ready for manual deployment!**

**⚠️ IMPORTANT:** System startuje w paper trading mode. Monitor przez 48+ godzin przed live trading.
