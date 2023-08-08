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
import json
import logging

logging.basicConfig(level=logging.INFO)

######################################################################

def _multi_paper_find_best(entry):
    """A helper function to find which 'publication_info' entry is
    best, when there is more than one option.

    Issues to deal with:
    1. The 'publication_info' array seems to be in an arbitrary order
    2. There may be more than one 'journal' in the array
    3. The year may be wrong

    Approach that looks like it will work for LRR entries in INSPIRE
    at the moment:
    1. Filter down to just the elements with the correct journal
    2. Pick the element with the largest journal_volume
    """

    possibilities = entry['metadata']['publication_info']
    possibilities = filter( lambda p: ('journal_title' in p.keys())
                            and
                            p['journal_title'] == 'Living Rev.Rel.',
                            possibilities)
    possibilities = sorted(possibilities,
                           key= lambda p: p['journal_volume'])

    return possibilities[-1]

def _doi_filter(entry):
    """A helper function to only allow certain DOIs.
    One (or more?) INSPIRE entry has multiple DOIs, and one comes from
    some journal that's not LRR.
    """

    allowed_doi_starts = ['10.12942', '10.1007/s41114',  '10.1007/lrr']

    allowed_dois = [doi_entry for doi_entry in entry['metadata']['dois']
                    if any([doi_entry['value'].startswith(start)
                            for start in allowed_doi_starts]) ]

    return allowed_dois[-1]['value']

class Paper:
    """A single paper in LRR. Depends on INSPIRE JSON format"""
    def __init__(self, entry):

        self.problematic = False

        md = entry['metadata']

        self.iid      = entry['id']
        self.title    = md['titles'][-1]['title']

        try:
            self.doi      = _doi_filter(entry)
        except:
            logging.warning(f"missing doi field in {entry['id']}")
            self.problematic = True
            self.doi = 'missing'

        best_pub_info = _multi_paper_find_best(entry)
        
        try:
            self.year     = best_pub_info['year']
        except:
            logging.warning(f"missing year field in {entry['id']}")
            self.problematic = True
            self.year = 'missing'
        try:
            self.volume   = best_pub_info['journal_volume']
        except:
            logging.warning(f"missing journal_volume field in {entry['id']}")
            self.problematic = True
            self.volume = 'missing'
        try:
            self.number   = best_pub_info['page_start']
        except:
            logging.warning(f"missing page_start field in {entry['id']}")
            self.problematic = True
            self.number = 'missing'
        try:
            self.abstract = md['abstracts'][-1]['value']
        except:
            logging.warning(f"missing abstract field in {entry['id']}")
            self.problematic = True
            self.abstract = 'missing'

        self.authors  = [a['full_name'] for a in
                         md['authors']]
        # If the author list is long, call it a collaboration paper
        # and change the author list
        if (len(self.authors) > 8):
            self.authors      = [self.authors[0], 'et al.']
            self.authorsLasts = [md['first_author']['last_name']]
        else:
            self.authorsLasts = [a['last_name'] for a in
                                 md['authors']]

def papersFromJSONTree(root, corrections):
    """Parse the records in an INSPIRE search response into a list of
    class Paper. Depends on INSPIRE JSON format"""

    paperDict = {entry['id']: entry for entry in root['hits']['hits']}
    # Apply corrections (thanks, shallow copies!)
    for c in corrections:
        md = paperDict[c['id']]['metadata']
        md.update(c['metadata'])

    return list(map(Paper, root['hits']['hits']))

######################################################################

def supersededList(filename):
    """Read a plain text file where each line is one INSPIRE record ID"""
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

def LRRIndexFromJSONTree(root, superseded, preamble, corrections):
    """Build the actual author index web page"""
    allPapers = papersFromJSONTree(root, corrections)
    papers = list(filter(lambda paper: paper.iid not in superseded,
                         allPapers))

    logging.info("{} papers after removing {} superseded".format(len(papers),
                                                                 len(superseded)))

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

    return outputPage, allPapers

######################################################################

def stringFromFile(filename):
    with open(filename, 'r') as f:
        string = f.read()

    return string

def stringFromURL(url):
    return urlopen(url).read().decode('utf-8')

######################################################################

defaultFilename = 'lrr.json'
defaultURL      = ('https://inspirehep.net/api/literature'
                   '?q=find+j+%22Living+Rev.Rel.%22'
                   '&format=json&size=1000')
supersededFilename = 'superseded.txt'
preambleFilename = 'preamble.txt'
correctionsFilename = 'corrections.json'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='lrr-index', description=__doc__)

    fileOrUrl = parser.add_mutually_exclusive_group(required=True)
    fileOrUrl.add_argument('--file', nargs='?',
                           type=argparse.FileType('r'),
                           default=defaultFilename,
                           help='Name of JSON file to read')
    fileOrUrl.add_argument('--url',  nargs='?',
                           default=defaultURL,
                           help='URL of INSPIRE query')

    parser.add_argument('--superseded', default=supersededFilename,
                        help=('Name of file containing list of DOIs'
                              ' which have been superseded, one per'
                              ' line.'))

    parser.add_argument('--preamble', default=preambleFilename,
                        help=('Name of file containing preamble for'
                              ' web page to emit.'))


    parser.add_argument('--corrections', default=correctionsFilename,
                        type=argparse.FileType('r'),
                        help=('Name of JSON file with corrections'
                              ' for info missing from INSPIRE.'))

    args = parser.parse_args()

    root = [];
    if args.file is not None:
        root = json.load(args.file)
    else:
        root = json.loads(stringFromURL(args.url))

    superseded = supersededList(args.superseded)
    preamble = stringFromFile(args.preamble)
    corrections = json.load(args.corrections)

    outputPage, allPapers = LRRIndexFromJSONTree(root, superseded,
                                                 preamble, corrections)
    print(outputPage)

    # Dump auxiliary info for problematic records

    problematicIDs = [ paper.iid for paper in allPapers if paper.problematic ]
    problematic = [ entry for entry in root['hits']['hits']
                    if entry['id'] in problematicIDs ]

    with open('problematic.json','w') as f:
        json.dump(problematic, f, indent=2)

    # Dump auxiliary info for superseded records

    supersededEntries = [ entry for entry in root['hits']['hits']
                          if entry['id'] in superseded ]

    with open('superseded.json','w') as f:
        json.dump(supersededEntries, f, indent=2)
