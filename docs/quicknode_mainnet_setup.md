# QuickNode Mainnet Endpoint Setup Guide

## 🎯 FAZA 1: Konfiguracja QuickNode Mainnet Endpoint

### Cel
Stworzenie i konfiguracja endpoint dla Solana Mainnet w panelu QuickNode, aby umożliwić THE OVERMIND PROTOCOL działanie na prawdziwych danych rynkowych w trybie paper trading.

### Obecny Status
- ✅ **Devnet endpoint skonfigurowany**: `distinguished-blue-glade.solana-devnet.quiknode.pro`
- ✅ **Płatny plan aktywny**: Build Plan $49.00
- ❌ **Mainnet endpoint**: Wymaga konfiguracji

### Instrukcje Krok po Kroku

#### Krok 1: Logowanie do Panelu QuickNode
1. Przejdź do [QuickNode Dashboard](https://dashboard.quiknode.pro/)
2. Zaloguj się na swoje konto
3. Sprawdź aktywny plan (powinien być Build Plan $49.00)

#### Krok 2: Tworzenie Mainnet Endpoint
1. Kliknij **"Create Endpoint"** lub **"+ New Endpoint"**
2. Wybierz **Solana** jako blockchain
3. Wybierz **Mainnet** jako sieć (nie Devnet!)
4. Wybierz region (zalecane: najbliższy Twojej lokalizacji)
5. Potwierdź konfigurację

#### Krok 3: Konfiguracja Endpoint
Po utworzeniu endpoint otrzymasz:
- **HTTP URL**: `https://your-mainnet-name.solana-mainnet.quiknode.pro/YOUR_MAINNET_KEY`
- **WSS URL**: `wss://your-mainnet-name.solana-mainnet.quiknode.pro/YOUR_MAINNET_KEY`

#### Krok 4: Aktualizacja .env
Skopiuj otrzymane URLs i zaktualizuj plik `.env`:

```bash
# =================================================
# 🌐 MAINNET CONFIGURATION (Production Environment)
# =================================================

# QuickNode Mainnet Endpoints (ZAKTUALIZUJ TE WARTOŚCI)
QUICKNODE_MAINNET_RPC_URL=https://your-mainnet-name.solana-mainnet.quiknode.pro/YOUR_MAINNET_KEY
QUICKNODE_MAINNET_WS_URL=wss://your-mainnet-name.solana-mainnet.quiknode.pro/YOUR_MAINNET_KEY
```

#### Krok 5: Weryfikacja Konfiguracji
Uruchom test konfiguracji:
```bash
cd /home/marcin/windsurf/Projects/LastBot
python tests/integration/test_environment_configuration.py
```

### Oczekiwane Rezultaty

#### Po Poprawnej Konfiguracji
```
🎉 ALL ENVIRONMENT CONFIGURATION TESTS PASSED!

✅ ACHIEVEMENTS:
   • Dynamic environment detection working
   • Devnet configuration loading correctly
   • Mainnet configuration validation ready
   • Configuration validation system operational
```

#### Test Mainnet (Paper Trading)
```bash
# Ustaw środowisko na production (Mainnet + Paper Trading)
export APP_ENV=production

# Uruchom test
python tests/integration/test_environment_configuration.py
```

### Bezpieczeństwo

#### ⚠️ WAŻNE ZASADY BEZPIECZEŃSTWA
1. **Zawsze rozpoczynaj z Paper Trading**: `APP_ENV=production` (Mainnet + Paper Trading)
2. **Nigdy nie używaj `APP_ENV=live`** bez pełnej walidacji
3. **Chroń swoje API keys**: Nie udostępniaj ich publicznie
4. **Monitoruj użycie**: Sprawdzaj zużycie API w panelu QuickNode

### Rozwiązywanie Problemów

#### Problem: "Mainnet QuickNode endpoint not configured"
**Rozwiązanie**: 
1. Sprawdź czy utworzyłeś Mainnet endpoint (nie Devnet)
2. Sprawdź czy skopiowałeś poprawne URLs do `.env`
3. Sprawdź czy nie ma literówek w nazwach zmiennych

#### Problem: "API rate limit exceeded"
**Rozwiązanie**:
1. Sprawdź zużycie w panelu QuickNode
2. Rozważ upgrade planu jeśli potrzebne
3. Zaimplementuj rate limiting w kodzie

#### Problem: "Connection timeout"
**Rozwiązanie**:
1. Sprawdź połączenie internetowe
2. Sprawdź status QuickNode na [status.quiknode.pro](https://status.quiknode.pro)
3. Spróbuj innego regionu endpoint

### Następne Kroki

Po pomyślnej konfiguracji Mainnet endpoint:

1. **Przetestuj Historical Data Framework** z prawdziwymi danymi Mainnet
2. **Skonfiguruj Kestrę** dla automatyzacji
3. **Uruchom 48-godzinny Paper Trading** na Mainnet
4. **Waliduj AI decisions** z prawdziwymi danymi rynkowymi

### Komendy Pomocnicze

#### Sprawdzenie Obecnej Konfiguracji
```bash
python -c "
from config.environment_loader import initialize_environment
loader = initialize_environment()
status = loader.get_status_report()
print(f'Environment: {status[\"environment\"]}')
print(f'Network: {status[\"network\"]}')
print(f'All valid: {status[\"all_valid\"]}')
for warning in status['warnings']:
    print(f'Warning: {warning}')
"
```

#### Test Połączenia z Mainnet
```bash
export APP_ENV=production
python -c "
import os
from config.environment_loader import initialize_environment
loader = initialize_environment()
config = loader.get_config()
print(f'Mainnet RPC: {config.rpc_url}')
print(f'Is Mainnet: {config.is_mainnet}')
print(f'Paper Trading: {loader.is_paper_trading()}')
"
```

### Kontakt i Wsparcie

Jeśli napotkasz problemy:
1. Sprawdź [QuickNode Documentation](https://www.quicknode.com/docs/solana)
2. Skontaktuj się z QuickNode Support
3. Sprawdź logi w `logs/overmind.log`

---

**🎯 Cel**: Po wykonaniu tych kroków będziesz mieć w pełni skonfigurowany Mainnet endpoint, gotowy do testowania THE OVERMIND PROTOCOL z prawdziwymi danymi rynkowymi w bezpiecznym trybie paper trading.
