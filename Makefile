.PHONY: lrr.xml

index.html: lrr.json preamble.txt superseded.txt lrr-index.py
	./lrr-index.py --file $< > $@

lrr.json:
	curl -o $@ "https://inspirehep.net/api/literature?q=find+j+%22Living+Rev.Rel.%22&format=json&size=1000"

lrr.xml:
	curl -o $@ "http://old.inspirehep.net/search?p=find+j+%22Living+Rev.Rel.%22&of=xe&rg=1000"
