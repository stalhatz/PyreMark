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
| `/js`       | Holds compiled js files                                    |
| `/pdf`      | Holds rendered pdf files                                   |
| `/specs`    | Contains specs for future features, bugfixes and refactors |
| `/src`      | Contains python package                                    |
| `/tests`    | Contains tests                                             |
| `/userdata` | Contains user data (`.yaml` + `.toml` files )              |


# Version Control
- Try to roughly base commit messages on [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
    - Let's try to stick as a rule of thumb to:
        - `fix: `
        - `feat: `
        - `build:`
        - `chore:`
        - `ci:`
        - `docs:`
        - `style:`
        - `refactor:`
        - `perf: `
        - `test:`
        - `spec:`

# Architecture
- Build configuration declares data files to be included in the current build
    - Build configuration can overwrite data variables: This way we are surfacing the most impactful parts of data to the topmost file so with some appropriate commentary we can quickly show the decisions made in this particular configuration
- Data declares templates to render it
- Html templates can be reused by multiple data elements
- Extra CSS templates are specified in the `.toml` file (not in the `.yaml` files) (cf. TODO)
- Two types of documents are supported : CVs and Cover Letters
    - Most code and architecture (and most of this document) applies to CVs


# Docstring style

Functions use compact docstrings with the following section layout:

```python
def my_function(param: str) -> bool:
    """Short description of what the function does.

    param: description of the parameter.

    Returns: description of the return value. (omitted if -> None)

    Raises:
        ValueError: condition that triggers the error. (omitted if none)

    Side-effects: description of side-effects. (omitted if none)
    """
```

- No `Args:` header — parameters are listed directly at line start.
- `Returns:` on its own line, inline (no indent). Omitted entirely for `None`-returning functions.
- `Raises:` each error on an indent line. Omitted if the function raises no documented exceptions.
- `Side-effects:` on its own line, inline. Omitted if the function has no side-effects.
- Each section is separated by a blank line.


# Mechanism
- main.py gets the template list and feeds it to the root template corresponding to each document type. 
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
