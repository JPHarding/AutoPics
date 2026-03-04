import io
from tempfile import NamedTemporaryFile

import pillow_avif
import pillow_jxl
from PIL import Image, ImageChops, ImageEnhance


def trim(im: Image.Image, trim_chbx_value: int) -> Image.Image:
    """This will remove all space around an object that is the same colour as the top left most pixel."""
    if trim_chbx_value == 1:
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        # diff = ImageChops.add(diff, diff, 2.0, -100)
        diff = ImageChops.add(diff, diff)
        bbox = diff.getbbox()
        if bbox:
            print("image trimed bbox")
            return im.crop(bbox)
        else:
            # needed as this func call its self
            local_trim_chbx_value = trim_chbx_value
            # Failed to find the borders, convert to "RGB"
            print("image trimed not bbox")
            return trim(im.convert("RGB"), local_trim_chbx_value)
    else:
        # Do nothing with the im if chbx not checked.
        print("I have not trimed the image")
        return im


def custom_resize(im: Image.Image, custom_resize_value: int) -> Image.Image:
    """This is the user defined resize function."""
    width, height = im.size
    max_dimension = max(width, height)

    ratio = custom_resize_value / max_dimension
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    new_size = (new_width, new_height)
    return im.resize(new_size, Image.Resampling.LANCZOS)


def resize(im: Image.Image, standard_Image_Resize: int) -> Image.Image:
    """this is the standards resize run when user does not enter a custom value by clicking on the checkbox"""
    width, height = im.size
    max_dimension = max(width, height)

    if max_dimension > standard_Image_Resize:
        ratio = standard_Image_Resize / max_dimension
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        new_size = (new_width, new_height)
        return im.resize(new_size, Image.Resampling.LANCZOS)
    else:
        return im  # No resize


def colourEnhancement(im, contrast_chbx_var, standard_Color):
    """enhance image image contrast by a factor of 1.5 1 being a normal photo."""
    if contrast_chbx_var == 1:
        im = im.convert("RGBA")
        contrast_en = ImageEnhance.Color(im)
        im = contrast_en.enhance(factor=standard_Color)
        print(f"Standard Contrast {standard_Color}")
        return im
    return im  # do nothing if the chbx is not ticked.


def sharpnessEnhancement(im, sharpen_chbx_var, standard_Sharpness):
    """Sharpen the photo with a factor of 2.0. checkbox needs to be ticked"""
    if sharpen_chbx_var == 1:
        im = im.convert("RGBA")
        sharp_en = ImageEnhance.Sharpness(im)
        im = sharp_en.enhance(factor=standard_Sharpness)
        print(f"Standard sharpness {standard_Sharpness}")
        return im
    return im  # do nothing if the chbx is not ticked.


def white_bg(im: Image.Image) -> Image.Image:
    """
    If the image has transparency, flatten it onto a white background.
    If it has no transparency, return it unchanged (except mode normalization).
    """

    # Ensure we have alpha to work with
    if im.mode != "RGBA":
        im_rgba = im.convert("RGBA")
    else:
        im_rgba = im

    alpha = im_rgba.getchannel("A")

    # If alpha channel is fully opaque, there's nothing to fix
    alpha_min, alpha_max = alpha.getextrema()
    if alpha_min == 255:
        # "ignored" case: no transparency present
        # If you want to strictly return original untouched, do: return im
        # If you want consistent output type (RGB), do:
        return im.convert("RGB") if im.mode != "RGB" else im

    bg = Image.new("RGB", im_rgba.size, (255, 255, 255))
    bg.paste(im_rgba, (0, 0), mask=alpha)
    return bg
