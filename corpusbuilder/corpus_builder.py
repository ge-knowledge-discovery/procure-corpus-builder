"""
A module for building a corpus
"""

import logging
import requests
import xml.etree.ElementTree as ET
from corpusbuilder.ftp_download import FTPDownload
from corpusbuilder.document_index import DocumentIndex
from corpusbuilder.helper import *
import geonamescache
import copy

class CorpusBuilder:
    """A class for building a corpus"""

    config = ""
    search_terms = ""
    pmcid_list = []

    def __init__(self, config, search_terms):
        """Constructor"""
        self.config = config
        self.search_terms = search_terms

        # exit if no email address configured
        if self.config.email is None or self.config.email.strip() == "":
            logging.error('Please add an email address to the config file')
            exit()

        self.__build()

    def __build(self):
        """Build the corpus"""

        # retrieve pmcids for the search terms
        self.pmcid_list = self.__retrieve_pmcids()
        logging.info('Retrieved ' + str(len(self.pmcid_list)) + ' PMCIDs: ' + str(self.pmcid_list))

        # instantiate FTPDownload object
        ftp_download = FTPDownload(self.config)

        # retrieve index file
        index_file = ftp_download.get_index_file()

        # instantiate file metadata from index file
        document_index = DocumentIndex(index_file, self.config)

        # for each PMCID, download and extract tar file
        logging.info('Retrieving PMC articles...')
        num_processed = 0
        for pmcid in self.pmcid_list:
            metadata = document_index.get_metadata('PMC' + pmcid)  # gets metadata and also checks license
            if metadata['result'] is True:
                ftp_download.download_ftp_file(self.config.pubmed_ftp_path + metadata['ftp_file_path'],
                                               metadata['file_name'])
                tar_file_path = self.config.corpus_download_dir + metadata['file_name']
                extract_tar_file(self.config.corpus_download_dir, tar_file_path)
                num_processed = num_processed + 1

        logging.info('Retrieved documents for ' + str(num_processed) + ' of ' + str(len(self.pmcid_list)) + ' PMCIDs')

    def __retrieve_pmcids(self):
        """Retrieve list of PMCIDs from PubMed, given search terms"""

        # execute call to PubMedCentral Search API (if behind firewall, may need HTTPS_PROXY environment variable)
        url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=' + self.search_terms + '&tool=' + self.config.tool + "&email=" + self.config.email
        if self.config.max_pmcids is not None:
            url = url + '&retmax=' + str(self.config.max_pmcids)
        r = requests.get(url, allow_redirects=True)

        logging.info(url)

        # write XML to file
        file_name = 'search-results-' + self.search_terms + '.xml'
        open(file_name, 'wb').write(r.content)

        # parse XML to get PMCIDs
        ids = []
        root = ET.parse(file_name).getroot()
        for id in root.findall("./IdList/"):
            ids.append(id.text)
        return ids

    @staticmethod
    def get_article_title(soup):
        """Returns article if available in the soup element"""
        article_title_group = soup.find('title-group')
        if article_title_group is not None:
            article_title = article_title_group.find('article-title')
            if article_title is not None:
                return article_title.text
            else:
                return ""
        else:
            return ""

    @staticmethod
    def get_publisher(soup):
        """Returns publisher dict if available in the soup element"""
        publisher_dict = {"publisher_name": "", "publisher_location": ""}
        journal_meta = soup.find('journal-meta')
        if journal_meta is not None:
            publisher = journal_meta.find('publisher')
            if publisher is not None:
                if publisher.find('publisher-name') is not None:
                    publisher_dict["publisher_name"] = publisher.find('publisher-name').text
                if publisher.find('publisher-loc') is not None:
                    publisher_dict["publisher_location"] = publisher.find('publisher-loc').text
        return publisher_dict

    @staticmethod
    def get_journal(soup):
        """Returns journal dict if available in the soup element"""
        journal_dict = {"journal_name": ""}
        if soup.find('journal-title-group') is not None:
            journal_title_group = soup.find('journal-title-group')
            if journal_title_group is not None:
                journal_title = journal_title_group.find('journal-title')
                if journal_title is not None:
                    journal_dict["journal_name"] = journal_title.text
                    return journal_dict
        return journal_dict

    @staticmethod
    def get_authors(affiliations, soup):
        """Returns authors dict, given affiliations and soup element"""
        article_meta = soup.find('article-meta')
        author_list = list()
        contrib_group = article_meta.find_all('contrib')
        if contrib_group is not None:
            for contrib in contrib_group:
                if contrib.attrs['contrib-type'] == 'author':
                    surname = ""
                    given_names = ""
                    if contrib.find('surname') is not None:
                        surname = contrib.find('surname').text
                    if contrib.find('given-names') is not None:
                        given_names = contrib.find('given-names').text

                    xref_tag = contrib.find_all('xref')
                    affiliation_list = []
                    if len(xref_tag) > 0:
                        for tag in xref_tag:
                            if 'rid' in tag.attrs and 'ref-type' in tag.attrs:
                                if tag.attrs['ref-type'] == 'aff':
                                    aff = tag.attrs['rid']
                                    # Checking if the aff value in the 'rid' tag has multiple values
                                    # if yes, loop through and add each affiliation val
                                    aff_list = aff.split(" ")
                                    for aff_val in aff_list:
                                        affiliation_list.append(affiliations[aff_val.strip()])

                    author_dic = {"surname": surname,
                                  "given_names": given_names,
                                  "affiliations": affiliation_list}

                    author_list.append(author_dic)
        return author_list

    @staticmethod
    def get_date_from_pub_tag(pub_date_list):
        """Returns publication dict from extracted publication element"""
        publication_dict = {}
        for pub_date in pub_date_list:
            if pub_date is not None:
                day = ""
                month = ""
                year = ""
                if pub_date.find('day') is not None:
                    day = int(pub_date.find('day').text)
                if pub_date.find('month') is not None:
                    month = int(pub_date.find('month').text)
                if pub_date.find('year') is not None:
                    year = int(pub_date.find('year').text)
                publication_dict = {"day": day,
                                    "month": month,
                                    "year": year}
        return publication_dict

    @staticmethod
    def get_publication_date(soup):
        """Returns publication dict if available in the soup element"""
        publication_dict = dict()
        pub_date_list = soup.select("pub-date[pub-type^=epub]")
        if pub_date_list is not None and len(pub_date_list) != 0:
            publication_dict = CorpusBuilder.get_date_from_pub_tag(pub_date_list)
        else:
            pub_date_list = soup.select("pub-date[date-type^=pub][publication-format^=electronic]")
            if pub_date_list is not None and len(pub_date_list) != 0:
                publication_dict = CorpusBuilder.get_date_from_pub_tag(pub_date_list)
        return publication_dict

    @staticmethod
    def get_funding_group(soup):
        """Returns funding group if available in the soup element"""
        if soup.find('funding-group') is not None:
            funding_group = soup.find('funding-group')
            if funding_group is not None:
                funding_source = funding_group.find('funding-source')
                if funding_source is not None:
                    return funding_source.text
                else:
                    return ""
            else:
                return ""
        elif soup.find('grant-num') is not None:
            grant_num = soup.find('grant-num')
            if grant_num is not None:
                grant_sponsor = grant_num.find('grant-sponsor')
                if grant_sponsor is not None:
                    return grant_sponsor.text
                else:
                    return ""
            else:
                return ""
        else:
            return ""

    @staticmethod
    def get_figures(soup, image_files):
        """Returns figure dict, given soup element and image_files in the directory"""
        figure_list = []
        figures = soup.find_all('fig')
        for figure in figures:
            caption = ""
            graphic = ""
            label = ""
            files = []
            if figure is not None:
                caption_tag = figure.find('caption')
                if caption_tag is not None:
                    caption = check_empty_tag(caption_tag)
                graphic_tag = figure.find('graphic')
                if graphic_tag is not None:
                    graphic = graphic_tag.attrs['xlink:href']
                    for file in image_files:
                        if graphic in file:
                            files.append(replace_slashes(file))
                label_tag = figure.find('label')
                if label_tag is not None:
                    label = clean_text(label_tag.text)
            figure_dic = {
                'caption': caption,
                'graphic': graphic,
                'id': label,
                'files': files,
                'references': []
            }
            figure_list.append(figure_dic)
        return figure_list

    @staticmethod
    def _separate_location_country(countries, location_country):
        """Returns location and country dict, given list of countries and string containing location and country"""

        """
        if: ","" is there in location_country sentence, then split and get the last element in the string and separate
        >> Nan Er Huan Road (Mid-section), Xi&#x02019;an, 710064 Shaanxi China

        if parsing the get_entity_dic country to render it correctly, separate
        >> Toscana Italy

        """
        temp_dic = {
            "location": "",
            "country": ""
        }

        for country in countries:
            if country in location_country:
                temp_dic["country"] = country
                location = (rreplace(location_country, country, "", 1))
                temp_dic["location"] = location

        return temp_dic

    @staticmethod
    def get_address_line(element):
        """Returns addr-line or city if available in the element"""
        address_tag = element.find("addr-line")
        city_tag = element.find("city")
        if address_tag is not None:
            return address_tag.text
        elif city_tag is not None:
            return city_tag.text
        else:
            return ""

    @staticmethod
    def get_country(element):
        """Returns country if available in the element"""
        country_tag = element.find("country")
        if country_tag is not None:
            return country_tag.text
        else:
            return ""

    @staticmethod
    def get_institution(element):
        """Returns institution if available in the element"""
        institution = ""  # name
        institution_tag = element.find_all('institution')
        if len(institution_tag) > 0:
            for tag in institution_tag:
                institution = institution + tag.text
        return remove_comma(institution.strip())

    @staticmethod
    def decompose_tag(tag, label):
        """removes label (tag) from the string, given string and label"""
        label_list_in_tag = tag.find_all(label)
        if label_list_in_tag is not None or len(label_list_in_tag) != 0:
            for tag_i in label_list_in_tag:
                tag_i.decompose()

    @staticmethod
    def _get_name_location(nlp, sentence):
        """Returns name and location in a dict, given spacy module and affiliation sentence"""
        dic = {"name": "",
               "location": ""
               }
        sentence_tuple = nlp(sentence).ents
        entity = ""
        remaining_sentence = ""
        for i in range(len(sentence_tuple)):
            ent = sentence_tuple[i]
            if ent.label_ == 'ORG':
                entity = ent.text
            else:
                if dic['name'] == "" and entity != "":
                    name = sentence[:sentence.find(entity) + len(entity)]
                    remaining_sentence = sentence[len(name) + 1:].strip()
                    dic['name'] = name.strip()
                    entity = ""
                entity = ent.text
        if dic['name'] != "":
            location = remaining_sentence[:remaining_sentence.find(entity) + len(entity)]
            dic['location'] = location
        else:
            name = sentence[:sentence.find(entity) + len(entity)]
            dic['name'] = name.strip()

        return dic

    @staticmethod
    def get_affiliation(aff, nlp):
        """Returns affiliation in a dict, given affiliation string, spacy module and countries list"""

        # get nested dictionary for countries
        # TODO if make these functions non-static, then create country dictionary only once upon initialization.  Keeping it here for now to facilitate testing of get_affiliation (and it runs in millisecs)
        gc = geonamescache.GeonamesCache()
        countries = gc.get_countries()
        countries = [*gen_dict_extract(countries, 'name')]
        countries.append("USA")
        countries.append("United States of America")
        countries.append("UK")

        aff_dic = {
            "name": "",
            "location": "",
            "country": ""
        }
        if aff.find('institution-wrap') is not None:
            aff_dic["name"] = CorpusBuilder.get_institution(aff)  # name

            temp = copy.copy(aff)

            CorpusBuilder.decompose_tag(temp, 'institution-wrap')
            CorpusBuilder.decompose_tag(temp, 'label')

            location_country = temp.get_text().strip()

            loc_country_dic = CorpusBuilder._separate_location_country(countries, location_country)

            if CorpusBuilder.get_address_line(aff) != "":
                aff_dic["location"] = CorpusBuilder.get_address_line(aff)
            else:
                aff_dic["location"] = remove_comma(loc_country_dic["location"])

            if CorpusBuilder.get_country(aff) != "":
                aff_dic["country"] = CorpusBuilder.get_country(aff)
            else:
                aff_dic["country"] = loc_country_dic["country"]

            return aff_dic
        elif aff.find('institution') is not None:

            aff_dic['name'] = CorpusBuilder.get_institution(aff)

            temp = copy.copy(aff)

            CorpusBuilder.decompose_tag(temp, 'institution')
            CorpusBuilder.decompose_tag(temp, 'label')
            CorpusBuilder.decompose_tag(temp, 'sup')
            CorpusBuilder.decompose_tag(temp, 'named-content')

            location_country = temp.get_text().strip()
            loc_country_dic = CorpusBuilder._separate_location_country(countries, location_country)

            if CorpusBuilder.get_address_line(aff) != "":
                aff_dic["location"] = CorpusBuilder.get_address_line(aff)
            else:
                aff_dic["location"] = remove_comma(loc_country_dic["location"])

            if CorpusBuilder.get_country(aff) != "":
                aff_dic["country"] = CorpusBuilder.get_country(aff)
            else:
                aff_dic["country"] = loc_country_dic["country"]

            return aff_dic
        else:
            temp = copy.copy(aff)
            CorpusBuilder.decompose_tag(temp, 'institution-wrap')
            CorpusBuilder.decompose_tag(temp, 'institution')
            CorpusBuilder.decompose_tag(temp, 'label')
            CorpusBuilder.decompose_tag(temp, 'sup')
            CorpusBuilder.decompose_tag(temp, 'email')
            CorpusBuilder.decompose_tag(temp, 'named-content')

            institution_loc_country = temp.get_text().strip()

            loc_country_dic = CorpusBuilder._separate_location_country(countries, institution_loc_country)
            aff_dic["country"] = loc_country_dic["country"]
            name_location_dic = CorpusBuilder._get_name_location(nlp, loc_country_dic["location"])
            aff_dic["name"] = name_location_dic["name"]
            aff_dic["location"] = name_location_dic["location"]
            return aff_dic

    @staticmethod
    def get_all_affiliations(nlp, soup):
        """Returns all affiliations in a dict, given spacy module, countries list and nxml object"""
        
        aff_tags = soup.find_all("aff")

        affiliations = dict()

        for aff in aff_tags:
            aff_id = aff_tags.index(aff)
            if 'id' in aff.attrs:
                aff_id = aff.attrs['id']
            affiliations[aff_id] = CorpusBuilder.get_affiliation(aff, nlp)

        return affiliations

    @staticmethod
    def populate_template(nlp, pmc_id, nxml_file_path, license, image_files):
        """Returns generated JSON template, given pmc_id, nxml_file_path, license and image files in the directory"""

        template_json = {'pmc_id': pmc_id,
                         'metadata': {"license": license,
                                      "article_title": "",
                                      "provenance": {"source_nxml_file": nxml_file_path,
                                                     "authors": [], "publisher": "", "publication_date": "",
                                                     "funding_group": ""}},
                         "html_tables": [],
                         "image_tables": [],
                         'figures': []}
        xml_data = ''

        with open(nxml_file_path, encoding='utf-8') as xml_file:
            xml_data = xml_file.readlines()

        xml_file.close()

        xml_data_str = ''.join(xml_data)

        # replace specific encoded characters, for example space and dash
        xml_data_str = replace_encodings(xml_data_str)

        soup = bs4(xml_data_str, 'html.parser')

        # Get list of affiliation dic {"name":"", "location":"", "country":""}
        affiliations = CorpusBuilder.get_all_affiliations(nlp, soup)

        # Addition of provenance field meta data
        template_json['metadata']['article_title'] = CorpusBuilder.get_article_title(soup)
        template_json['metadata']['provenance']['authors'] = CorpusBuilder.get_authors(affiliations, soup)
        template_json['metadata']['provenance']['publisher'] = CorpusBuilder.get_publisher(soup)
        template_json['metadata']['provenance']['publication_date'] = CorpusBuilder.get_publication_date(soup)
        template_json['metadata']['provenance']['funding_group'] = CorpusBuilder.get_funding_group(soup)
        template_json['metadata']['provenance']['publisher'] = append_dict(CorpusBuilder.get_journal(soup),
                                                                           CorpusBuilder.get_publisher(soup))

        # Addition of figures
        template_json['figures'] = CorpusBuilder.get_figures(soup, image_files)

        tables = soup.find_all('table-wrap')
        tables_list = []
        image_table_list = []

        for table in tables:
            s = bs4(str(table), 'html.parser')
            table_html = s.find('table')  # table
            table_label = s.find('label')
            table_caption = s.find('caption')
            table_footer = s.find('table-wrap-foot')
            table_image = s.find('graphic')
            if table_html is not None:
                table_dic = {
                    "id": (clean_text(get_text_from_tag(table_label))),
                    "table_html": (check_empty_tag(table_html)),
                    "table_caption": (check_empty_tag(table_caption)),
                    "table_footer": (check_empty_tag(table_footer)),
                    "table_image": (check_empty_tag(table_image)),
                    "references": []
                }
                tables_list.append(table_dic)
            else:
                image_dic = {
                    "id": (clean_text(get_text_from_tag(table_label))),
                    "table_image": (check_empty_tag(table_image)),
                    "table_caption": (check_empty_tag(table_caption)),
                    "table_footer": (check_empty_tag(table_footer)),
                    "references": []
                }
                image_table_list.append(image_dic)

        template_json['html_tables'] = tables_list
        template_json['image_tables'] = image_table_list
        return template_json
