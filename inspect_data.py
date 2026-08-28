from pathlib import Path

# ==========================================
# 🇪🇬 Egypt Explorer AI
# Inspect Kaggle Dataset
# ==========================================

DATA_DIR = Path("data/raw")

print("=" * 60)
print("🇪🇬 EGYPT EXPLORER AI")
print("📊 DATASET INSPECTION")
print("=" * 60)

if not DATA_DIR.exists():
    print("❌ data/raw does not exist!")
    exit()

print("\n📁 Dataset location:")
print(DATA_DIR.resolve())

print("\n📦 Files and folders:")
print("-" * 60)

items = list(DATA_DIR.rglob("*"))

for item in items:

    if item.is_file():
        size_mb = item.stat().st_size / (1024 * 1024)

        print(
            f"📄 {item.relative_to(DATA_DIR)} "
            f"({size_mb:.2f} MB)"
        )

    elif item.is_dir():
        print(
            f"📁 {item.relative_to(DATA_DIR)}/"
        )

print("\n" + "=" * 60)
print(f"Total items: {len(items)}")
print("=" * 60)