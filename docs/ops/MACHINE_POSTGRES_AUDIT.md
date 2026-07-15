# Machine audit — PostgreSQL (macOS / Homebrew)

**Host:** Apple Silicon Homebrew (`/opt/homebrew`)  
**Audit date:** 2026-03-20 (regenerate after major brew changes)

## Summary

| Finding | Detail |
|--------|--------|
| **Active server** | **PostgreSQL 18.3** (`postgresql@18`) — **LISTEN on 127.0.0.1:5432** and `[::1]:5432` |
| **Conflict risk** | **`postgresql@17` is configured with `port = 5432`** but its **service is stopped**. Starting both **@17** and **@18** will **contend for 5432** (one will fail or behave unpredictably). |
| **PostgreSQL 14** | Data cluster exists; **`port = 5434`** — does **not** conflict with 5432; service **not running** (`pg_isready` on 5434: no response). |
| **PostGIS** | Installed via Homebrew (`postgis`); usable with PG18 (extensions load per database). |
| **Docker / Postgres.app** | No Postgres containers observed while Docker checked; no `Postgres.app` under `/Applications`. |
| **Other DB ports** | 3306, 27017, 6379, 9000 — no listeners seen at audit time. |

## Installed Homebrew formulae (relevant)

- `postgresql@14`, `postgresql@17`, `postgresql@18`
- `postgis`, `libpq`

## Data directory footprint

| Cluster | Path | Approx size | `postgresql.conf` port |
|--------|------|-------------|-------------------------|
| 14 | `/opt/homebrew/var/postgresql@14` | ~42 MB | **5434** |
| 17 | `/opt/homebrew/var/postgresql@17` | **~6.5 GB** | **5432** |
| 18 | `/opt/homebrew/var/postgresql@18` | ~73 MB | default **5432** (commented `#port = 5432`) |

**Interpretation:** The large **@17** cluster likely holds historical work (e.g. former `suhail` DB). **@18** is the current target for this project (`suhail_pipeline` per repo `.env.example`).

## `brew services` snapshot

- `postgresql@18` — **started**
- `postgresql@14`, `postgresql@17` — **none** (not running as brew services)

## Upgrade / standardize on PostgreSQL 18 — recommended plan

### Already done (typical for this repo)

- PG18 running on **5432**, app DB **`suhail_pipeline`**, migrations applied, tests passing against PG18.

### If you still need data from the old PG17 cluster

1. **Do not** start PG17 while PG18 owns 5432.
2. Edit **`/opt/homebrew/var/postgresql@17/postgresql.conf`**: set **`port = 5433`** (or another free port).
3. `brew services start postgresql@17` (or run `postgres -D ...` manually).
4. `pg_dump` from 5433 (old DBs) → `pg_restore` / `psql` into PG18 on 5432 (create target DB, extensions, then restore).
5. Stop PG17 when finished: `brew services stop postgresql@17`.
6. Optional: after verified migration, **`brew uninstall postgresql@17`** and remove `/opt/homebrew/var/postgresql@17` **only after backup** (frees ~6.5 GB).

### If you do not need PG17 data

- Optional: `brew uninstall postgresql@17` and archive/remove the data directory after you confirm nothing else references it.

### PostgreSQL 14

- Only needed for legacy apps expecting 5434. If unused: `brew uninstall postgresql@14` after backup.

### PostGIS after PG upgrades

- For each database: `CREATE EXTENSION IF NOT EXISTS postgis;` (already done for `suhail_pipeline` in this project).

## Conflict prevention checklist

- [ ] Only **one** brew `postgresql@*` service bound to **5432** at a time.
- [ ] If keeping PG17 for dumps, set **`port = 5433`** (or stop PG18 temporarily — not recommended if others depend on it).
- [ ] Point **`DATABASE_URL`** at the intended host/port/db (this repo: PG18 / `suhail_pipeline`).
- [ ] Document team-standard: “local dev = PG18 on 5432”.

## Re-audit commands

```bash
brew list --formula | rg -i 'postgres|postgis'
brew services list | rg -i postgres
lsof -nP -iTCP:5432 -sTCP:LISTEN
ps aux | rg '[p]ostgres'
du -sh /opt/homebrew/var/postgresql@*
grep -E '^port' /opt/homebrew/var/postgresql@*/postgresql.conf
```
