import logging
import os
import re
import yaml

from typing import Any
from collections.abc import Callable

logger = logging.getLogger(__name__)


def deep_merge(d1: Any, d2: Any, replace: bool = False) -> Any:
    """Recursively merge two dicts, bundling conflicting leaf values into lists.

    d1: lower-priority dictionary.
    d2: higher-priority dictionary.
    replace: if True, d2 values replace d1 values on conflict instead of bundling into a list.

    Returns: merged dict, or flattened list when both values are non-dicts.
    """
    if isinstance(d1, dict) and isinstance(d2, dict):
        # Unwrap d1 and d2 in new dictionary to keep non-shared keys with **d1, **d2
        # Next unwrap a dict that treats shared keys
        # If two keys have an equal value, we take that value as new value
        # If the values are not equal, we recursively merge them
        return {
            **d1, **d2,
            **{k: d1[k] if d1[k] == d2[k] else deep_merge(d1[k], d2[k],replace)
            for k in {*d1} & {*d2}}
        }
    elif not replace:
        # This case happens when values are merged
        # It bundle values in a list, making sure
        # to flatten them if they are already lists
        return [
            *(d1 if isinstance(d1, list) else [d1]),
            *(d2 if isinstance(d2, list) else [d2])
        ]
    else:
        return d2


def tr(prop: Any, lang: str | None = None, default: Any = None) -> Any:
    '''
    Returns the i18n version of a dictionary property

    returns prop or prop[lang] or prop['def'] or default if no such values exist
    '''
    if isinstance(prop, dict):
        if lang is not None and lang in prop:
            return prop[lang]
        elif "def" in prop:
            return prop["def"]
        else:
            return default
    else:
        if prop is not None:
            return prop
        else:
            return default


def readYamlData(yamlFiles: list[str]) -> dict:
    """Read and merge data from a list of YAML files, left to right.

    yamlFiles: list of paths to .yaml files.

    Returns: merged dictionary from all files.

    Raises:
        ValueError: if any file does not have a .yaml extension.
    """
    if any( [ os.path.splitext(k)[1]!= ".yaml" for k in yamlFiles] ):
        nonYamlValues = filter(lambda x: os.path.splitext(x)[1]!= ".yaml" , yamlFiles)
        raise ValueError("Expected only .yaml files as input but was given : " + str(list(nonYamlValues)))
    logger.info("Received the following yaml files as input :" + str(yamlFiles))
    #Read yaml file
    data = {}
    for yamlFile in yamlFiles:
        with open(yamlFile,"r") as yf:
            data = deep_merge(data,yaml.load(yf, Loader=yaml.SafeLoader))
    return data


def yearInDateString(s: str) -> str | None:
    '''
    return the year value contained in a string

    s: the string to get the year value from
    return : year value or None if no such value in s
    '''
    matches = re.findall(r'\d{4}', s)
    if len(matches) == 0:
        return None
    else:
        return matches[0]


def findDateField(x: Any) -> int | None:
    '''
    Find the date/year corresponding to a record

    x: the record
    returns : corresponding date/year to x, or None if no year found
    '''
    d = x[1]["date"]
    # First element without caring about key should give the date
    if type(d) is dict:
        dateString = list(d.items())[0][1]
    else:
        dateString = d
    year_str = yearInDateString(dateString)
    if year_str is None:
        return None
    return int(year_str)


def sortDict(lines: dict, dsc: bool, key: Callable[[Any], Any]) -> dict:
    """Order a dictionary by applying a key function to its items.

    lines: dictionary to sort.
    dsc: True for descending order, False for ascending.
    key: unary function applied to each (k, v) item — return value is used for comparison.

    Returns: new dictionary with items in sorted order.
    """
    linesList = list(lines.items())
    linesList.sort(key=key,reverse = dsc)
    return dict(linesList)


def sortData(data: Any, dsc: bool = False) -> None:
    """Recursively sort "lines" dicts within data by date, descending or ascending.

    data: nested dict structure (mutated in-place).
    dsc: True for descending order, False for ascending.

    Side-effects: mutates data by reordering "lines" dicts.
    """
    if type(data) is dict:
        for k in data.keys():
            if k == "lines":
                if type(data["lines"]) is dict:
                    try:
                        data["lines"] = sortDict(data["lines"],dsc,findDateField)
                    except (TypeError,KeyError):
                        pass
            else:
                sortData(data[k],dsc)


def load_and_merge_data(
    yaml_files: list[str] | None,
    data_override: dict | None = None,
    body_data: dict | None = None,
    frontmatter_data: dict | None = None,
) -> dict:
    """Read YAML files, sort sections by date, and apply optional data overrides.

    yaml_files: list of YAML file paths (may be None).
    data_override: optional dict from TOML [data] section (priority 3).
    body_data: optional dict from markdown body (priority 4, cover letter only).
    frontmatter_data: optional dict from markdown frontmatter data: (priority 4).

    Returns: the fully merged and sorted data dictionary.

    Merge priority (low → high): YAML files < data_override < body_data < frontmatter_data.
    """
    data = {}
    if yaml_files is not None:
        data = readYamlData(yaml_files)
    sortData(data, True)
    yaml_data = data.get("data", {})
    if data_override is not None:
        yaml_data = deep_merge(yaml_data, data_override, replace=True)
    if body_data is not None:
        yaml_data = deep_merge(yaml_data, body_data, replace=True)
    if frontmatter_data is not None:
        yaml_data = deep_merge(yaml_data, frontmatter_data, replace=True)
    data["data"] = yaml_data
    return data


def prepare_data(data: dict, lang: str) -> dict:
    """Ensure styles/script keys exist in data and set the lang field.

    data: the data dictionary (not mutated — a copy is returned).
    lang: language code to set as data["lang"].

    Returns: new dictionary with styles, script, and lang populated.
    """
    if "styles" not in data:
        data["styles"] = {}
    if "script" not in data:
        data["script"] = {}
    data = dict(data)
    data["lang"] = lang
    return data
