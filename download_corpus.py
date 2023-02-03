""" Script to download corpus documents from PMC """

import logging

from corpusbuilder.corpus_builder import CorpusBuilder
from corpusbuilder.config import Config
from corpusbuilder.command_line import CommandLineForDownload

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    # get config and search terms from command line
    cmd_line = CommandLineForDownload()
    config = Config(cmd_line.get_config_file())
    search_terms = cmd_line.get_search_terms()
        
    # build the corpus
    builder = CorpusBuilder(config, search_terms)
