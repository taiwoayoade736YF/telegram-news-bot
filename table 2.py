from rich.console import Console
from rich.table import Table
import csv

table = Table(title="📄 Scraped Text Nodes", show_lines=True)
table.add_column("Text", style="cyan", no_wrap=False)
table.add_column("Parent Tag", style="magenta")

with open('output.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        table.add_row(row[0], row[1])

Console().print(table)