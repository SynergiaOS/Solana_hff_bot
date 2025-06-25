# THE OVERMIND PROTOCOL - Mission Control UI

## 🎯 Captain's Bridge - Web Dashboard

Prosty, ale potężny interfejs webowy do monitorowania i kontroli systemu THE OVERMIND PROTOCOL.

### ✨ Funkcje

#### 📊 System Status Dashboard
- **Real-time status** wszystkich komponentów systemu
- **AI Brain Manager** monitoring (port 8000)
- **Rust Executor** health checks (port 8081)
- **DragonflyDB** connection status (port 6379)

#### 💰 Trading Metrics
- Liczba wykonanych transakcji
- Wskaźnik sukcesu (success rate)
- Dzienny P&L (Profit & Loss)
- Bieżące pozycje
- Latencja systemu

#### 📡 Communication Queues
- Monitoring kolejek DragonflyDB
- Status przetwarzania sygnałów
- Komend oczekujących na wykonanie
- Decyzji AI gotowych do realizacji

#### 🚨 Emergency Controls
- **EMERGENCY STOP** button
- Manual refresh systemu
- Auto-refresh co 15 sekund

### 🚀 Jak Uruchomić

#### Metoda 1: Za pomocą pixi
```bash
pixi run start-mission-control
```

#### Metoda 2: Bezpośrednio
```bash
cd mission_control_ui
python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 🌐 Dostęp

Po uruchomieniu, Mission Control UI będzie dostępny pod adresem:
- **Local**: http://localhost:8501
- **Network**: http://89.117.53.53:8501 (dla dostępu zdalnego)

### 🎨 Interface Design

#### Main Header
- Gradient background z logo OVERMIND
- Informacje o systemie i architekturze

#### Three-Column Layout
1. **System Status** (lewa kolumna)
   - Status komponentów
   - Health checks
   - Emergency controls

2. **Trading Metrics** (środkowa kolumna)
   - Kluczowe metryki
   - Performance indicators
   - Real-time data

3. **System Information** (prawa kolumna)
   - Informacje o środowisku
   - Linki do komponentów
   - System metadata

#### Full-Width Sections
- **Communication Queues**: Status kolejek komunikacyjnych
- **Activity Log**: Dziennik ostatnich aktywności
- **Footer**: Informacje o systemie

### 🔧 Technologie

- **Framework**: Streamlit (Python web framework)
- **HTTP Client**: httpx (for API calls)
- **Data Processing**: pandas (for data tables)
- **Styling**: Custom CSS with gradients and cards
- **Auto-refresh**: 15-second intervals

### 📚 API Integration

Mission Control UI komunikuje się z:

#### Brain Manager API (port 8000)
- `GET /status` - System status
- `GET /health` - Health check

#### Rust Executor API (port 8081)
- `GET /health` - Executor health
- `GET /metrics` - Trading metrics
- `POST /control/emergency-stop` - Emergency stop

#### DragonflyDB (port 6379)
- Queue monitoring via Redis protocol
- Real-time message passing

### 🎯 Future Enhancements

- **Real-time charts** dla P&L i metryki
- **WebSocket integration** dla live updates
- **Advanced controls** dla trading parameters
- **Alert system** dla critical events
- **Mobile responsive design**
- **User authentication** dla production

### 🔐 Security Notes

- Currently designed for development/demo use
- No authentication implemented
- Local network access only recommended
- Emergency stop requires additional validation for production

---

**THE OVERMIND PROTOCOL** - Mission Control UI provides a user-friendly interface to monitor and control the most advanced AI trading system for Solana blockchain.