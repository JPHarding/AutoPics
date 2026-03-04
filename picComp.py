from __future__ import annotations

import os
import tempfile
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from io import BytesIO
from multiprocessing import freeze_support
from pathlib import Path
from typing import Callable

from PIL import Image

import imageEditing as imageEditing


@dataclass(frozen=True)
class EncodeResult:
    quality: int
    data: bytes


class PicComp:
    def __init__(
        self,
        source_folder: Path,
        comp_folder: Path,
        encoder: str,
        rename: str,
        disable_resize: bool,
        image_quality: str,
        custom_resize_px: int,
        custom_resize_bool: bool | None,
        contrast_chbx_var: bool,
        sharpen_chbx_var: bool,
        dic_standards: dict[str, str],
        trim_chbx_value: bool,
        source_images: list[str],
        ensure_standards_chbx_var: bool,
    ) -> None:
        self.source_folder: Path = source_folder
        self.comp_folder: Path = comp_folder
        self.encoder: str = encoder
        self.rename = rename
        self.disable_resize: bool = disable_resize
        self.image_quality: str = image_quality
        self.custom_resize_px: int = custom_resize_px
        self.custom_resize_bool: bool | None = custom_resize_bool
        self.contrast_chbx_var: bool = contrast_chbx_var
        self.sharpen_chbx_var: bool = sharpen_chbx_var
        self.dic_standards: dict[str, str] = dic_standards
        self.trim_chbx_value: bool = trim_chbx_value
        self.source_images: list[str] = source_images
        self.ensure_standards_chbx_var: bool = ensure_standards_chbx_var
        self.jxl_chbx_var: int = 0
        self.avif_chbx_var: int = 0
        self.png_chbx_var: int = 0
        self.prefix = ".jpg"
        Image.MAX_IMAGE_PIXELS = 500_000_000
        # This is most of the supported file formats
        self.SUFFIXES = (
            ".jpg",
            ".jpeg",
            ".jxl",
            ".png",
            ".tif",
            ".webp",
            ".bmp",
            ".ico",
            ".psd",
            ".avif",
            ".jfif",
            ".jpe",
            ".j2c",
            ".j2k",
            ".jp2",
            ".jpc",
            ".jpf",
            ".jpx",
            ".pcx",
            ".apng",
            ".tiff",
        )

    def img_compression(self, source_image_path: Path, renamed_image_name: str) -> str:
        try:
            comp_run_im = self.handle_img_editing(source_image_path)
        except IOError as e:
            print(f"Error: Reason: {e}")
            return f"Error: Reason: {e}"

        new_img_name_path = self.rename_images(source_image_path, renamed_image_name)
        source_img_file_size = Path(source_image_path).stat().st_size

        if self.png_chbx_var == 1:
            self.save_to_png(comp_run_im, new_img_name_path)
            return "Saved to PNG!"

        target_bytes = self._get_usr_target_bytes()

        res = self.compress_under_size(
            comp_run_im,
            source_img_file_size,
            target_bytes=target_bytes,
            format=self.encoder,
        )
        if res is None:
            raise ValueError("Could not hit target file size")

        with open(new_img_name_path, "wb") as file:
            file.write(res.data)

        return f"{os.path.basename(new_img_name_path)} at Quality {res.quality} at Bytes: {round(len(res.data) / 1024, 2)}KB"

    def save_to_png(self, source_image: Image.Image, comp_file_path: Path) -> None:
        source_image.save(comp_file_path, format="PNG")

    def _encode_to_bytes(self, img: Image.Image, fmt: str, save_kwargs: dict) -> bytes:
        buf = BytesIO()
        img.save(buf, format=fmt, **save_kwargs)
        return buf.getvalue()

    def _get_selected_usr_quality(self) -> int:
        image_q = self.image_quality.lower()
        if image_q == "high quality":
            return int(self.dic_standards["highQualityMozjpegQuality"])
        elif image_q == "medium quality":
            return int(self.dic_standards["mediumQualityMozjpegQuality"])
        else:
            return int(self.dic_standards["lowQualityMozjpegQuality"])

    def _get_usr_target_bytes(self) -> int:
        return int(self.dic_standards["standardMaxYourStandardsFileSizeInBytes"])

    def _binary_search_quality(
        self,
        img: Image.Image,
        target_bytes: int,
        source_img_file_size: int,
        encode_fn: Callable[[int], bytes],
        q_min: int,
        q_max: int,
    ) -> EncodeResult | None:
        lo, hi = q_min, q_max
        best: EncodeResult | None = None

        while lo <= hi:
            mid = (lo + hi) // 2
            data = encode_fn(mid)

            if len(data) <= target_bytes and len(data) <= source_img_file_size:
                best = EncodeResult(mid, data)
                lo = mid + 1
            else:
                hi = mid - 1

        if best is not None:
            return best

        fallback_q = max(q_min, min(30, q_max))
        return EncodeResult(fallback_q, encode_fn(fallback_q))

    def compress_under_size(
        self,
        img: Image.Image,
        source_img_file_size: int,
        *,
        target_bytes: int,
        format: str,
    ) -> EncodeResult | None:
        format = format.upper()

        # Find out what q_min and q_max should be.
        selected_usr_quality = self.image_quality.lower()
        print(f"ensure standards chbx var = {self.ensure_standards_chbx_var}")
        print(f"selected usr q is {selected_usr_quality}")
        print("------------------------------------------------------------------")
        if self.ensure_standards_chbx_var:
            q_min = 30
            q_max = 100
            print("standards chbx selected.")
        elif selected_usr_quality == "high quality":
            q_max = self._get_selected_usr_quality()
            q_min = int(self.dic_standards["mediumQualityMozjpegQuality"])
            print(f"qmin = {q_min} and qmax = {q_max}")
            print("high quality selected")
        elif selected_usr_quality == "medium quality":
            q_max = self._get_selected_usr_quality()
            q_min = int(self.dic_standards["lowQualityMozjpegQuality"])
            print(f"qmin = {q_min} and qmax = {q_max}")
            print("medium quality selected")
        else:
            q_max = self._get_selected_usr_quality()
            q_min = 30
            print(f"qmin = {q_min} and qmax = {q_max}")
            print("low quality default")

        if format in {"JPEG", "JPG"}:
            base = img.convert("RGB")

            def enc(q: int) -> bytes:
                return self._encode_to_bytes(
                    base,
                    "JPEG",
                    {
                        "quality": q,
                        "optimize": True,
                        "progressive": True,
                        "subsampling": "4:2:2",
                    },
                )

            return self._binary_search_quality(
                base, target_bytes, source_img_file_size, enc, q_min=q_min, q_max=q_max
            )

        if format == "AVIF":
            # AVIF supports RGB/RGBA. Keep alpha if present.
            base = (
                img.convert("RGBA")
                if img.mode in {"RGBA", "LA"}
                else img.convert("RGB")
            )

            def enc(q: int) -> bytes:
                # Use plugin-supported kwargs
                return self._encode_to_bytes(
                    base,
                    "AVIF",
                    {
                        "quality": q,  # 0..100
                        "speed": 6,  # try 4 or 3 if you want smaller files at same quality
                        "subsampling": "4:2:2",
                    },
                )

            return self._binary_search_quality(
                base, target_bytes, source_img_file_size, enc, q_min=q_min, q_max=q_max
            )

        if format in {"JXL", "JPEGXL"}:
            # JXL supports RGB/RGBA/L/LA.
            base = (
                img.convert("RGBA")
                if img.mode in {"RGBA", "LA"}
                else img.convert("RGB")
            )

            def enc(q: int) -> bytes:
                return self._encode_to_bytes(
                    base,
                    "JXL",
                    {
                        "quality": q,
                        "lossless": False,  # if True, plugin forces quality=100
                        "effort": 7,  # higher -> smaller, slower
                        "decoding_speed": 0,
                        "use_container": False,
                        "use_original_profile": False,
                        "num_threads": -1,
                    },
                )

            return self._binary_search_quality(
                base, target_bytes, source_img_file_size, enc, q_min=q_min, q_max=q_max
            )

        raise ValueError(f"Unsupported format: {format}")

    def handle_img_editing(self, image_path: Path) -> Image.Image:
        with Image.open(image_path) as img_file:
            im = img_file.convert("RGBA")
            im = imageEditing.trim(im, self.trim_chbx_value)
            standard_color = float(self.dic_standards["standardColor"])
            standard_sharpness = float(self.dic_standards["standardSharpness"])
            im = imageEditing.colourEnhancement(
                im, self.contrast_chbx_var, standard_color
            )
            im = imageEditing.sharpnessEnhancement(
                im, self.sharpen_chbx_var, standard_sharpness
            )

            if self.disable_resize == 0 and self.custom_resize_bool == 0:
                print(f"Resizing photo with your Standards({self.custom_resize_px})")
                standard_Image_Resize = int(self.dic_standards["standardImageResize"])
                im = imageEditing.resize(im, standard_Image_Resize)
            elif self.disable_resize == 0 and self.custom_resize_bool == 1:
                print(
                    f"Resizing photo with custom resize value {self.custom_resize_px}"
                )
                im = imageEditing.custom_resize(im, self.custom_resize_px)
            return imageEditing.white_bg(im)

    def rename_images(self, source_image_path: Path, renamed_image_name: str) -> Path:
        """Renames the image to either the value of the rename entry or the source image if rename is not set.
        returns a path to the compressed folder with the renamed image along with the correct file extension."""
        if self.rename == "":
            renamed_image_name = os.path.basename(source_image_path)
        if self.avif_chbx_var == 1:
            new_file_ext, _ = os.path.splitext(renamed_image_name)
            new_file_ext = new_file_ext + ".avif"
            print(new_file_ext)
        elif self.jxl_chbx_var == 1:
            new_file_ext, _ = os.path.splitext(renamed_image_name)
            new_file_ext = new_file_ext + ".jxl"
            print(new_file_ext)
        elif (
            self.jxl_chbx_var != 1
            and self.avif_chbx_var != 1
            and self.png_chbx_var != 1
        ):
            new_file_ext, _ = os.path.splitext(renamed_image_name)
            new_file_ext = new_file_ext + ".jpg"
            print(new_file_ext)
        else:
            new_file_ext, _ = os.path.splitext(renamed_image_name)
            new_file_ext = new_file_ext + ".png"
            print(new_file_ext)

        new_file_ext = os.path.basename(new_file_ext)
        # * user selected compressed photos file path.
        return Path(self.comp_folder) / new_file_ext

    def process_pics(self):
        self.which_encoder()
        # apparently needed to work with pyinstaller.
        freeze_support()

        photonum = 0  # use to create the names.
        photo_list = []  # List of photos.
        photo_name = []  # List of photo names.

        # Make list of source photos.
        # Make list of renamed photos.
        # * List dirs create a list of the dirs found in the given path. In this case that would be the photos and comp folder. (we then use an if to only run code on things that is a photo.)
        for full_image_path in self.source_images:
            if full_image_path.lower().endswith(self.SUFFIXES):
                photo_list.append(full_image_path)
                photo_name.append(
                    self.rename.replace(" ", "-") + f"-{photonum}" + self.prefix
                )
                photonum += 1
                print(
                    f"Photo list {full_image_path}\nPhoto name: {self.rename.replace(' ', '-') + f'-{photonum}' + self.prefix}"
                )
        self.multithreading_service(photo_list=photo_list, photo_name=photo_name)

    def multithreading_service(self, photo_list, photo_name):
        try:
            with ProcessPoolExecutor() as executor:
                print("running the processes now")
                print("Initialize an empty list to hold the futures")
                futures = []
                print(
                    "Iterate through each pair of photo and name from photo_list and photo_name"
                )
                for image_path, renamed_image_name in zip(photo_list, photo_name):
                    print(
                        "Submit a new task to the executor for each pair of photo and name"
                    )
                    future = executor.submit(
                        self.img_compression, image_path, renamed_image_name
                    )
                    print("Append the future object to the list of futures")
                    futures.append(future)
                print("Iterate through the futures as they complete")
                for future in as_completed(futures):
                    print("Print the result of each completed future")
            print("\n")
            self.write_results_file(futures)
        except Exception as e:
            print(f"Error in processpool: {e}")
            traceback.print_exc()
        # Close Photoshop
        print("I should be done now\n")

    def write_results_file(self, futures):
        # printing results of image compression by using the return of the function.
        BRIDGE = Path(tempfile.gettempdir()) / "autopics_results_bridge.txt"
        with BRIDGE.open("w", encoding="utf-8") as file:
            pass
        with BRIDGE.open("a", encoding="utf-8") as file:
            for future in futures:
                _ = file.write(f"{future.result()}\n")
                print(f"{future.result()}")

    def which_encoder(self):
        """Sets the corect encoder based on the value of self.encorder"""
        if "jpeg" == self.encoder:
            self.jxl_chbx_var = 0
            self.avif_chbx_var = 0
            self.png_chbx_var = 0
            self.prefix = ".jpg"
        elif "avif" == self.encoder:
            self.jxl_chbx_var = 0
            self.avif_chbx_var = 1
            self.png_chbx_var = 0
            self.prefix = ".avif"
        elif "PNG" == self.encoder:
            self.jxl_chbx_var = 0
            self.avif_chbx_var = 0
            self.png_chbx_var = 1
            self.prefix = ".png"
        else:
            self.jxl_chbx_var = 1
            self.avif_chbx_var = 0
            self.png_chbx_var = 0
            self.prefix = ".jxl"
