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
    - Either "page" or "section" or "container"

The Layoute/appearance that the template renders should be either:
- "section"
    - Opportunistically take up as much space as possible within the page it is placed in (flex layout)
    - It's up to the user to place it, just like any other section
- "page"
    - A separate page at the end of the document that it will consume all by itself
- "container"
    - Placed within a specific container class (let's say `.qr-container`) where it will take the size of the container

All this must be controlled by parameterizing the yaml corresponding to the qr-code. 

As it is convention it should be better to parameterize such an impactful variable directly from the .conf file.

# Technical 
The `qrcode` python package should be well suited for this job