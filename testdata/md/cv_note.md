---
title: CV Application for ACME Corp
author: Alex
pyremark:
  extends: /home/stalhatz/Dev/PyreMark/testdata/cv/single_page.toml
  config:
    lang: fr
    output: CV_ACME.pdf
    layout:
      sections: [details, experience, qrcode]
  data:
    sender:
      name: Alex
---

This body text is ignored because the document type is CV.
