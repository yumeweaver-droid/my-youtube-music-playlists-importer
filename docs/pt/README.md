# Importador de Playlists para YouTube Music

Importa suas playlists de arquivos JSON (exportados de outras plataformas) para o YouTube Music para migração,
restauração de backup ou sincronização multiplataforma.

---

## Descrição

`my_youtube_music_playlists_importer.py` é um script Python de linha de comando projetado para importar suas playlists
para o YouTube Music a partir de arquivos JSON gerados por ferramentas
como [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader).

Este script se conecta à sua conta do YouTube Music através do `ytmusicapi` e permite:

- Criar novas playlists (ou usar playlists existentes)
- Pesquisar e adicionar faixas pelo nome e artista
- Prevenir duplicatas (opcional)
- Realizar tentativas automáticas (retry) para erros de API transitórios (por exemplo, HTTP 409 Conflict)

Este projeto é ideal para:

- Migrar sua biblioteca musical do Spotify para o YouTube Music
- Reconstruir playlists ao trocar de plataforma
- Manter backups sincronizados entre diferentes serviços
- Aprender automação com a API não oficial do YouTube Music usando Python

O projeto é distribuído sob licença MIT e é destinado para uso pessoal e educacional.

---

## Funcionalidades

- Importa playlists de um **arquivo JSON exportado por scripts de download do Spotify**
- Opcionalmente **exclui playlists existentes** com o mesmo nome antes de importar
- **Prevenção de duplicatas** (comportamento padrão)
- Flag opcional para **permitir duplicatas** nas playlists importadas
- Implementa **retry com backoff exponencial** para erros transitórios 409 Conflict
- Delay configurável entre chamadas de API para evitar rate limiting
- **Logging** no console e em arquivo para auditoria e depuração
- **Portável** – funciona em Windows, macOS e Linux

---

## Requisitos

- Python 3.10 ou superior
- [ytmusicapi](https://ytmusicapi.readthedocs.io/)
- Uma **conta do YouTube Music** (não é necessário Premium)
- Seus **headers de autenticação** exportados do navegador para autenticar o `ytmusicapi`

Instale as dependências com:

```shell
pip install -r requirements.txt
````

---

## Configuração

1. **Clone o repositório**

    ```shell
    git clone https://github.com/yourusername/my_youtube_music_playlists_importer.git
    cd my_youtube_music_playlists_importer
    ```

2. **Crie o seu arquivo `.env`**

    Copie o exemplo fornecido:

    ```shell
    cp .env.example .env
    ```

3. **Edite o `.env` e defina suas variáveis**

    **Obrigatórias:**

    - `HEADERS_RAW_FILE`: Caminho para o arquivo de texto com os headers exportados do DevTools do navegador.

    **Opcionais:**

    - `AUTH_GENERATED_FILE`: Caminho para o arquivo de autenticação gerado (default: ./browser.json)
    - `YT_API_DELAY_SECONDS`: Delay entre a adição de faixas (default: 1)
    - `YT_API_MAX_RETRIES`: Número máximo de tentativas para erros 409 Conflict (default: 3)
    - `LOG_DIR`: Diretório para armazenar logs (default: local do script)
    - `LOG_LEVEL`: Nível de log (default: INFO)

### Autenticação via navegador com `ytmusicapi`

Este script utiliza **autenticação baseada no navegador** com `ytmusicapi`, exigindo que você copie os headers de
requisição do YouTube Music após fazer login em [music.youtube.com](https://music.youtube.com).

#### Por que isso é necessário?

Diferente de APIs oficiais, o YouTube Music não fornece um método direto de autenticação para desenvolvedores.
O `ytmusicapi` funciona simulando sua sessão do navegador, permitindo executar ações em sua conta usando seus cookies e
headers de autenticação.

#### Como extrair seus headers do YouTube Music

1. **Faça login** na sua conta do YouTube Music no navegador (Chrome ou Firefox recomendados).
2. Abra as **DevTools (F12)**.
3. Vá para a aba **Network**.
4. Atualize a página para capturar as requisições.
5. Procure uma requisição **POST** para `music.youtube.com` e inspecione os headers. O método mais simples é filtrar
   por `browse`.
6. Copie todos os **Request Headers** (no Firefox: clique direito > copiar > copiar request headers).

Para um guia detalhado passo a passo, consulte
a [documentação de setup do ytmusicapi](https://ytmusicapi.readthedocs.io/en/latest/setup/browser.html).

#### Salvando seus headers

Após copiar os headers corretamente:

- Crie um arquivo chamado `headers_raw.txt` no diretório do projeto.
- Cole o conteúdo dos headers neste arquivo e salve.

> ⚠️ **Nota de segurança:**
> Este arquivo contém informações de autenticação vinculadas à sua conta Google. Mantenha-o **privado**, não o adicione
> ao controle de versão e armazene-o em local seguro.

---

## Exemplo de estrutura do arquivo JSON

O arquivo JSON de entrada deve conter uma lista de playlists, cada uma com a seguinte estrutura mínima:

```json
[
  {
    "playlist_name": "Minhas músicas favoritas",
    "description": "Descrição opcional da playlist",
    "tracks": [
      {
        "name": "Título da música",
        "artist": "Nome do artista"
      },
      {
        "name": "Outra música",
        "artist": "Outro artista"
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

### ✅ **Campos obrigatórios**

- `playlist_name`: Nome da playlist a ser criada ou atualizada
- Cada objeto track deve incluir:

  - `name`: Título da música
  - `artist`: Artista da música

### ℹ️ **Campos opcionais**

- `description`: Descrição da playlist (pode ser vazia)

> ⚠️ **Nota:**
> O arquivo exportado pelo [My Spotify Playlists Downloader](https://github.com/novama/my-spotify-playlists-downloader) é compatível por padrão.
> Se usar outro exportador, garanta que produza JSON com esta estrutura.

---

## Uso

### Importar playlists para o YouTube Music

```shell
python my_youtube_music_playlists_importer.py --playlists_file /caminho/para/playlists.json
```

### Permitir faixas duplicadas nas playlists

```shell
python my_youtube_music_playlists_importer.py --playlists_file /caminho/para/playlists.json --allow_duplicates
```

### Excluir playlists existentes com o mesmo nome antes de importar

```shell
python my_youtube_music_playlists_importer.py --playlists_file /caminho/para/playlists.json --delete_if_exists
```

---

## Resumo do Output

Ao final, o script exibirá:

- Total de playlists criadas
- Total de playlists excluídas
- Total de playlists existentes (não excluídas)
- Total de faixas adicionadas com sucesso
- Total de faixas ignoradas por prevenção de duplicatas
- Total de faixas que falharam ao serem adicionadas (não encontradas ou erro de API)
- Tempo total de execução

---

## Aviso

Este script é fornecido apenas para fins educacionais.
Use-o com responsabilidade na sua conta do YouTube Music.
O autor não se responsabiliza por uso indevido ou perda de dados resultante do seu uso.
O código é limpo e livre de componentes maliciosos.

## Aviso de marca registrada

YouTube e YouTube Music são marcas registradas da Google LLC.
Este projeto **não é afiliado, patrocinado ou endossado pelo Google** de nenhuma forma.
Todas as referências ao YouTube Music são feitas exclusivamente para fins informativos e educacionais.

---

## Licença

Este projeto está licenciado sob a [Licença MIT](../../LICENSE).
