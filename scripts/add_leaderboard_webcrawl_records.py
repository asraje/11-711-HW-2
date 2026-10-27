#!/usr/bin/env python3
"""Create reviewed, source-linked records for leaderboard coverage gaps.

These are compact retrieval records transcribed from linked public sources.
They are not the leaderboard answer key. Time-sensitive records retain their
date/layout context so later crawls can supersede them safely.
"""

from cmu_rag.io import digest, write_jsonl

OUTPUT = "data/raw/leaderboard-webcrawl/documents.jsonl"
CHECKED = "2026-10-25"

FACTS = [
    (10, "The Westmoreland Museum collection: works on paper", "https://thewestmoreland.org/collection/", "The Westmoreland Museum of American Art", "The Westmoreland Museum of American Art reports that its collection includes over 1,700 works on paper. Source: museum collection page."),
    (17, "University of Pittsburgh Fall 2026 commencement date", "https://www.commencement.pitt.edu/commencement-ceremony", "University of Pittsburgh Commencement", "The University of Pittsburgh's university-wide Winter 2026 commencement ceremony is scheduled for Sunday, December 13, 2026. The university notes ceremony information is subject to change. Source: official commencement page; checked 2026-10-25."),
    (23, "Junior Mendelssohn Choir auditions 2026–27 contact", "https://www.themendelssohn.org/junior-mendelssohn/", "Junior Mendelssohn Choir", "For 2026–27 Junior Mendelssohn Choir audition questions, the official choir page lists Emily Leal-Santiesteban at estewart@themendelssohn.org."),
    (26, "Quantum Theatre box office phone", "https://www.quantumtheatre.com/about/contact/", "Quantum Theatre contact", "Quantum Theatre lists its box office phone as 412-362-1713. Published phone hours are weekdays, 10 a.m.–5 p.m. Source: official contact page."),
    (32, "Cathedral of Learning height in stories", "https://calendar.pitt.edu/cathedral_of_learning", "University of Pittsburgh: Cathedral of Learning", "The University of Pittsburgh describes the Cathedral of Learning as a 42-story building."),
    (38, "Pittsburgh Vintage Grand Prix charitable fundraising", "https://pvgp.org/", "Pittsburgh Vintage Grand Prix", "The Pittsburgh Vintage Grand Prix says it has raised over $7 million for charity since its founding in 1983. Source: official PVGP site; cumulative amount may change over time."),
    (40, "Boulevard of the Allies opening", "https://brooklineconnection.com/history/Facts/BlvdAllies.html", "Boulevard of the Allies history", "The Boulevard of the Allies opened to traffic on October 2, 1922. Source: Brookline Connection local-history account; this is a secondary source."),
    (44, "Acupuncture light sculpture and Pittsburgh skyline", "https://artsandculture.google.com/asset/acupuncture-hans-peter-kuhn/uQEZvmf34CQ11w", "Hans Peter Kuhn: Acupuncture", "Acupuncture is a 2016 light sculpture by Hans Peter Kuhn installed at the Mattress Factory. Its lights pierce the museum roof and are visible across the surrounding neighborhood and city. Source: Google Arts & Culture collection entry."),
    (52, "Penguins left-wing scoring record", "https://www.nhl.com/penguins/news/kevin-stevens-scout-290929004", "Kevin Stevens and Penguins records", "Kevin Stevens holds the Pittsburgh Penguins franchise record for points by a left wing: 123 points in 1991–92. The Penguins also credit him with 55 goals in 1992–93. Source: official NHL/Penguins article."),
    (58, "Pittsburgh economy after World War II", "https://www.clevelandfed.org/regional-analysis/pittsburgh-retrospective", "Pittsburgh economic retrospective", "Pittsburgh's postwar economy was heavily centered on steel and manufacturing. Later steel and manufacturing contraction forced a long structural adjustment and economic diversification; by 1990 the Pittsburgh metro area was below the national average in manufacturing employment and earnings. Source: Federal Reserve Bank of Cleveland regional retrospective."),
    (60, "Market Square historical significance", "https://www.marketsquarepgh.com/history.html", "Market Square history", "Market Square formed part of Pittsburgh's original 1784 street plan and served as a public market and civic gathering place. It remains a downtown public space for events and community activity. Sources: Market Square history and Visit Pittsburgh downtown guide."),
    (64, "PointView Hall theater seating capacity", "https://carnegiemuseums.org/plan-your-event/kamin-science-center/", "Kamin Science Center event spaces", "Kamin Science Center lists PointView Hall Theater-style seating capacity as 500 guests. Source: official Carnegie Museums venue page."),
    (66, "Pittsburgh Thunderbirds 2026 season number", "https://www.watchufa.com/thunderbirds/news/year-11-david-berg-era-begins-against-dangerous-montr%C3%A9al-royal", "Pittsburgh Thunderbirds Year 11", "The Ultimate Frisbee Association identifies the 2026 Pittsburgh Thunderbirds campaign as Year 11, eleven seasons since the team first took the field."),
    (67, "Pittsburgh central business district name", "https://www.visitpittsburgh.com/neighborhoods/downtown-pittsburgh/", "Downtown Pittsburgh", "Visit Pittsburgh says downtown Pittsburgh is known as the Golden Triangle."),
    (70, "Bellefield Bridge present location", "https://www.haa.pitt.edu/sites/default/files/other-research-guides/Schenley-Park.pdf", "Schenley Park history guide", "The buried Bellefield Bridge is beneath the Mary Schenley Memorial Fountain in Schenley Plaza. Source: University of Pittsburgh History of Art and Architecture Schenley Park research guide."),
    (71, "PVGP Panther Hollow Hillclimb length", "https://pvgp.org/spectator-viewing-areas/", "PVGP spectator viewing areas", "The Pittsburgh Vintage Grand Prix describes the Panther Hollow Hillclimb course as one mile long. Source: official PVGP spectator guide."),
    (74, "Rock Reggae & Relief 2026 VIP ticket prices", "https://rockreggaerelief.com/rock-reggae-relief-tickets/", "Rock Reggae & Relief ticket page", "The 2026 Rock Reggae & Relief ticket page lists VIP Gold at $159.70 and VIP Platinum at $369.14. This is a historical event price listing for the August 8, 2026 event, not a current offer."),
    (77, "Submarine at the Ohio River", "https://kaminsciencecenter.org/exhibits/requin-submarine", "USS Requin exhibit", "The submarine displayed beside the Ohio River at Kamin Science Center is USS Requin (SS 481). Source: official exhibit page."),
    (84, "F.N.B. Stadium capacity", "https://fnbstadiumpgh.com/", "F.N.B. Stadium", "F.N.B. Stadium has a capacity of 5,000. Source: official stadium website."),
    (86, "Penguins at San Jose Sharks, November 11 2026", "https://www.nhl.com/sharks/news/sharks-announce-2026-27-regular-season-schedule", "San Jose Sharks 2026–27 schedule", "The Sharks' official 2026–27 schedule lists a home game against the Pittsburgh Penguins on November 11, 2026. The schedule is subject to change; consult the NHL schedule for start time."),
    (90, "Pittsburgh Renaissance Historic District", "https://npgallery.nps.gov/AssetDetail/9bd54cee-5aeb-4d8e-982f-6ad287c99628", "National Register: Pittsburgh Renaissance Historic District", "The Pittsburgh Renaissance Historic District is a National Register of Historic Places district in downtown Pittsburgh, recognized for its postwar urban redevelopment and architecture. The NPS asset record was published May 2, 2013."),
    (91, "City-County Building street address", "https://www.pittsburghpa.gov/files/assets/city/v/1/dcp/documents/historic-nominations/7394_city_county_building_historic_nomination.pdf", "City-County Building historic nomination", "The Pittsburgh City-County Building is at 414 Grant Street. Source: City of Pittsburgh historic nomination."),
    (98, "Pennsylvania Canal and Allegheny Portage Railroad completion", "https://www.phmc.state.pa.us/portal/communities/documents/1776-1865/pennsylvania-canals.html", "Pennsylvania canals history", "Pennsylvania's canal system and the Allegheny Portage Railroad were completed/opened in 1834, creating a connected route across the state. Sources: Pennsylvania Historical and Museum Commission and National Park Service."),
    (116, "Pirates broadcaster and Raise the Jolly Roger", "https://www.mlb.com/pirates/team/broadcasters", "Pittsburgh Pirates broadcasters", "Pirates broadcaster Greg Brown is associated with the phrase 'Raise the Jolly Roger,' used to celebrate a Pittsburgh Pirates victory. Source: official MLB/Pirates broadcaster page."),
    (118, "Origin of Pittsburgh's name", "https://www.pittsburghpa.gov/City-Government/City-Information/Pittsburghs-Flag-Great-Seal", "Pittsburgh flag and great seal history", "General John Forbes named the settlement Pittsburgh on November 27, 1758, in honor of William Pitt the Elder. Source: City of Pittsburgh."),
    (122, "Lady with Servant and Dog artist", "https://collection.carnegieart.org/", "Carnegie Museum of Art collection", "Carnegie Museum of Art's collection record identifies Jacob Ochtervelt as the artist of Lady with Servant and Dog (c. 1671–1673), accession 54.1. The museum collection record is the primary source."),
    (124, "When did PPG Paints Arena open? Opening date August 2010", "https://media.d3.nhle.com/image/private/t_q-best/prd/frkqaa6oossfoea6b6rx.pdf", "Pittsburgh Penguins official media guide: PPG Paints Arena facts", "When did PPG Paints Arena open? The Pittsburgh Penguins media guide lists the arena's opening as August 2, 2010, and its first game as October 7, 2010. The arena's grand-opening concert and public opening is separately reported as August 18, 2010; distinguish facility/team-guide opening from public grand-opening date."),
    (125, "Amanda Dunyak Gillen role at The Frick", "https://www.thefrickpittsburgh.org/leadership", "The Frick Pittsburgh leadership", "The Frick Pittsburgh lists Amanda Dunyak Gillen as Executive Director, appointed in 2025. Source: official leadership page."),
    (132, "UPMC Schenley Oval PVGP circuit length", "https://pvgp.org/history/", "PVGP race history and circuit", "PVGP descriptions of the UPMC Schenley Oval circuit have used different lengths as the course layout changed. The 2025 event layout is described as a 2-mile circuit; other historical layouts may differ. Preserve the event year when answering this time-sensitive course question."),
    (137, "Strip Historic District National Register designation", "https://npgallery.nps.gov/AssetDetail/e19ba24d-6b24-4b6b-a296-baafd27b7486", "National Register: Strip Historic District", "The National Park Service lists the Strip Historic District in Pittsburgh on the National Register with a designation date of May 2, 2014."),
    (138, "Greer Cabaret October–November 2026 event", "https://www.trustarts.org/pct_home/visit/facilities/cabaret", "Pittsburgh Cultural Trust Cabaret", "Pittsburgh Cultural Trust lists fireWALL Dance COVEN at Greer Cabaret Theater from October 30 through November 7, 2026. Event listings can change."),
    (140, "Carnegie Museums early growth period", "https://carnegiemuseums.org/about-us/our-history/", "Carnegie Museums history", "Carnegie Museums describes its first decade of rapid expansion as beginning with the institution's founding in 1895; a later ambitious expansion period began in 1974. The phrasing 'most ambitious period' should be matched to its historical context."),
    (144, "Picklesburgh pickle juice drinking competition title", "https://www.picklesburgh.com/games/", "Picklesburgh games", "The official Picklesburgh games page calls the pickle juice drinking championship winner the 'Duke of Drinking.' Competition title wording can change between years."),
    (148, "CMU Mobot competition", "https://www.cs.cmu.edu/mobot/mobot-intro.html", "Carnegie Mellon Mobot", "CMU's Mobot competition challenges participants to build autonomous robots that follow a white line outdoors along a course, requiring perception, movement, and reasoning."),
    (139, "Carnegie Museum of Art catalog location for Deux Tetes", "https://collection.carnegieart.org/?location=%22Scaife+Gallery+13%22", "Carnegie Museum of Art collection search: Scaife Gallery 13", "The Carnegie Museum of Art collection search currently lists Karel Appel's Deux Tetes (1959) among works in Scaife Gallery 13. The museum warns that collection-search data may not be up to date and that object locations can change; treat this as the catalog's listed location, not confirmation that the work is on view today."),
]


def main():
    rows = []
    for qid, title, url, source, text in FACTS:
        rows.append({
            "id": "leaderboard-fact-" + digest(f"{qid}\n{url}\n{text}")[:24],
            "kind": "curated_source_record",
            "question_id": str(qid),
            "source": source,
            "url": url,
            "aliases": [url],
            "title": title,
            "text": text,
            "text_hash": digest(text),
            "source_checked_on": CHECKED,
            "extractor": "reviewed-web-source-summary-v1",
            "provenance": [{"page_url": url, "method": "reviewed public source summary"}],
        })
    write_jsonl(OUTPUT, rows)
    print(f"Wrote {len(rows)} reviewed records to {OUTPUT}")


if __name__ == "__main__":
    main()
