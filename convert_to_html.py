#!/usr/bin/env python3
"""Convert DocBook XML to OASIS-styled HTML using the same XSLT pipeline as oasis-tcs/ubl.

This script mirrors the local-preview path from the oasis-tcs/ubl repository
(ubl-2.5 branch), using Saxon HE to apply the OASIS 2025 DocBook-to-HTML
stylesheet chain:

    oasis-2025-spec-note-html.xsl
      ├── imports:  docbook/xsl/html/docbook.xsl  (standard DocBook XSL)
      ├── includes: titlepage-2025-html.xsl
      └── includes: oasis-mathml-html.xsl

The 2025 stylesheet produces a self-contained HTML file with the OASIS logo
embedded as a base64 data URI and the CSS inlined in the <head>.

Requirements:
    - Java Runtime Environment (JRE) 8+
    - Saxon HE 9 jar at utilities/saxon9he/saxon9he.jar
    - OASIS stylesheets + DocBook XSL at db/spec-0.9/htmlruntime/
"""

import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SAXON_JAR = os.path.join(SCRIPT_DIR, "utilities", "saxon9he", "saxon9he.jar")

STYLESHEET = os.path.join(
    SCRIPT_DIR, "db", "spec-0.9", "htmlruntime", "spec-0.9",
    "stylesheets", "oasis-2025-spec-note-html.xsl"
)

DEFAULT_INPUT = os.path.join(SCRIPT_DIR, "UBL-2.5-JSON-Syntax-Binding.xml")


def check_java():
    """Verify that Java is available."""
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("ERROR: Java is installed but returned an error.", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        # Java -version prints to stderr
        version_line = (result.stderr or result.stdout).strip().split("\n")[0]
        print(f"  Java: {version_line}")
    except FileNotFoundError:
        print("ERROR: Java is not installed or not on PATH.", file=sys.stderr)
        print("  Install a JRE (e.g., apt-get install default-jre-headless)", file=sys.stderr)
        sys.exit(1)


def check_prerequisites(input_xml):
    """Verify all required files exist."""
    print("Checking prerequisites...")
    check_java()

    for label, path in [
        ("Saxon HE", SAXON_JAR),
        ("XSLT stylesheet", STYLESHEET),
        ("Input XML", input_xml),
    ]:
        if not os.path.isfile(path):
            print(f"ERROR: {label} not found: {path}", file=sys.stderr)
            sys.exit(1)
        print(f"  {label}: {path} ({os.path.getsize(path):,} bytes)")


def prepare_input(input_xml):
    """Resolve internal entities and strip DOCTYPE from input XML.

    The DocBook XML uses entity references (e.g. &standard;, &pubdate;)
    defined in the DOCTYPE's internal subset.  We extract those definitions
    with a regex, expand every reference in the document body, then strip the
    entire DOCTYPE block so Saxon never needs to fetch the external DTD over
    the network.
    """
    import re
    import tempfile

    with open(input_xml, "r", encoding="utf-8") as f:
        content = f.read()

    # ------------------------------------------------------------------
    # 1. Extract the DOCTYPE block (including the internal subset [...]).
    #    The block starts with "<!DOCTYPE" and ends at the matching "]>"
    #    (when an internal subset is present) or the first bare ">".
    #
    #    We use find() rather than a DOTALL regex so that we never
    #    accidentally match a "]]>" from a CDATA section later in the
    #    document.  The DOCTYPE is always before the root element, so
    #    any "]>" we find starting from the "[" position is guaranteed
    #    to be the DOCTYPE's closing delimiter and not a CDATA end-tag.
    # ------------------------------------------------------------------
    entities = {}
    doctype_start = content.find('<!DOCTYPE')
    if doctype_start != -1:
        bracket_pos = content.find('[', doctype_start)
        close_tag_pos = content.find('>', doctype_start)

        if bracket_pos != -1 and bracket_pos < close_tag_pos:
            # Has internal subset — find the closing ]>
            # This is safe: "[" is inside the DOCTYPE prolog, well before
            # any element content, so the first "]>" from here belongs to
            # the DOCTYPE, not to a CDATA section.
            subset_end = content.find(']>', bracket_pos)
            if subset_end != -1:
                doctype_end = subset_end + 2  # include the ]>
            else:
                doctype_end = close_tag_pos + 1
        else:
            # No internal subset — just find the closing >
            doctype_end = close_tag_pos + 1

        doctype_block = content[doctype_start:doctype_end]

        # 2. Extract all <!ENTITY name "value"> declarations from the block
        for m in re.finditer(r'<!ENTITY\s+(\S+)\s+"([^"]*)"', doctype_block):
            entities[m.group(1)] = m.group(2)

        # 3. Remove the entire DOCTYPE block from the content
        content = content[:doctype_start] + content[doctype_end:]

    # 4. Expand entity references in the remaining content.
    #    Only expand the entities we found; leave standard XML entities alone
    #    (&amp; &lt; &gt; &apos; &quot;) — the XML parser handles those itself.
    if entities:
        def replace_entity(m):
            name = m.group(1)
            return entities.get(name, m.group(0))  # leave unknown refs untouched

        # Build a pattern that matches only our custom entities
        pattern = r'&(' + '|'.join(re.escape(k) for k in entities) + r');'
        content = re.sub(pattern, replace_entity, content)

    if entities:
        print(f"  Resolved {len(entities)} internal entities: {', '.join(entities)}")

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", dir=SCRIPT_DIR, delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    print(f"  Preprocessed input (entities resolved, DOCTYPE stripped): {tmp.name}")
    return tmp.name


def run_saxon(input_xml, output_html):
    """Run Saxon HE to transform DocBook XML to HTML."""
    # Preprocess input to strip DOCTYPE (avoids remote DTD resolution)
    processed_xml = prepare_input(input_xml)

    try:
        cmd = [
            "java",
            "-jar", SAXON_JAR,
            f"-s:{processed_xml}",
            f"-xsl:{STYLESHEET}",
            f"-o:{output_html}",
        ]

        print(f"\nRunning XSLT transformation...")
        print(f"  Command: java -jar saxon9he.jar -s:... -xsl:... -o:...")
        print()

        result = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        os.unlink(processed_xml)

    # Saxon prints warnings to stderr even on success
    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            if line.strip():
                print(f"  Saxon: {line}")

    if result.returncode != 0:
        print(f"\nERROR: Saxon exited with code {result.returncode}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        sys.exit(1)

    return result.returncode == 0


def fix_encoding(output_html):
    """Re-encode HTML from ISO-8859-1 to UTF-8.

    The OASIS DocBook XSL stylesheet declares ISO-8859-1 encoding.
    GitHub Pages (and most modern servers) serve files as UTF-8,
    causing mojibake for non-ASCII characters.  We convert the file
    to UTF-8 and update the meta charset declaration.
    """
    with open(output_html, "rb") as f:
        raw = f.read()

    # Detect if it's ISO-8859-1 by checking the meta tag
    if b'charset=ISO-8859-1' in raw or b'charset=iso-8859-1' in raw:
        text = raw.decode("iso-8859-1")
        text = text.replace(
            'charset=ISO-8859-1', 'charset=UTF-8'
        ).replace(
            'charset=iso-8859-1', 'charset=UTF-8'
        )
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  Re-encoded from ISO-8859-1 to UTF-8")
    else:
        print(f"  Encoding: already UTF-8 (no conversion needed)")


def validate_output(output_html):
    """Basic validation of the generated HTML."""
    if not os.path.isfile(output_html):
        print(f"ERROR: Output file was not created: {output_html}", file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(output_html)
    if size < 1000:
        print(f"WARNING: Output file is suspiciously small: {size} bytes", file=sys.stderr)

    with open(output_html, "r", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "Contains <html": "<html" in content,
        "Contains <head": "<head" in content,
        "Contains <body": "<body" in content,
        "Contains document title": "UBL 2.5 JSON Syntax Binding" in content,
        "File size reasonable": size > 10000,
    }

    print(f"\nOutput validation:")
    print(f"  File: {output_html}")
    print(f"  Size: {size:,} bytes")
    all_pass = True
    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {check}: {status}")
        if not passed:
            all_pass = False

    return all_pass


def main():
    input_xml = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    output_html = os.path.splitext(input_xml)[0] + ".html"

    if len(sys.argv) > 2:
        output_html = sys.argv[2]

    print(f"DocBook XML to OASIS HTML Converter")
    print(f"{'=' * 40}")
    print(f"  Input:  {input_xml}")
    print(f"  Output: {output_html}")
    print()

    check_prerequisites(input_xml)
    run_saxon(input_xml, output_html)
    fix_encoding(output_html)
    success = validate_output(output_html)

    if success:
        print(f"\nDone. HTML written to {output_html}")
    else:
        print(f"\nWARNING: Output was generated but some checks failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
