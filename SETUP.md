# Einrichtung GitHub-Profil (sidneyerklaert)

GitHub zeigt eine Profil-README nur, wenn das Repo **öffentlich** ist und genauso heißt wie der Benutzername: `sidneyerklaert/sidneyerklaert`.

## Dateien
- `README.md` – bindet `dark_mode.svg` / `light_mode.svg` per `<picture>` ein (je nach Hell/Dunkel-Modus des Besuchers).
- `today.py` – rechnet Uptime und GitHub-Stats aus und schreibt beide SVGs neu. Nur Standardbibliothek.
- `ascii.txt` / `ascii_dark.txt` – ASCII-Porträt für hell/dunkel (44 × 37 Zeichen).
- `tools/make_ascii.py` – erzeugt `ascii.txt` aus einem Foto (lokal, braucht `pip install pillow`).
- `cache/stats.json`, `cache/loc.json` – zuletzt geholte Zahlen; Repo-Namen sind gehasht, private Namen landen also nicht im öffentlichen Repo.
- `.github/workflows/build.yml` – läuft täglich und bei jedem Push.

## Porträt neu erzeugen
Das Foto liegt bewusst nicht im Repo. Neu erzeugen (lokal):
```bash
pip install pillow "rembg[cpu]"
python tools/make_ascii.py foto.png --rembg --cols 44 --rows 37 --crop 90,20,500,576 --flatten 0.9 --gamma 1.1 --blur 12   # Werte für das 576×576-Foto
python today.py --offline
```
Ergebnis: `ascii.txt` (hell) und `ascii_dark.txt` (dunkel, invertiert).

## Offen
- Optional: `Türkçe` bei `Languages.Real` in `today.py` ergänzen.

## Veröffentlichen
1. Auf GitHub ein **öffentliches** Repo `sidneyerklaert` anlegen (leer, ohne README).
2. Token anlegen: Settings → Developer settings → Personal access tokens → Fine-grained.
   - Repository access: *All repositories* (damit private Commits/Zeilen mitgezählt werden)
   - Permissions: *Contents: Read-only*, *Metadata: Read-only*
   - Alternativ Classic Token mit `repo` und `read:user`.
3. Im neuen Repo: Settings → Secrets and variables → Actions → *New repository secret* → Name `ACCESS_TOKEN`, Wert = Token.
4. Pushen:
   ```bash
   git remote add origin git@github.com:sidneyerklaert/sidneyerklaert.git
   git push -u origin main
   ```
5. Actions-Tab öffnen und prüfen, ob „Profil-SVGs aktualisieren“ grün durchläuft (oder manuell über *Run workflow* starten).

## Lokal testen
```bash
python today.py --offline     # rendert aus cache/stats.json
ACCESS_TOKEN=… python today.py # holt live Zahlen
```

Hinweis: Öffentlich wird nur dieses eine Repo. Die übrigen Repos bleiben privat, niemand sieht Namen oder Inhalte. Die Stats zeigen nur Summen (Anzahl, Commits, Codezeilen) über alle eigenen Repos.
