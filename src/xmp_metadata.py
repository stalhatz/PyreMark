import hashlib
import json
import logging
from datetime import datetime

from pypdf import PdfReader, PdfWriter
from pypdf.generic import StreamObject, NameObject

logger = logging.getLogger(__name__)


def compute_data_hash(data: dict) -> str:
    """Compute a SHA-256 hash of a data dictionary.

    data: dictionary to hash.

    Returns: 64-character hexadecimal hash string.
    """
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def build_xmp_metadata(
    data_hash: str,
    pyremark_version: str,
    pyremark_git: str | None,
    data_git: str | None,
    tags: list[str],
) -> str:
    """Build XMP metadata for a PDF document.

    data_hash: SHA-256 hash of the merged data dictionary.
    pyremark_version: PyreMark version string.
    pyremark_git: git hash of the PyreMark repository, or None.
    data_git: git hash of the data repository, or None.
    tags: list of document tags.

    Returns: XMP metadata as an XMP packet XML string.
    """
    if pyremark_git:
        creator_tool = f"PyreMark {pyremark_version} ({pyremark_git})"
    else:
        creator_tool = f"PyreMark {pyremark_version}"

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    dc_description_xml = ""
    if tags:
        tag_items = "".join(f"<rdf:li>{_xml_escape(tag)}</rdf:li>" for tag in tags)
        dc_description_xml = f"""<rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:subject>
        <rdf:Bag>
          {tag_items}
        </rdf:Bag>
      </dc:subject>
    </rdf:Description>"""

    version_id_xml = ""
    if data_git:
        version_id_xml = f"<xmpMM:VersionID>{_xml_escape(data_git)}</xmpMM:VersionID>"

    xmp_content = f"""<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    {dc_description_xml}
    <rdf:Description rdf:about=""
        xmlns:xmp="http://ns.adobe.com/xap/1.0/">
      <xmp:CreatorTool>{_xml_escape(creator_tool)}</xmp:CreatorTool>
      <xmp:CreateDate>{now}</xmp:CreateDate>
      <xmp:ModifyDate>{now}</xmp:ModifyDate>
      <xmp:MetadataDate>{now}</xmp:MetadataDate>
    </rdf:Description>
    <rdf:Description rdf:about=""
        xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/">
      <xmpMM:DocumentID>{_xml_escape(data_hash)}</xmpMM:DocumentID>
      {version_id_xml}
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>"""

    xpacket_start = '<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
    xpacket_end = '\n<?xpacket end="w"?>'

    return xpacket_start + xmp_content + xpacket_end


def _xml_escape(text: str) -> str:
    """Escape special XML characters.

    text: string to escape.

    Returns: escaped string safe for XML content.
    """
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


def inject_xmp_metadata(pdf_path: str, xmp_xml: str) -> None:
    """Inject XMP metadata into an existing PDF file.

    pdf_path: path to the PDF file to modify.
    xmp_xml: XMP metadata as an XMP packet XML string.

    Side-effects: overwrites the PDF file with XMP metadata added.
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    if reader.metadata is not None:
        writer.add_metadata(reader.metadata)

    stream = StreamObject()
    stream._data = xmp_xml.encode("utf-8")
    stream[NameObject("/Type")] = NameObject("/Metadata")
    stream[NameObject("/Subtype")] = NameObject("/XML")

    writer._add_object(stream)
    writer._root_object[NameObject("/Metadata")] = stream.indirect_reference

    with open(pdf_path, "wb") as f:
        writer.write(f)
