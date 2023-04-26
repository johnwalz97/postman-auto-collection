import os
from typing import List

import click
import dotenv
import openai
from tree_sitter import Language, Parser

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

PY_LANGUAGE = Language('postman_auto_collection/language_libs.so', 'python')

IGNORE = ["__pycache__", ".env", ".git", "venv", "node_modules"]


def gather_files(local_path: str) -> List[str]:
    file_paths = []
    for root, _, files in os.walk(local_path):
        for file in files:
            if any(ignore in file for ignore in IGNORE) or any(
                ignore in root for ignore in IGNORE
            ):
                continue
            file_paths.append(os.path.join(root, file))
    return file_paths


def prompt_for_relevant_files(file_paths: List[str]) -> List[str]:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": f"""Consider your knowledge of how REST APIs are commonly built using Python.
Which of the following files are likely candidates for containing the code for an API and its endpoints?
Please respond with only the list of files.
Do not respond with any acknowledgement or explanation.
Please respond with the plain raw text of the list of files.
Please order the files you respond with by their likelihood to have important API code in them.
{''.join(file_paths)}""",
            },
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content.strip().split("\n")


def extract_functions(relevant_files: List[str]) -> List[str]:
    parser = Parser()
    parser.set_language(PY_LANGUAGE)

    functions = {}

    for file in relevant_files:
        with open(file, "rb") as f:
            tree = parser.parse(f.read())

        query = PY_LANGUAGE.query("""
(function_definition
name: (identifier) @function_name
body: (block) @function_body
)
        """)
        captures = query.captures(tree.root_node)

        func_name = None
        for capture in captures:
            if capture[1] == "function_name":
                func_name = capture[0].text.decode("utf-8")
                functions[func_name] = {
                    "file": file,
                    "body": None,
                }
            elif capture[1] == "function_body":
                functions[func_name]["body"] = capture[0].text.decode("utf-8")

    return functions


def prompt_for_relevant_functions(function_definitions: List[str]) -> List[str]:
    relevant_functions = []

    for function in function_definitions:
        if function.startswith("async def search"):
            relevant_functions.append(function)

    return relevant_functions


def generate_context(relevant_functions: List[str]) -> str:
    return "\n".join(relevant_functions)


def generate_collection(context: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """You are an Postman Collection expert AI.
You are given a code snippet and asked to generate a Postman collection for the API implemented by this code.
You will respond with a Postman collection in JSON format.
You will respond only with the JSON, not with any other text.
You will NOT respond with Markdown.
You will respond with pure, raw JSON.""",
            },
            {
                "role": "user",
                "content": f"""Here are the functions relevant to the API I am trying to generate a Postman collection for:
```python
{context}
```""",
            },
            {
                "role": "user",
                "content": "Given the above functions, please generate a Postman collection for the API implemented by this code.",
            },
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content.strip()


@click.command()
@click.option("--repo-url", help="The URL of the repository to analyze.")
@click.option("--local-path", help="The local path of the repository to analyze.")
@click.option(
    "--output-file",
    default="postman_collection.json",
    help="The name of the output file for the generated Postman collection.",
)
def main(repo_url, local_path, output_file):
    """This tool generates a Postman collection from a given repository by
    analyzing its code with the help of GPT-4

    Provide either the URL of the repository or the local path to the repository.
    """
    if not repo_url and not local_path:
        click.echo("Error: Please provide either --repo-url or --local-path.")
        return

    click.echo(
        f"Generating Postman collection for {'remote' if repo_url else 'local'} repository..."
    )

    if repo_url:
        click.echo(f"Repository URL: {repo_url}")
        click.echo("Not implemented yet.")
        return

    file_paths = gather_files(local_path)
    click.echo(f"Found {len(file_paths)} files in {local_path}")

    relevant_files = prompt_for_relevant_files(file_paths)
    click.echo(f"GPT asked for {len(relevant_files)} relevant files.")
    for file in relevant_files:
        click.echo(f" - {file}")

    functions = extract_functions(relevant_files)
    click.echo(f"Found {len(functions)} function definitions.")
    for function in functions:
        click.echo(f" - {function}")

    relevant_function_defs = prompt_for_relevant_functions(list(functions.keys()))
    click.echo(f"GPT asked for {len(relevant_function_defs)} relevant functions.")

    relevant_functions = [functions[function] for function in relevant_function_defs]

    context = generate_context(relevant_functions)

    click.echo(f"\Context:\n'''\n{context}\n'''")

    collection = generate_collection(context)

    with open(output_file, "w") as f:
        f.write(collection)
        click.echo(f"Postman collection generated and saved to {output_file}")


if __name__ == "__main__":
    main()
