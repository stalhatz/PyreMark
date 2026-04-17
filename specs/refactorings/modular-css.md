# Turn the current styling system into a modular theme-based css architecture

- Easy extensibility
    - Either to create a new theme from scratch
    - Either to extend an existing theme without altering the file defining it
- Modularity
    - **Theming layer** (colors, typography, standard html classes)
    - **Widget architecture** using theming layer variables defining standard typography (and web that can be used in typography) elements like cards, pills and pill containers, photo frames etc.
    - **Templates** should use directly widget classes (or customize them into a new class) and thus keep template styles css interventions to a minimum level
        - Ideally template styles should not be overridden for the case of a new theme, it's the widgets that should be overridden
        - Data (`.yaml`) files should continue to include css files + template
- Maintain current ability to modify some key global variables via jinja2 templating
    - This is needed as quickly repameterizing and reproducing a CV file is crucial for cases that doesn't respect some conditions (text length most importantly). We are dealing big variability in input data and should thus make available at the heighest possible level some parameters that could help users get a presentable result (that doesn't mean that we shouldn't remind them design assumptions)

So, trying to create a new CV presentation (and to this end defining a new theme) the elements in terms of stability should be (from most stable to less stable):
1. Template html
2. Template css
3. Widget css
4. Theming css

- A theme should be able to define its own template html if needed. This should be discouraged but if that is needed, the inclusion of a named html template inside the theme directory should replace the standard html template. For example if inside `themes/unicorn` there is a file `knowledge.html.j2` than this file should be used rather than the one the project defines by default for this template.
    - For example if we were to create a two column design, it would be difficult to use html code that assumes all elements go under the same root `<div>` element. We would need to introduce one div for the smaller column and another for the main column
