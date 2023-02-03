import tarfile
import json
import os
import uuid
import logging
from bs4 import BeautifulSoup as bs4

def has_nxml_file(files):
    """Returns true if the given file list contains an .nxml file"""
    for file in files:
        if ".nxml" in file:
            return True
    return False

def create_dir(path):
    """If directory does not exist, create it"""
    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except Exception as e:
        logging.exception("Error creating directory " + path)
        exit(0)

def extract_tar_file(output_path, tar_input_file):
    """Unpack the PMC tar.gz archive and delete the file"""
    if os.path.exists(tar_input_file):
        if tarfile.is_tarfile(tar_input_file):
            try:
                file = tarfile.open(tar_input_file, "r:gz")
                file.extractall(output_path)
                file.close()
            except Exception as e:
                logging.exception("Error during unpacking the archive")
            # delete the archive file
            os.remove(tar_input_file)

def write_json(path, file_name, output_json):
    """Write generated JSON, given path, file_name and JSON blob """   
    json_file_path = path + "/" + file_name + ".json"
    with open(json_file_path, 'w') as file:
        file.write(json.dumps(output_json))

def get_file_name_from_path(file):
    """Return file name from path, given path"""
    return file[file.rfind("/") + 1:]

def remove_comma(sentence):
    """Strips and remove ',' at the end"""
    sentence = sentence.strip()
    if sentence != '':
        if sentence[len(sentence)-1] == ",":
            sentence = sentence[:len(sentence)-1]
    return sentence

def rreplace(s, old, new, occurrence):
    """Replaces old string with new string given the number of occurrence, starting from end of the given string"""
    li = s.rsplit(old, occurrence)
    return new.join(li)

def clean_text(text):
    """Strips extra space and removes period"""
    text_strip = text.replace(".", "").strip()
    return text_strip

def get_text_from_tag(tag_element):
    """Return text from HTML tag, given HTML tagged text"""
    if tag_element is not None:
        return tag_element.text
    else:
        return ""

def append_dict(dict_1, dict_2):
    dict_1.update(dict_2)
    return dict_1

def replace_slashes(paths):
    """Replace backslashes with forward slashes, in a path or list of paths"""
    if type(paths) is list:
        corrected_path_list = []
        for path in paths:
            corrected_path_list.append(path.replace("\\", "/"))
        return corrected_path_list
    if type(paths) is str:
        return paths.replace("\\", "/")

def check_empty_tag(tag):
    """If tag is empty, return empty string"""
    if tag is None or tag == "":
        return ""
    return str(tag)

def replace_encodings(string):
    """Return string with some encodings replaced"""
    return string.replace("&#x000a0;", " ").replace("&#x02212;", "-")

def get_file_paths(file_extension_list, path):
    """Return list of files in a directory, given list of file extensions and path to directory"""
    result = []
    for extension in file_extension_list:
        for root, dirs, files in os.walk(path):
            for file in files:
                if extension in file:
                    result.append(os.path.join(root, file))
    return result

def gen_dict_extract(var, key):
    """Return a list of values from a dictionary, given a key"""
    if isinstance(var, dict):
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, (dict, list)):
                yield from gen_dict_extract(v, key)
    elif isinstance(var, list):
        for d in var:
            yield from gen_dict_extract(d, key)