# PyreMark

PYthon REsume for Markdown  : Customizable CV based on a template

# Introduction
Do you have multiple job profiles you need to switch between? Do you have experiences that better suit each profile that need to be highlighted differently? Do you need to have the same CV in multiple languages?

PyreMark is a python backend that support CV creation via a pipeline of YAML -> Jinja2 -> HTML/CSS -> Chromium -> pdf. 

# Uses
The end goal is to have plugins for most markdown apps where a note corresponding to a job listing can come with it's corresponding CV and/or Cover letter. This way a record of correspondance between job applications and CVs/Cover Letters is kept from the input elements used to produce the documents.

YAML can be written and maintained with your favorite note-taking program 

# What this project isn't
A universal CV design creator. This has no need to go down the canvas / drag n' drop / create your own design path. This could be a different project using this one.

That means that the user needs to be able to write some html and css to create their design. In my eyes, this makes sense: A cv is something quite personal and a cookie-cutter manner of going about it shouldn't cut it for most people given the plethora of tools out there making custom design accessible.

# Future features
- Obsidian plugin