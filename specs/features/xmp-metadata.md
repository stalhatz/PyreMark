---
size: medium
---

Add metadata to pdfs

**Goal**: Link to PyreMark version for better support, link to data repo version for better traceability, add tags to the document to help automated systems categorize it 

- hash or build version 
- Use XMP metadata
    - XMP is an industry-standard, XML-based format for storing metadata, created by Adobe and standardized as ISO 16684. In a PDF, this data is embedded as a separate XML document, allowing it to be understood across many different applications and platforms.
        - **`xmpMM:VersionID`** : Concerning the version of the document (maybe the data repo version/hash)
            - **`stVer:VersionID`**: The specific version number (e.g., "1.0").
            - **`stVer:ModifyDate`**: The date and time the version was saved.
            - **`stVer:Modifier`**: The name of the person who made the changes.
            - **`stVer:Comments`**: A text description of what changed in this version
            - **`stEvt:softwareAgent`** PyreMark
            - **`stVer:VersionID`** : Here we could put the version/hash of PyreMark that created it



# Technical
We could use [pypdf](https://pypdf.readthedocs.io/en/stable/user/metadata.html) 