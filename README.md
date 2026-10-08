# 🍅 pomo — Pomodoro CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform: macOS / Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)]()

Un minuteur Pomodoro élégant, moderne et interactif directement dans votre terminal, doté d'un affichage grand format en chiffres ASCII, d'un suivi visuel des sessions, de notifications système et d'un tableau de bord de statistiques.

```text
╭────────────────────────────────────────────────────────╮
│  🍅 SESSION 1/4 • [Recherche & Code]                   │
│  Progression : [▶] [ ] [ ] [ ]                         │
╰────────────────────────────────────────────────────────╯

             _    _         _    _ 
            / \  |_|   .   / \  / \
            \_/   |    .   \_/  \_/

       [Espace] Pause  •  [+] +1m  •  [-] -1m  •  [q] Quitter
```

---

## ✨ Fonctionnalités

- **Interface interactive plein écran (Curses)** : Grand affichage numérique de l'heure en chiffres ASCII.
- **Suivi visuel des sessions** : Barre de progression avec plusieurs styles disponibles :
  - Cases : `[✓] [▶] [ ] [ ]`
  - Blocs : `[■] [▣] [ ] [ ]`
  - Points : `● ◐ ○ ○`
  - Tomates : `🍅 ⏳ ⚪ ⚪`
- **Contrôles en temps réel** :
  - `Espace` : Mettre en pause / reprendre.
  - `+` / `=` : Ajouter 1 minute à la session en cours.
  - `-` : Retirer 1 minute.
  - `q` : Quitter proprement.
- **Notifications de bureau & alertes sonores** : Notifications système natives sur macOS (`osascript` / `afplay`) et Linux (`notify-send`).
- **Annonces vocales optionnelles (`--voice`)** : Synthèse vocale prévenant de la fin des sessions ou des pauses.
- **Tableau de bord statistique (`--stats`)** : Total des heures de concentration, objectif du jour avec barre de progression et historique des tâches récentes.
- **Cycles automatiques ou manuels** : Alternance automatique ou confirmée entre travail, pause courte et longue pause après un cycle complet.

---

## 🚀 Installation

### Méthode 1 : Installation automatique en une ligne (Recommandé)

Exécutez simplement cette commande dans votre terminal :

```bash
curl -fsSL https://raw.githubusercontent.com/HinBenjamin/pomo/main/install.sh | bash
```

Le script installe l'exécutable `pomo` (et le lien symbolique `pomodoro`) dans `~/.local/bin/`.

> [!NOTE]
> Assurez-vous que `~/.local/bin` est dans votre `PATH` (ajoutez `export PATH="$HOME/.local/bin:$PATH"` à votre `~/.zshrc` ou `~/.bashrc` si nécessaire).

---

### Méthode 2 : Avec `pipx` ou `pip`

```bash
pipx install git+https://github.com/HinBenjamin/pomo.git
```

ou :

```bash
pip install git+https://github.com/HinBenjamin/pomo.git
```

---

### Méthode 3 : Installation manuelle

```bash
git clone https://github.com/HinBenjamin/pomo.git
cd pomo
mkdir -p ~/.local/bin
cp pomo ~/.local/bin/pomo
chmod +x ~/.local/bin/pomo
```

---

## 📖 Utilisation

### Lancement standard

```bash
pomo
```
> Démarre une session standard de 25 minutes de travail, suivie d'une pause de 5 minutes.

### Spécifier les durées rapidement

```bash
# 50 minutes de travail, 10 minutes de pause
pomo 50 10
```

### Associer un nom de projet / tâche

```bash
pomo -t "Rapport d'écologie" -w 30 -b 5
```

### Options utiles

| Commande | Description |
|---|---|
| `pomo --stats` | Affiche le tableau de bord des statistiques et l'historique |
| `pomo --style tomatoes` | Utilise les émojis tomates (`🍅 ⏳ ⚪`) |
| `pomo --voice` | Active les annonces vocales en fin de session |
| `pomo --auto` | Enchaîne automatiquement travail et pauses sans confirmation |
| `pomo -n 6` | Configure un cycle de 6 sessions au lieu de 4 |
| `pomo -l 20` | Définit la longue pause à 20 minutes |
| `pomo --reset` | Réinitialise l'avancement du cycle en cours à zéro |
| `pomo --done 2` | Indique que 2 sessions ont déjà été faites |
| `pomo --add 1 -t "Revue bibliographique"` | Ajoute manuellement une session à l'historique |

---

## 📊 Tableau de bord statistique

Pour voir vos statistiques du jour et votre historique cumulé :

```bash
pomo --stats
```

Exemple d'affichage :

```text
╭────────────────────────────────────────────────────────╮
│  📊 TABLEAU DE BORD POMODORO                           │
├────────────────────────────────────────────────────────┤
│  📅 Aujourd'hui : 4 session(s)  •  1.7h (100m)
│  🎯 Objectif    : ■■■■■■■□□□□□□□ 50% (4/8)
│  🏆 Total cumul : 24 session(s)  •  10.0h (600m)
├────────────────────────────────────────────────────────┤
│  Dernières sessions du jour :
│    14:30  ✓  Analyse de données       (25m)
│    15:05  ✓  Rédaction stage          (25m)
│    15:40  ✓  Code C++                 (25m)
│    16:15  ✓  Revue biblio             (25m)
╰────────────────────────────────────────────────────────╯
```

Les données sont sauvegardées localement au format JSON dans `~/.pomodoro_history.json`.

---

## ⌨️ Raccourcis clavier (en session)

| Touche | Action |
|---|---|
| `Espace` | Mettre en pause ou reprendre le décompte |
| `+` ou `=` | Ajouter 1 minute |
| `-` | Retirer 1 minute |
| `q` | Quitter la session |

---

## 📦 Dépendances optionnelles

Le programme utilise uniquement la bibliothèque standard de Python (`curses`, `argparse`, etc.).  
Pour un rendu de police ASCII encore plus soigné, vous pouvez installer optionnellement `pyfiglet` :

```bash
pip install pyfiglet
```

---

## 📄 Licence

Ce projet est sous licence libre [MIT](LICENSE).
