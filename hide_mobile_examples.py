from pathlib import Path
from datetime import datetime
import shutil

html_file = Path("templates/index.html")

if not html_file.exists():
    print("ERROR: templates/index.html not found.")
    raise SystemExit(1)

content = html_file.read_text(encoding="utf-8")

marker = "/* Hide example service buttons on mobile */"

if marker in content:
    print("Mobile service-button hiding rule already exists.")
    raise SystemExit(0)

# Backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = Path(
    f"checkpoints/index_before_hide_mobile_examples_{timestamp}.html"
)

backup_file.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(html_file, backup_file)

print(f"Backup created: {backup_file}")

mobile_css = r'''
/* Hide example service buttons on mobile */
@media (max-width: 700px) {
    .ask-card .examples {
        display: none !important;
    }
}
'''

style_end = content.rfind("</style>")

if style_end == -1:
    print("ERROR: </style> not found.")
    raise SystemExit(1)

content = (
    content[:style_end]
    + "\n"
    + mobile_css
    + "\n"
    + content[style_end:]
)

html_file.write_text(content, encoding="utf-8")

# Verify
updated = html_file.read_text(encoding="utf-8")

if marker not in updated:
    print("ERROR: Mobile CSS could not be verified.")
    raise SystemExit(1)

print("")
print("SUCCESS.")
print("The three example service buttons are now hidden on mobile.")
print("They remain visible on desktop.")
