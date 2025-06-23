# 🔐 THE OVERMIND PROTOCOL - Bezpieczeństwo pliku .env

## 📋 Zasady bezpieczeństwa pliku .env

### 1. Przechowywanie pliku .env
- ✅ Plik `.env` NIGDY nie powinien być commitowany do repozytorium
- ✅ Plik `.env` powinien mieć uprawnienia `chmod 600` (tylko owner może czytać/pisać)
- ✅ Plik `.env` powinien być dodany do `.gitignore`
- ✅ Regularne tworzenie zaszyfrowanych kopii zapasowych pliku `.env`

### 2. Zawartość pliku .env
- ✅ Wszystkie klucze API powinny być przechowywane w pliku `.env`
- ✅ Używaj zmiennych w URL-ach (np. `https://api.example.com/?api-key=${API_KEY}`)
- ✅ Unikaj hardcodowania kluczy w kodzie źródłowym
- ✅ Używaj różnych kluczy dla środowisk dev/staging/production

### 3. Rotacja kluczy
- ✅ Regularna rotacja kluczy co 90 dni
- ✅ Tworzenie kopii zapasowych przed rotacją
- ✅ Aktualizacja wszystkich środowisk po rotacji

## 🚀 Instrukcja konfiguracji pliku .env

### Konfiguracja początkowa:
```bash
# Skopiuj szablon
cp .env.example .env

# Ustaw bezpieczne uprawnienia
chmod 600 .env

# Edytuj plik i dodaj swoje klucze API
nano .env
```

### Zabezpieczanie pliku .env:
```bash
# Uruchom skrypt zabezpieczający
./scripts/secure_env.sh
```

### Tworzenie kopii zapasowej:
```bash
# Utwórz zaszyfrowaną kopię zapasową
./scripts/backup_env.sh
```

### Odzyskiwanie z kopii zapasowej:
```bash
# Odzyskaj plik .env z kopii zapasowej
openssl enc -d -aes-256-cbc -in ./backups/env/env_backup_YYYYMMDD_HHMMSS.enc -out .env -pass file:~/.overmind_backup_password
```

## ⚠️ Procedura w przypadku wycieku kluczy API

1. **Natychmiastowe działania:**
   - Dezaktywuj skompromitowane klucze API w panelach dostawców
   - Wygeneruj nowe klucze API
   - Zaktualizuj plik `.env` z nowymi kluczami
   - Zrestartuj wszystkie usługi

2. **Analiza bezpieczeństwa:**
   - Sprawdź logi pod kątem nieautoryzowanego dostępu
   - Sprawdź historię git pod kątem przypadkowego commitowania pliku `.env`
   - Przeprowadź audyt bezpieczeństwa systemu

3. **Zapobieganie w przyszłości:**
   - Przeszkol zespół w zakresie bezpieczeństwa kluczy API
   - Rozważ użycie dedykowanego systemu zarządzania sekretami (np. HashiCorp Vault)
   - Wdrożenie automatycznych testów bezpieczeństwa w CI/CD

## 📝 Przykładowa zawartość pliku .env

```
# THE OVERMIND PROTOCOL - Environment Configuration
# =================================================

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key

# Helius API
HELIUS_API_KEY=your-helius-api-key
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=${HELIUS_API_KEY}

# QuickNode API
QUICKNODE_API_KEY=your-quicknode-api-key
QUICKNODE_RPC_URL=https://your-endpoint.quiknode.pro/${QUICKNODE_API_KEY}

# Trading Configuration
SNIPER_TRADING_MODE=paper
SNIPER_MAX_POSITION_SIZE=1.0
```