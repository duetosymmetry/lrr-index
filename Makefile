.PHONY: lrr.xml

index.html: lrr-massaged.xml preamble.txt superseded.txt
	./lrr-index.py --file $< > $@

lrr.xml:
	curl -o $@ "http://old.inspirehep.net/search?p=find+j+%22Living+Rev.Rel.%22&of=xe&rg=1000"
