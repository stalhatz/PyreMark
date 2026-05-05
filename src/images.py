import logging
import os
import hashlib
import qrcode
import shutil

from src.data import tr

logger = logging.getLogger(__name__)


def generate_qr_code(url: str, output_path: str) -> None:
    """Generate a QR code PNG image for a URL.

    url: URL the QR code will encode.
    output_path: path for the generated PNG file.

    Raises:
        AttributeError: if url is None.

    Side-effects: writes a PNG file to output_path.
    """
    if url is None:
        raise AttributeError("url is required")
    qr = qrcode.QRCode(
        version=3,
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # pyright: ignore[reportAttributeAccessIssue]
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)  # pyright: ignore[reportArgumentType]
    logger.debug(f"Generated QR code for {url} at {output_path}")


def createQRCode(data: dict, lang: str, img_dir: str) -> None:
    """Generate QR code images for sections with template "qr-code.html.j2".

    data: the full data dictionary (mutated in-place).
    lang: language code for resolving multilingual link fields.
    img_dir: directory path to write QR code images into.

    Side-effects: writes PNG files to img_dir, mutates data by setting section["qr_image"].
    """
    # Access the nested data dict where sections are stored
    sections_data = data.get("data", {})
    for section_name in data.get("sections", []):
        section = sections_data.get(section_name)
        if isinstance(section, dict) and section.get("template") == "qr-code.html.j2":
            linkSection = section.get("link")
            link = tr(linkSection, lang)
            if link:
                url_hash = hashlib.sha256(link.encode()).hexdigest()[:16]
                filename = f"qr_{url_hash}.png"
                output_path = os.path.join(img_dir, filename)
                generate_qr_code(link, output_path)
                # Relative path from html output to img directory
                section["qr_image"] = f"../img/{filename}"
                logger.info(f"Generated QR code for section '{section_name}': {filename}")
            else:
                logger.warning(f"QR section '{section_name}' missing 'link', skipping QR generation.")


_IMAGE_FIELDS = [
    (("data", "details"), "photo"),
    (("sender",), "signaturePhoto"),
]


def resolve_user_images(data: dict, data_root: str, img_dir: str) -> None:
    """Resolve user image paths against data_root, copy to build output, rewrite paths.

    data: the full data dictionary (mutated in-place).
    data_root: base directory for resolving relative image paths.
    img_dir: directory to copy resolved images into.

    Side-effects: copies image files to img_dir, mutates data by rewriting paths.
    """
    for dict_path, field in _IMAGE_FIELDS:
        d = data
        for key in dict_path:
            if isinstance(d, dict):
                d = d.get(key, {})
            else:
                d = {}
        if not isinstance(d, dict):
            continue
        value = d.get(field)
        if not value or not isinstance(value, str):
            continue
        if value.startswith("http://") or value.startswith("https://"):
            continue
        if os.path.isabs(value):
            continue

        resolved = os.path.join(data_root, value)
        resolved = os.path.abspath(resolved)
        dotpath = '.'.join(dict_path)
        if not os.path.exists(resolved):
            logger.warning(f"Image '{dotpath}.{field}': file '{resolved}' not found — keeping original path")
            continue
        if not os.path.isfile(resolved):
            logger.warning(f"Image '{dotpath}.{field}': path '{resolved}' is a directory — skipping")
            continue

        basename = os.path.basename(resolved)
        dest = os.path.join(img_dir, basename)
        shutil.copy2(resolved, dest)
        d[field] = f"../img/{basename}"
        logger.info(f"Resolved image '{dotpath}.{field}': {value!r} → {d[field]!r}")
