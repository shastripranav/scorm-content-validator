"""Parse imsmanifest.xml into structured ManifestData.

Handles both SCORM 1.2 and 2004 namespace variations. The parser auto-detects
the version from the root element namespace and schemaversion value.
"""

from lxml import etree

from scorm_validator.models import (
    NAMESPACES,
    NS_TO_VERSION,
    SCHEMA_VERSION_MAP,
    FileRef,
    Item,
    ManifestData,
    Organization,
    Resource,
)


class ManifestParseError(Exception):
    pass


def parse_manifest(xml_bytes: bytes) -> ManifestData:
    """Parse raw XML bytes from imsmanifest.xml into a ManifestData model."""
    # strip BOM if present — common in packages exported from Windows tools
    if xml_bytes.startswith(b"\xef\xbb\xbf"):
        xml_bytes = xml_bytes[3:]

    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise ManifestParseError(f"Malformed XML: {exc}") from exc

    ns_prefix, ns_uri = _detect_namespace(root)
    if ns_prefix is None:
        raise ManifestParseError("Root element is not a recognized SCORM manifest")

    ns = {
        "cp": ns_uri,
        "adlcp": NAMESPACES[f"adlcp{ns_prefix}"],
    }

    manifest = ManifestData(
        identifier=root.get("identifier"),
    )

    _parse_metadata(root, ns, manifest)
    _parse_organizations(root, ns, manifest)
    _parse_resources(root, ns, ns_prefix, manifest)

    # derive title from the default org if we haven't set it yet
    if not manifest.title and manifest.organizations:
        default_id = manifest.default_org
        for org in manifest.organizations:
            if org.identifier == default_id:
                manifest.title = org.title
                break
        if not manifest.title:
            manifest.title = manifest.organizations[0].title

    return manifest


def _detect_namespace(root: etree._Element) -> tuple[str | None, str | None]:
    """Figure out if this is a 1.2 or 2004 manifest from the root namespace."""
    tag = root.tag
    if not tag.startswith("{"):
        return None, None

    ns_uri = tag.split("}")[0][1:]
    version_family = NS_TO_VERSION.get(ns_uri)
    if version_family == "1.2":
        return "12", ns_uri
    elif version_family == "2004":
        return "2004", ns_uri
    return None, None


def _parse_metadata(root: etree._Element, ns: dict, manifest: ManifestData):
    meta = root.find("cp:metadata", ns)
    if meta is None:
        return

    version_el = meta.find("cp:schemaversion", ns)

    if version_el is not None and version_el.text:
        raw = version_el.text.strip()
        manifest.version = SCHEMA_VERSION_MAP.get(raw)
        # fallback: try case-insensitive match
        if manifest.version is None:
            manifest.version = SCHEMA_VERSION_MAP.get(raw.lower())

    desc_el = meta.find("cp:description", ns)
    if desc_el is not None and desc_el.text:
        manifest.description = desc_el.text.strip()


def _parse_organizations(root: etree._Element, ns: dict, manifest: ManifestData):
    orgs_el = root.find("cp:organizations", ns)
    if orgs_el is None:
        return

    manifest.default_org = orgs_el.get("default")

    for org_el in orgs_el.findall("cp:organization", ns):
        org_id = org_el.get("identifier", "")
        title_el = org_el.find("cp:title", ns)
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        items = _parse_items(org_el, ns)
        manifest.organizations.append(
            Organization(identifier=org_id, title=title, items=items)
        )


def _parse_items(parent: etree._Element, ns: dict) -> list[Item]:
    items = []
    for item_el in parent.findall("cp:item", ns):
        title_el = item_el.find("cp:title", ns)
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        children = _parse_items(item_el, ns)
        items.append(
            Item(
                identifier=item_el.get("identifier", ""),
                title=title,
                identifierref=item_el.get("identifierref"),
                children=children,
            )
        )
    return items


def _parse_resources(
    root: etree._Element, ns: dict, ns_prefix: str, manifest: ManifestData
):
    res_el = root.find("cp:resources", ns)
    if res_el is None:
        return

    # SCORM 1.2 uses scormtype (lowercase), 2004 uses scormType (camelCase)
    scorm_type_attr = (
        f"{{{NAMESPACES[f'adlcp{ns_prefix}']}}}"
        + ("scormtype" if ns_prefix == "12" else "scormType")
    )

    for resource_el in res_el.findall("cp:resource", ns):
        files = []
        for file_el in resource_el.findall("cp:file", ns):
            href = file_el.get("href")
            if href:
                files.append(FileRef(href=href))

        manifest.resources.append(
            Resource(
                identifier=resource_el.get("identifier", ""),
                type=resource_el.get("type", ""),
                href=resource_el.get("href"),
                scorm_type=resource_el.get(scorm_type_attr),
                files=files,
            )
        )
