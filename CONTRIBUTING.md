# File structure

|   File Type | Role                |
| ----------- | ------------------- |
| `.toml`     | Build Configuration |
| `.yaml`     | Data                |
| `.html.j2`  | Html Template       |
| `.css.j2`   | CSS Template        |

| Folder      | Role                                                       |
| ----------- | ---------------------------------------------------------- |
| `/css`      | Holds compiled css files                                   |
| `/html`     | Holds compiled html files                                  |
| `/img`      | Static assets                                              |
| `/j2`       | Jinja2 templates (both css, html and js)                   |
| `/js`       | Holds compiled js files                                    |
| `/pdf`      | Holds rendered pdf files                                   |
| `/specs`    | Contains specs for future features, bugfixes and refactors |
| `/src`      | Contains python code                                       |
| `/tests`    | Contains tests                                             |
| `/userdata` | Contains user data (`.yaml` + `.toml` files )              |


# Architecture

- Build configuration declares data files to be included in the current build
    - Build configuration can overwrite data variables: This way we are surfacing the most impactful parts of data to the topmost file so with some appropriate commentary we can quickly show the decisions made in this particular configuration
- Data declares templates to render it
- Html templates can be reused by multiple data elements
- Extra CSS templates are specified in the `.toml` file (not in the `.yaml` files) (cf. TODO)
- Two types of documents are supported : CVs and Cover Letters
    - Most code and architecture (and most of this document) applies to CVs


# Mechanism
- build.py gets the template list and feeds it to the root template corresponding to each document type. 
- the root template traverses a list of sections (corresponding to the names of the data objects) and instantiates the templates each object specifies
    - This happens in a recursive manner as templates can instantate other templates

# CV-document specifics
- Single column cv supported
- Each `html.j2` template is a section (or subsection) of the cv
    - `resume.j2.html` is the root template for cv documents

# TODO
## Necessary for functionality / maintainability / ease of use
- [JSON Schema for data](./specs/features/JSON-schema.md) or [Pydantic classes](./specs/features/pydantic-classes.md)
- [Theming](./specs/refactorings/modular-css.md)
- [xmp-metadata](./specs/features/xmp-metadata.md)

## Long-term / Possible routes of eveolution
- [MCP-server](./specs/features/MCP-server.md)
- [webapp](./specs/features/webapp.md)
