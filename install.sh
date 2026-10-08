#!/usr/bin/env bash
set -e

# Couleurs ANSI
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}🍅 Installation de pomo (Pomodoro CLI)...${RESET}"

TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"

INSTALL_URL="https://raw.githubusercontent.com/HinBenjamin/pomo/main/pomo"
TARGET_FILE="$TARGET_DIR/pomo"

echo "Téléchargement depuis GitHub..."
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$INSTALL_URL" -o "$TARGET_FILE"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TARGET_FILE" "$INSTALL_URL"
else
    echo "Erreur : curl ou wget requis pour l'installation." >&2
    exit 1
fi

chmod +x "$TARGET_FILE"

# Création du lien symbolique 'pomodoro'
ln -sf "$TARGET_FILE" "$TARGET_DIR/pomodoro"

echo -e "${GREEN}${BOLD}✓ pomo installé avec succès dans $TARGET_DIR/pomo${RESET}"

# Vérifier si ~/.local/bin est dans le PATH
case ":$PATH:" in
  *":$TARGET_DIR:"*) ;;
  *)
    echo -e "${YELLOW}⚠️ Attention : $TARGET_DIR n'est pas dans votre PATH.${RESET}"
    echo "Ajoutez cette ligne à votre ~/.bashrc ou ~/.zshrc :"
    echo -e "  ${BOLD}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
    ;;
esac

echo -e "\n${BOLD}Lancement rapide :${RESET}"
echo "  pomo              # Lance une session standard (25 min travail, 5 min pause)"
echo "  pomo 50 10        # 50 min travail, 10 min pause"
echo "  pomo --stats      # Tableau de bord des statistiques"
echo "  pomo --help       # Voir toutes les options"
