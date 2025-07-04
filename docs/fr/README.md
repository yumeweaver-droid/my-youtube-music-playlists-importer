# Importateur de Playlists pour YouTube Music

Importe vos playlists depuis des fichiers JSON (exportés d'autres plateformes) vers YouTube Music pour la migration, la
restauration de sauvegarde ou la synchronisation multi-plateforme.

---

## Description

`my_youtube_music_playlists_importer.py` est un script Python en ligne de commande conçu pour importer vos playlists
dans YouTube Music à partir de fichiers JSON générés par des outils tels
que [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader).

Ce script se connecte à votre compte YouTube Music via `ytmusicapi` et permet de :

- Créer de nouvelles playlists (ou mettre à jour des playlists existantes)
- Rechercher et ajouter des morceaux par nom et artiste
- Prévenir les doublons (optionnel)
- Effectuer des tentatives automatiques (retry) en cas d'erreurs API transitoires (par exemple, HTTP 409 Conflict)

Cet outil est idéal pour :

- Migrer votre bibliothèque musicale de Spotify vers YouTube Music
- Reconstituer vos playlists après un changement de plateforme
- Maintenir des sauvegardes synchronisées entre plusieurs services
- Apprendre l'automatisation de l'API YouTube Music avec Python

Le projet est distribué sous licence MIT et destiné à un usage personnel et éducatif.

---

## Fonctionnalités

- Importe des playlists depuis un **fichier JSON exporté par un script de téléchargement Spotify**
- Peut **supprimer des playlists existantes** portant le même nom avant l'importation
- **Prévention des doublons** (comportement par défaut)
- Option pour **autoriser les doublons** dans les playlists importées
- Implémente un **retry avec backoff exponentiel** pour les erreurs transitoires 409 Conflict
- Délai configurable entre les appels API pour éviter le rate limiting
- **Logging** sur la console et dans un fichier pour audit et débogage
- **Portable** – fonctionne sur Windows, macOS et Linux

---

## Prérequis

- Python 3.9 ou version supérieure
- [ytmusicapi](https://ytmusicapi.readthedocs.io/)
- Un **compte YouTube Music** (Premium non requis)
- Vos **headers d’authentification** exportés depuis votre navigateur pour authentifier `ytmusicapi`

Installez les dépendances avec :

```shell
pip install -r requirements.txt
````

---

## Configuration

1. **Clonez le dépôt**

    ```shell
    git clone https://github.com/yourusername/my_youtube_music_playlists_importer.git
    cd my_youtube_music_playlists_importer
    ```

2. **Créez votre fichier `.env`**

   Copiez l’exemple fourni :

    ```shell
    cp .env.example .env
    ```

3. **Modifiez `.env` et renseignez vos variables**

   **Obligatoire :**

    - `HEADERS_RAW_FILE` : Chemin vers le fichier texte contenant vos headers exportés depuis DevTools du navigateur.

   **Optionnel :**

    - `AUTH_GENERATED_FILE` : Chemin vers le fichier d’authentification généré (par défaut : ./browser.json)
    - `YT_API_DELAY_SECONDS` : Délai entre l’ajout de morceaux (par défaut : 1)
    - `YT_API_MAX_RETRIES` : Nombre maximal de tentatives pour les erreurs 409 Conflict (par défaut : 3)
    - `LOG_DIR` : Répertoire où stocker les logs (par défaut : répertoire du script)
    - `LOG_LEVEL` : Niveau de log (par défaut : INFO)

### Authentification via navigateur avec `ytmusicapi`

Ce script utilise **l’authentification basée sur le navigateur** via `ytmusicapi`, ce qui nécessite de copier vos
headers de requêtes YouTube Music après vous être connecté à [music.youtube.com](https://music.youtube.com).

#### Pourquoi est-ce nécessaire ?

Contrairement aux API officielles, YouTube Music ne fournit pas de méthode directe d’authentification pour les
développeurs.
`ytmusicapi` fonctionne en simulant votre session navigateur, ce qui lui permet d’exécuter des actions en votre nom
grâce à vos cookies et headers d’authentification.

#### Comment extraire vos headers YouTube Music

1. **Connectez-vous** à votre compte YouTube Music dans votre navigateur (Chrome ou Firefox recommandé).
2. Ouvrez les **Outils de développement (F12)**.
3. Allez dans l’onglet **Network**.
4. Actualisez la page pour capturer les requêtes.
5. Recherchez une requête **POST** vers `music.youtube.com` et inspectez ses headers. Le moyen le plus simple est de
   filtrer sur `browse`.
6. Copiez tous les **Request Headers** (sur Firefox : clic droit > copier > copier les headers de requête).

Pour un guide détaillé étape par étape, consultez
la [documentation d’installation de ytmusicapi](https://ytmusicapi.readthedocs.io/en/latest/setup/browser.html).

#### Sauvegarde de vos headers

Une fois les headers copiés correctement :

- Créez un fichier nommé `headers_raw.txt` dans le répertoire du projet.
- Collez le contenu des headers dans ce fichier et sauvegardez.

> ⚠️ **Note de sécurité :**
> Ce fichier contient des informations d’authentification liées à votre compte Google. Gardez-le **privé**, ne le
> committez pas dans un dépôt public et stockez-le en lieu sûr.

---

## Exemple de structure du fichier JSON

Le fichier JSON d’entrée doit contenir une liste de playlists, chacune avec la structure minimale suivante :

```json
[
  {
    "playlist_name": "Mes chansons préférées",
    "description": "Description optionnelle de cette playlist",
    "tracks": [
      {
        "name": "Titre de la chanson",
        "artist": "Nom de l'artiste"
      },
      {
        "name": "Une autre chanson",
        "artist": "Un autre artiste"
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

### ✅ **Champs requis**

- `playlist_name` : Nom de la playlist à créer ou mettre à jour
- Chaque objet track doit inclure :

  - `name` : Titre de la chanson
  - `artist` : Artiste de la chanson

### ℹ️ **Champs optionnels**

- `description` : Description de la playlist (peut être vide)

> ⚠️ **Note :**
> Le fichier exporté par [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader)
> est compatible par défaut.
> Si vous utilisez un autre exporteur, assurez-vous qu’il produise un JSON conforme à cette structure.

---

## Utilisation

### Importer des playlists dans YouTube Music

```shell
python my_youtube_music_playlists_importer.py --playlists_file /chemin/vers/playlists.json
```

### Autoriser les morceaux en doublon dans les playlists

```shell
python my_youtube_music_playlists_importer.py --playlists_file /chemin/vers/playlists.json --allow_duplicates
```

### Supprimer les playlists existantes avant import

```shell
python my_youtube_music_playlists_importer.py --playlists_file /chemin/vers/playlists.json --delete_if_exists
```

---

## Résumé du script

À la fin de l’exécution, le script affiche :

- Nombre total de playlists créées
- Nombre total de playlists supprimées
- Nombre total de playlists existantes (non supprimées)
- Nombre total de morceaux ajoutés avec succès
- Nombre total de morceaux ignorés (prévention des doublons)
- Nombre total de morceaux non ajoutés (non trouvés ou erreur API)
- Temps total d’exécution

---

## Avertissement

Ce script est fourni uniquement à des fins éducatives.
Utilisez-le de manière responsable avec votre compte YouTube Music.
L’auteur décline toute responsabilité en cas de mauvaise utilisation ou de perte de données.
Le code est propre et exempt de composants malveillants.

## Avertissement sur la marque

YouTube et YouTube Music sont des marques déposées de Google LLC.
Ce projet **n’est ni affilié, ni sponsorisé, ni approuvé par Google** de quelque manière que ce soit.
Toutes les références à YouTube Music sont uniquement destinées à des fins informatives et éducatives.

---

## Licence

Ce projet est sous licence [MIT](../../LICENSE).
