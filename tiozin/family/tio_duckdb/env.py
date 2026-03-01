from environs import Env

_env = Env(expand_vars=True)

# ===============================================
#           PostgreSQL
# ===============================================
# PGHOST - PostgreSQL server hostname.
PGHOST = _env("PGHOST", "localhost")

# PGPORT - PostgreSQL server port.
PGPORT = _env.int("PGPORT", 5432)

# PGDATABASE - PostgreSQL database name.
PGDATABASE = _env("PGDATABASE", "postgres")

# PGUSER - PostgreSQL username for authentication.
PGUSER = _env("PGUSER", "postgres")

# PGPASSWORD - PostgreSQL password for authentication.
PGPASSWORD = _env("PGPASSWORD", "postgres")

# PGSCHEMA - Default PostgreSQL schema.
PGSCHEMA = _env("PGSCHEMA", "public")
