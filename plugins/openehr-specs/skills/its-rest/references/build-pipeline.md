# ITS-REST Build Pipeline

Build commands run from the `development/` directory within the `specifications-ITS-REST` repo.

## Quick Reference

```bash
# Initial setup
cd development
docker-compose build php
docker-compose run --rm php composer install

# Bundle all specs
make all

# Bundle a single spec
make bundle SPEC=ehr    # one of: overview|system|ehr|query|definition|demographic|admin

# Validate
make validate SPEC=ehr
make validate-all

# Live preview
./watch.sh ehr          # Opens Redocly preview at http://localhost:80

# Code generation
make generate SPEC=ehr LANG=kotlin
```

## Build Pipeline Per Spec

1. **Redocly bundle**: authoring YAML → single JSON (`computable/OAS/<spec>.openapi.json`)
2. **PHP transform**: JSON → three flavors: `-codegen`, `-validation`, `-html` (via `development/bin/generate_all`)
3. **Redocly YAML**: JSON flavors → YAML (`computable/OAS/<spec>-*.openapi.yaml`)
4. **Redocly HTML**: HTML docs → `docs/<spec>.html`

## Toolchain Details

- **Redocly CLI** (v1.33.1): bundles, lints, converts, and renders HTML
- **PHP tool** (`development/bin/generate_all`): transforms bundled JSON into three flavors
  - `Writer\Codegen` — codegen-friendly schemas (normalizes `$ref`, removes `format: uuid`, populates discriminator mappings)
  - `Writer\Validation` — validation-oriented spec
  - `Writer\Html` — extends Validation for doc rendering
- **swagger-cli**: additional validation
- Docker containers: `php` (PHP 8.3), `redocly`, `swagger-cli`

## Validation

```bash
# From development/ directory
./validate.sh <spec|all>

# Or via Make
make validate SPEC=<spec>
make validate-all
```

Validation runs:
- `redocly lint` on authoring YAML and built YAML variants
- `swagger-cli validate` on built YAML variants

## Live Preview

```bash
./watch.sh <spec>
```

Launches Redocly preview-docs on ports 80 and 32201.

## Code Generation

```bash
./generate.sh openapi <spec>   # OpenAPI Generator (multiple languages)
./generate.sh swagger <spec>   # Swagger Codegen (multiple languages)
./generate.sh single <spec> <lang> [extra options]

# Or via Make
make generate SPEC=<spec> LANG=<language>
make generate-all
```

Outputs go to `codegen/oas-<spec>/<language>` and `codegen/swagger-<spec>/<language>`.

## Further Details

For PHP tooling internals, Docker configuration, and troubleshooting, see `.junie/guidelines.md`
in the `specifications-ITS-REST` repository.
