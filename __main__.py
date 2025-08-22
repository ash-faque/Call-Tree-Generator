from enum import IntEnum, auto
import sys
import argparse
import json
import os
from call_tree import CallTree, ProjectAnalyzer


class OutputFormat(IntEnum):
    HTML = auto()
    JSON = auto()
    VISJS = auto()


parser = argparse.ArgumentParser(
    description="Analyze function call tree in a project.")
parser.add_argument("project_directory",
                    help="Directory containing the project source files")
parser.add_argument("-o", choices=[f.name.lower()
                    for f in OutputFormat], help="Output format (html, json, visjs)")
args = parser.parse_args()

project_directory: str = args.project_directory
output_format = OutputFormat[args.o.upper()] if args.o else None

analyzer = ProjectAnalyzer(project_directory)
call_tree = CallTree(project_directory)

for source_file in analyzer.get_source_files():
    tu = analyzer.get_translation_unit(source_file)
    if tu:
        call_tree.build(tu)


# Handle output
match output_format:
    case OutputFormat.HTML:
        call_tree.to_html()
    case OutputFormat.JSON:
        call_tree.to_json()
    case OutputFormat.VISJS:
        visjs_data = call_tree.to_visjs()
        with open(os.path.join(project_directory, "calltree_visjs.json"), "w") as f:
            json.dump(visjs_data, f, indent=4)
        print(
            f"Vis.js data saved at {os.path.join(project_directory, 'calltree_visjs.json')}")
    case _:
        call_tree.print()
