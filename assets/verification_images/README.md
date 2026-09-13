# Historical verification fixtures

28 image files required by bundled few-shot/reference/test fixtures, retained byte-for-byte. `manifest.json` records SHA256 and size. These are a small reproducibility subset, not the COCO validation dataset.

Files are named by content hash so different historical encodings of one COCO image remain distinguishable. Image IDs and original semantic contexts remain in the JSONL fixtures referencing these files. Do not replace a fixture by a same-ID official download without creating a new experimental condition and reviewing its hash and provenance.

Images originate from COCO experiment data and remain subject to their original image rights; the repository software license does not relicense the photographs. Full COCO information: https://cocodataset.org/
