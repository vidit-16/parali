# Label revisions, Kaithal study area

The plots below were first labelled `not_burnt` by hand. The rules flagged each as a possible burn, so they
were looked at again. At the labeller's request the second look was done by the AI assistant (Claude Code),
reading the same image strips; the labeller did not re-inspect them. Two were changed to `burnt`, three to
`unsure` (left out of accuracy), two kept.

| plot | first label | revised | reason |
|---|---|---|---|
| p053_006 | not_burnt | burnt | 20 Oct: dark burn signature inside the plot box in the SWIR view, grey-dark in true colour |
| p072_000 | not_burnt | burnt | 20 Oct: dark burn signature over the plot box |
| p007_082 | not_burnt | unsure | 17 Oct: a darker square under the box, not clearly a burn |
| p137_031 | not_burnt | unsure | 6 Nov: dark, but not the burn colour |
| p061_105 | not_burnt | unsure | 4 Nov clouded; dark on 9 Nov, not the burn colour |
| p057_047 | not_burnt | kept | dark patches next to the box, not in it |
| p085_001 | not_burnt | kept | nothing burnt in the box |

The headline numbers use only the labeller's own labels (labels.csv -> data/eval/results.json), so no AI judgement
enters the test set. The revised labels (labels_revised.csv -> data/eval/results_revised_labels.json) are a
sensitivity check: with them, clean fields wrongly flagged drop from 1.9% to 1.5% (fire alerts 8.7% -> 8.8%).


## Second batch (labelled 10 Oct)

| plot | first label | revised | reason |
|---|---|---|---|
| p045_100 | not_burnt | burnt | 25 Oct: dark burn signature inside the box, grey-dark in true colour |
| p035_041 | not_burnt | burnt | 15 Oct: dark burn signature inside the box, dark brown in true colour |
| p075_090 | not_burnt | unsure | 6 Nov: dark, but not the burn colour |
| p040_059 | not_burnt | kept | the dark patch is above the box |
| p016_131 (Patran) | not_burnt | kept | nothing burnt in the box |
