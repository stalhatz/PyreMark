import pytest
import sys
from pathlib import Path

from copy import deepcopy

test_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(test_dir.parent / "src"))

from build import yearInDateString

def test_yearInDateString_one_date():
    assert yearInDateString("Hello_World_2030") == "2030"
def test_yearInDateString_two_dates():
    assert yearInDateString("Hello_2033World_2031") == "2033"
def test_yearInDateString_consecutive_numbers():
    assert yearInDateString("Hello_2032031") == "2032"
def test_yearInDateString_no_numbers():
    assert yearInDateString("Hello_World") is None

from build import findDateField
def test_findDateField_single_level():
    inputDate = ("a",{"date":"2023"})
    assert findDateField(inputDate) == 2023
def test_findDateField_double_level():
    inputDate = ("a",{"date": {"fr":"aout 2023","en":"august 2023"}})
    assert findDateField(inputDate) == 2023
def test_findDateField_not_a_tuple():
    inputDate = "hello"
    with pytest.raises(TypeError):
        findDateField(inputDate)

from build import sortDict
def test_sortLines_int():
    inputData = {"a": 1, "v":45 , "c":2}
    # Ascending
    assert sortDict(inputData,True,lambda x:x[1]) == {"a": 1, "c":2 ,"v":45}
    # Descending
    assert sortDict(inputData,False,lambda x:x[1]) == {"v":45, "c":2, "a": 1}


def dict_to_list_of_lists(d):
    if isinstance(d, dict):
        return [[k, dict_to_list_of_lists(v)] for k, v in d.items()]
    elif isinstance(d, (list, tuple)):
        return [dict_to_list_of_lists(item) for item in d]
    else:
        return d

def compareDicts(a,b):

    lla = dict_to_list_of_lists(a)
    llb = dict_to_list_of_lists(b)
    print("\n")
    print(lla)
    print(llb)
    return lla == llb

from build import sortData
def test_sortData():
    d2010 = {"py" : {"date":"2010" , "test":"python"}}
    d2005 = {"by":{"date":"2005" , "best":"bython"}}
    d2007 = {"cy":{"date":"2007" , "cest":"cython"}}


    inputData = {"a": {"b" : {"lines" : d2010 | d2005 | d2007 } } }
    # Ascending
    cloneData = deepcopy(inputData)
    expectedResult = {"a": {"b" : {"lines" : d2010 | d2007 | d2005  } } }
    sortData(cloneData,dsc = True) 
    assert compareDicts(cloneData,expectedResult)
    
    # Descending
    cloneData = deepcopy(inputData)
    expectedResult = {"a": {"b" : {"lines" : d2005 | d2007 | d2010  } } }
    sortData(cloneData,dsc = False) 
    assert compareDicts(cloneData,expectedResult)
