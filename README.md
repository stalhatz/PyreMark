# Web CV tool

Let's quickly go over the project folders

## `./css`
Here we store the `.css` files for the different `.j2` templates

## `./html`

This is were the `.html` output is stored. This is either temporary in order to create the `.pdf` file or it could be the end result and alongside the stylesheet it could be incorporated in a page.

## `./img`

Different image assets used. Icons and profile pictures.

## `./j2`

The jinja2 template file used to customize html

## `./pdf`

This is were the `.pdf` output files are stored.

## `./src`

This is were scripts are kept.

## `./yaml`

The `.yaml` files hold the data to customize the jinja templates. `.yaml` files can be composed via the `./src/merge_yaml.py` script.