import os
import hashlib

username_pattern = r'[A-Za-z0-9_-]{4,10}'
password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[.-_@$!%*?&])[A-Za-z\d.-_@$!%*?&]{8,}$'
email_pattern = r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
name_pattern = r'[A-Za-z0-9 ]{5,30}'

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return salt.hex() + hashed_password

def verify_password(stored_hash: str, password: str) -> bool:
    salt = bytes.fromhex(stored_hash[:32])
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return stored_hash[32:] == hashed_password


def markdown_to_html(markdown_text):
    lines = markdown_text.split('\n')
    html_output = []
    active_formats = {"ol": False, "ul": False}
    for line, i in zip(lines, range(len(lines))):
        if line.strip().startswith('# '):
            html_output.append(f'<h1>{line.replace('# ', '', 1)}</h1>')
        elif line.strip().startswith('## '):
            html_output.append(f'<h2>{line.replace('## ', '', 1)}</h2>')
        elif line.strip().startswith('### '):
            html_output.append(f'<h3>{line.replace('### ', '', 1)}</h3>')
        elif line.strip().startswith('&gt; '):
            html_output.append(f'<blockquote>{line.replace('&gt; ', '', 1)}</blockquote>')
        elif line.strip().startswith('---'):
            html_output.append('<hr>')
        elif line.strip().startswith('- '):
            if not active_formats["ul"]:
                html_output.append('<ul>')
                active_formats["ul"] = True
            html_output.append(f'<li>{line.replace('- ', '', 1)}</li>')
            if i == len(lines) - 1 or not lines[i + 1].strip().startswith('- '):
                html_output.append('</ul>')
                active_formats["ul"] = False
        elif line.strip().startswith('X. '):
            if not active_formats["ol"]:
                html_output.append('<ol>')
                active_formats["ol"] = True
            html_output.append(f'<li>{line.replace('X. ', '', 1)}</li>')
            if i == len(lines) - 1 or not lines[i + 1].strip().startswith('X. '):
                html_output.append('</ol>')
                active_formats["ol"] = False
        else:
            html_output.append(line)
            html_output.append('<br>')

    html_output = '\n'.join(html_output)
    return replace_formats(html_output)


def replace_formats(text):
    active_formats = {"**": False, "*": False, "`": False, "```": False, "~~": False, "==": False, "^": False,
                      "~": False}
    markdown_formats_open = {"**": "<b>", "*": "<i>", "```": "<pre><code>", "`": "<code>", "~~": "<del>",
                             "==": "<mark>", "^": "<sup>", "~": "<sub>"}
    markdown_formats_close = {"**": "</b>", "*": "</i>", "```": "</code></pre>", "`": "</code>", "~~": "</del>",
                              "==": "</mark>", "^": "</sup>", "~": "</sub>"}
    result = ""
    i = 0
    while i < len(text):
        matched = False

        # First check for the triple backtick (```), to handle multi-line code blocks
        if text[i:i + 3] == "```":
            fmt = "```"
            if active_formats[fmt]:
                result += markdown_formats_close[fmt]
            else:
                result += markdown_formats_open[fmt]
            active_formats[fmt] = not active_formats[fmt]
            i += 3
            matched = True

        # If not a triple backtick, check for other formatting (including single backtick)
        if not matched:
            for fmt in active_formats:
                if fmt != "```" and text[i:i + len(fmt)] == fmt:
                    if active_formats[fmt]:
                        result += markdown_formats_close[fmt]
                    else:
                        result += markdown_formats_open[fmt]
                    active_formats[fmt] = not active_formats[fmt]
                    i += len(fmt)
                    matched = True
                    break

        # If no format matched, just add the current character
        if not matched:
            result += text[i]
            i += 1

    return result


if __name__ == '__main__':
    # Beispieltext
    markdown_text = """
    # H1
    ## H2
    ### H3
    
    **bold text**
    
    *italicized text*
    
    > blockquote
    
    1. First item
    2. Second item
    3. Third item
    
    - First item
    - Second item
    - Third item
    
    `code`
    
    ---
    
    [title](https://www.example.com)
    
    ![alt text](image.jpg)
    
    | Syntax | Description |
    | ----------- | ----------- |
    | Header | Title |
    | Paragraph | Text |
    
    { "firstName": "John", "lastName": "Smith", "age": 25 }
    
    Here's a sentence with a footnote. [^1]
    
    [^1]: This is the footnote.
    
    ### My Great Heading {#custom-id}
    
    term: definition
    
    ~~The world is flat.~~
    
    - [x] Write the press release
    - [ ] Update the website
    - [ ] Contact the media
    
    I need to highlight these ==very important words==.
    
    H~2~O
    
    X^2^
    """

    print(markdown_to_html(markdown_text))
