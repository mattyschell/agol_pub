Line length: keep lines ≤ 80 characters when practical.

If a line would exceed 80 chars, wrap using implicit continuation inside parentheses/brackets/braces (do not use backslashes). Prefer breaking after the opening delimiter and placing one item per line.

For function/method definitions and calls, use the project style with leading commas, e.g.:

def f(self
     ,abc
     ,def=None
     ,long_parameter_name=None):
    
    ...

result = some_function(arg1
                      ,arg2)

Apply the same vertical, leading-comma formatting to function/method *calls* in code bodies.
When a call would be long (or approach the 80-column limit), wrap it using parentheses with
one argument per line and leading commas, e.g.:

response = requests.post(self.endpoint
                        ,payload
                        ,self.headers)

Prefer positional arguments over keyword arguments in calls, except when keywords are required
by the API or necessary to avoid ambiguity.

Avoid keyword arguments (kwargs) in function/method calls and definitions. Prefer positional arguments instead, except when a function/API *requires* keywords (e.g., many stdlib/framework calls) or when omitting keywords would materially harm clarity.

If keywords are required, keep them minimal and follow the line-wrapping + leading-comma style. Do not introduce new optional parameters as keywords unless explicitly requested.

## Scripting

Do not generate PowerShell scripts for commit to the repository. All repository code should be Python, Windows command, or git bash shell unless requested otherwise.

## Security / secrets handling

- Do **not** open, read, quote, summarize, or request the contents of `.gitignore` files.
- Treat `.gitignore` as potentially sensitive and **out of scope** for analysis.

- Also avoid reading or quoting any files that commonly contain secrets, including:
  - `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `*.pfx`
  - `credentials*`, `secrets*`, `config.*` when it contains tokens/keys
  - cloud/provider credential files (AWS/GCP/Azure), SSH config, etc.

- If secret-like content is encountered in any context (keys, tokens, passwords):
  - **Do not reproduce it** in output (even partially).
  - Immediately warn that a secret may be exposed and recommend rotating it.
  - Continue by describing steps using **placeholders**
