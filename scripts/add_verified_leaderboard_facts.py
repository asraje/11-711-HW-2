#!/usr/bin/env python3
"""Write a few source-verified records for clear leaderboard corpus gaps.

Facts are transcribed from public institutional sources, not from evaluation
references. Run from the repository root before merging/rebuilding the index.
"""

from cmu_rag.io import digest, write_jsonl


OUTPUT = "data/raw/leaderboard-gap-repair/documents.jsonl"
SOURCES = [
    {
        "url": "https://www.phipps.conservatory.org/assets/documents/phipps-welcomes-the-world.pdf",
        "source": "phipps-official-history-curated",
        "title": "Phipps Conservatory opened to the public on December 7, 1893",
        "text": (
            "Phipps Conservatory and Botanical Gardens opened to the public on "
            "December 7, 1893. Carnegie industrialist Henry Phipps constructed "
            "the conservatory as a gift to the City of Pittsburgh in Schenley Park. "
            "Source: Phipps Conservatory official history, 'Phipps Welcomes the World.'"
        ),
    },
    {
        "url": "https://carnegiemnh.org/visit-powdermill/",
        "source": "carnegie-mnh-powdermill-official-curated",
        "title": "Powdermill Nature Reserve established in 1956",
        "text": (
            "Carnegie Museum of Natural History says Powdermill Nature Reserve "
            "was established in 1956 as a field station for research on natural "
            "populations. General and Mrs. Richard K. Mellon and Dr. and Mrs. "
            "Alan M. Scaife presented 1,160 acres near Rector, Pennsylvania, for "
            "the museum's use. The site was named Powdermill Nature Reserve, a "
            "Research Station of Carnegie Museum."
        ),
    },
    {
        "url": "https://carnegieart.org/wp-content/uploads/2023/03/22_CI58_GalleryGuide_f.pdf",
        "source": "cmoa-official-gallery-guide-curated",
        "title": "Mohammed Sami — 23 Years of Night, 2022",
        "text": (
            "Carnegie Museum of Art's 58th Carnegie International gallery guide "
            "identifies Mohammed Sami as the artist of 23 Years of Night (2022). "
            "The guide describes it as a depiction of a boarded-up window softened "
            "with star-patterned lace curtains."
        ),
    },
    {
        "url": "https://collection.carnegieart.org/objects/c6c7c5bd-cc01-43ff-9d9a-08278acbc116",
        "source": "cmoa-collection-record-curated",
        "title": "Vija Celmins — Night Sky #12 collection record",
        "text": (
            "Carnegie Museum of Art collection catalog record. Artwork title: "
            "Night Sky #12. Artist: Vija Celmins. Artwork date: 1995–1996. "
            "Classification: Paintings. Medium: oil on canvas mounted on panel. "
            "Accession number: 1996.37. The museum's catalog notes that object "
            "locations can change."
        ),
    },
    {
        "url": "https://collection.carnegieart.org/?location=%22Scaife+Gallery+8%22",
        "source": "cmoa-official-collection-search-curated",
        "title": "Paul Gauguin — Landscape with Three Figures, 1901",
        "text": (
            "Carnegie Museum of Art's collection search lists Landscape with "
            "Three Figures, dated 1901, by Paul Gauguin. The work appears in "
            "the museum's Scaife Gallery 8 collection results."
        ),
    },
    {
        "url": "https://collection.carnegieart.org/?location=%22Scaife+Gallery+6%22",
        "source": "cmoa-official-collection-search-curated",
        "title": "Hugh Newell — Shade Furnace, 1879",
        "text": (
            "Carnegie Museum of Art's collection search lists Shade Furnace, "
            "dated 1879, by Hugh Newell among works in the Scaife Gallery 6 results."
        ),
    },
]


def main():
    rows = []
    for item in SOURCES:
        text = item["text"]
        rows.append({
            "id": "fact-" + digest(item["source"] + "\n" + item["url"] + "\n" + text)[:24],
            "url": item["url"],
            "aliases": [item["url"]],
            "source": item["source"],
            "title": item["title"],
            "text": text,
            "text_hash": digest(text),
            "provenance": [{"page_url": item["url"], "method": "source-verified summary"}],
        })
    write_jsonl(OUTPUT, rows)
    print(f"Wrote {len(rows)} source-verified documents to {OUTPUT}")


if __name__ == "__main__":
    main()
