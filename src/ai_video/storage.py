"""Storage utilities for reading and writing artifacts."""

import json
from pathlib import Path
from typing import Any, TypeVar, Type
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

def write_json(data: Any, file_path: Path, indent: int = 2) -> None:
    """Write data to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if isinstance(data, BaseModel):
        json_data = data.model_dump(mode='json')
    else:
        json_data = data
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=indent, ensure_ascii=False)

def read_json(file_path: Path) -> dict:
    """Read JSON data from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_model(file_path: Path, model_class: Type[T]) -> T:
    """Load a Pydantic model from a JSON file."""
    data = read_json(file_path)
    return model_class(**data)

def save_model(model: BaseModel, file_path: Path) -> None:
    """Save a Pydantic model to a JSON file."""
    write_json(model, file_path)

def write_text(text: str, file_path: Path) -> None:
    """Write text to a file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

def read_text(file_path: Path) -> str:
    """Read text from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    return file_path.exists() and file_path.is_file()
