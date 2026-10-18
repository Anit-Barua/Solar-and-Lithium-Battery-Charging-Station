.PHONY: all test results figures paper pdf clean
all: test results figures paper pdf
test:     ; python -m pytest -q
results:  ; python -m src.run_all
figures:  ; python -m src.make_figures
paper:    ; python -m src.build_paper
pdf:      ; cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
clean:    ; rm -f paper/*.aux paper/*.log paper/*.out paper/*.bbl paper/*.blg
