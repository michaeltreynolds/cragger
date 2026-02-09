"""
Convert markdown files to Jupyter notebook.

Usage:
    python convert_to_notebook.py

This will read all markdown files in notebook_content/ and create setup.ipynb
"""

import json
import os
import re
import ast
from pathlib import Path

def validate_python_syntax(code, filename="<code block>"):
    """Validate Python code syntax using AST"""
    # Skip validation for Colab cells with shell commands or magic commands
    lines = code.split('\n')
    has_shell_command = any(line.strip().startswith('!') for line in lines)
    has_magic_command = any(line.strip().startswith('%') for line in lines)
    
    if has_shell_command or has_magic_command:
        # Colab-specific, can't validate with AST
        return True, None
    
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error in {filename} at line {e.lineno}: {e.msg}"

def create_markdown_cell(content):
    """Create a markdown cell"""
    lines = content.split('\n')
    # Jupyter requires each line (except the last) to end with \n
    source = [line + '\n' for line in lines[:-1]] + [lines[-1]] if lines else []
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source
    }

def create_code_cell(content, is_form=False, filename="<code block>"):
    """Create a code cell with syntax validation"""
    # Validate syntax
    is_valid, error = validate_python_syntax(content, filename)
    if not is_valid:
        print(f"  ⚠️  {error}")
        print(f"     Code preview: {content[:100]}...")
    
    metadata = {}
    if is_form:
        metadata["cellView"] = "form"
    
    lines = content.split('\n')
    # Jupyter requires each line (except the last) to end with \n
    source = [line + '\n' for line in lines[:-1]] + [lines[-1]] if lines else []
    
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": metadata,
        "outputs": [],
        "source": source
    }

def parse_markdown_file(filepath):
    """Parse a markdown file and extract cells"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cells = []
    parts = re.split(r'```python\n', content)
    
    filename = os.path.basename(filepath)
    
    # First part is always markdown
    if parts[0].strip():
        cells.append(create_markdown_cell(parts[0].strip()))
    
    # Process code blocks
    for i in range(1, len(parts)):
        # Split on closing ```
        code_and_rest = parts[i].split('```', 1)
        
        if len(code_and_rest) == 2:
            code, markdown = code_and_rest
            
            # Check if it's a form cell (starts with # @title)
            is_form = code.strip().startswith('# @title')
            
            # Add code cell
            if code.strip():
                cells.append(create_code_cell(code.strip(), is_form, filename))
            
            # Add following markdown if exists
            if markdown.strip():
                cells.append(create_markdown_cell(markdown.strip()))
        else:
            # Just code, no closing ```
            if code_and_rest[0].strip():
                is_form = code_and_rest[0].strip().startswith('# @title')
                cells.append(create_code_cell(code_and_rest[0].strip(), is_form, filename))
    
    return cells

def create_notebook(content_dir='notebook_content'):
    """Create Jupyter notebook from markdown files"""
    
    # Create base notebook structure
    notebook = {
        "cells": [],
        "metadata": {
            "colab": {
                "provenance": [],
                "collapsed_sections": []
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 0
    }
    
    # Get all markdown files in order
    content_path = Path(content_dir)
    md_files = sorted([f for f in content_path.glob('*.md') if f.name != 'README.md'])
    
    print(f"Processing {len(md_files)} markdown files...")
    
    # Process each file
    for md_file in md_files:
        print(f"  - {md_file.name}")
        cells = parse_markdown_file(md_file)
        notebook["cells"].extend(cells)
    
    print(f"\nCreated notebook with {len(notebook['cells'])} cells")
    
    return notebook

def main():
    """Main function"""
    output_file = "setup.ipynb"
    
    print("📓 Converting markdown to Jupyter notebook...\n")
    
    try:
        notebook = create_notebook()
        
        # Write notebook
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Created {output_file}")
        print(f"   Total cells: {len(notebook['cells'])}")
        print(f"\nYou can now:")
        print(f"   1. Upload {output_file} to Google Colab")
        print(f"   2. Or open it locally in Jupyter")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
