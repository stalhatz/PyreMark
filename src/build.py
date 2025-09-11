

import argparse
from enum import Enum
import logging
import os
from re import compile
import subprocess
import tempfile

import jinja2
from jinja2 import Environment, BaseLoader, TemplateNotFound
import yaml

from transform_md_to_yaml_html import tranformMD
from os.path import join, exists, getmtime
from itertools import batched

class MyLoader(BaseLoader):

    def __init__(self, path):
        self.path = path

    def get_source(self, environment, template):
        path = join(self.path, template)
        if not exists(path):
            raise TemplateNotFound(template)
        mtime = getmtime(path)
        with open(path) as f:
            source = f.read()
        return source, path, lambda: mtime == getmtime(path)

class DocumentType(str, Enum):
    resume = 'resume'
    coverLetter = 'coverLetter'

def showHTML(htmlFile):
    htmlViewerArgs = []
    htmlViewerArgs += ["chromium"]
    htmlViewerArgs += [htmlFile]
    logger.info(" ".join(htmlViewerArgs))
    result = subprocess.run(htmlViewerArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.debug(result.stdout)
    logger.debug(result.stderr)


def viewPDF(pdfFile):
    pdfViewerArgs = []
    pdfViewerArgs += ["okular"]
    pdfViewerArgs += ["--unique"]
    pdfViewerArgs += [pdfFile]
    logger.info(" ".join(pdfViewerArgs))
    result = subprocess.run(pdfViewerArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.debug(result.stdout)
    logger.debug(result.stderr)

def renderPDF(htmlFile, pdfFile):
    pdfRendererArgs = []
    pdfRendererArgs += ["chromium"]
    pdfRendererArgs += ["--enable-logging=stderr"]
    pdfRendererArgs += ["--headless"]
    pdfRendererArgs += ["--disable-gpu"]
    pdfRendererArgs += [f"--print-to-pdf={pdfFile}"]
    pdfRendererArgs += ["--no-pdf-header-footer"]
    pdfRendererArgs += ["--virtual-time-budget=42000"]
    pdfRendererArgs += [htmlFile]
    logger.info(" ".join(pdfRendererArgs))
    result = subprocess.run(pdfRendererArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.debug(result.stdout)
    logger.debug(result.stderr)
    

# Copied from https://stackoverflow.com/a/50441142
def update_merge(d1, d2):
    if isinstance(d1, dict) and isinstance(d2, dict):
        # Unwrap d1 and d2 in new dictionary to keep non-shared keys with **d1, **d2
        # Next unwrap a dict that treats shared keys
        # If two keys have an equal value, we take that value as new value
        # If the values are not equal, we recursively merge them
        return {
            **d1, **d2,
            **{k: d1[k] if d1[k] == d2[k] else update_merge(d1[k], d2[k])
            for k in {*d1} & {*d2}}
        }
    else:
        # This case happens when values are merged
        # It bundle values in a list, making sure
        # to flatten them if they are already lists
        return [
            *(d1 if isinstance(d1, list) else [d1]),
            *(d2 if isinstance(d2, list) else [d2])
        ]

logger = logging.getLogger(__name__)
FORMAT = '[%(funcName)s] : %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

def renderTemplateAndWriteToFile(template, data, filename):
    logger.debug(f"Using template file : {template}")

    with open(template,"r") as tf:
        template = tf.read()

    template = Environment(loader=MyLoader(".")).from_string(template)
    logger.debug(f"Merging template with data : {data}")
    rendered = template.render(data)

    with open(filename,"w") as hf:
        logger.info(f"Writing rendered template to {filename}")
        hf.write(rendered)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-m","--md", help=".md file containing data and metadata for creating the document")
    parser.add_argument("-y","--yaml", help="(a series of) .yaml file(s) containing data for creating the document",nargs='+')
    parser.add_argument("--type",help="The type of document required. This is mutually exclusive with --template and --css.",choices = ["coverletter","CV"])
    parser.add_argument("--layout",help="String with dictionary values to define layout and customize the default template", nargs='+')
    parser.add_argument("--metadata",help="Extra metadata")
    parser.add_argument("--template",help="the html jinja2 template (.j2) to be customized.")
    parser.add_argument("-c","--css",help="the css jinja2 template (.j2) to be customized.")
    parser.add_argument("-l","--lang",help="language to be used for the output document. Defaults to English", default="en")
    parser.add_argument("-o","--output",help="location of the output file. A .pdf suffix will be added if not already present in the filename")
    parser.add_argument("-s","--show",help="Show rendered html pdf or None",default= "None",choices=["pdf","html","None"])

    parser.add_argument("-v","--verbose",help="set to one of warn, info , debug",default="info", choices=["info","warn","debug"])


    args = parser.parse_args()

    # Argument validation
    if args.type is not None:
        if args.template is not None:
            print("--template is mutually exclusive with --type. Exiting")
            exit(1)
        if args.type == "CV":
            args.template = "./j2/resume.html.j2"
            if args.css is None:
                args.css = "./j2/resume.css.j2"
        if args.type == "coverletter":
            args.template = "./j2/cover_letter.html.j2"
            if args.css is None:
                args.css = "./j2/cover_letter.css.j2"

    # Create dictionary out of layout arguments
    layout = None
    if args.layout is not None:
        layout = {}
        for i,j in batched(args.layout,2):
            layout[i] = j

    if (args.verbose == "info"):
        logging.basicConfig(level=logging.INFO)
    if (args.verbose == "debug"):
        logging.basicConfig(level=logging.DEBUG)
    if (args.verbose == "warn"):
        logging.basicConfig(level=logging.WARN)

    yamlFiles = []
    outputName = None
    if (args.md is not None):
        args.type = "coverletter"
        if os.path.splitext(args.md)[1] != ".md":
            raise ValueError("Expected a .md file as input")
        yamlFiles = [tempfile.mkstemp(suffix=".yaml")[1]]
        logger.info(f"Using {yamlFiles[0]} as temporary .yaml file")
        tranformMD(["None",args.md , yamlFiles[0]])
        args.template   = "./j2/cover_letter.html.j2"
        args.css        = "./j2/cover_letter.css.j2"
        outputName = args.md

    if (args.yaml is not None):
        if any( [ os.path.splitext(k)[1]!= ".yaml" for k in args.yaml] ):
            raise ValueError("Expected only .yaml files as input but was given : " + str(args.yaml))
        yamlFiles = args.yaml
        logger.info("Received the following yaml files as input :" + str(yamlFiles))
        if outputName is None: outputName = args.yaml[0]

    lang = args.lang
    assert(lang == "en" or lang == "fr" or lang=="gr")

    if (args.template is None):
        logger.error("No html template provided. Exiting " + DocumentType.resume)
        exit()
    template = args.template

    cssTemplateFile = args.css

    if args.output is not None:
        outputName = args.output

    assert(outputName is not None)

    #Read yaml file
    data = {}
    if layout is not None:
        data["layout"] = layout
    for yamlFile in yamlFiles:
        with open(yamlFile,"r") as yf:
            data = update_merge(data,yaml.load(yf, Loader=yaml.SafeLoader))

    ## Done to get the linter satisfied
    data = dict(data)
    data["lang"] = lang
    htmlFile="./html/tmp.html"

    if cssTemplateFile:
        cssFile="./css/tmp.css"
        renderTemplateAndWriteToFile(cssTemplateFile,data,cssFile)
        ## Get relative css path
        cssFile = os.path.relpath(cssFile,os.path.dirname(htmlFile))
        logger.debug(cssFile)
        data["styles"]["cssfile"] = cssFile


    renderTemplateAndWriteToFile(template,data,htmlFile)

    if args.show == "html":
        showHTML(htmlFile)

    if args.output is not None:
        pdfFile= args.output
        renderPDF(htmlFile,pdfFile)
        if args.show == "pdf":
            viewPDF(pdfFile)
