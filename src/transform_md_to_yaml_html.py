import sys
import markdown2 as md
from markdown2 import Markdown
import os 
import yaml
import logging

logger = logging.getLogger(__name__)


def tranformMD(args):
    logger.debug(os.getcwd())
    outputLines = []
    with ( open(args[1] , "r" )) as input:
        # Get Metadata
        html = md.markdown(input.read() , extras = ["metadata"])
        metadata = html.metadata
        metadata = yaml.dump(metadata,default_flow_style=False,explicit_start=False,indent = 4, allow_unicode=True , width=float("inf"))
        outputLines = metadata.split("\n")
        logger.debug(outputLines)

    htmlLines = []
    with ( open(args[1] , "r" )) as input:
        ## Find the second line with a "---" string. 
        ## (Not the actual rule, but good enough for the time being)
        lines = input.readlines()
        numYamlString = 0
        for i,line in enumerate(lines):
            if line.find("---") != -1:
                numYamlString += 1
                if numYamlString == 2:
                    numYamlString = i
                    break
        logger.debug(numYamlString)
        lines = lines[numYamlString+1:]
        lines = [line for line in lines if line != "\n"]
        for line in lines:
            if line != "":
                outputLine = md.markdown(line)
                outputLine = outputLine.partition("<p>")[2]
                outputLine = outputLine.rpartition("</p>")[0]
                htmlLines.append(outputLine)
        logger.debug(htmlLines[0])
        dictObject = {"text":htmlLines}
        yamldump = yaml.dump(dictObject,default_flow_style=False,explicit_start=False,indent = 4,allow_unicode=True , width=float("inf"))
        outputLines = outputLines + yamldump.split("\n")
    logger.debug(len(outputLines))
    outputLines = [line + "\n" for line in outputLines]
    with ( open(args[2] , "w")) as output:
        output.writelines(outputLines)

if __name__ == "__main__":
    tranformMD(sys.argv)