""" Test parsing affiliations"""

import spacy
from bs4 import BeautifulSoup

from corpusbuilder.corpus_builder import CorpusBuilder
from corpusbuilder.config import Config


def test_affiliation():
    
    # extract json generated by code
    config = Config("config.ini")
    nlp = spacy.load(config.spacy_model)
    
    # test affiliation containing institution-wrap tag (from PMC8175420)
    aff = BeautifulSoup('<aff id="Aff1"><label>1</label><institution-wrap><institution-id institution-id-type="GRID">grid.47840.3f</institution-id><institution-id institution-id-type="ISNI">0000 0001 2181 7878</institution-id><institution>Division of Environmental Health Sciences, </institution><institution>UC Berkeley, </institution></institution-wrap>Berkeley, CA 94720 USA </aff>', "html.parser")
    aff_dic = CorpusBuilder.get_affiliation(aff, nlp)
    assert aff_dic["name"] == "Division of Environmental Health Sciences, UC Berkeley"
    assert aff_dic["location"] == "Berkeley, CA 94720"
    assert aff_dic["country"] == "USA"
    
    # test affiliation containing institution-wrap tag (from PMC8175420)
    aff = BeautifulSoup('<aff id="Aff3"><label>3</label><institution-wrap><institution-id institution-id-type="GRID">grid.16463.36</institution-id><institution-id institution-id-type="ISNI">0000 0001 0723 4123</institution-id><institution>School of Mathematical Sciences, </institution><institution>University of Kwazulu-Natal, </institution></institution-wrap>Durban, 4000 South Africa </aff>', "html.parser")
    aff_dic = CorpusBuilder.get_affiliation(aff, nlp)
    assert aff_dic["name"] == "School of Mathematical Sciences, University of Kwazulu-Natal"
    assert aff_dic["location"] == "Durban, 4000"
    assert aff_dic["country"] == "South Africa"
    
    # test affiliation containing institution tag (from PMC8219862)
    aff = BeautifulSoup('<aff id="aff4"><sup>4</sup><institution>Bizkaisida</institution>, <addr-line>Bilbao</addr-line>, <country>Spain</country></aff>', "html.parser")
    aff_dic = CorpusBuilder.get_affiliation(aff, nlp)
    assert aff_dic["name"] == "Bizkaisida"
    assert aff_dic["location"] == "Bilbao"
    assert aff_dic["country"] == "Spain"
    
    # test affiliation
    aff = BeautifulSoup('<aff id="aff003"><label>3</label><addr-line>Commonwealth Trade Partners Inc., Alexandria, VA, United States of America</addr-line></aff>', "html.parser")
    aff_dic = CorpusBuilder.get_affiliation(aff, nlp)
    assert aff_dic["name"] == "Commonwealth Trade Partners Inc."
    assert aff_dic["location"] == "Alexandria, VA"
    assert aff_dic["country"] == "United States of America"

    # test affiliation
    aff = BeautifulSoup('<aff id="af1-vaccines-09-00030">Department of Microbiological Sciences, North Dakota State University, Fargo, ND 58104, USA; <email>Birgit.Pruess@ndsu.edu</email>; Tel.: +1-701-231-7848</aff>', "html.parser")
    aff_dic = CorpusBuilder.get_affiliation(aff, nlp)
    assert aff_dic["name"] == "Department of Microbiological Sciences, North Dakota State University"
    assert aff_dic["location"] == "Fargo, ND 58104"
    assert aff_dic["country"] == "USA"
