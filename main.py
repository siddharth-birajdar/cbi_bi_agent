import json
from crewai import Crew, Process
from agent import schema_analyst, dimensional_modeller, sql_writer
from tasks import schema_analysis, dimensional_modelling, sql_writing
from datamodels import PipelineOutput
from json_toon import json_to_toon

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

import json
from jsonschema import validate, ValidationError

DATASET_SCHEMA = {
    "type": "object",
    "properties": {
        "datasets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["table_name", "columns", "primary_key"],
                "properties": {
                    "table_name": {"type": "string"},
                    "description": {"type": "string"},
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "type"],
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "primary_key": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "foreign_keys": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["column", "references"],
                            "properties": {
                                "column": {"type": "string"},
                                "references": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    },
    "required": ["datasets"]
}


def validate_json(data: dict, verbose=False) -> bool:
    try:
        validate(instance=data, schema=DATASET_SCHEMA)
        return True
    except ValidationError as e:
        if verbose:
            print("❌ Validation error:", e.message)
            print("Path:", list(e.path))
        return False


def is_valid_input(data: dict) -> bool:
    # Lenient check FIRST (prevents false negatives)
    return (
        isinstance(data, dict)
        and "datasets" in data
        and isinstance(data["datasets"], list)
    )


def load_input(raw: str) -> tuple[str, bool]:
    content = raw.strip()

    try:
        with open(content, "r") as f:
            parsed = json.load(f)
    except Exception:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            print("\n[main] Input is plain text — run schema analyst.\n")
            return content, False

    # Lenient detection (no noisy errors)
    if is_valid_input(parsed):
        print("\n[main] Dataset input detected.\n")
        return json.dumps(parsed), True

    # Optional strict validation (only if needed)
    validate_json(parsed, verbose=True)

    print("\n[main] Unknown structure — run schema analyst.\n")
    return json.dumps(parsed), False






def get_input() -> str:
    """
    Supports:
    1. File path input
    2. Inline JSON
    3. Multi-line paste (ends with empty line)
    """
    raw = input("\nEnter file path OR paste JSON (press Enter twice to finish):\n> ").strip()

    # If it's likely a file path, return directly
    try:
        with open(raw, "r"):
            return raw
    except Exception:
        pass

    # If user pasted JSON in one line
    if raw.startswith("{") or raw.startswith("["):
        return raw

    # Otherwise, treat as multi-line input
    print("\nPaste multi-line content. Press Enter twice to finish:\n")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)

    return "\n".join(lines)



def print_model(model: PipelineOutput):
    print("\n" + "─" * 60)
    print("DIMENSIONAL MODEL")
    print("─" * 60)

    print("\nFACT TABLES")
    for fact in model.fact_tables:
        print(f"\n  {fact.name}")
        print(f"  Grain   : {fact.grain}")
        print(f"  Measures: {', '.join(fact.measures)}")
        print(f"  Columns :")
        for col in fact.columns:
            print(f"    - {col.name} ({col.data_type})")

    print("\nDIMENSION TABLES")
    for dim in model.dimension_tables:
        print(f"\n  {dim.name}")
        print(f"  Type    : {dim.dimension_type.value}")
        if dim.notes:
            print(f"  Notes   : {dim.notes}")
        print(f"  Columns :")
        for col in dim.columns:
            print(f"    - {col.name} ({col.data_type})")

    print("\n" + "─" * 60)


def ask_for_changes(model: PipelineOutput) -> tuple[PipelineOutput, bool]:
    """
    Prints the model and asks the user if they want changes.
    Loops until the user is satisfied.
    Returns the (possibly updated) model and whether to proceed.
    """
    while True:
        
        print("\nAre you happy with this model?")
        print("  [y] Yes, proceed")
        print("  [n] No, describe your changes")
        print("  [q] Quit")

        choice = input("\n> ").strip().lower()

        if choice == "y":
            return model, True

        elif choice == "q":
            print("\nExiting.")
            return model, False

        elif choice == "n":
            changes = input("\nDescribe the changes you want:\n> ").strip()

            print("\n[main] Rerunning dimensional modeller with your feedback...\n")

            refinement_crew = Crew(
                agents=[dimensional_modeller],
                tasks=[dimensional_modelling],
                process=Process.sequential,
                verbose=False,
            )

            result = refinement_crew.kickoff(inputs={
                "raw_input": (
                    f"Here is the current dimensional model:\n{model.model_dump_json(indent=2)}\n\n"
                    f"The user wants the following changes:\n{changes}\n\n"
                    f"Return an updated PipelineOutput JSON."
                ),
                "entity_map": ""
            })

            model = result.pydantic
            continue

        else:
            print("Please enter y, n, or q.")


def ask_for_sql() -> bool:
    print("\nDo you want to generate SQL DDL for this model?")
    print("  [y] Yes")
    print("  [n] No")
    choice = input("\n> ").strip().lower()
    return choice == "y"


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("─" * 60)
    print("DIMENSIONAL MODELLING AGENT")
    print("─" * 60)
    print("\nPaste your schema, SQL DDL, or enter a file path:")

    # Usage
    business_question = """Given the promotions run by retails store,
                            identify the key factors that influence the success of a promotion 
                            and provide recommendations for optimizing future promotions based on 
                            the dataset provided."""
    raw_input = "metadata.json" # get_input()
    content, is_structured = load_input(raw_input)
    # content = json_to_toon(json.loads(content))
    print(content)

    # ── Step 1: Schema analysis (conditional) ──
    if is_structured:
        entity_map = content
    else:
        schema_crew = Crew(
            agents=[schema_analyst],
            tasks=[schema_analysis],
            process=Process.sequential,
            verbose=False,
        )
        schema_result = schema_crew.kickoff(inputs={"raw_input": content})
        entity_map = schema_result.raw

    # ── Step 2: Dimensional modelling ──
    modelling_crew = Crew(
        agents=[dimensional_modeller],
        tasks=[dimensional_modelling],
        verbose=True,
    )
    modelling_result = modelling_crew.kickoff(inputs={"raw_input": "", "entity_map": entity_map})


    import pandas as pd

    # Convert JSON string to Python list of dictionaries
    data = json.loads(modelling_result.raw)
    data = pd.json_normalize(data)  # Normalize nested structures into flat tables



    data = json.loads(modelling_result.raw)

    rows = []

    # Fact tables
    for fact in data["fact_tables"]:
        for col in fact["columns"]:
            rows.append({
                "table_name": fact["name"],
                "column_name": col["name"],
                "data_type": col["data_type"],
                "table_role": "Fact",
                "dimension_type": None
            })

    # Dimension tables
    for dim in data["dimension_tables"]:
        for col in dim["columns"]:
            rows.append({
                "table_name": dim["name"],
                "column_name": col["name"],
                "data_type": col["data_type"],
                "table_role": "Dimension",
                "dimension_type": dim.get("dimension_type")
            })

    df = pd.DataFrame(rows)
    df = pd.DataFrame(rows)

    print(df)

    model: PipelineOutput = modelling_result.pydantic

    # ── Step 3: Human review loop ──
    model, approved = ask_for_changes(model)
    if not approved:
        return

    # ── Step 4: SQL generation (optional) ──
    if ask_for_sql():
        print("\n[main] Generating SQL DDL...\n")
        sql_crew = Crew(
            agents=[sql_writer],
            tasks=[sql_writing],
            process=Process.sequential,
            verbose=False,
        )
        sql_result = sql_crew.kickoff(inputs={"business_question": business_question})

        print("\n" + "─" * 60)
        print("SQL DDL")
        print("─" * 60)
        print(sql_result.raw)
        print("─" * 60)
    else:
        print("\nDone. No SQL generated.")


if __name__ == "__main__":
    main()