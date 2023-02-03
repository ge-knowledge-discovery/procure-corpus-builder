""" Script to extract table and image data from downloaded corpus documents """

import logging
import traceback

from corpusbuilder.config import Config
from corpusbuilder.corpus_builder import CorpusBuilder
from corpusbuilder.command_line import CommandLineForExtract
from corpusbuilder.document_index import DocumentIndex
from corpusbuilder.helper import *
import spacy

if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG)
    
    # get items from command line
    cmd_line = CommandLineForExtract()
    config = Config(cmd_line.get_config_file())
    index_file = cmd_line.get_index_file()

    # create corpus extract directory if doesn't exist
    create_dir(config.corpus_extract_dir)

    # instantiate file metadata from index file
    document_index = DocumentIndex(index_file, config)

    # file extensions of interest
    FILE_EXTENSION_NXML = ["nxml"]
    FILE_EXTENSION_IMAGE = ["gif", "jpeg", "jpg", "png", "tif", "tiff", "bmp", "eps"]

    # Initializing spacy
    nlp = spacy.load(config.spacy_model)

    # for each article in the corpus download directory, create json file(s)
    num_processed = 0
    logging.info('Extracting table and image data from documents in ' + config.corpus_download_dir + '...')
    for root, dirs, files in os.walk(config.corpus_download_dir):
        path = root.split(os.sep)
        if has_nxml_file(files):
            pmc_id = os.path.basename(root)
            metadata = document_index.get_metadata(pmc_id)
            
            nxml_files = replace_slashes(get_file_paths(FILE_EXTENSION_NXML, root))
            image_files = replace_slashes(get_file_paths(FILE_EXTENSION_IMAGE, root))

            corpus_extract_subdir = config.corpus_extract_dir + pmc_id
            create_dir(corpus_extract_subdir)

            for nxml_file in nxml_files:
                try:
                    extract_json = CorpusBuilder.populate_template(nlp, pmc_id, nxml_file, metadata['pmc_license'], image_files)
                    write_json(corpus_extract_subdir, pmc_id, extract_json)
                    num_processed += 1
                except Exception as exception:
                    logging.error('Failed to extract JSON from ' + str(pmc_id))
                    traceback.print_exception(type(exception), exception, exception.__traceback__)
    logging.info('Extracted table and image data from ' + str(num_processed) + ' documents')
