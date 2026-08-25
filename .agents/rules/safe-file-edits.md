# Rule: Safe File Edits

When modifying files—especially code containing special characters, template literals, or shell variables (`$`, backticks, quotes)—adhere strictly to the following constraints to prevent interpolation bugs:

1. **Prefer Native Editing Tools:** ALWAYS use `replace_file_content` or `multi_replace_file_content` to edit files. These tools safely handle special characters without shell interpolation.
2. **Avoid Inline Scripting via PowerShell:** NEVER write inline Python or Bash scripts wrapped in PowerShell strings (e.g., `Set-Content -Value @" ... "@`) to modify files. PowerShell interpolates `$` variables inside `@""@` blocks, which will silently strip JavaScript/Python variables from your code.
3. **Targeted Edits Only:** Do not try to read the entire file into a variable, modify a string, and write the entire file back using the CLI. Use the dedicated editing tools which provide built-in safeguards and syntax preservation.
