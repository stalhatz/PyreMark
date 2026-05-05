import logging
import subprocess

from jinja2 import Environment, TemplateNotFound

from src.theme import ThemeLoader

logger = logging.getLogger(__name__)


def renderTemplateAndWriteToFile(template_filename: str | None, data: dict, output_filename: str, search_paths: list[str] | None = None) -> None:
    """Render a Jinja2 template with data and write the result to a file.

    template_filename: name of the template to render (may use path components).
    data: dictionary to use for template variable substitution.
    output_filename: path for the rendered output file.
    search_paths: ordered list of directories to search for templates (defaults to ["."]).

    Raises:
        ValueError: if template_filename is None.
        TemplateNotFound: if the template cannot be found in any search path.

    Side-effects: writes rendered template to output_filename.
    """
    if template_filename is None:
        raise ValueError("template_filename is required")
    if template_filename == "":
        raise TemplateNotFound("")
    if search_paths is None:
        search_paths = ["."]
    logger.debug(f"Using template file : {template_filename}")
    loader = ThemeLoader(search_paths)
    env = Environment(loader=loader)
    template = env.get_template(template_filename)
    logger.debug(f"Merging template with data : {data}")
    rendered = template.render(data)
    with open(output_filename, "w") as hf:
        logger.info(f"Writing rendered template to {output_filename}")
        hf.write(rendered)


def showHTML(htmlFile: str) -> None:
    """Open an HTML file in an external browser (Firefox).

    htmlFile: path to the HTML file to display.

    Side-effects: launches a Firefox browser process.
    """
    htmlViewerArgs = []
    htmlViewerArgs += ["firefox"]
    htmlViewerArgs += ["--private-window"]
    htmlViewerArgs += [htmlFile]
    logger.info(" ".join(htmlViewerArgs))
    result = subprocess.run(htmlViewerArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.debug(result.stdout)
    logger.debug(result.stderr)


def viewPDF(pdfFile: str) -> None:
    """Open a PDF file in an external viewer (Okular).

    pdfFile: path to the PDF file to display.

    Side-effects: launches an Okular viewer process.
    """
    pdfViewerArgs = []
    pdfViewerArgs += ["okular"]
    pdfViewerArgs += ["--unique"]
    pdfViewerArgs += [pdfFile]
    logger.info(" ".join(pdfViewerArgs))
    result = subprocess.run(pdfViewerArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.debug(result.stdout)
    logger.debug(result.stderr)


import asyncio
from playwright.async_api import async_playwright


async def html_to_pdf_chromium(html_path: str, output_path: str) -> None:
    """Convert an HTML file to PDF using headless Chromium via Playwright.

    html_path: path to the input HTML file.
    output_path: path for the generated PDF file.

    Side-effects: launches a headless Chromium browser, writes a PDF to output_path.
    """

    async with async_playwright() as p:
        # Launch Chromium (default)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Load local HTML file
        await page.goto(f'file://{html_path}', wait_until='networkidle')
        
        # Generate PDF with no margins
        await page.pdf(
            path=output_path,
            format='A4',
            margin={
                'top': '0mm',
                'right': '0mm',
                'bottom': '0mm',
                'left': '0mm'
            },
            print_background=True  # Include background colors/images
        )
        
        await browser.close()
