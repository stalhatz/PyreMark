

import argparse
from enum import Enum
import logging
import os
from re import template
import subprocess
import tempfile

import jinja2
from jinja2 import Environment, PackageLoader
import yaml

from transform_md_to_yaml_html import tranformMD

class DocumentType(str, Enum):
    resume = 'resume'
    coverLetter = 'coverLetter'

def showHTML(htmlFile):
    htmlViewerArgs = []
    htmlViewerArgs += ["chromium"]
    htmlViewerArgs += [htmlFile]
    print(" ".join(htmlViewerArgs))
    subprocess.run(htmlViewerArgs)


def viewPDF(pdfFile):
    pdfViewerArgs = []
    pdfViewerArgs += ["okular"]
    pdfViewerArgs += ["--unique"]
    pdfViewerArgs += [pdfFile]
    subprocess.run(pdfViewerArgs)

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
    print(" ".join(pdfRendererArgs))
    subprocess.run(pdfRendererArgs)

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


parser = argparse.ArgumentParser()
parser.add_argument("-m","--md", help=".md file containing data and metadata for creating a cover letter and customizing a cv")
parser.add_argument("-y","--yaml", help="(a series of) .yaml file(s) containing data for creating a cover letter or cv",nargs='+')
parser.add_argument("-t","--template",type = DocumentType,help="the type of document to output", choices=[dt.value for dt in DocumentType])
parser.add_argument("-l","--lang",help="language to be used for the output document")
parser.add_argument("-o","--output",help="location of the output file. A .pdf suffix will be added if not already present in the filename")
parser.add_argument("-s","--showHtml",help="If set, shows html in browser",action='store_true')


args = parser.parse_args()

yamlFile = None
outputName = None
if (args.md is not None):
    if os.path.splitext(args.md)[1] != ".md":
        raise ValueError("Expected a .md file as input")
    yamlFiles = [tempfile.mkstemp(suffix=".yaml")[1]]
    logger.info(f"Using {yamlFiles[0]} as temporary .yaml file")
    tranformMD(["None",args.md , yamlFiles[0]])
    args.template = DocumentType.coverLetter
    outputName = args.md

if (args.yaml is not None):
    if any( [ os.path.splitext(k)[1]!= ".yaml" for k in args.yaml] ):
        raise ValueError("Expected only .yaml files as input but was given : " + str(args.yaml))
    yamlFiles = args.yaml
    if outputName is None: outputName = args.yaml[0]

if (args.lang is None):
    logger.info("No output language argument provided. Setting output language to english (EN)")
    lang = "en"
else:
    lang = args.lang

templateFilesDict = {DocumentType.resume:"./j2/resume.html.j2", DocumentType.coverLetter:"./j2/cover_letter.html.j2"}

if (args.template is None):
    logger.info("No output document type provided. Setting template to " + DocumentType.resume)
templateFilename = templateFilesDict[args.template]

assert(outputName is not None)

outputName = os.path.basename(outputName)
print(outputName)

htmlFile="./html/tmp.html"

#Read yaml file
data = {}
for yamlFile in yamlFiles:
    with open(yamlFile,"r") as yf:
        data = update_merge(data,yaml.load(yf, Loader=yaml.SafeLoader))

## Done to get the linter satisfied
data = dict(data)
data["lang"] = lang

with open(templateFilename,"r") as tf:
    template = tf.read()

template = jinja2.Template(template)
html = template.render(data)

with open(htmlFile,"w") as hf:
    hf.write(html)

if args.showHtml:
    showHTML(htmlFile)

if args.output is not None:
    pdfFile="./pdf/test.pdf"
    renderPDF(htmlFile,pdfFile)
    viewPDF(pdfFile)
