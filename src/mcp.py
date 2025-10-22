from pathlib import Path 
import json
#from fastmcp import FastMCP

BASE_DIR_PATH = Path(".").absolute()
DATA_DIR_PATH = (BASE_DIR_PATH / "data").absolute()

#mcp = FastMCP(
#    name="MainServer",
#    instructions="""
#        This server provides information about cocktails.
#    """,
#)

def import_cocktails_data_from_json() -> dict:
    try:
        cocktail_dataset_path = (DATA_DIR_PATH / "cocktail_dataset.json").absolute()
        with open(cocktail_dataset_path, mode = 'r', encoding = 'utf-8') as file:
            cocktail_json = json.load(file)
        return cocktail_json
    except Exception as e:
        print(f"Error occured in import_cocktails_data_from_json()\nError log: {e}")
        return {}


if __name__ == "__main__":
    data = import_cocktails_data_from_json()
