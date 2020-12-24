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
    """Parse the records in an INSPIRE search response into a list of
    class Paper. Depends on INSPIRE XML format"""
    return [Paper(record) for record in root.findall("records/record")]

######################################################################

def supersededList(filename):
    """Read a plain text file where each line is one DOI"""
    with open(filename, 'r') as f:
        lines = f.readlines()

    superseded = [line.strip() for line in lines]

    return superseded

######################################################################

def formatPaper(paper, number):
    paperTemplate = """<div class="list__item">
  <article class="archive__item">
    <h2 class="archive__item-title" itemprop="title">
      <a href="http://dx.doi.org/{paper.doi}" rel="permalink">{paper.title}</a>
    </h2>
    <p class="lrr-author" itemprop="author">{authorList}</p>
    <p class="lrr-jref"   itemprop="jref"><i>Living Rev. Rel.</i>, <b>{paper.volume}</b>, ({paper.year}), {paper.number}.</p>
    <input type="checkbox" class="toggleCheck" id="ch{number}"><label class="toggleLabel" for="ch{number}"> Show/hide abstract</label>
    <p class="archive__item-excerpt" itemprop="abstract">{paper.abstract}</p>
  </article>
</div>
"""
    return paperTemplate.format(paper=paper, authorList="/".join(paper.authors), number=number)

def formatLetter(letter):
    letterTemplate = """  <a href="#{0}" class="page__taxonomy-item" rel="initial">{0}</a>
"""
    return letterTemplate.format(letter)

def formatLetters(letters):
    lettersTemplate = """
<p class="page__taxonomy page__meta">
{}</p>
<hr>
"""
    innerLinks = "".join(map(formatLetter, letters))
    return lettersTemplate.format(innerLinks)

######################################################################

def LRRIndexFromXMLTree(root, superseded, preamble):
    """Build the actual author index web page"""
    allPapers = papersFromXMLTree(root)
    papers = list(filter(lambda paper: paper.doi not in superseded, allPapers))

    print("{} papers after removing {} superseded".format(len(papers), len(superseded)),
          file=sys.stderr)

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

    outputPage = preamble

    outputPage += formatLetters(fstInits)

    lastInit = ""
    number = 0
    for author, paper in authsPaps:

        curInit = author[0].upper()
        if curInit != lastInit:
            # The <i></i> here is to insert an extra DOM element,
            # to keep the coloring even/odd
            outputPage += '<i></i><a name="{}"></a>\n'.format(curInit)
            lastInit = curInit

        outputPage += formatPaper(paper, number)
        number += 1

    return outputPage

######################################################################

def stringFromFile(filename):
    with open(filename, 'r') as f:
        string = f.read()

    return string

def xmlStringFromURL(url):
    return urlopen(url).read().decode('utf-8')

def LRRIndexURL(url):
    root = ET.fromstring(xmlStringFromURL(url))
    LRRIndexFromXMLTree(root)
    return root

def LRRIndexFile(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    LRRIndexFromXMLTree(root)
    return root

######################################################################

defaultFilename = 'lrr.xml'
defaultURL      = ('http://inspirehep.net/search'
                   '?p=find+j+%22Living+Rev.Rel.%22'
                   '&of=xe&rg=1000')
supersededFilename = 'superseded.txt'
preambleFilename = 'preamble.txt'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='lrr-index', description=__doc__)

    fileOrUrl = parser.add_mutually_exclusive_group(required=True)
    fileOrUrl.add_argument('--file', nargs='?', const=defaultFilename,
                           help='Name of XML file to read')
    fileOrUrl.add_argument('--url',  nargs='?', const=defaultURL,
                           help='URL of INSPIRE query')

    parser.add_argument('--superseded', default=supersededFilename,
                        help=('Name of file containing list of DOIs'
                              ' which have been superseded, one per'
                              ' line.'))

    parser.add_argument('--preamble', default=preambleFilename,
                        help=('Name of file containing preamble for'
                              ' web page to emit.'))

    args = parser.parse_args()

    root = [];
    if args.file is not None:
        tree = ET.parse(args.file)
        root = tree.getroot()
    else:
        root = ET.fromstring(xmlStringFromURL(args.url))

    superseded = supersededList(args.superseded)
    preamble = stringFromFile(args.preamble)

    print(LRRIndexFromXMLTree(root, superseded, preamble))
