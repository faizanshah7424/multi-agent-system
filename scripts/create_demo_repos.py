import os
from pathlib import Path


def create_demos():
    examples_dir = Path("examples")
    examples_dir.mkdir(exist_ok=True)

    projects = {
        "nextjs-blog": [
            (
                "package.json",
                '{\n  "name": "nextjs-blog",\n  "version": "1.0.0",\n  "scripts": {\n    "dev": "next dev",\n    "build": "next build"\n  }\n}',
            ),
            (
                "tsconfig.json",
                '{\n  "compilerOptions": {\n    "target": "es5",\n    "module": "commonjs"\n  }\n}',
            ),
            (
                "README.md",
                "# Next.js Blog Demo\nThis is a production-quality Next.js + TypeScript static blogging project template.",
            ),
        ],
        "ecommerce": [
            (
                "main.py",
                'def calculate_cart_total(items):\n    return sum(item["price"] * item["quantity"] for item in items)\n',
            ),
            (
                "test_ecommerce.py",
                'from main import calculate_cart_total\n\ndef test_cart_total():\n    items = [{"price": 10, "quantity": 2}]\n    assert calculate_cart_total(items) == 20\n',
            ),
            (
                "README.md",
                "# E-commerce System Demo\nThis project simulates a shop checkout system with discount multipliers.",
            ),
        ],
        "fastapi-crud": [
            (
                "main.py",
                'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/")\ndef index():\n    return {"status": "ok"}\n',
            ),
            (
                "README.md",
                "# FastAPI CRUD API Demo\nFastAPI web endpoint server with structured pydantic filters.",
            ),
        ],
        "hospital": [
            (
                "patients.py",
                "class PatientRegistry:\n    def __init__(self):\n        self.records = {}\n",
            ),
            (
                "README.md",
                "# Hospital Management System\nSimulates patient check-ins and clinical scheduling algorithms.",
            ),
        ],
        "react-dashboard": [
            (
                "package.json",
                '{\n  "name": "react-dashboard",\n  "version": "0.1.0",\n  "dependencies": {\n    "react": "^18.0.0"\n  }\n}',
            ),
            (
                "README.md",
                "# React Dashboard Demo\nFrontend charts and diagnostic monitors mockup.",
            ),
        ],
        "python-cli": [
            ("cli.py", 'import sys\ndef run():\n    print("Hello from CLI")\n'),
            (
                "README.md",
                "# Python CLI Project\nStandard python entry points and test configurations.",
            ),
        ],
    }

    for proj_name, files in projects.items():
        proj_path = examples_dir / proj_name
        proj_path.mkdir(parents=True, exist_ok=True)
        for filename, content in files:
            file_path = proj_path / filename
            file_path.write_text(content, encoding="utf-8")
            print(f"Created: {file_path}")


if __name__ == "__main__":
    create_demos()
