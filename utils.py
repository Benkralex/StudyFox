import os
import hashlib

username_pattern = r'[A-Za-z0-9_-]{4,10}'
password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[.-_@$!%*?&])[A-Za-z\d.-_@$!%*?&]{8,}$'
email_pattern = r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
name_pattern = r'[A-Za-z0-9 ]{5,30}'
replace_list = ["b", "i", "mark", "small", "del", "ins", "sub", "sup", "br",
                    "table", "thead", "tbody", "tfoot", "td", "th",
                    "blockquote", "h1", "h2", "h3", "h4", "h5", "h6",
                    "hr", "ul", "ol", "li", "p", "code", "pre"]

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


def escapedhtml_to_html(escapedhtml_text):
    #a and img are not included because they have attributes
    escapedhtml_text = escapedhtml_text.replace("&amp;", "&")
    for tag in replace_list:
        escapedhtml_text = escapedhtml_text.replace("&lt;" + tag + "&gt;", "<" + tag + ">")
        escapedhtml_text = escapedhtml_text.replace("&lt;/" + tag + "&gt;", "</" + tag + ">")

    #a and img only with files and links on the server
    escapedhtml_text = escapedhtml_text.replace("&lt;a href=&#34;", "<a target=\"_blank\" href=\"/link/")
    escapedhtml_text = escapedhtml_text.replace("&lt;/a&gt;", "</a>")
    escapedhtml_text = escapedhtml_text.replace("&lt;img src=&#34;", "<img src=\"/img/")
    escapedhtml_text = escapedhtml_text.replace("&#34; alt=&#34;", "\" alt=\"")
    escapedhtml_text = escapedhtml_text.replace("&#34; width=&#34;", "\" width=\"")
    escapedhtml_text = escapedhtml_text.replace("&#34; height=&#34;", "\" height=\"")
    escapedhtml_text = escapedhtml_text.replace("&#34;&gt;", "\">")

    return escapedhtml_text

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
