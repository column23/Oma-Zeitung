# Oma-Zeitung

Eine tägliche Online-Zeitung im klassischen Zeitungslayout - für die Nutzung auf einem Tablet
(getestet für Samsung Galaxy Tab A 10.1, 1920×1200). Rubriken: **Lokal** (Flensburg/Schleswig-Holstein),
**Welt**, **Sport** (Tennis), **Wetter**, **Auf den Tag vor X Jahren**, dazu ein **Archiv**,
**Spiele** (Sudoku, Kreuzworträtsel, Solitär) und **Druckansicht/PDF-Export**.

Die App ist als **Progressive Web App (PWA)** gebaut: installierbar auf dem Homescreen,
läuft im Vollbild und cached die zuletzt geladene Ausgabe für kurze Offline-Phasen.

## Zwei Betriebsarten

Die Zeitung kann auf zwei Wegen laufen:

1. **Kostenlos in der Cloud (empfohlen, „von überall erreichbar")** – GitHub Actions erzeugt
   jeden Morgen automatisch die neue Ausgabe und veröffentlicht sie als statische Seite auf
   GitHub Pages. Kein eigener Server, kein dauerlaufender PC, keine laufenden Kosten. Siehe
   Abschnitt **„Cloud-Betrieb"** weiter unten.
2. **Lokal / im Heimnetz** – die Ausgabe wird auf einem eigenen Rechner erzeugt und über einen
   kleinen Flask-Server ausgeliefert. Siehe Abschnitte 1–4.

In beiden Fällen liest das Frontend die Inhalte aus statischen JSON-Dateien unter
`frontend/data/` (erzeugt vom Skript `python -m backend.main`).

## Projektstruktur

```
Zeitung/
├── backend/
│   ├── config.py            Zentrale Konfiguration (.env, RSS-Feeds, Wetter-Ort, ...)
│   ├── db.py                 SQLite-Speicherung (eine Ausgabe pro Tag)
│   ├── claude_client.py      Wrapper für die Anthropic API
│   ├── fetch_news.py         RSS-Fetching + Zusammenfassung Lokal/Welt
│   ├── fetch_sport.py        RSS-Fetching + Zusammenfassung Sport/Tennis
│   ├── fetch_weather.py      Wetter für Flensburg (Open-Meteo)
│   ├── fetch_history.py      "Auf den Tag vor X Jahren" (Claude)
│   ├── games/
│   │   ├── sudoku.py          Sudoku-Generator
│   │   └── crossword.py       Kreuzworträtsel-Generator (Begriffe von Claude + Gitter-Algorithmus)
│   ├── export_static.py       Exportiert die Ausgaben als statische JSON (frontend/data/)
│   ├── main.py                Orchestrator - erzeugt die komplette Tagesausgabe (für Cronjob)
│   └── server.py              Flask-Server: liefert Frontend + JSON-API (nur für lokalen Betrieb)
├── frontend/                  Statisches HTML/CSS/JS (kein Framework), PWA-Manifest + Service Worker
│   └── data/                   Erzeugte Ausgaben als JSON (latest.json, index.json, <datum>.json)
├── data/                       SQLite-Datenbank (wird automatisch angelegt)
├── .github/workflows/daily.yml Tägliche Erzeugung + Veröffentlichung auf GitHub Pages
├── requirements.txt
├── .env.example
└── README.md
```

## 1. Einrichtung

### Voraussetzungen

- Python 3.10 oder neuer
- Ein Anthropic API-Key (https://console.anthropic.com/)

### Installation

```bash
cd Zeitung
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### Konfiguration

```bash
cp .env.example .env
```

Dann `.env` öffnen und den eigenen `ANTHROPIC_API_KEY` eintragen. Die übrigen Werte
(Modellname, Datenbankpfad, Port) können auf den Standardwerten bleiben.

Die RSS-Feed-URLs (NDR Schleswig-Holstein, shz.de, tagesschau.de) stehen in
[`backend/config.py`](backend/config.py). RSS-Adressen ändern sich gelegentlich - falls ein Feed
keine Artikel mehr liefert, dort die URL aktualisieren (auf der jeweiligen Webseite nach "RSS" suchen).

## 2. Erste Ausgabe erzeugen

```bash
python -m backend.main
```

Das Skript lädt die RSS-Feeds, lässt Claude die Artikel zusammenfassen, holt Wetter- und
Sport-Daten, erzeugt den historischen Rückblick sowie Sudoku und Kreuzworträtsel des Tages,
speichert alles in `data/omazeitung.db` **und exportiert die Ausgabe als JSON nach
`frontend/data/`**. Das dauert je nach Anzahl Artikel und Internetverbindung ca. 1-3 Minuten
(mehrere Claude-Aufrufe).

## 3. Lokal starten

```bash
python -m backend.server
```

Anschließend im Browser öffnen: **http://localhost:5000**

Der Server liefert sowohl das Frontend als auch die JSON-API (`/api/edition/latest`,
`/api/edition/<datum>`, `/api/editions`).

Zum schnellen Testen kann eine neue Ausgabe auch direkt über die API angestoßen werden
(praktisch für lokale Tests statt auf den Cronjob zu warten):

```bash
curl -X POST http://localhost:5000/api/generate
```

---

# Cloud-Betrieb (GitHub Pages) — von überall erreichbar, PC kann aus sein

Dieser Weg macht die Zeitung **kostenlos und rund um die Uhr** aus dem Internet erreichbar –
auch wenn dein eigener PC ausgeschaltet ist. GitHub übernimmt beides: das tägliche Erzeugen
der Ausgabe (statt Cronjob) und das Ausliefern der Seite (statt Server).

**So funktioniert es:** Ein fertig eingerichteter Workflow ([`.github/workflows/daily.yml`](.github/workflows/daily.yml))
läuft jeden Morgen automatisch, erzeugt die neue Ausgabe mit deinem Anthropic-Key und
veröffentlicht die statischen Dateien auf GitHub Pages. Es läuft kein Server – deshalb kann
auch niemand über das Internet deine API-Credits verbrauchen.

### Einmalige Einrichtung

**1. Erste Ausgabe lokal erzeugen** (damit die Seite von Anfang an Inhalt hat):

```bash
python -m backend.main
```

Dadurch entstehen die Dateien unter `frontend/data/` (`latest.json`, `index.json`,
`<datum>.json`). Diese werden mit eingecheckt.

**2. Projekt zu GitHub hochladen.** Ein neues, **privates oder öffentliches** Repository auf
GitHub anlegen und das Projekt hochladen:

```bash
git init
git add .
git commit -m "Oma-Zeitung"
git branch -M main
git remote add origin https://github.com/<DEIN-NAME>/<REPO>.git
git push -u origin main
```

> Wichtig: Die Datei `.env` mit deinem API-Key wird durch `.gitignore` **nicht** hochgeladen –
> das ist so gewollt. Der Key kommt im nächsten Schritt sicher als „Secret" hinterlegt.

**3. API-Key als Secret hinterlegen.** Im GitHub-Repo:
`Settings` → `Secrets and variables` → `Actions` → `New repository secret`
- Name: `ANTHROPIC_API_KEY`
- Wert: dein Anthropic-Key (`sk-ant-...`)

**4. GitHub Pages aktivieren.** Im Repo: `Settings` → `Pages` →
unter „Build and deployment" bei **Source** `GitHub Actions` auswählen.

**5. Ersten Lauf starten.** Im Repo: `Actions` → Workflow „Tägliche Ausgabe erstellen &
veröffentlichen" → `Run workflow`. Nach ~2–3 Minuten ist die Seite online unter:

```
https://<DEIN-NAME>.github.io/<REPO>/
```

Diese Adresse funktioniert von jedem Gerät mit Internet – Handy, anderes Tablet, unterwegs.
Ab dann erzeugt GitHub die Zeitung jeden Morgen automatisch neu (Uhrzeit im Workflow unter
`cron:` einstellbar; Standard 05:00 UTC = 7 Uhr Sommerzeit).

### Kosten

- GitHub Actions & Pages: für dieses kleine Projekt **kostenlos**.
- Anthropic API: pro Tagesausgabe wenige Cent. Guthaben unter
  [console.anthropic.com](https://console.anthropic.com/) → „Plans & Billing".

### PWA auf dem Tablet (Cloud-Variante)

Auf dem Tablet einfach die GitHub-Pages-Adresse in Chrome öffnen und wie unten beschrieben
„Zum Startbildschirm hinzufügen". Kein lokaler Server, kein gleiches WLAN nötig.

---

## 4. Cronjob einrichten (tägliche Erzeugung) — nur für lokalen Betrieb

> Nur nötig, wenn du **nicht** den Cloud-Betrieb (oben) nutzt, sondern lokal/im Heimnetz.

Die Ausgabe sollte einmal morgens automatisch erzeugt werden, bevor die Zeitung gelesen wird.

### Linux/macOS (crontab)

```bash
crontab -e
```

Zeile hinzufügen (Beispiel: täglich um 6:00 Uhr):

```
0 6 * * * cd /pfad/zu/Zeitung && /pfad/zu/Zeitung/.venv/bin/python -m backend.main >> /pfad/zu/Zeitung/data/cron.log 2>&1
```

### Windows (Aufgabenplanung)

1. "Aufgabenplanung" öffnen → "Aufgabe erstellen"
2. Trigger: täglich, z. B. 06:00 Uhr
3. Aktion: Programm starten
   - Programm/Skript: `C:\Pfad\zu\Zeitung\.venv\Scripts\python.exe`
   - Argumente: `-m backend.main`
   - Starten in: `C:\Pfad\zu\Zeitung`

### Server dauerhaft laufen lassen

Der Flask-Server (`backend/server.py`) muss separat dauerhaft laufen (z. B. über `systemd`,
`pm2`, einen Windows-Dienst oder einfach ein Terminal-Fenster/`screen`/`tmux` auf einem
Heim-Server), damit das Tablet die Zeitung jederzeit abrufen kann. Für den produktiven
Betrieb empfiehlt sich zusätzlich ein WSGI-Server wie `waitress` oder `gunicorn` anstelle
des eingebauten Flask-Entwicklungsservers.

## 5. PWA auf dem Tablet installieren (Samsung Galaxy Tab A 10.1)

1. Sicherstellen, dass der Server erreichbar ist (gleiches WLAN, z. B.
   `http://<IP-des-Servers>:5000`).
2. Auf dem Tablet mit **Chrome** die Adresse öffnen.
3. Chrome-Menü (drei Punkte oben rechts) → **"Zum Startbildschirm hinzufügen"**
   (bzw. es erscheint automatisch ein Banner "App installieren").
4. Namen bestätigen ("Oma-Zeitung") → **Hinzufügen**.
5. Auf dem Homescreen erscheint nun ein Icon. Beim Start über dieses Icon öffnet sich die
   App im Vollbildmodus ohne Browser-Adressleiste.

Nach der ersten Installation lädt der **Service Worker** die App-Oberfläche und die zuletzt
angezeigte Ausgabe automatisch für die Offline-Nutzung vor. Fällt das WLAN kurz aus, wird
weiterhin die zuletzt geladene Ausgabe angezeigt (mit einem Hinweisbanner).

## 6. Schriftgröße & Bedienung

- Oben rechts befinden sich die Buttons **A- / A / A+** zur Anpassung der Schriftgröße.
  Die Wahl wird im Browser gespeichert und beim nächsten Besuch automatisch übernommen.
- Navigation zwischen **Titelseite**, **Spiele** und **Archiv** über die großen Reiter oder
  per Wisch-Geste (nach links/rechts wischen).
- Über den Button **"Drucken / PDF"** lässt sich die aktuelle Ausgabe drucken oder (über den
  Druckdialog des Browsers, "Als PDF speichern") als PDF exportieren.

## 7. Spiele

- **Sudoku**: täglich neues Rätsel (mittlerer Schwierigkeitsgrad), Eingabe über ein
  Zahlenfeld unterhalb des Gitters.
- **Kreuzworträtsel**: Begriffe werden von Claude passend zu den Tagesnachrichten erzeugt und
  automatisch zu einem Gitter zusammengesetzt. Eingabe direkt in die Gitterfelder.
- **Solitär (Klondike)**: eigenständiges Kartenspiel, komplett clientseitig, mit Touch-Drag&Drop
  (kurzes Antippen einer Karte versucht automatisch, sie auf einen passenden Ablagestapel zu legen).

## Hinweise

- Alle Texte (Nachrichten-Zusammenfassungen, historischer Rückblick, Kreuzworträtsel-Begriffe)
  werden von Claude (Anthropic API) erzeugt. Eine entsprechende Kennzeichnung ("Erstellt mit
  Künstlicher Intelligenz") befindet sich im Footer jeder Seite.
- Es werden bewusst keine wörtlichen Zitate aus den Originalartikeln übernommen; stattdessen
  wird bei jeder Meldung ein Link zur Originalquelle angezeigt.
- Das Frontend verwendet bewusst kein JavaScript-Framework, keine Web-Fonts und kaum
  Animationen, um auch auf leistungsschwächeren Tablets flüssig zu laufen.
