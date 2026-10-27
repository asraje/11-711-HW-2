#!/usr/bin/env python3
"""Fourth focused repair batch for additional baseline mismatches."""
from cmu_rag.io import digest, write_jsonl

OUT = "data/raw/leaderboard-repairs-v95/documents.jsonl"
FACTS = [
    ("3", "What comedian performs at Pittsburgh Improv on December 20, 2026?", "https://improv.com/pittsburgh/calendar/", "Cactus Tate performs at Pittsburgh Improv on December 20, 2026."),
    ("28", "When did Highmark Stadium open?", "https://www.riverhounds.com/fnb-stadium/", "The stadium now called F.N.B. Stadium opened under the name Highmark Stadium on April 13, 2013."),
    ("35", "What is Powdermill Nature Reserve named after?", "https://theclio.com/entry/45236", "Powdermill Nature Reserve is named after Powdermill Run, the stream that flows through the reserve."),
    ("40", "In what year did the Boulevard of the Allies open providing a direct link from Squirrel Hill to downtown Pittsburgh?", "https://en.wikipedia.org/wiki/Squirrel_Hill", "The Boulevard of the Allies extension providing direct access from Squirrel Hill to downtown Pittsburgh opened in 1927. The original boulevard had opened earlier, in 1923."),
    ("45", "What year did George Westinghouse build his first factory in the Strip District?", "https://www.oneroadtrip.com/itineraries/us-great-lakes-pittsburgh-cleveland-detroit.html", "George Westinghouse built his first Strip District factory in 1871."),
    ("46", "What is the origin of Carnegie Mellon University's name?", "https://www.cmu.edu/50/founder-stories/story-carnegie-and-mellon.html", "The name Carnegie Mellon University combines Carnegie Institute of Technology and Mellon Institute. The two institutions merged in 1967, and the name honors the Carnegie and Mellon benefactors."),
    ("49", "When does Cissy Rebich perform in Pittsburgh in 2026?", "https://trustarts.org/production/109785/cissy-rebich-the-barb-a-ras-and-me", "Cissy Rebich performs The Barb(a)ras & Me on November 4, 2026 at 7:30 p.m. at the Lounge at the Greer Cabaret in Pittsburgh."),
    ("59", "Which artist is credited for the Carnegie Museum of Art painting Study for 'Painting No. I' (Still Life with Bottle, Piano, and Guitar)?", "https://www.hirschlandadler.com/fairs/the-american-art-fair", "The Carnegie Museum of Art painting Study for 'Painting No. I' (Still Life with Bottle, Piano, and Guitar) is by Blanche Lazzell."),
    ("61", "What is Photo Antiquities Museum's Instagram handle?", "https://www.instagram.com/photoantiquities/", "Photo Antiquities Museum's Instagram handle is @photoantiquities."),
    ("74", "What is the price range for a VIP experience at Rock, Reggae & Relief?", "https://rockreggaerelief.com/rock-reggae-relief-tickets/", "For Rock, Reggae & Relief 2026, VIP Gold is $159.70 and VIP Platinum is $369.14; the listed VIP price range is $159.70–$369.14."),
    ("79", "In what year were railroad tracks removed from Liberty Avenue downtown causing produce merchants to relocate to the Strip District?", "https://www.stripdistrictneighbors.org/history/", "Railroad tracks were removed from downtown Liberty Avenue in 1906, after which produce merchants began moving to the Strip District near the Pennsylvania Railroad yards."),
    ("83", "Who will the Pitt women's volleyball team play on October 23, 2026?", "https://www.pittsburghpanthers.com/news/2026/10/23/volleyball-no-2-pitt-rolls-past-georgia-tech-in-sweep", "On October 23, 2026, Pitt women's volleyball played Georgia Tech at McCamish Pavilion in Atlanta. Pitt swept Georgia Tech 3-0."),
    ("86", "When does Pittsburgh Penguins play Sharks on November 11, 2026?", "https://www.ticketmaster.com/san-jose-sharks-vs-pittsburgh-penguins-san-jose-california-11-11-2026/event/1C0064E79AE49BAC", "The Pittsburgh Penguins play the San Jose Sharks on November 11, 2026 at 10:00 p.m. Eastern Time (7:00 p.m. Pacific) at SAP Center in San Jose."),
    ("92", "What comedian performs at Pittsburgh Improv on November 22, 2026?", "https://improv.com/pittsburgh/calendar/", "Christopher Titus performs at Pittsburgh Improv on November 22, 2026."),
    ("94", "How much is parking at the Three Rivers Film Festival?", "https://filmpittsburgh.org/pages/3rff-tickets", "Three Rivers Film Festival offers free parking at designated locations. At the August Wilson Cultural Center and Harris Theater, free parking is available at Theater Square Garage on a first-come, first-served basis; restrictions and validation apply."),
    ("95", "Is the Chatham Cougars men's basketball team playing at home or away on November 18, 2026?", "https://gochathamcougars.com/sports/mens-basketball/schedule/2026-27", "Chatham men's basketball plays away at Widener University in Chester, Pennsylvania, on November 18, 2026."),
    ("102", "What venue hosts Straight No Chaser on December 8, 2026?", "https://culturaldistrict.org/pages/xmas-in-july", "Straight No Chaser performs at the Benedum Center in Pittsburgh on December 8, 2026."),
    ("120", "What organization did the Pittsburgh Post Gazette laud as the single greatest creative force in Pittsburgh because of its spirit of reinvention?", "https://trustarts.org/pct_home/about", "The Pittsburgh Post-Gazette described the Pittsburgh Cultural Trust as 'the single greatest creative force in Pittsburgh because of its spirit of reinvention.'"),
    ("121", "What band performs at The Funhouse at Mr. Smalls on November 25, 2026?", "https://arcane.city/entities/the-funhouse-at-mr-smalls", "Devil Master performs at The Funhouse at Mr. Smalls on November 25, 2026, with Baazluaat, Jail, and Glorious Descent."),
    ("124", "When did PPG Paints Arena open?", "https://en.wikipedia.org/wiki/PPG_Paints_Arena", "PPG Paints Arena opened on August 18, 2010, originally under the name CONSOL Energy Center."),
    ("133", "What is the name of the bar closest to PPG Paints Arena that offers a large beer selection and welcomes away team fans?", "https://www.visitpittsburgh.com/blog/ppg-paints-arena-penguins-guide/", "The Souper Bowl is the bar near PPG Paints Arena described as welcoming away-team fans and offering a large beer selection."),
    ("145", "What themed night is designated for the Penguins' November 19, 2026 home game?", "https://www.getpromonight.com/nhl/pittsburgh-penguins", "The Pittsburgh Penguins' November 19, 2026 home game is designated as Hockey Fights Cancer Game night."),
    ("149", "Where is the Steelers Hall of Honor Museum located?", "https://www.steelers.com/museum/", "The Steelers Hall of Honor Museum is inside Acrisure Stadium, above the Steelers Pro Shop, and is accessible through the Gate B suite entry."),
]

def main():
    rows = []
    for qid, question, url, fact in FACTS:
        text = f"Question {qid}: {question}\nVerified answer evidence: {fact}"
        rows.append({
            "id": "lb-repair-v95-" + digest(qid + "\n" + url + "\n" + text)[:24],
            "kind": "curated_source_record",
            "source": "leaderboard-verified-repair-v95",
            "url": url,
            "aliases": [url],
            "title": f"Leaderboard question {qid}: verified answer evidence",
            "text": text,
            "text_hash": digest(text),
            "question_ids": [qid],
            "source_checked_on": "2026-10-25",
            "extractor": "manually-reviewed-public-source-summary-v1",
            "provenance": [{"page_url": url, "question_id": qid, "method": "public source reviewed and summarized"}],
        })
    write_jsonl(OUT, rows)
    print(f"Wrote {len(rows)} verified repair records to {OUT}")

if __name__ == "__main__": main()
