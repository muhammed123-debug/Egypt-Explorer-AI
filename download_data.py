import kagglehub
from pathlib import Path
import shutil

# ==========================================
# 🇪🇬 Egypt Explorer AI
# Download Egypt Landmarks Dataset
# ==========================================

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("🔄 Downloading Egypt Landmarks Dataset...")

path = kagglehub.dataset_download(
    "aymanmostafa11/eg-landmarks"
)

print(f"✅ Dataset downloaded to:")
print(path)

# Copy dataset into our project
source = Path(path)

print("\n📦 Copying dataset into project...")

for item in source.iterdir():

    destination = DATA_DIR / item.name

    if item.is_dir():
        shutil.copytree(
            item,
            destination,
            dirs_exist_ok=True
        )
    else:
        shutil.copy2(
            item,
            destination
        )

print("\n🎉 Dataset is now inside:")

print(DATA_DIR.resolve())