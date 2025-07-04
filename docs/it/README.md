# Importatore di Playlist per YouTube Music

Importa le tue playlist da file JSON (esportati da altre piattaforme) su YouTube Music per migrazione, ripristino di
backup o sincronizzazione multipiattaforma.

---

## Descrizione

`my_youtube_music_playlists_importer.py` è uno script Python da riga di comando progettato per importare le tue playlist
su YouTube Music da file JSON generati da strumenti
come [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader).

Questo script si connette al tuo account YouTube Music tramite `ytmusicapi` e permette di:

- Creare nuove playlist (o utilizzare quelle esistenti)
- Cercare e aggiungere brani per nome e artista
- Prevenire duplicati (opzionale)
- Gestire errori API transitori con retry (ad esempio HTTP 409 Conflict)

Questo strumento è ideale per:

- Migrare la tua libreria musicale da Spotify a YouTube Music
- Ricostruire playlist dopo il passaggio a un'altra piattaforma
- Mantenere backup sincronizzati su più servizi
- Imparare l'automazione con l'API non ufficiale di YouTube Music usando Python

Il progetto è rilasciato sotto licenza MIT ed è destinato a scopi educativi e personali.

---

## Funzionalità

- Importa playlist da un **file JSON esportato da script di downloader di Spotify**
- Opzionalmente **elimina playlist esistenti** con lo stesso nome prima di importare
- **Prevenzione dei duplicati** (comportamento predefinito)
- Flag opzionale per **consentire duplicati** nelle playlist importate
- Implementa **retry con backoff esponenziale** per errori transitori 409 Conflict
- Delay configurabile tra le chiamate API per evitare rate limiting
- **Logging** su console e file per audit e debug
- **Portabile** – funziona su Windows, macOS e Linux

---

## Requisiti

- Python 3.10 o superiore
- [ytmusicapi](https://ytmusicapi.readthedocs.io/)
- Un **account YouTube Music** (non è richiesto Premium)
- I tuoi **header di autenticazione** esportati dal browser per autenticare `ytmusicapi`

Installa le dipendenze con:

```shell
pip install -r requirements.txt
````

---

## Configurazione

1. **Clona il repository**

    ```shell
    git clone https://github.com/yourusername/my_youtube_music_playlists_importer.git
    cd my_youtube_music_playlists_importer
    ```

2. **Crea il tuo file `.env`**

   Copia l'esempio fornito:

    ```shell
    cp .env.example .env
    ```

3. **Modifica `.env` e definisci le tue variabili**

   **Obbligatorie:**

    - `HEADERS_RAW_FILE`: Percorso al file di testo con gli header esportati dalle DevTools del browser.

   **Opzionali:**

    - `AUTH_GENERATED_FILE`: Percorso al file di autenticazione generato (default: ./browser.json)
    - `YT_API_DELAY_SECONDS`: Delay tra l'aggiunta di brani (default: 1)
    - `YT_API_MAX_RETRIES`: Numero massimo di retry per errori 409 Conflict (default: 3)
    - `LOG_DIR`: Directory per i log (default: directory dello script)
    - `LOG_LEVEL`: Livello di log (default: INFO)

### Autenticazione browser con `ytmusicapi`

Questo script utilizza l'**autenticazione basata su browser** con `ytmusicapi`, il che richiede di copiare gli header
delle richieste dopo aver effettuato l'accesso a [music.youtube.com](https://music.youtube.com).

#### Perché è necessario?

A differenza delle API ufficiali, YouTube Music non fornisce un metodo diretto di autenticazione per gli sviluppatori.
`ytmusicapi` funziona simulando la tua sessione browser, permettendo di eseguire azioni come se fossi tu, utilizzando i
cookie e gli header di autenticazione.

#### Come estrarre gli header da YouTube Music

1. **Accedi** al tuo account YouTube Music nel browser (consigliati Chrome o Firefox).
2. Apri le **DevTools (F12)**.
3. Vai alla scheda **Network**.
4. Ricarica la pagina per catturare le richieste.
5. Cerca una richiesta **POST** a `music.youtube.com` e ispeziona gli header. Il modo più semplice è filtrare
   per `browse`.
6. Copia tutti i **Request Headers** (in Firefox: tasto destro > copia > copia request headers).

Per una guida dettagliata passo-passo, consulta
la [documentazione di setup di ytmusicapi](https://ytmusicapi.readthedocs.io/en/latest/setup/browser.html).

#### Salvataggio degli header

Dopo aver copiato correttamente gli header:

- Crea un file chiamato `headers_raw.txt` nella directory del progetto.
- Incolla gli header e salva il file.

> ⚠️ **Nota di sicurezza:**
> Questo file contiene informazioni di autenticazione legate al tuo account Google. Mantienilo **privato**, non
> inserirlo sotto controllo versione e conservalo in un luogo sicuro.

---

## Esempio di struttura del file JSON

Il file JSON di input deve contenere un elenco di playlist, ognuna con la seguente struttura minima:

```json
[
  {
    "playlist_name": "Le mie canzoni preferite",
    "description": "Descrizione opzionale della playlist",
    "tracks": [
      {
        "name": "Titolo del brano",
        "artist": "Nome dell'artista"
      },
      {
        "name": "Un'altra canzone",
        "artist": "Un altro artista"
      }
    ]
  },
  {
    "playlist_name": "Chill Vibes",
    "description": "",
    "tracks": [
      {
        "name": "Chill Song 1",
        "artist": "Chill Artist"
      }
    ]
  }
]
````

### ✅ **Campi obbligatori**

- `playlist_name`: Nome della playlist da creare o aggiornare
- Ogni oggetto track deve includere:

  - `name`: Titolo del brano
  - `artist`: Artista del brano

### ℹ️ **Campi opzionali**

- `description`: Descrizione della playlist (può essere vuota)

> ⚠️ **Nota:**
> Il file esportato da [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader) è
> compatibile di default.
> Se utilizzi un tuo esportatore, assicurati che produca JSON con questa struttura.

---

## Utilizzo

### Importare playlist su YouTube Music

```shell
python my_youtube_music_playlists_importer.py --playlists_file /percorso/a/playlists.json
```

### Consentire brani duplicati nelle playlist

```shell
python my_youtube_music_playlists_importer.py --playlists_file /percorso/a/playlists.json --allow_duplicates
```

### Eliminare playlist esistenti con lo stesso nome prima di importare

```shell
python my_youtube_music_playlists_importer.py --playlists_file /percorso/a/playlists.json --delete_if_exists
```

---

## Sommario output

Al termine, lo script registrerà:

-Totale playlist create
-Totale playlist eliminate
-Totale playlist esistenti (non eliminate)
-Totale brani aggiunti con successo
-Totale brani saltati per prevenzione duplicati
-Totale brani non aggiunti (non trovati o errore API)
-Tempo totale di esecuzione

---

## Disclaimer

Questo script è fornito solo a scopo educativo.
Usalo responsabilmente con il tuo account YouTube Music.
L'autore non si assume alcuna responsabilità per uso improprio o perdita di dati causata dal suo utilizzo.
Il codice è pulito e privo di componenti malevoli.

## Avviso di marchio registrato

YouTube e YouTube Music sono marchi registrati di Google LLC.
Questo progetto **non è affiliato, sponsorizzato o approvato da Google** in alcun modo.
Tutti i riferimenti a YouTube Music sono effettuati esclusivamente a scopo informativo ed educativo.

---

## Licenza

Questo progetto è distribuito sotto licenza [MIT](../../LICENSE).
