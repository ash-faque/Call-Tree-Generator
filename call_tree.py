import os
import sys
import json
from collections import defaultdict
from typing import List, Set, Dict, Optional
from clang.cindex import Index, Cursor, CursorKind, TranslationUnit, Config, SourceLocation
from project import ProjectAnalyzer
from template import HTML_TEMPLATE, JSON_REPLACE_HINT


class FunctionInfo:
    def __init__(self, cursor: Cursor):
        if hasattr(cursor, 'spelling'):
            self.name: str = cursor.spelling
            self.file: str = cursor.location.file.name
            self.line: int = cursor.location.line
            self.column: int = cursor.location.column
        else:
            self.name: str = cursor.name
            self.file: str = cursor.file
            self.line: int = cursor.line
            self.column: int = cursor.column

    def __repr__(self) -> str:
        return f"{self.name} {self.file}:{self.line}:{self.column}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "column": self.column
        }

    def json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)


class CallTree:
    """
    Represents the call tree for a program, focusing only on functions within the project directory.
    """

    def __init__(self, project_root: str):
        self.tree: Dict[FunctionInfo, Set[FunctionInfo]] = defaultdict(set)
        self.project_root: str = project_root

    def _is_in_project(self, file_path: str) -> bool:
        """Check if the file path is within the project directory."""
        return os.path.abspath(file_path).startswith(os.path.abspath(self.project_root))

    def add(self, caller: Cursor, callee: Cursor) -> None:
        """Add a callee to the caller's set only if the callee is from the project."""
        if self._is_in_project(callee.location.file.name):
            self.tree[FunctionInfo(caller)].add(FunctionInfo(callee))

    def functions(self) -> List[FunctionInfo]:
        """Return all known functions in the call tree."""
        return list(self.tree.keys())

    def calls(self, caller: Cursor) -> Set[FunctionInfo]:
        """Return the set of functions called by the given caller."""
        return self.tree[caller]

    def build(self, translation_unit: TranslationUnit) -> None:
        """
        Build a call tree for the given translation unit, considering only functions within the project.
        """
        self._rec_build(translation_unit.cursor, translation_unit.cursor)

    def _rec_build(self, node: Cursor, caller: Cursor) -> None:
        """
        Recursively build the call tree by visiting all nodes in the AST, 
        considering only functions from the project directory.
        """
        func_kinds: List[CursorKind] = [
            CursorKind.FUNCTION_DECL,
            CursorKind.CXX_METHOD,
            CursorKind.CONSTRUCTOR,
            CursorKind.DESTRUCTOR
        ]

        if node.kind in func_kinds:
            caller = node
        elif node.kind == CursorKind.CALL_EXPR and node.referenced:
            func = node.referenced
            if self._is_in_project(func.location.file.name):
                caller_str = FunctionInfo(caller) if not isinstance(
                    caller, TranslationUnit) else FunctionInfo(caller.cursor)
                self.add(caller_str, func)

        for child in node.get_children():
            self._rec_build(child, caller)

    def print(self):
        """Function to print tree structure with ASCII art"""
        def print_tree(caller, callees, depth=0):
            print(f'{caller}')
            for i, callee in enumerate(callees):
                if i == len(callees) - 1:
                    print('\t' * (depth + 1) + f'|')
                    print('\t' * (depth + 1) + f'|______ {callee}')
                else:
                    print('\t' * (depth + 1) + f'|')
                    print('\t' * (depth + 1) + f'|______ {callee}')
                    print('\t' * (depth + 1) + f'|')
            print('')

        # Group by caller
        grouped_callers = defaultdict(list)
        for caller, callees in self.tree.items():
            grouped_callers[caller].extend(callees)

        # Print grouped callers
        for caller, callees in grouped_callers.items():
            print_tree(caller, callees)
            print()  # Add a blank line for readability between different callers

    def as_dict(self) -> dict:
        """Function to save tree structure as JSON with merged duplicate callers"""
        # Dictionary to group callers by their unique identifier (name, file, line, column)
        caller_groups = {}

        for caller in self.tree:
            # Create a unique key for this caller based on its attributes
            caller_key = (
                getattr(caller, 'name', 'Unknown'),
                getattr(caller, 'file', 'Unknown'),
                getattr(caller, 'line', 0),
                getattr(caller, 'column', 0)
            )

            # If this caller already exists, add its callees to the existing entry
            if caller_key in caller_groups:
                # Add new callees to the existing list
                current_callees = caller_groups[caller_key]["callees"]
                for callee in self.tree[caller]:
                    callee_dict = {
                        "name": getattr(callee, 'name', 'Unknown'),
                        "file": getattr(callee, 'file', 'Unknown'),
                        "line": getattr(callee, 'line', 0),
                        "column": getattr(callee, 'column', 0)
                    }
                    if callee_dict not in current_callees:  # Avoid duplicates
                        current_callees.append(callee_dict)
            else:
                # Create new entry for this caller
                callees_list = []
                for callee in self.tree[caller]:
                    callee_dict = {
                        "name": getattr(callee, 'name', 'Unknown'),
                        "file": getattr(callee, 'file', 'Unknown'),
                        "line": getattr(callee, 'line', 0),
                        "column": getattr(callee, 'column', 0)
                    }
                    callees_list.append(callee_dict)

                caller_groups[caller_key] = {
                    "name": caller_key[0],  # Name
                    "file": caller_key[1],  # File
                    "line": caller_key[2],  # Line
                    "column": caller_key[3],  # Column
                    "callees": callees_list
                }

        # Convert grouped callers to the final "calltree" list
        calltree_list = list(caller_groups.values())

        # Create the final structure with "calltree" as the root key
        return {"calltree": calltree_list}

    def to_json(self):
        json_filepath = os.path.join(self.project_root, "calltree.json")
        with open(json_filepath, "w") as json_file:
            json.dump(self.as_dict(), json_file, indent=4)
        print(f"JSON calltree saved at {json_filepath}")

    def to_html(self):
        json_data = json.dumps(self.as_dict(), indent=4)
        html_filepath = os.path.join(self.project_root, "calltree.html")
        with open(html_filepath, "w") as html_file:
            html_file.write(HTML_TEMPLATE.replace(JSON_REPLACE_HINT, json_data))
        print(f"HTML calltree saved at {html_filepath}")

    def to_visjs(self):
        """Output call tree in a format compatible with Vis.js"""
        nodes = []
        edges = []
        modules = {}

        for caller in self.tree:
            file_path = caller.file  # Assuming caller has a 'file' attribute
            base_name = os.path.basename(file_path).split('.')[0]  # Get base name (e.g., "main" from "main.c")

            if base_name not in modules:
                module_id = f"module_{base_name}"
                modules[base_name] = module_id
                nodes.append({
                    "id": module_id,
                    "label": f"Module: {base_name}\n({file_path})",
                    "group": "module",
                    "shape": "box",
                    "color": {"background": "#f8f9fa", "border": "#4a90e2"},
                    "font": {"size": 14, "color": "#333"},
                    "size": 50
                })

            caller_id = f"func_{base_name}_{caller.name}"
            nodes.append({
                "id": caller_id,
                "label": caller.name,
                "group": "function",
                "shape": "box",
                "color": {"background": "#e6f3ff", "border": "#4a90e2"},
                "font": {"size": 12},
                "size": 30,
                "parent": modules[base_name]  # Link to module
            })

            # Link module to function
            edges.append({
                "from": modules[base_name],
                "to": caller_id,
                "arrows": "to",
                "color": {"color": "#888888"},
                "smooth": True
            })

            for callee in self.tree[caller]:  # Assuming self.tree[caller] gives callees
                callee_file = callee.file  # Assuming callee has a 'file' attribute
                callee_base_name = os.path.basename(callee_file).split('.')[0]
                if callee_base_name not in modules:
                    module_id = f"module_{callee_base_name}"
                    modules[callee_base_name] = module_id
                    nodes.append({
                        "id": module_id,
                        "label": f"Module: {callee_base_name}\n({callee_file})",
                        "group": "module",
                        "shape": "box",
                        "color": {"background": "#f8f9fa", "border": "#4a90e2"},
                        "font": {"size": 14, "color": "#333"},
                        "size": 50
                    })

                callee_id = f"func_{callee_base_name}_{callee.name}"
                if not any(node["id"] == callee_id for node in nodes):
                    nodes.append({
                        "id": callee_id,
                        "label": callee.name,
                        "group": "function",
                        "shape": "box",
                        "color": {"background": "#e6f3ff", "border": "#4a90e2"},
                        "font": {"size": 12},
                        "size": 30,
                        "parent": modules[callee_base_name]
                    })

                edges.append({
                    "from": caller_id,
                    "to": callee_id,
                    "arrows": "to",
                    "color": {"color": "#ff4444"},
                    "smooth": {"type": "curvedCW", "roundness": 0.5},
                    "width": 2
                })

        return {"nodes": nodes, "edges": edges}


if __name__ == '__main__':
    project_directory: str = r"D:/AUTOSAR_Training/CDD/"
    project_directory: str = r"data"
    analyzer = ProjectAnalyzer(project_directory)
    call_tree = CallTree(project_directory)

    for source_file in analyzer.get_source_files():
        tu = analyzer.get_translation_unit(source_file)
        if tu:
            call_tree.build(tu)

    call_tree.to_json()
