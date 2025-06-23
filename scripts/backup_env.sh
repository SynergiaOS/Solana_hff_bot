#!/bin/bash
# THE OVERMIND PROTOCOL - Backup .env file

set -e

ENV_FILE=".env"
BACKUP_DIR="./backups/env"
BACKUP_FILE="${BACKUP_DIR}/env_backup_$(date +%Y%m%d_%H%M%S).enc"
PASSWORD_FILE="${HOME}/.overmind_backup_password"

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Funkcja do wyświetlania komunikatów
log() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Sprawdź czy plik .env istnieje
if [ ! -f "$ENV_FILE" ]; then
  error "Plik $ENV_FILE nie istnieje."
  exit 1
fi

# Utwórz katalog backupu jeśli nie istnieje
if [ ! -d "$BACKUP_DIR" ]; then
  log "Tworzenie katalogu backupu $BACKUP_DIR..."
  mkdir -p "$BACKUP_DIR"
  chmod 700 "$BACKUP_DIR"
fi

# Sprawdź czy openssl jest zainstalowany
if ! command -v openssl &> /dev/null; then
  error "openssl nie jest zainstalowany. Zainstaluj openssl aby kontynuować."
  exit 1
fi

# Generuj lub użyj istniejącego hasła do szyfrowania
if [ ! -f "$PASSWORD_FILE" ]; then
  log "Generowanie hasła do szyfrowania backupów..."
  openssl rand -base64 32 > "$PASSWORD_FILE"
  chmod 600 "$PASSWORD_FILE"
  success "Wygenerowano hasło do szyfrowania backupów w $PASSWORD_FILE"
fi

# Szyfruj plik .env
log "Tworzenie zaszyfrowanego backupu pliku $ENV_FILE..."
openssl enc -aes-256-cbc -salt -in "$ENV_FILE" -out "$BACKUP_FILE" -pass file:"$PASSWORD_FILE"

# Ustaw bezpieczne uprawnienia dla pliku backupu
chmod 600 "$BACKUP_FILE"

success "Utworzono zaszyfrowany backup pliku $ENV_FILE w $BACKUP_FILE"

# Wyświetl informacje o odzyskiwaniu
echo ""
echo "🔄 Aby odzyskać plik .env z backupu, użyj:"
echo "  openssl enc -d -aes-256-cbc -in $BACKUP_FILE -out $ENV_FILE -pass file:$PASSWORD_FILE"
echo ""
echo "🔒 Hasło do szyfrowania znajduje się w pliku: $PASSWORD_FILE"
echo "   ZACHOWAJ TEN PLIK W BEZPIECZNYM MIEJSCU!"