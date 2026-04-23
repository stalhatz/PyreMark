---
size: small
---

Add a qr code template.

**Goal**: provide a way for someone that receives a CV in physical (printed out) form to access the digitalised format

Data (Yaml) related to this template should be: 
- a link 
    - to the site that hosts (or probably will host) the pdf file
    - `tr()` and corresponding yaml fields convention for i18n versions
- (optional) a header text to put over the qr code. 
    - `tr()` and corresponding yaml fields convention to be translated in supported languages
- Layout / appearance option
    - Either "page" or "section"

The layout/appearance that the template renders should be either:
- "section"
    - Opportunistically take up as much space as possible within the page it is placed in (flex layout)
- "page"
    - The template is rendered in a separated page. This page is inserted at the place of the document it is inserted per the existing template ordering mechanism
        - The intended use is to be placed at the back of the CV but nothing should stop the user from putting it at the fronto r in the middle


All this must be controlled by parameterizing the yaml corresponding to the qr-code. 

As it is convention it should be better to parameterize such an impactful variable directly from a .toml configuration file.

# Technical 
- Read [CONTRIBUTING.md](../../CONTRIBUTING.md) if you haven't already
- The `qrcode` python package should be well suited for this job
- QR codes are created at build time using python and stored as images in the `/img` directory
- QR codes are inserted via specifying the corresponding image names in the yaml section and inserting it into the code via the jinja2 template
- The QR-code template tries to encapsulate implementation details as much as possible. Avoid significantly modifying the root template (resume.html.j2) and its css classes  as that would have larger effects on the other sections. 
    - If that is not possible make explicit the changes that need to happen: This could generalize and lead to a separate commit

# Configuration Example

To use the QR code feature, create a YAML file (e.g., `userdata/yaml/qr_code.yaml`) with the following structure:

```yaml
data:
  qrcode:
    title:
      fr: Version Numérique
      en: Digital Version
      gr: Ψηφιακή Έκδοση
    link: "https://example.com/your-cv.pdf"
    header:
      fr: Scannez pour consulter la version en ligne
      en: Scan to view the online version
      gr: Σαρώστε για να δείτε την online έκδοση
    layout: "page"   # or "section"
    template: "qr-code.html.j2"
```

Then, in your TOML configuration (e.g., `userdata/cv/your_cv.toml`):

- Add the YAML file to the `yaml` list:
  ```toml
  yaml = [
    # ... other yaml files ...,
    './userdata/yaml/qr_code.yaml',
  ]
  ```

- Add the section name `'qrcode'` to the `layout.sections` array at the desired position:
  ```toml
  [layout]
  sections = [
    # ... other sections ...,
    'qrcode'
  ]
  ```

- Ensure the CSS template includes any required styles (the default `resume.css.j2` already includes the necessary `.qr-code-section` and `.qr-code-page` styles when using the standard build).

The QR code will be generated automatically at build time and embedded in the output document. For `layout: "page"`, the QR code will occupy a full page; for `layout: "section"`, it will appear inline within the page content.
