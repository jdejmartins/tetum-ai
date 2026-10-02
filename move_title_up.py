from pathlib import Path
from datetime import datetime
import shutil

html_file = Path("templates/index.html")

if not html_file.exists():
    print("ERROR: templates/index.html not found.")
    raise SystemExit(1)

content = html_file.read_text(encoding="utf-8")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = Path(
    f"checkpoints/index_before_move_title_up_{timestamp}.html"
)

backup_file.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(html_file, backup_file)

print(f"Backup created: {backup_file}")

old_desktop = "padding:28px 22px 24px"
new_desktop = "padding:18px 22px 24px"

old_mobile = "padding:22px 16px 20px"
new_mobile = "padding:14px 16px 20px"

changes = 0

if old_desktop in content:
    content = content.replace(old_desktop, new_desktop, 1)
    print("Desktop title moved upward.")
    changes += 1

if old_mobile in content:
    content = content.replace(old_mobile, new_mobile, 1)
    print("Mobile title moved upward.")
    changes += 1

if changes == 0:
    print("WARNING: Expected hero padding values were not found.")
    raise SystemExit(1)

html_file.write_text(content, encoding="utf-8")

updated = html_file.read_text(encoding="utf-8")

if new_desktop in updated and new_mobile in updated:
    print("")
    print("SUCCESS.")
    print("Title section moved upward by approximately 10px.")
else:
    print("ERROR: Could not verify the change.")
    raise SystemExit(1)
