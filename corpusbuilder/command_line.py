import argparse
import logging


class CommandLineForDownload:
    """Command line parser for download command"""
        
    def __init__(self):
        parser = argparse.ArgumentParser(description="Description for my parser")

        parser.add_argument("-c", "--config", help="Enter path to config file", required=True, default="")
        parser.add_argument("-s", "--search", help="Enter search term string (e.g. '(covid)+AND+(gel%20electrophoresis)')", required=True, default="")

        self.argument = parser.parse_args()

        if self.argument.config:
            logging.info("Using config file: {0}".format(self.argument.config))
        if self.argument.search:
            logging.info("Using search terms: {0}".format(self.argument.search))

    def get_config_file(self):
        return self.argument.config
    
    def get_search_terms(self):
        return self.argument.search


class CommandLineForExtract:
    """Command line parser for extract command"""
    
    def __init__(self):
        parser = argparse.ArgumentParser(description="Description for my parser")

        parser.add_argument("-c", "--config", help="Enter path to config file", required=True, default="")
        parser.add_argument("-f", "--file",
                            help="Enter path to index file", required=True,
                            default="")

        self.argument = parser.parse_args()

        if self.argument.config:
            logging.info("Using config file: {0}".format(self.argument.config))
        if self.argument.file:
            logging.info("Using index file terms: {0}".format(self.argument.file))

    def get_config_file(self):
        return self.argument.config

    def get_index_file(self):
        return self.argument.file
