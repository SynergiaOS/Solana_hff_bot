# QuickNode Mainnet Endpoint Setup Guide

## 🎯 **ZADANIE: Configure QuickNode Mainnet Endpoint**

**Cel:** Stworzenie endpoint dla Solana Mainnet w panelu QuickNode z odpowiednimi limitami API

**Status:** 🔄 IN PROGRESS

---

## 📋 **INSTRUKCJE KROK PO KROKU**

### **Krok 1: Przygotowanie**

**Co już masz:**
- ✅ QuickNode Build Plan ($49.00/miesiąc)
- ✅ Devnet endpoint: `distinguished-blue-glade.solana-devnet.quiknode.pro`
- ✅ API Key: `QN_882d2e1f3f274132bb4f1cd2a47cc04d`

**Co musisz zrobić:**
- ❌ Utworzyć Mainnet endpoint
- ❌ Skonfigurować .env z nowymi URLs

### **Krok 2: Logowanie do QuickNode Dashboard**

1. **Otwórz przeglądarkę** i przejdź do: https://dashboard.quiknode.pro/
2. **Zaloguj się** na swoje konto (to samo co używasz dla Devnet)
3. **Sprawdź plan** - powinien być widoczny "Build Plan" za $49.00

### **Krok 3: Tworzenie Mainnet Endpoint**

1. **Kliknij "Create Endpoint"** (duży niebieski przycisk) lub **"+ New Endpoint"**

2. **Wybierz blockchain:**
   - Kliknij na **"Solana"**
   - Upewnij się że to Solana, nie Ethereum czy inne

3. **Wybierz sieć:**
   - ⚠️ **WAŻNE**: Wybierz **"Mainnet"** (nie Devnet!)
   - Powinieneś zobaczyć opcje: Mainnet, Devnet, Testnet
   - Kliknij **"Mainnet"**

4. **Wybierz region:**
   - Zalecane: **Europe** (jeśli jesteś w Polsce)
   - Alternatywnie: **US East** (dobra latencja do Europy)

5. **Konfiguracja dodatkowa:**
   - Zostaw domyślne ustawienia
   - Nie musisz włączać dodatkowych add-onów na razie

6. **Potwierdź utworzenie:**
   - Kliknij **"Create Endpoint"**
   - Poczekaj na utworzenie (może potrwać 1-2 minuty)

### **Krok 4: Skopiowanie URLs**

Po utworzeniu endpoint zobaczysz:

**HTTP URL (RPC):**
```
https://your-mainnet-name.solana-mainnet.quiknode.pro/YOUR_MAINNET_KEY
```

**WebSocket URL (WSS):**
```
wss://your-mainnet-name.solana-mainnet.quiknode.pro/YOUR_MAINNET_KEY
```

**Przykład** (na podstawie Twojego Devnet):
- Devnet: `distinguished-blue-glade.solana-devnet.quiknode.pro`
- Mainnet: `distinguished-blue-glade.solana-mainnet.quiknode.pro` (prawdopodobnie)

### **Krok 5: Aktualizacja .env**

1. **Otwórz plik `.env`** w głównym katalogu projektu

2. **Znajdź sekcję Mainnet** (około linii 35):
```bash
# QuickNode Mainnet Endpoints (TO BE CONFIGURED)
# TODO: Stwórz Mainnet endpoint w panelu QuickNode
QUICKNODE_MAINNET_RPC_URL=https://your-mainnet-endpoint.quiknode.pro/YOUR_MAINNET_KEY
QUICKNODE_MAINNET_WS_URL=wss://your-mainnet-endpoint.quiknode.pro/YOUR_MAINNET_KEY
```

3. **Zastąp placeholder URLs** rzeczywistymi URLs z QuickNode:
```bash
# QuickNode Mainnet Endpoints (CONFIGURED)
QUICKNODE_MAINNET_RPC_URL=https://your-actual-mainnet-name.solana-mainnet.quiknode.pro/YOUR_ACTUAL_MAINNET_KEY
QUICKNODE_MAINNET_WS_URL=wss://your-actual-mainnet-name.solana-mainnet.quiknode.pro/YOUR_ACTUAL_MAINNET_KEY
```

4. **Zapisz plik**

### **Krok 6: Walidacja Konfiguracji**

Uruchom skrypt walidacyjny:

```bash
cd /home/marcin/windsurf/Projects/LastBot
python scripts/validate_quicknode_mainnet.py
```

**Oczekiwany rezultat:**
```
🚀 QuickNode Mainnet Endpoint Validation
==================================================
Environment: production
Network: mainnet
Is Mainnet: True

🔗 Testing Mainnet Endpoints:
RPC URL: https://your-mainnet-name.solana-mainnet.qui...
WS URL: wss://your-mainnet-name.solana-mainnet.quikn...

🧪 Testing RPC Connection...
  Testing getVersion...
    ✅ Solana version: 1.18.x
  Testing getSlot...
    ✅ Current slot: 123456789
  Testing getAccountInfo...
    ✅ SOL account info retrieved
  Testing rate limits...
    ✅ 5 requests completed in 0.85s

✅ QuickNode Mainnet endpoint validation PASSED

🎉 VALIDATION COMPLETE!
QuickNode Mainnet endpoint is ready for trading!
```

---

## 🚨 **TROUBLESHOOTING**

### **Problem: "Invalid Host header" lub 401 Unauthorized**
**Rozwiązanie:**
- Sprawdź czy skopiowałeś pełny URL z kluczem API
- Upewnij się że endpoint jest dla Mainnet, nie Devnet
- Sprawdź czy nie ma literówek w .env

### **Problem: "Rate limit exceeded"**
**Rozwiązanie:**
- To normalne dla Build Plan
- Sprawdź limity w panelu QuickNode
- Rozważ upgrade jeśli potrzebne

### **Problem: Connection timeout**
**Rozwiązanie:**
- Sprawdź połączenie internetowe
- Sprawdź status QuickNode: https://status.quiknode.pro
- Spróbuj innego regionu endpoint

---

## ✅ **KRYTERIA SUKCESU**

Zadanie jest ukończone gdy:

1. ✅ **Mainnet endpoint utworzony** w panelu QuickNode
2. ✅ **URLs skopiowane** do .env
3. ✅ **Walidacja przeszła** - skrypt zwraca sukces
4. ✅ **RPC calls działają** - getVersion, getSlot, getAccountInfo
5. ✅ **Rate limits OK** - brak błędów 429

---

## 🎯 **NASTĘPNE KROKI**

Po ukończeniu tego zadania:

1. **Implement SOL Momentum Strategy** - implementacja strategii tradingowej
2. **Setup Paper Trading Infrastructure** - infrastruktura do symulacji
3. **Basic Risk Management** - podstawowe zarządzanie ryzykiem

---

## 📞 **WSPARCIE**

Jeśli napotkasz problemy:
1. Sprawdź [QuickNode Documentation](https://www.quicknode.com/docs/solana)
2. Sprawdź status: https://status.quiknode.pro
3. Skontaktuj się z QuickNode Support
4. Uruchom ponownie skrypt walidacyjny

**Powodzenia! 🚀**
