# paper/

Two papers live here, one per week. They disagree with each other in places, and
that is deliberate.

## The submission

**`week2/main.pdf`** — ten pages, IJCAI-ECAI 26 format. This is the deliverable.
It stands alone; nothing in the repository is needed to read it.

## Everything else

| Path | What it is |
|---|---|
| `week2/main.tex`, `week2/references.bib`, `week2/figures/` | What builds the Week 2 paper. `figures/make_figures.py` regenerates the three figures |
| `main.pdf`, `main.tex` | The **Week 1** paper, nine pages. Kept as it was submitted |
| `figures/` | The three Week 1 figures and the script that builds them |
| `preprint.md` | The Week 1 argument in markdown, written before the LaTeX version |
| `limitations.md` | Long-form limitations, longer than either paper's section has room for |

## Why the Week 1 paper is still here

Week 2 corrects it. The zero-bits invariance it reports as a property of secret
scanning is a property of credential formats that hide the identifier; the
escalation result it reports as structural is a consequence of pricing
escalation as though it competed on expected cost; and the cost of dismissing a
live key that it prices at 2400 minutes contains an unstated probability of
exploitation equal to one.

Overwriting it would have destroyed the record of those corrections, and the
corrections are the more interesting half of Week 2. Read Week 1 first if you
want the sequence; read `week2/main.pdf` alone if you want the result.

## Building either one

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

`ijcai26.sty` and `named.bst` come from the official IJCAI author kit and are
gitignored rather than redistributed. Copy both alongside whichever `main.tex`
you are building. Both PDFs are committed, so this is only needed to rebuild.
