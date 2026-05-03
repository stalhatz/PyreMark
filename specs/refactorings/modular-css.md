# Turn the current styling system into a modular theme-based css architecture

## Content-based modularity (Done)
### Current state:
All declarations and variables are declared in an ad hoc manner between three style files 
- `resume.css.j2`
- `microcredits_cards.css.j2`
- `cover_letter.html.j2`

Hard to maintain, track changes or edit

### Target state:
Break up declarations into files corresponding to components we are using:
- tokens.j2.css 
    - implement all css variables as jinja2 overridable values
        - example: ` --primaryColor : {styles.primaryColor | default(#aabbcc)}`
- primitives.css (html elements : <p>, <h1>...<h5>, etc.)
- Components
    - card.css
    - pillbox.css
    - details.css (concerning the `.details-list` class in `preambule.html.j2`)
    - icon.css
    - photo.css
    - <any other component you can identify>.css

Note: The cover letter CSS (`cover_letter.css.j2`) is deliberately excluded from this phase. 
It will be refactored into a proper named theme as part of Phase 2 (Theme-based modularity), 
since it represents a fundamentally different document layout that benefits from the theme 
override mechanism.

In `tokens.css`, define semantic tokens (name for what they do, not for how the look like). We should allow for utility classes to exist but only for specific customization, like for example the specialization of a card element:
```html
<div class="card top-margin-0">
    ...
</div>
```
This means that we allow utility classes but reserve them for special, well defined, need-only occasions to permit modularity and clarity of html code not as a styles structuring technique.

Everytime we build, merge all the `.css` files into a single `.css` (`/css/styles.css`) to include in the html

Reproduce perfectly the current theme within the new system. Just regroup declarations in files and introduce variables for better maintainability.

## Theme-based modularity (Done)
### Current state
Ways to apply theming:
- Modify `resume.css.j2` template 
    - Get accustomed to all the bells and whistles of the current implementation.
        - Too much friction
- Modify token values via the configuration file (TOML)
    - Limited expressivity

### Target state
- A theme contains:
    - .j2.html templates
    - .css files and .j2.css templates
    - .js files
    - Corollary : A theme can recreate most of the mechanism already existing in the library.
        - In practice we want to give the user depending on their needs to define the amount of customization they want to apply to their document
            1. Create a new theme from scratch
            2. Extend an existing theme by redefining as many files as needed
            3. Define only a subset of theme files without needing to define a theme
            4. Define .css files to be added at the beginning and the end of compiled .css declarations
            5. Redefine style tokens directly from the configuration file

We want any user/dev that wants to apply theming to be able to (let's continue supposing our theme is called `newTheme`):

- Specify a theme path in the configuration file, containing appropriately structured files and folders that will be applied for theming (e.g `/themes/newTheme`)
- Use filename matching to implement an override/redefinition scheme to define, structure and provide the capacity to **define a new theme** via extending an existing one 
    - A valid theme should have a `manifest.md` file in its root dir (`/themes/newTheme`)
        - This file identifies the theme that is being extended (or skip the property if it is not extending any theme) and other properties
            - We should only add properties here that cannot be understood from the file structure of the theme. 
    - Define one or more files and directories insider the roor dir (`/themes/newTheme`), that will automatically override the file with the same name defined in the theme that is being extended
        - Especially for .css files where the cascade exists it should be clear (via commentary and/or cli messages) that files are being replaced and not included together in the final .css
- Use filename matching to implement a override/redefinition scheme to extend themes in an flexible way for end users
    - Define one or more files in a /theme subdirectory inside a data directory, that will automatically override the file with the same name defined in the current (specified) theme
        - Especially for .css files where the cascade exists it should be clear that files are being replaced and not included together in the final .css
    - Arrange that if a `post_styles.css` (a specifically named file) is part of the css that will be included at the end of the `.css`
    - Arrange that if a `pre_styles.css` (a specifically named file) is part of the css that will be included at the beginning of the `.css`
        

In addition to the above mechanisms, we need to reorganize our code to make it adhere to them. Namely:
- Arrange our existing theme into the `/themes` folder

### Concretely
- Create a theme called `default` out of the current CV theme
- Create a theme called `cover_letter` out of the current cover letter theme
- Create a new theme `new_theme_example`
    - Make it implement all templates (=rendering all possible data)
- Create an example theme extending `default` called `ext_default_example` 
    - Make it reimplement a single template and redefine the `photo.css` to give a funky frame to the profile pic an make it colored.
- Add a `theme/` folder in `/testdata` where `preambule.html.j2` is reimplemented to change the order of the `.titlename` elements and also their layout (vertical)
- Define a `pre_styles.css` and a `post_styles.css`  in `/testdata` that will make two specific and visible changes

### Testing
Add tests for all 5 customizaiton options and their logical compositions


## Template-based modularity
### Current state:
Styles is broken into modules but `.css` files to be included are being declared in the configuration file and merged into a single .css
### Target state:
Css to be applied to an `.html` template is declared in data. Since `.css` and `.html` templates can be reused and we want to allow different `.css` implementations to style the same `html` template in the same documents we need some form of **encapsulation** for styles that are defined this way. This form should come in the "automatic" nesting of declaration under a class, which would correspond to the template parent element. So for example if we have the following data for a competencies section:

``` yaml
data:
  competencies:
    title: "competencies"
    template: "competencies.html.j2" 
    css : "colourful.css.j2"
```

and the following template for `competencies.html.j2`

``` html
<div class = "competencies card-container">
    <p> competence 1 </p>
</div>
```
and `colourful.css.j2` contains a single declaration: `p{ color: blue}`, the generated file, let's call it `<unique-class-name>_colourful.css` should automatically contain : `.<unique-class-name> { p {color:blue} }`

in order for the wraping class to be unique we need to 
1. find a unique name for it
2. inject the name as an extra class in the root element of the template declaration
3. use that name to encapsulate the css

The unique name should be a short random alphanum string : ".enc-4d52f"

The recommended and preferable way for this to happen is via jinja2 template compilation and python. Try to limit the syntactic sugar needed (macros) to achieve the intended result as much as possible.

# Spec planning
Create three separate plans for this spec, one after the first one has been implemented and commited (plan->implementation->commit->plan->implementation etc.), in the following sequence:
1. Content-based modularity
2. Theme-based modularity
3. Template-based modularity