import pandas as pd
from rich import print

def process_json(input_data: str, is_file:bool=True, indent: int=4):
    """
    Processes JSON data to flatten and normalize nested structures.

    Args:
        input_data (str): JSON data as a string or path to a JSON file.
        is_file (bool): If True, treats `input_data` as a file path; otherwise as raw JSON string.
        indent (int): Number of spaces for indentation in the output JSON.

    Returns:
        dict: Processed JSON as a Python dictionary.
    """
    # load the JSON file
    if is_file:
        df = pd.read_json(input_data)
    else:
        df = pd.read_json(input_data, orient="records")

    # display the initial DataFrame
    # print("[bold magneta]Initial DataFrame:[/]")
    # print(df)

    # exploding the 'facts' column
    df = df.explode("facts")

    # extract keys and values from the exploded 'facts' column
    df["fact_key"] = df["facts"].apply(lambda x: x if isinstance(x, str) else list(x.keys())[0] if isinstance(x, dict) else None)
    df["facts_value"] = df["facts"].apply(lambda x: None if isinstance(x, str) else list(x.values())[0] if isinstance(x, dict) else None)

    # drop the original 'facts' column for clarity
    df = df.drop(columns=["facts"])
    # print("\n[bold magenta]DataFrame after exploding and separating 'facts':[/]")
    # print(df)

    # handle cases where 'facts_value' is None or non-dict
    df["facts_value"] = df["facts_value"].apply(lambda x: x if isinstance(x, dict) else {})

    # normalize nested dictionaries in 'facts_value'
    fact_values_normalized = pd.json_normalize(df["facts_value"])

    # combine the normalized data back with the main DataFrame
    final_df = pd.concat([df.drop(columns=["facts_value"]), fact_values_normalized], axis=1)

    # display the final DataFrame
    # print("\n[bold magenta]Final Flattened DataFrame:[/]")
    # print(final_df)

    # save the result to a new JSON file
    processed_data = final_df.to_dict(orient="records")
    return processed_data

file_path = "CIK0000001750.json"
print(f"[bold magenta]Processing file:[/] [bold white]{file_path}[/]")
processed_data = process_json(file_path)
print(processed_data)