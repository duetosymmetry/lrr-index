.PHONY: lrr.xml lrr.json

index.html: lrr.json preamble.txt superseded.txt corrections.json lrr-index.py
	./lrr-index.py --file $< > $@

lrr.json:
	curl -o $@ 'https://inspirehep.net/api/literature?q=find+j+%22Living+Rev.Rel.%22&format=json&size=1000&fields=authors.full_name,authors.last_name,first_author,abstracts,titles,dois,publication_info.journal_title,publication_info.journal_volume,publication_info.year,publication_info.artid,publication_info.page_start,arxiv_eprints'

lrr.xml:
	curl -o $@ "http://old.inspirehep.net/search?p=find+j+%22Living+Rev.Rel.%22&of=xe&rg=1000"
