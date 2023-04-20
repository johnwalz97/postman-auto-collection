import os
from typing import List

import click
import dotenv
import openai
from pygments import lex
from pygments.lexers import PythonLexer

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def gather_files(local_path: str) -> List[str]:
    file_paths = []
    for root, _, files in os.walk(local_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


def prompt_for_relevant_files(file_paths: List[str]) -> List[str]:
    relevant_files = []

    for file in file_paths:
        if file.endswith("search.py"):
            relevant_files.append(file)

    return relevant_files


def extract_functions(relevant_files: List[str]) -> List[str]:
    functions = {}

    for file in relevant_files:
        with open(file, "r") as f:
            content = f.read()

            in_function = False
            in_multiline = False
            function = ""

            for line in content.splitlines():
                if line.startswith("def ") or line.startswith("async def "):
                    function_definition = line
                    function = line
                    in_function = True
                elif in_function:
                    function += f"\n{line}"

                    if in_multiline or line.startswith("    "):
                        if '"""' in line or "'''" in line:
                            in_multiline = not in_multiline

                        continue

                    else:
                        functions[function_definition] = function
                        in_function = False

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

    functions = extract_functions(relevant_files)
    click.echo(f"Found {len(functions)} function definitions.")

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
