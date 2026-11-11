"""Optional local check: pip install jsonschema (in a virtual environment)."""
from pathlib import Path
import json

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit("Install 'jsonschema' in .venv: python -m pip install jsonschema") from exc

root = Path(__file__).resolve().parents[1]
for name in ("SpotMap_Wakesurf_Passport_v1.schema.json", "SpotMap_Cable_Installation_v1.schema.json"):
    schema = json.loads((root / "contracts/jsonschema" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    print("Schema valid:", name)
schema = json.loads((root / "contracts/jsonschema/SpotMap_Wakesurf_Passport_v1.schema.json").read_text(encoding="utf-8"))
example = json.loads((root / "examples/synthetic/example_wakesurf_passport_synthetic.json").read_text(encoding="utf-8"))
Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)
print("Synthetic example valid")
