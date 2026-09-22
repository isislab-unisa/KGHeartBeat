# Containers

Run these commands from the repository root with Docker Engine and Compose v2.

## Batch analysis

Edit `src/configuration.json` to select your graphs, then run:

```bash
docker compose build kgheartbeat
docker compose run --rm kgheartbeat
```

The job runs `src/manager.py` once and exits. CSV, Turtle, logs and profiles are
saved to the host's `Analysis results/` directory. MongoDB is not required.
`docker compose up --build` also runs only this batch job by default.
The image includes the catalogue snapshots and runtime dependencies; optional
LLM experiments under `src/from_kg_to_csv` are excluded from its dependencies.
The container needs outbound network access for endpoint checks and KGSum.

Without Compose:

```bash
docker build -t kgheartbeat:local .
docker run --rm \
  --mount "type=bind,src=$PWD/src/configuration.json,dst=/app/src/configuration.json,readonly" \
  --mount "type=bind,src=$PWD/Analysis results,dst=/app/Analysis results" \
  kgheartbeat:local
```

`src/Dockerfile` is a compatibility symlink to the root Dockerfile; always use
the repository root as the build context.

## Optional MongoDB

```bash
docker compose --profile mongodb up -d mongodb
```

MongoDB uses the persistent `mongodb-data` named volume and is available to
containers at `mongodb:27017`. It has no published host port and no authentication;
this setup is intended for local use. For an authenticated external database,
set `MONGO_URI` and `DB_NAME` in an environment file and pass it with
`docker compose --env-file /path/to/file ...`. Use `--no-deps` with the backend or
import service when you do not want Compose to start the bundled database.

Batch results are not automatically inserted into MongoDB. After a completed
analysis, export and import them with:

```bash
docker compose --profile import run --rm --build import-results
```

This converts the host CSVs to JSON using the existing exporter, including saved
profiles, and upserts the JSON assessments by `(kg_id, analysis_date)` into
`KGHeartbeatDB.quality_analysis_data`. Repeating the command replaces matching
assessments instead of creating duplicates. It imports all exported JSON files,
including historical files already in `Analysis results/json_files/`.
Do not run it concurrently with a batch analysis or another import.

## Optional web app

```bash
docker compose --profile webapp up -d --build mongodb backend frontend assessment-api assessment-worker
```

Open <http://localhost:3001>. The catalogue API runs at <http://localhost:5006>
and the assessment API at <http://localhost:8000>. The API and worker share a
persistent `assessment-data` volume. The catalogue is initially empty until you
import results. Interactive assessments use their own saved jobs and downloads;
they do not automatically populate the MongoDB catalogue.

The explicit service list starts the web stack without running a batch analysis.
To start both together, use `docker compose --profile webapp up -d --build`.
The batch container still exits when its analysis finishes.

The SPARQL editor additionally needs an RDF store. You can configure an external
`SPARQL_ENDPOINT_URL`, or start the existing Fuseki setup:

```bash
docker compose --profile sparql up -d triplestore triplestore-init
```

This uses the web app's existing FAIR Turtle seed file and initializer. That
initializer **replaces the `fair` dataset when rerun**. MongoDB results are not
automatically synchronized into Fuseki.

Services bind to localhost for local use. For remote deployment, configure a
reverse proxy, authentication where needed, and browser-accessible URLs using
`docker/.env.example` as a template. Frontend URLs are build arguments and require
a rebuild after changes. Environment files, local dependencies, existing results
and credentials are excluded from image build contexts. To pass additional Python
runtime settings, use `docker compose run --rm -e NAME=value kgheartbeat`, or a
Compose override with `environment`/`env_file`.

Stop the services while retaining data:

```bash
docker compose --profile '*' down
```

Adding `--volumes` deletes named volumes, including MongoDB and saved assessment
jobs. Host files under `Analysis results/` are retained.

## Validation

```bash
docker compose config --quiet
docker compose --profile '*' config --quiet
docker compose build
docker compose run --rm kgheartbeat python -c 'import analyses, evaluate_fairness, evaluate_human_centered_acc'
```

Profile behavior and startup conditions follow the
[Docker Compose profiles documentation](https://docs.docker.com/compose/how-tos/profiles/).
