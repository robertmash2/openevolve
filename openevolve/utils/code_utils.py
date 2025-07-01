"""
Utilities for code parsing, diffing, and manipulation
"""

import re
from typing import Dict, List, Optional, Tuple, Union

def inspect_strings(s1, s2):
    """
    Compares two strings character by character, printing their
    ASCII/Unicode ordinal values to find the first difference.
    """
    print(f"String 1: '{s1}'")
    print(f"String 2: '{s2}'")
    print("-" * 40)
    print("Index | Char 1 (Ord) | Char 2 (Ord)")
    print("------|--------------|--------------")

    # Find the length of the longer string to iterate through
    max_len = max(len(s1), len(s2))
    
    # Iterate through the strings
    for i in range(max_len):
        # Get characters and their ordinal values, handle different lengths
        char1 = s1[i] if i < len(s1) else " "
        ord1 = ord(char1) if i < len(s1) else "N/A"
        
        char2 = s2[i] if i < len(s2) else " "
        ord2 = ord(char2) if i < len(s2) else "N/A"

        # Check for differences and print
        diff_marker = ">>" if char1 != char2 else "  "
        print(f"{diff_marker} {i:<4} | '{char1}' ({ord1:<6}) | '{char2}' ({ord2:<6})")

        # Stop after finding the first difference to keep output clean
        if char1 != char2:
            print("-" * 40)
            print(f"Difference found at index {i}.")
            return

    print("-" * 40)
    print("No difference found (but lengths might differ if one is a prefix of the other).")


def print_diff(string1, string2):
    import difflib
       
    # The strings need to be split into lists of lines
    lines1 = string1.splitlines()
    lines2 = string2.splitlines()
    
    # Create a diff generator
    diff = difflib.unified_diff(
        lines1, 
        lines2, 
        fromfile='original', 
        tofile='modified', 
        lineterm=''
    )
    
    # Print the differences
    for line in diff:
        print(line)

def enforce_evolve_block(child_code: str, initial_program_code: str) -> str:
    child_start = child_code.find("# EVOLVE-BLOCK-START")
    child_end = child_code.find("# EVOLVE-BLOCK-END") + len("# EVOLVE-BLOCK-END")

    initial_start = initial_program_code.find("# EVOLVE-BLOCK-START")
    initial_end = initial_program_code.find("# EVOLVE-BLOCK-END") + len("# EVOLVE-BLOCK-END")
    
    if child_code[:child_start] == initial_program_code[:initial_start]:
        print('pre-evolve-block matches.')
    else:
        print('pre-evolve-block MIS-MATCH')
        print_diff(initial_program_code[:initial_start], child_code[:child_start])
   
    if child_code[child_end:] == initial_program_code[initial_end:]:
        print('post-evolve-block matches.')
    else:

        print('post-evolve-block MIS-MATCH')       
        print_diff(initial_program_code[initial_end:], child_code[child_end:])
  
    output = initial_program_code[:initial_start] + child_code[child_start:child_end] + initial_program_code[initial_end:]

    return output

def parse_evolve_blocks(code: str) -> List[Tuple[int, int, str]]:
    """
    Parse evolve blocks from code

    Args:
        code: Source code with evolve blocks

    Returns:
        List of tuples (start_line, end_line, block_content)
    """
    
    lines = code.split("\n")
    blocks = []

    in_block = False
    start_line = -1
    block_content = []

    for i, line in enumerate(lines):
        if "# EVOLVE-BLOCK-START" in line:
            in_block = True
            start_line = i
            block_content = []
        elif "# EVOLVE-BLOCK-END" in line and in_block:
            in_block = False
            blocks.append((start_line, i, "\n".join(block_content)))
        elif in_block:
            block_content.append(line)

    return blocks


def apply_diff(original_code: str, diff_text: str) -> str:
    """
    Apply a diff to the original code

    Args:
        original_code: Original source code
        diff_text: Diff in the SEARCH/REPLACE format

    Returns:
        Modified code
    """
    # Split into lines for easier processing
    original_lines = original_code.split("\n")
    result_lines = original_lines.copy()

    # Extract diff blocks
    diff_blocks = extract_diffs(diff_text)

    # Apply each diff block
    for search_text, replace_text in diff_blocks:
        search_lines = search_text.split("\n")
        replace_lines = replace_text.split("\n")

        # Find where the search pattern starts in the original code
        for i in range(len(result_lines) - len(search_lines) + 1):
            if result_lines[i : i + len(search_lines)] == search_lines:
                # Replace the matched section
                result_lines[i : i + len(search_lines)] = replace_lines
                break

    return "\n".join(result_lines)


def extract_diffs(diff_text: str) -> List[Tuple[str, str]]:
    """
    Extract diff blocks from the diff text

    Args:
        diff_text: Diff in the SEARCH/REPLACE format

    Returns:
        List of tuples (search_text, replace_text)
    """
    diff_pattern = r"<<<<<<< SEARCH\n(.*?)=======\n(.*?)>>>>>>> REPLACE"
    diff_blocks = re.findall(diff_pattern, diff_text, re.DOTALL)
    return [(match[0].rstrip(), match[1].rstrip()) for match in diff_blocks]


def parse_full_rewrite(llm_response: str, language: str = "python") -> Optional[str]:
    """
    Extract a full rewrite from an LLM response

    Args:
        llm_response: Response from the LLM
        language: Programming language

    Returns:
        Extracted code or None if not found
    """
    code_block_pattern = r"```" + language + r"\n(.*?)```"
    matches = re.findall(code_block_pattern, llm_response, re.DOTALL)

    if matches:
        return matches[0].strip()

    # Fallback to any code block
    code_block_pattern = r"```(.*?)```"
    matches = re.findall(code_block_pattern, llm_response, re.DOTALL)

    if matches:
        return matches[0].strip()

    # Fallback to plain text
    return llm_response


def format_diff_summary(diff_blocks: List[Tuple[str, str]]) -> str:
    """
    Create a human-readable summary of the diff

    Args:
        diff_blocks: List of (search_text, replace_text) tuples

    Returns:
        Summary string
    """
    summary = []

    for i, (search_text, replace_text) in enumerate(diff_blocks):
        search_lines = search_text.strip().split("\n")
        replace_lines = replace_text.strip().split("\n")

        # Create a short summary
        if len(search_lines) == 1 and len(replace_lines) == 1:
            summary.append(f"Change {i+1}: '{search_lines[0]}' to '{replace_lines[0]}'")
        else:
            search_summary = (
                f"{len(search_lines)} lines" if len(search_lines) > 1 else search_lines[0]
            )
            replace_summary = (
                f"{len(replace_lines)} lines" if len(replace_lines) > 1 else replace_lines[0]
            )
            summary.append(f"Change {i+1}: Replace {search_summary} with {replace_summary}")

    return "\n".join(summary)


def calculate_edit_distance(code1: str, code2: str) -> int:
    """
    Calculate the Levenshtein edit distance between two code snippets

    Args:
        code1: First code snippet
        code2: Second code snippet

    Returns:
        Edit distance (number of operations needed to transform code1 into code2)
    """
    if code1 == code2:
        return 0

    # Simple implementation of Levenshtein distance
    m, n = len(code1), len(code2)
    dp = [[0 for _ in range(n + 1)] for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i

    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if code1[i - 1] == code2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )

    return dp[m][n]


def extract_code_language(code: str) -> str:
    """
    Try to determine the language of a code snippet

    Args:
        code: Code snippet

    Returns:
        Detected language or "unknown"
    """
    # Look for common language signatures
    if re.search(r"^(import|from|def|class)\s", code, re.MULTILINE):
        return "python"
    elif re.search(r"^(package|import java|public class)", code, re.MULTILINE):
        return "java"
    elif re.search(r"^(#include|int main|void main)", code, re.MULTILINE):
        return "cpp"
    elif re.search(r"^(function|var|let|const|console\.log)", code, re.MULTILINE):
        return "javascript"
    elif re.search(r"^(module|fn|let mut|impl)", code, re.MULTILINE):
        return "rust"
    elif re.search(r"^(SELECT|CREATE TABLE|INSERT INTO)", code, re.MULTILINE):
        return "sql"

    return "unknown"
