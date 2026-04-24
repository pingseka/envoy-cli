# envoy-cli

> A CLI tool for managing and syncing `.env` files across multiple environments with secret masking and diff support.

---

## Installation

```bash
pip install envoy-cli
```

Or with pipx for isolated installs:

```bash
pipx install envoy-cli
```

---

## Usage

```bash
# Initialize envoy in your project
envoy init

# Sync .env from staging to production (secrets masked in output)
envoy sync --from staging --to production

# Show a diff between two environment files
envoy diff .env.staging .env.production

# Pull the latest .env for a specific environment
envoy pull --env development

# Push local changes and mask sensitive values in logs
envoy push --env staging --mask-secrets
```

A typical workflow:

```bash
envoy init
envoy pull --env development
# make your changes...
envoy diff .env .env.production
envoy push --env production
```

---

## Configuration

Envoy reads from an `envoy.toml` file in your project root:

```toml
[envoy]
environments = ["development", "staging", "production"]
mask_keys = ["SECRET_KEY", "DATABASE_URL", "API_TOKEN"]
```

---

## License

MIT © [envoy-cli contributors](https://github.com/your-org/envoy-cli)