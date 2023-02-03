import configparser

class Config:
    """Configuration items needed to build corpus"""
     
    # for retrieving PMCIDs
    tool = ""
    email = ""
    max_pmcids = ""
    
    # for retrieving PMC index file and documents
    pubmed_ftp_server = ""
    pubmed_ftp_path = ""
    index_file_name = ""
    index_file_local = ""
    corpus_download_dir = ""    # for downloaded corpus files 
    corpus_extract_dir = ""     # for files (e.g. json) extracted from downloaded corpus files
    proxy = ""

    def __init__(self, config_file_path):
        """Read the config from a file"""
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.tool = config["DEFAULT"]["Tool"]
        self.email = config["DEFAULT"]["Email"]
        self.max_pmcids = config["DEFAULT"]["MaxPMCIDs"]
        self.pubmed_ftp_server = config["DEFAULT"]["PubMedFTPServer"]
        self.pubmed_ftp_path = config["DEFAULT"]["PubMedFTPPath"]
        self.index_file_name = config["DEFAULT"]["IndexFileName"]
        self.index_file_local = config["DEFAULT"]["IndexFileLocal"]
        self.corpus_download_dir = config["DEFAULT"]["CorpusDownloadDir"]
        self.accession_id_csvheader, self.file_url_csvheader, self.license_csvheader = self.get_csv_header_name(config["DEFAULT"]["IndexFileCSVHeaders"])
        self.corpus_extract_dir = config["DEFAULT"]["CorpusExtractDir"]
        self.proxy = config["DEFAULT"]["Proxy"]
        self.spacy_model = config["DEFAULT"]["SpacyModel"]

    @staticmethod
    def get_csv_header_name(csv_headers):
        """Parse 3 header names from a single config file entry"""
        csv_headers_list = csv_headers.split(",")
        if len(csv_headers_list) == 3:
            return csv_headers_list[0].strip(), csv_headers_list[1].strip(), csv_headers_list[2].strip()
        if len(csv_headers_list) == 2:
            return csv_headers_list[0].strip(), csv_headers_list[1].strip()
        if len(csv_headers_list) == 1:
            return csv_headers_list[0].strip()


