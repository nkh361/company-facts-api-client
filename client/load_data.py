import json
import os
import pandas as pd
from rich import print

datasource_dir = os.path.join(os.path.dirname(__file__), '../datasource')

# list files in the directory
files = [f for f in os.listdir(datasource_dir) if f.endswith('.json')]

# check if there are json files
if not files:
    print("[bold orange]No json files found in directory![/]")
else:
    print(f"[bold green]Found json files: {files}")

    file_path = os.path.join(datasource_dir, files[0])
    with open(file_path, 'r') as infile:
        data = json.load(infile)

    print(f"[bold magenta]Loaded data from {files[0]}:[/]")
    print(json.dumps(data, indent=2))

    df = pd.json_normalize(data)
    print("[bold white]Dataframe preview:[/]")
    print(f"[bold white]{df.head()}[/]")

    output_path = os.path.join(os.path.dirname(__file__), 'output.csv')
    df.to_csv(output_path, index=False)
    print(f"[bold magenta]Data saved to {output_path}")