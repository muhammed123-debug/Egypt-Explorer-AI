from pathlib import Path
import csv

# ==========================================
# 🇪🇬 Egypt Explorer AI
# Extract Landmark Names
# ==========================================

DATA_DIR = Path("data/raw/images")
OUTPUT_FILE = Path("data/landmarks.csv")

print("=" * 60)
print("🇪🇬 EGYPT EXPLORER AI")
print("🏛️ LANDMARK EXTRACTION")
print("=" * 60)

# Check dataset folder
if not DATA_DIR.exists():
    print(f"❌ Images folder not found:")
    print(DATA_DIR.resolve())
    exit()

# Get all landmark folders
landmark_folders = sorted([
    folder for folder in DATA_DIR.iterdir()
    if folder.is_dir()
])

print(f"\n🏛️ Number of landmarks: {len(landmark_folders)}")

# Prepare output directory
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

rows = []

for folder in landmark_folders:

    # Count images
    image_files = [
        file for file in folder.iterdir()
        if file.is_file()
        and file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ]

    landmark_name = folder.name.replace("_", " ")

    rows.append({
        "landmark_id": len(rows) + 1,
        "landmark_name": landmark_name,
        "folder_name": folder.name,
        "image_count": len(image_files)
    })

# Save CSV
with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "landmark_id",
            "landmark_name",
            "folder_name",
            "image_count"
        ]
    )

    writer.writeheader()
    writer.writerows(rows)

print("\n✅ Extraction completed!")

print(f"\n📄 Output file:")
print(OUTPUT_FILE.resolve())

print("\n📊 First 10 landmarks:")
print("-" * 60)

for row in rows[:10]:

    print(
        f"{row['landmark_id']:3} | "
        f"{row['landmark_name']:<45} | "
        f"{row['image_count']} images"
    )

print("\n" + "=" * 60)
print("🎉 landmarks.csv created successfully!")
print("=" * 60)