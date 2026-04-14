from crewai import Agent, LLM
import os

# os.environ["OPENAI_API_KEY"] = "NA"
# # Local LLM
# llm = LLM(
#     model="ollama/mistral", # Very bad model, but free and fast for testing.
#     base_url="http://localhost:11434",
# )


import os
from dotenv import load_dotenv
load_dotenv()


os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
llm = LLM(
    model = "gemini-2.5-flash-lite"
    ,temperature=1
    )


schema_analyst = Agent(
    role="Schema Analyst",
    goal="Parse raw input into a clean list of entities, attributes, and relationships.",
    tools=[],
    verbose=False,
    backstory=(
        "An expert data engineer who specialises in reading raw data descriptions, "
        "SQL DDL, and CSV headers and converting them into a structured entity map. "
        "The agent identifies all tables and columns present in the input, their data types, "
        "and how entities relate to one another. "
        "The output is always a clean, structured JSON entity map "
        "that the dimensional modeller can reason over."
    ),
    llm=llm,
)


dimensional_modeller = Agent(
    role="Dimensional Modeller",
    goal=(
        "Produce a complete dimensional model with fact tables, dimension tables, "
        "grain definitions, measures, and dimension types."
    ),
    tools=[],
    verbose=False,
    backstory=(
        "A senior data warehouse architect trained in Kimball dimensional modelling. "
        "The agent reads a structured entity map and decides what becomes a fact table "
        "and what becomes a dimension table. "
        "For every fact table the agent defines the grain in plain English — one row per what. "
        "For every dimension table the agent assigns the correct dimension type: "
        "conformed, degenerate, junk, role-playing, scd, outrigger, or static. "
        "The agent is strict about grain — a poorly defined grain is the root cause of most "
        "data warehouse failures. "
        "The output is always a valid JSON object matching the PipelineOutput model, "
        "excluding the ddl field which is handled downstream."
    ),
    llm=llm,
)


sql_writer = Agent(
    role="SQL Writer",
    goal="Generate clean, production-ready DDL from a validated dimensional model.",
    tools=[],
    verbose=False,
    backstory=(
        "A database engineer who specialises in writing warehouse-specific DDL. "
        "The agent takes a validated dimensional model and generates CREATE TABLE statements "
        "for every fact and dimension table. "
        "Dimension type drives the DDL — scd dimensions get effective_date, expiry_date, "
        "and is_current columns, degenerate dimensions are added as columns on the fact table "
        "rather than separate tables, junk dimensions are collapsed into a single table, "
        "and role-playing dimensions are generated as views over the physical table. "
        "The agent also writes a short rationale explaining the key design decisions made."
    ),
    llm=llm,
)