from fastmcp import FastMCP
from pathlib import Path
import json
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from typing import Any

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR_PATH = (PROJECT_ROOT_DIR / "data")
SRC_DIR_PATH = (PROJECT_ROOT_DIR/"src")

def _validate_alcohol_related_field(value: Any) -> bool|None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    try:
        return bool(int(value))
    except (ValueError, TypeError):
        return None

class Ingredient(BaseModel):

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    description: str | None = None
    alcohol: bool | None = None
    type: str | None = None
    percentage: float | None = None
    imageUrl: str | None = None
    measure: str | None = None

    @field_validator("alcohol", mode="before")
    @classmethod
    def _validate_alcohol(cls,value: Any) -> bool|None:
        return _validate_alcohol_related_field(value)

class Cocktail(BaseModel):

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    category: str | None = None
    glass: str | None = None
    tags: list[str] = Field(default_factory=list)
    instructions: str | None = None
    imageUrl: str | None = None
    alcoholic: bool | None = None
    ingredients: list[Ingredient] = Field(default_factory=list)


    @field_validator("alcoholic", mode="before")
    @classmethod
    def _validate_alcoholic(cls,value:Any) -> bool|None:
        return _validate_alcohol_related_field(value)

    @field_validator("tags", mode="before")
    @classmethod
    def _validate_tags(cls, value: Any) -> list:
        if value is None:
            return []
        if isinstance(value,str):
            return [value]
        return value


server = FastMCP(
    name="main_server",
    instructions="""
        Serwer który odpowiada na pytania dotyczące koktajli zawartych w bazie danych.
        Może też proponować koktajle na podstawie preferencji smakowych czy składników.
    """,
)
def load_cocktails_data():
    cocktail_dataset_path = (DATA_DIR_PATH / "cocktail_dataset.json").resolve()
    try:
        with cocktail_dataset_path.open('r', encoding='utf-8') as file:
            raw_data: list[dict[str,Any]] = json.load(file)
    except FileNotFoundError:
        print(f"Nie znaleziono pliku {cocktail_dataset_path}.")
        return []
    except json.JSONDecodeError as e:
        print(f"Błąd podczas parsowania.\nLOG: {e}")
        return []

    cocktails: list[Cocktail] = []
    for entry in raw_data:
        try:
            cocktails.append(Cocktail.model_validate(entry))

        except ValidationError as e:
            cocktail_id = entry.get("id", "<brak_id>")
            print(f"Bład podczas validowania. Pomijam {cocktail_id} LOG: {e}")

    return cocktails

if __name__ == "__main__":
    cocktails = load_cocktails_data()
    server.run()
