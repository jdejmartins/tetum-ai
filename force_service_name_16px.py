from pathlib import Path
from datetime import datetime
import shutil
import re

html_file = Path("templates/index.html")

if not html_file.exists():
    print("ERROR: templates/index.html not found.")
    raise SystemExit(1)

content = html_file.read_text(encoding="utf-8")

# Find the .service-name CSS rule
pattern = r'(\.service-name\s*\{[^}]*?)font-size\s*:\s*[^;]+;([^}]*\})'

match = re.search(pattern, content, re.DOTALL)

if not match:
    print("ERROR: Could not find .service-name CSS rule.")
    raise SystemExit(1)

old_rule = match.group(0)

# Backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = Path(
    f"checkpoints/index_before_service_name_16px_fix_{timestamp}.html"
)

backup_file.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(html_file, backup_file)

print(f"Backup created: {backup_file}")
print("")
print("Current .service-name rule:")
print(old_rule)

# Replace only the font-size inside .service-name
new_rule = re.sub(
    r'font-size\s*:\s*[^;]+;',
    'font-size:16px;',
    old_rule,
    count=1
)

content = content.replace(old_rule, new_rule, 1)

html_file.write_text(content, encoding="utf-8")

# Verify
updated = html_file.read_text(encoding="utf-8")

verify = re.search(
    r'\.service-name\s*\{[^}]*font-size\s*:\s*16px;[^}]*\}',
    updated,
    re.DOTALL
)

print("")
if verify:
    print("SUCCESS.")
    print("The .service-name font size is now 16px.")
    print("")
    print("Updated rule:")
    print(verify.group(0))
else:
    print("ERROR: Could not verify the 16px rule.")
    raise SystemExit(1)
