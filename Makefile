.PHONY: lrr.xml

index.html: lrr-massaged.xml
	./lrr-index.py --file $< > $@

lrr.xml:
	curl -o $@ "http://inspirehep.net/search?p=find+j+%22Living+Rev.Rel.%22&of=xe&rg=1000"
