#!/usr/bin/env python3

"""
lrr-index: Build old-style indices for Living Reviews in Relativity,
since Springer got rid of them. Emit markdown that should work with
Jekyll.
"""

__author__      = "Leo C. Stein"
__copyright__   = u"Copyright © 2017"

import sys, string, argparse
from urllib.request import urlopen
import xml.etree.ElementTree as ET

######################################################################

class Paper:
    """A single paper in LRR. Depends on INSPIRE XML format"""
    def __init__(self, xmlElement):
        self.title    = xmlElement.find("titles/title").text
        self.doi      = xmlElement.find("electronic-resource-num").text
        self.year     = xmlElement.find("dates/year").text
        self.volume   = xmlElement.find("volume").text
        self.number   = xmlElement.find("pages").text
        self.abstract = xmlElement.find("abstract").text
        self.authors  = [a.text for a in
                         xmlElement.findall("contributors/authors/author")]
        # If the author list is long, call it a collaboration paper
        # and change the author list
        if (len(self.authors) > 8):
            self.authors      = [self.authors[0], 'et al.']
            self.authorsLasts = [self.authors[0].split(',')[0]]
        else:
            self.authorsLasts = [author.split(',')[0]
                                 for author in self.authors]

def papersFromXMLTree(root):
    """TODO Document this. Depends on INSPIRE XML format"""
    return [Paper(record) for record in root.findall("records/record")]

######################################################################

def supersededList():
    """TODO Document this"""
    supersededFilename = "superseded.txt"
    f = open(supersededFilename, 'r')
    lines = f.readlines()
    f.close()

    superseded = [line.strip() for line in lines]
    
    return superseded

superseded = supersededList()

######################################################################

def LRRIndexFromXMLTree(root):
    """TODO Document this"""
    allPapers = papersFromXMLTree(root)
    papers = list(filter(lambda paper: paper.doi not in superseded, allPapers))
    # for paper in papers:
    #     if paper.doi is None:
    #         print("Living Rev. Rel. {0}, {1} ({2}), "
    #               "{3}".format(paper.volume, paper.number, paper.year,
    #                            paper.authorsLasts))

    # for paper in papers:
    #     if paper.doi is None:
    #         print("{}, {}".format("/".join(paper.authorsLasts), paper.title))

    # Make a list of all of the (author, paper) pairs, for *every*
    # author of a paper. Sort this list by the last names of the
    # authors.
    authsPaps = [(author, paper)
                 for paper in papers
                 for author in paper.authorsLasts]
    authsPaps.sort(key=lambda pair: "".join(pair[0].lower().split()))

    # List of first initials that appear
    fstInits = [author[0].upper()
                for paper in papers
                for author in paper.authorsLasts]
    fstInits = list(set(fstInits))
    fstInits.sort()
    print(fstInits)

    lastInit = ""
    for author, paper in authsPaps:
        curInit = author[0].upper()
        if curInit != lastInit:
            print("-- {} --".format(curInit))
            lastInit = curInit
        print("{}: {}, {}".format(paper.doi,
                                  "/".join(paper.authors),
                                  paper.title))

    return papers

######################################################################

defaultFilename = 'lrr.xml'
defaultURL      = ('http://inspirehep.net/search'
                   '?p=find+j+%22Living+Rev.Rel.%22'
                   '&of=xe&rg=1000')

def xmlStringFromFile(filename):
    """TODO Document this"""
    f = open(filename, 'r')
    xmlString = f.read()
    f.close()

    return xmlString

def xmlStringFromURL(url):
    """TODO Document this"""
    return urlopen(url).read().decode('utf-8')

def LRRIndexURL(url):
    """TODO Document this"""
    root = ET.fromstring(xmlStringFromURL(url))
    LRRIndexFromXMLTree(root)
    return root

def LRRIndexFile(filename):
    """TODO Document this"""
    tree = ET.parse(filename)
    root = tree.getroot()
    LRRIndexFromXMLTree(root)
    return root

######################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='lrr-index', description=__doc__)

    fileOrUrl = parser.add_mutually_exclusive_group(required=True)
    fileOrUrl.add_argument('--file', nargs='?', const=defaultFilename,
                           help='Name of XML file to read')
    fileOrUrl.add_argument('--url',  nargs='?', const=defaultURL,
                           help='URL of INSPIRE query')

    args = parser.parse_args()

    xmlString = ''
    if args.file is not None:
        LRRIndexFile(args.file)
    else:
        LRRIndexURL(args.url)
