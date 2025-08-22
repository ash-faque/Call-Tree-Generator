import os
import sys
import json
from typing import List, Set, Dict, Optional
from clang.cindex import Index, Cursor, CursorKind, TranslationUnit, Config, SourceLocation


class ProjectAnalyzer:
    def __init__(self, project_root: str):
        self.project_root: str = project_root

    def get_source_files(self) -> List[str]:
        """Collect all C and header files in the project directory."""
        source_files: List[str] = []
        for root, dirs, files in os.walk(self.project_root):
            if "build" in dirs:
                dirs.remove("build")
            for file in files:
                if file.endswith(('.c')):
                    source_files.append(os.path.join(root, file))
        return source_files

    def get_include_dirs(self) -> List[str]:
        """Find all directories that might contain header files."""
        include_dirs: List[str] = []
        for root, dirs, _ in os.walk(self.project_root):
            if "build" not in dirs:
                include_dirs.append(root)
        return include_dirs

    def get_translation_unit(self, file_path: str) -> Optional[TranslationUnit]:
        """Parse the given file into a TranslationUnit."""
        index = Index.create()
        options = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
        args: List[str] = ['-x', 'c'] + \
            [f'-I{dir}' for dir in self.get_include_dirs()]

        tu = index.parse(file_path, args=args, options=options)

        for diag in tu.diagnostics:
            if diag.severity >= 3:
                print(
                    f"[ERROR] {diag.location.file}:{diag.location.line} {diag.spelling}", file=sys.stderr)

        return tu if not tu.diagnostics else None
