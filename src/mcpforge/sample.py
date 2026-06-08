"""A small, self-contained petstore-style OpenAPI 3 document.

Bundling a sample spec means the demo, README examples and the entire test suite
need no external files and run identically everywhere.
"""

from __future__ import annotations

from typing import Any

SAMPLE_OPENAPI: dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "Petstore", "version": "1.2.0"},
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "description": "Maximum number of pets to return.",
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100},
                    },
                    {
                        "name": "tag",
                        "in": "query",
                        "required": False,
                        "description": "Filter pets by tag.",
                        "schema": {"type": "string"},
                    },
                ],
            },
            "post": {
                "operationId": "createPet",
                "summary": "Create a pet",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/NewPet"},
                        },
                    },
                },
            },
        },
        "/pets/{petId}": {
            "get": {
                "operationId": "getPetById",
                "summary": "Get a pet by its id",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "description": "The id of the pet to fetch.",
                        "schema": {"type": "integer"},
                    }
                ],
            }
        },
    },
    "components": {
        "schemas": {
            "NewPet": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "The pet's name."},
                    "tag": {"type": "string", "description": "An optional tag."},
                },
            }
        }
    },
}
