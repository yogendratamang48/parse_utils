"""
reads irs 990 forms

writes three files
- section_a.csv: employee data in section a (part ii)
- schedule_j.csv: employee data in schedule j (part ii)
- version_summary.csv: schema version of the form
"""
import requests
from parse_utils.page_parser import ItemExtractor
from lxml import html
import sys
import json
import csv
from multiprocessing.pool import Pool
import os
# object_id = sys.argv[1].strip()

TMP_TEXT_DIR = 'tmp_texts'

BATCH_SIZE = 10
SECTION_A_FILE = 'section_a.csv'
SCHEDULE_J_FILE = 'schedule_j.csv'
VERSION_FILE = 'version_summary.csv'

SECTION_A_HEADER = [
    'ObjectID',
    'Name',
    'Title',
    'AvgHoursPerWeek',
    'ReportableCompFromOrganization',
    'ReportableCompFromRelatedOrgs',
    'OtherCompensation',
    'Officer',
]
SCHEDULE_J_HEADER = [
    "ObjectID",
    "NamePerson",
    "BaseCompensationFilingOrg",
    "CompBasedOnRelatedOrgs",
    "BonusFilingOrg",
    "BonusRelatedOrgs",
    "OtherCompensationFilingOrg",
    "OtherCompensationRelatedOrgs",
    "DeferredCompFilingOrg",
    "DeferredCompRelatedOrgs",
    "NontaxableBenefitsFilingOrg",
    "NontaxableBenefitsRelatedOrgs",
    "TotalCompensationFilingOrg",
    "TotalCompensationRelatedOrgs",
    "CompReportPrior990FilingOrg",
    "CompReportPrior990RelatedOrgs",
]
VERSION_HEADER = [
    'ObjectID',
    'Version',
    'SectionAItems',
    'ScheduleJItems',
]


def build_batches(filename):
    """ creates batch of size BATCH_SIZE

    Args-
    filename : str  : location to filename
    """
    batch = []
    with open(filename, 'r') as fp:
        for _id in fp:
            if not _id.strip():
                continue
            batch.append(_id.strip())
            if len(batch) == BATCH_SIZE:
                yield batch
                batch = []
    if batch:
        yield batch

def write_to_csv(filename, header, items=None, init=None):
    """
    Args-
    filename : str  : filename
    header   : list : header row
    items    : list : list of items to write
    init     : bool : if True, writes file in write mode, default is append
    """
    write_mode = "a" 
    if init:
        write_mode = "w"
    
    with open(filename, write_mode, encoding='utf-8') as fp:
        writer = csv.writer(fp)
        if init:
            writer.writerow(header)
        else:
            for item in items:
                row = [item.get(_, '') for _ in header]
                writer.writerow(row)

config = {
    'results': ['//form990partviisectiona', ],
    'version': '//return/@returnversion',
    'fields': {
        'Name': ['./nameperson/text()'],
        'Title': ['./title/text()'],
        'AvgHoursPerWeek': ['./averagehoursperweek/text()'],
        'ReportableCompFromOrganization': ['./reportablecompfromorganization/text()'],
        'ReportableCompFromRelatedOrgs': ['./reportablecompfromrelatedorgs/text()'],
        'OtherCompensation': ['./othercompensation/text()'],
        'Officer': ['./officer/text()'],
    }
}

s_config = {
    'results': '//form990schedulejpartii',
    'version': '//return/@returnversion',
    "fields": {
        "NamePerson": ["./nameperson/text()"],
        "BaseCompensationFilingOrg": ["./basecompensationfilingorg/text()"],
        "CompBasedOnRelatedOrgs": ["./compbasedonrelatedorgs/text()"],
        "BonusFilingOrg": ["./bonusfilingorg/text()"],
        "BonusRelatedOrgs": ["./bonusrelatedorgs/text()"],
        "OtherCompensationFilingOrg": ["./othercompensationfilingorg/text()"],
        "OtherCompensationRelatedOrgs": ["./othercompensationrelatedorgs/text()"],
        "DeferredCompFilingOrg": ["./deferredcompfilingorg/text()"],
        "DeferredCompRelatedOrgs": ["./deferredcomprelatedorgs/text()"],
        "NontaxableBenefitsFilingOrg": ["./nontaxablebenefitsfilingorg/text()"],
        "NontaxableBenefitsRelatedOrgs": ["./nontaxablebenefitsrelatedorgs/text()"],
        "TotalCompensationFilingOrg": ["./totalcompensationfilingorg/text()"],
        "TotalCompensationRelatedOrgs": ["./totalcompensationrelatedorgs/text()"],
        "CompReportPrior990FilingOrg": ["./compreportprior990filingorg/text()"],
        "CompReportPrior990RelatedOrgs": ["./compreportprior990relatedorgs/text()"],
    }
}

def process_object_id(object_id):
    """handles single object id

    Args
    object_id : str filing ojbect id
    """
    url = f"https://s3.amazonaws.com/irs-form-990/{object_id}_public.xml"
    resp = requests.get(url)
    items = []
    s_items = []
    versions = []
    print(f"ObjectID: {object_id}, Response: {resp.status_code}")
    if resp.status_code == 200:
        page = html.fromstring(resp.content)
        version = page.xpath(config['version'])
        # Part VII Section A
        items = ItemExtractor.extract_items(config["results"], config["fields"], resp.content)
        items = map(lambda item: dict(item, ObjectID=object_id), items)
        s_items = ItemExtractor.extract_items(s_config["results"], s_config["fields"], resp.content)
        s_items = map(lambda item: dict(item, ObjectID=object_id), s_items)
        if version:
            version_dict = dict(
                ObjectID=object_id,
                Version=version[0],
                SectionAItems=len(list(items)),
                ScheduleJItems=len(list(s_items))
              )
            versions.append(version_dict)
        return (versions, list(items), list(s_items))
    return (versions, items, s_items)


def write_to_file(values):
    """Writes to files

    filename : tuple()  : Tupple
    """
    for versions, items, s_items in values:
        if items:
            write_to_csv(SECTION_A_FILE, SECTION_A_HEADER, items)
        if s_items:
            write_to_csv(SCHEDULE_J_FILE, SCHEDULE_J_HEADER, s_items)
        if versions:
            write_to_csv(VERSION_FILE, VERSION_HEADER, versions)


if __name__ == '__main__':
    #- listing files
    files = os.listdir(TMP_TEXT_DIR)
    # Initializing csv files with header
    write_to_csv(SECTION_A_FILE, SECTION_A_HEADER, init=True)
    write_to_csv(SCHEDULE_J_FILE, SCHEDULE_J_HEADER, init=True)
    write_to_csv(VERSION_FILE, VERSION_HEADER, init=True)

    for _file in files:
        # print(ids)
        filename = f"{TMP_TEXT_DIR}/{_file}"
        print(f"Working on: {filename}")
        for batch_i, batch in enumerate(build_batches(filename)):
            print(f"Batch: {batch_i}, size: {len(batch)}")
            with Pool() as P:
                values = P.map(process_object_id, batch)
                write_to_file(values)
