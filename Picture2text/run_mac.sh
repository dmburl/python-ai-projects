
#!/usr/bin/env bash
# Simple launcher for macOS that runs the system Python to start `ocr2md.py`.
# If double-clicking opens this file in an editor, rename it to `run_mac.command`
# and make it executable with `chmod +x run_mac.command`.

DIR="$(cd "$(dirname "$0")" && pwd)"

python3 "$DIR/ocr2md.py"

exit 0
