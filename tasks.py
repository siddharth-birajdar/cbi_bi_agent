from crewai import Task
from agent import schema_analyst, dimensional_modeller, sql_writer
from datamodels import PipelineOutput


schema_analysis = Task(
    description=(
        "Parse the following raw input: {raw_input}. "
        "Identify all entities, their attributes, data types, and relationships. "
        "Return a structured JSON entity map."
    ),
    expected_output=(
        "A JSON entity map listing all entities, their columns with data types, "
        "and the relationships between them."
    ),
    agent=schema_analyst,
)


dimensional_modelling = Task(
    description=("{raw_input}"
        "Using the {entity_map} from the schema analyst, produce a complete dimensional model. "
        "For every fact table define the grain in plain English — one row per what. "
        "For every dimension table assign the correct dimension type: "
        "conformed, degenerate, junk, role-playing, scd, outrigger, or static. "
        "List all measures on each fact table."
    ),
    expected_output=(
        "A validated PipelineOutput object with fact_tables and dimension_tables. "
        "Each fact table has a grain statement and a list of measures. "
        "Each dimension table has a dimension_type and optional notes."
    ),
    agent=dimensional_modeller,
    context=[schema_analysis],
    output_pydantic=PipelineOutput,
)


sql_writing = Task(
    description=("Given the business question {business_question}"
        "Generate SQL queries to create fact and dimension tables based on the identified facts and dimensions. "
        "The SQL should include necessary joins and aggregations to prepare the data for Power BI analysis."
        "The process is to create dimension tables first using the dimension  and dimension types, "
        "followed by creating fact tables that reference these dimensions."
    ),
        
    expected_output="A single string of valid SQL queries for creating "
                    "and inserting into fact and dimension tables, using dimension queries and raw tables.",
    agent=sql_writer,
    context=[dimensional_modelling],
)