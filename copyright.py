from pathlib import Path

HEADER_MARKER = 'SPDX-License-Identifier'  # used to detect existing header
HEADER_FILE = Path('copyright.txt')

header = HEADER_FILE.read_text(encoding='utf-8').rstrip() + '\n\n'

for path in Path('.').rglob('*.py'):
    text = path.read_text(encoding='utf-8')

    # Skip files that already have the header
    if HEADER_MARKER in text[:1000]:
        continue

    lines = text.splitlines(keepends=True)

    # Preserve shebang
    insert_at = 1 if lines and lines[0].startswith('#!') else 0

    new_text = (
        ''.join(lines[:insert_at]) +
        header +
        ''.join(lines[insert_at:])
    )

    path.write_text(new_text, encoding='utf-8')
    print(f'Updated: {path}')
