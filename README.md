# PyreMark

PYthon REsume for Markdown  : Multi-lingual customizable CV based on yaml templates

# Introduction
Do you have multiple job profiles you need to switch between? Do you have experiences that better suit each profile that need to be highlighted differently? Do you need to have the same CV in multiple languages?

PyreMark is a python backend that support CV creation via a pipeline of Markdown -> YAML -> Jinja2 -> HTML/CSS -> Chromium -> pdf. 

# What is interesting about this
- **Multi-lingualism built-in**
    - If you need to maintain a multilingual resume you need to be able to update/maintain/add sections in a unified fashion. The current system permits for a default value and as many translations as needed.
- **Modularity**
    - It's quite frequent that resume documents have length restrictions (single-page mostly). That leads to always include a subset of one's career is included taking into account what is relevent for the occasion.
- **Markdown integration**
    - Given the above, when we're managing job hunting through a note-taking app a very useful feature is to easily update and maintain the resume sent to each listing by specifying the elements included in the resume at the frontmatter of the Markdown file relating to the listing.

# What this project isn't
A universal CV design creator. This project has no need to go down the canvas / drag n' drop / create-your-own-design path. This could be a different project using this one.

That means that the user needs to be able to write some html and css to create a design that *exactly* fits their needs. In my eyes, this makes sense: A cv is a personal production and a cookie-cutter manner of going about it shouldn't cut it for most people given the plethora of tools out there making custom design accessible. Nonetheless, a set of modular chapter/element designs combined with CSS customization (local elementwise and global) could fit some use cases

# Concerns
A major concern at this moment is the schema of the yaml that describes the resume which is essentially in an ad-hoc state. There exists schemas like (JSON Resume)[https://jsonresume.org/] but it also feels rather ad-hoc-ish while not taking into account translations which was a key motivation for developing PyreMark. That said, extending JSON Resume should be take under consideration.

# Similar projects
1. (Yaml Resume)[https://yamlresume.dev/]
    - Hard to customize appearance (Latex based rendering), not multilingual

# Future features
- Obsidian plugin
- Web app