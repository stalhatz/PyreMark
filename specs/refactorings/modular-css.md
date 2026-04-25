# Turn the current styling system into a modular theme-based css architecture

## Content-based modularity
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

In `tokens.css`, define semantic tokens (name for what they do, not for how the look like). We should allow for utility classes to exist but only for specific customization, like for example the specialization of a card element:
```html
<div class="card top-margin-0">
    ...
</div>
```
This means that we allow utility classes but reserve them for special, well defined, need-only occasions to permit modularity and clarity of html code not as a styles structuring technique.

Everytime we build, merge all the `.css` files into a single `.css` (`/css/styles.css`) to include in the html

Reproduce perfectly the current theme within the new system. Just regroup declarations in files and introduce variables for better maintainability.


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

## Theme-based modularity
### Current state
Only way to apply theming is to touch upon the `resume.css.j2` template which mean getting accustomed to all the bells and whistles of the current implementation
### Target state
We want any user/dev that wants to apply theming to be able to cleanly define a file and thus override semantically significant parts of the default implementation (typography, colors) without having to have full knowledge of every part of the theme they are extending.

We need a file organization and inclusion system that permits users to define the files they want to override either 
- to define their own named themes
- to define anonymous ad-hoc overrides
- to override variables from within the configuration file (maximum flexibility)

# Technical
Create three separate plans for this spec, one after the first one has been implemented and commited (plan->implementation->commit->plan->implementation etc.), in the following sequence:
1. Content-based modularity
2. Template-based modularity
3. Theme-based modularity

