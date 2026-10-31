# Einrichtung GitHub-Profil (sidneyerklaert)

GitHub zeigt eine Profil-README nur, wenn das Repo **öffentlich** ist und genauso heißt wie der Benutzername: `sidneyerklaert/sidneyerklaert`.

## Dateien
- `README.md` – bindet `dark_mode.svg` / `light_mode.svg` per `<picture>` ein (je nach Hell/Dunkel-Modus des Besuchers).
- `today.py` – rechnet Uptime und GitHub-Stats aus und schreibt beide SVGs neu. Nur Standardbibliothek.
- `ascii.txt` – das ASCII-Porträt (38 × 26 Zeichen).
- `tools/make_ascii.py` – erzeugt `ascii.txt` aus einem Foto (lokal, braucht `pip install pillow`).
- `cache/stats.json`, `cache/loc.json` – zuletzt geholte Zahlen; Repo-Namen sind gehasht, private Namen landen also nicht im öffentlichen Repo.
- `.github/workflows/build.yml` – läuft täglich und bei jedem Push.

## Vor dem Veröffentlichen (TODO)
1. **Geburtsdatum**: in `today.py` `BIRTHDATE` setzen und `PLACEHOLDER_BIRTHDATE = False`. Sonst steht nur „40 Jahre“ da.
2. **Foto**: `python tools/make_ascii.py dein-foto.jpg` ausführen (heller, ruhiger Hintergrund). Das aktuelle Porträt basiert auf dem Standard-Identicon.
3. **Handles prüfen**: TikTok und Threads in `ROWS` in `today.py`.
4. Optional: `Türkçe` bei `Languages.Real` ergänzen.

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

Hinweis: Die Stats zeigen Summen über alle eigenen Repos, auch private (nur Zahlen, keine Namen).
