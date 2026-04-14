from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DimensionType(str, Enum):
    conformed = "conformed"
    degenerate = "degenerate"
    junk = "junk"
    role_playing = "role_playing"
    scd = "scd"
    outrigger = "outrigger"
    static = "static"


class Column(BaseModel):
    name: str
    data_type: str
    nullable: bool = True


class DimensionTable(BaseModel):
    name: str
    dimension_type: DimensionType
    columns: List[Column]
    notes: Optional[str] = None


class FactTable(BaseModel):
    name: str
    grain: str = Field(..., description="One row per ...")
    columns: List[Column]
    measures: List[str]


class PipelineInput(BaseModel):
    raw_input: str


class PipelineOutput(BaseModel):
    fact_tables: List[FactTable]
    dimension_tables: List[DimensionTable]