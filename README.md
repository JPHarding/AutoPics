# AutoPics
# AutoPics
Automated image preparation and compression tool.

AutoPics is a desktop application for preparing and compressing product or catalog images in batches.
It provides a Qt-based GUI for selecting source/output folders, applying optional image cleanup/enhancement steps, and exporting optimized files in modern formats.

## What AutoPics does

- Batch-processes images from a source folder into a target `comp` folder.
- Supports output to **JPEG**, **AVIF**, **JPEG XL**, and **PNG**.
- Lets you choose quality presets (High / Medium / Low) or enforce a target size standard.
- Includes optional image operations:
  - automatic trimming of flat-color borders,
  - color enhancement,
  - sharpness enhancement,
  - standard or custom max-dimension resize.
- Uses parallel processing to speed up large batches.
- Displays run results in-app and previews output images while processing.

## Tech stack

- **Python**
- **PySide6** for the desktop GUI
- **Pillow** for image manipulation
- **pillow-avif-plugin** and **pillow-jxl-plugin** for AVIF/JXL support

## Requirements

- Python **3.14+** (as defined in `pyproject.toml`)
- A platform supported by PySide6 and your selected image codec plugins

## Installation

This project uses [`uv`](https://docs.astral.sh/uv/) in its lockfile workflow.

```bash
uv sync
```

If you do not use `uv`, install dependencies manually from `pyproject.toml`:

```bash
pip install pyside6 pillow-avif-plugin pillow-jxl-plugin
```

## Running the app

From the project root:

```bash
python AutoPics.py
```

## Usage overview

1. Click **Browse** and select your source image folder.
2. Confirm or adjust the output `comp` folder path.
3. (Optional) Enter a rename prefix for generated files.
4. Configure settings:
   - quality mode,
   - resize behavior,
   - output format,
   - enhancement options.
5. Click **Process**.
6. Review the output summary and generated files in the `comp` folder.

## Project structure

- `AutoPics.py` — main GUI application.
- `picComp.py` — batch orchestration, encoding logic, and multiprocessing pipeline.
- `imageEditing.py` — reusable image editing utilities.
- `third_party_licenses/` — bundled third-party license texts.

## Licensing

- Project license: see [`LICENSE`](LICENSE).
- Third-party notices: see files under [`third_party_licenses/`](thiAutomated image preparation and compression tool.

AutoPics is a desktop application for preparing and compressing product or catalog images in batches.
It provides a Qt-based GUI for selecting source/output folders, applying optional image cleanup/enhancement steps, and exporting optimized files in modern formats.

## What AutoPics does

- Batch-processes images from a source folder into a target `comp` folder.
- Supports output to **JPEG**, **AVIF**, **JPEG XL**, and **PNG**.
- Lets you choose quality presets (High / Medium / Low) or enforce a target size standard.
- Includes optional image operations:
  - automatic trimming of flat-color borders,
  - color enhancement,
  - sharpness enhancement,
  - standard or custom max-dimension resize.
- Uses parallel processing to speed up large batches.
- Displays run results in-app and previews output images while processing.

## Tech stack

- **Python**
- **PySide6** for the desktop GUI
- **Pillow** for image manipulation
- **pillow-avif-plugin** and **pillow-jxl-plugin** for AVIF/JXL support

## Requirements

- Python **3.14+** (as defined in `pyproject.toml`)
- A platform supported by PySide6 and your selected image codec plugins

## Installation

This project uses [`uv`](https://docs.astral.sh/uv/) in its lockfile workflow.

```bash
uv sync
```

If you do not use `uv`, install dependencies manually from `pyproject.toml`:

```bash
pip install pyside6 pillow-avif-plugin pillow-jxl-plugin
```

## Running the app

From the project root:

```bash
python AutoPics.py
```

## Usage overview

1. Click **Browse** and select your source image folder.
2. (Optional) Enter a rename prefix for generated files.
3. Configure settings:
   - quality mode,
   - resize behavior,
   - output format,
   - enhancement options.
4. Click **Process**.
5. Review the output summary and generated files in the `comp` folder.

## Project structure

- `AutoPics.py` — main GUI application.
- `picComp.py` — batch orchestration, encoding logic, and multiprocessing pipeline.
- `imageEditing.py` — reusable image editing utilities.
- `third_party_licenses/` — bundled third-party license texts.

## Licensing

- Project license: see [`LICENSE`](LICENSE).
- Third-party notices: see files under [`third_party_licenses/`](third_party_licenses).

