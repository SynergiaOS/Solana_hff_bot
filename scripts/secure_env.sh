#!/bin/bash
# THE OVERMIND PROTOCOL - Secure .env file

set -e

ENV_FILE=".env"
ENV_EXAMPLE_FILE=".env.example"
ENV_TEMPLATE_FILE="config/environments/.env.template"
GITIGNORE_FILE=".gitignore"

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
  warn "Plik $ENV_FILE nie istnieje. Tworzenie z szablonu..."
  
  if [ -f "$ENV_TEMPLATE_FILE" ]; then
    cp "$ENV_TEMPLATE_FILE" "$ENV_FILE"
    log "Utworzono $ENV_FILE z szablonu $ENV_TEMPLATE_FILE"
  elif [ -f "$ENV_EXAMPLE_FILE" ]; then
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    log "Utworzono $ENV_FILE z przykładu $ENV_EXAMPLE_FILE"
  else
    error "Nie znaleziono pliku szablonu. Utwórz plik $ENV_FILE ręcznie."
    exit 1
  fi
fi

# Ustaw bezpieczne uprawnienia dla pliku .env
log "Ustawianie bezpiecznych uprawnień dla pliku $ENV_FILE..."
chmod 600 "$ENV_FILE"
success "Ustawiono uprawnienia 600 (tylko właściciel może czytać/pisać) dla $ENV_FILE"

# Sprawdź czy plik .env jest w .gitignore
if [ -f "$GITIGNORE_FILE" ]; then
  if ! grep -q "^$ENV_FILE$" "$GITIGNORE_FILE"; then
    warn "Plik $ENV_FILE nie jest w .gitignore. Dodawanie..."
    echo "" >> "$GITIGNORE_FILE"
    echo "# Sensitive environment variables" >> "$GITIGNORE_FILE"
    echo "$ENV_FILE" >> "$GITIGNORE_FILE"
    success "Dodano $ENV_FILE do .gitignore"
  else
    log "Plik $ENV_FILE jest już w .gitignore"
  fi
else
  warn "Plik .gitignore nie istnieje. Tworzenie..."
  echo "# Sensitive environment variables" > "$GITIGNORE_FILE"
  echo "$ENV_FILE" >> "$GITIGNORE_FILE"
  success "Utworzono .gitignore z wpisem dla $ENV_FILE"
fi

# Sprawdź czy są klucze API w pliku .env
log "Sprawdzanie kluczy API w pliku $ENV_FILE..."

required_keys=(
  "OPENAI_API_KEY"
  "HELIUS_API_KEY"
  "QUICKNODE_API_KEY"
)

missing_keys=0
for key in "${required_keys[@]}"; do
  if ! grep -q "^$key=" "$ENV_FILE" || grep -q "^$key=$" "$ENV_FILE" || grep -q "^$key=your-" "$ENV_FILE"; then
    warn "Brakujący lub nieprawidłowy klucz: $key"
    missing_keys=$((missing_keys+1))
  fi
done

if [ $missing_keys -gt 0 ]; then
  warn "Znaleziono $missing_keys brakujących lub nieprawidłowych kluczy API."
  warn "Uzupełnij brakujące klucze w pliku $ENV_FILE"
else
  success "Wszystkie wymagane klucze API są skonfigurowane."
fi

# Sprawdź czy nie ma commitów z plikiem .env
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git ls-files --error-unmatch "$ENV_FILE" >/dev/null 2>&1; then
    error "UWAGA: Plik $ENV_FILE jest śledzony przez git!"
    error "Usuń plik $ENV_FILE z repozytorium:"
    echo "  git rm --cached $ENV_FILE"
    echo "  git commit -m \"Remove $ENV_FILE from repository\""
  else
    success "Plik $ENV_FILE nie jest śledzony przez git."
  fi
fi

success "Zabezpieczanie pliku $ENV_FILE zakończone."
echo ""
echo "🔒 PAMIĘTAJ:"
echo "  1. NIGDY nie commituj pliku $ENV_FILE do repozytorium"
echo "  2. Regularnie zmieniaj klucze API"
echo "  3. Twórz kopie zapasowe pliku $ENV_FILE w bezpiecznym miejscu"
echo "  4. Ogranicz dostęp do pliku $ENV_FILE tylko dla uprawnionych osób"