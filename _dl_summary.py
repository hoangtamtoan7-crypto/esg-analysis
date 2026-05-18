import csv
from pathlib import Path

log_path = Path("data/download_log.csv")
with open(log_path, "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))

success = [r for r in reader if r["status"] == "success"]
fail = [r for r in reader if r["status"] != "success"]

print(f"Total: {len(reader)} | Success: {len(success)} | Failed: {len(fail)}")

if fail:
    print("\nFailed companies:")
    for row in fail:
        print(f"  {row['code']} {row['name']}: {row['status']}")

# Show some stats
pdfs = sorted(Path("data/pdfs").glob("*.pdf"))
sizes = [p.stat().st_size for p in pdfs]
total_mb = sum(sizes) / 1024 / 1024
print(f"\nTotal size: {total_mb:.0f} MB")
print(f"Average size: {total_mb/len(pdfs):.1f} MB")
print(f"Largest: {max(sizes)/1024/1024:.0f} MB")
print(f"Smallest: {min(sizes)/1024/1024:.0f} MB")
