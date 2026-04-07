## Response style
- Start with the direct answer; minimize preamble and filler.
- If my statement is incorrect, say so explicitly and correct it.
- If my proposal is risky or a bad idea, say so explicitly, explain why
  briefly, and suggest a better alternative.

## Code style
- Line length: keep lines ≤ 80 characters when practical.
- If a line would exceed 80 chars, wrap using implicit continuation inside
  parentheses/brackets/braces (do not use backslashes). Prefer breaking
  after the opening delimiter and placing one item per line.
- Use leading-comma vertical formatting for long function/method
  definitions and calls, e.g.:

  ```python
  def f(self
       ,abc
       ,def=None
       ,long_parameter_name=None):

      ...

  result = some_function(arg1
                        ,arg2)
  ```

- Prefer positional arguments in calls when it improves readability and
  matches existing project conventions. Use keyword arguments when
  required by the API, when parameters are ambiguous, or when doing so
  materially improves clarity.
- Avoid adding new `**kwargs`/catch-all parameters unless explicitly
  requested or already a project pattern.

## Scripting
- Do not generate PowerShell scripts intended to be committed to the repo.
  Repository scripts should be Python, Windows command, or git-bash shell
  unless requested otherwise.

## Security / secrets handling
- Do **not** open, read, quote, summarize, or request the contents of any
  `.gitignore` files.
- Avoid reading or quoting files that commonly contain secrets, including:
  - `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `*.pfx`
  - `credentials*`, `secrets*`, and `config.*` if it contains tokens/keys
  - cloud/provider credential files (AWS/GCP/Azure), SSH config, etc.
- If secret-like content is encountered (keys, tokens, passwords):
  - **Do not reproduce it** in output (even partially).
  - Warn that a secret may be exposed and recommend rotating it.
  - Continue using **placeholders** (never real secret values).