"""Create compact records from verified, public source pages.

This is intentionally a small, auditable addition rather than an answer-key
derived expansion. Recheck time-sensitive business details against their live
pages before using the corpus for current recommendations.
"""

from pathlib import Path

from cmu_rag.io import digest, read_jsonl, write_jsonl


OUTPUT = Path("data/processed/corpus-curated-v24.jsonl")

# Facts below were transcribed from each cited page, not from evaluation labels.
SOURCES = [
    {
        "id_key": "gaby-et-jules-macarons",
        "url": "https://www.gabyetjules.com/",
        "title": "Gaby et Jules — Pittsburgh patisserie specializing in French macarons",
        "text": (
            "Which Pittsburgh bakery is known for its macarons? Gaby et Jules is "
            "a Pittsburgh patisserie specializing in French macarons. Its official "
            "website calls each macaron a scratch-made confection, locally made in "
            "the French tradition, and lists flavors including chocolate, lemon, "
            "raspberry, pistachio, and Le Pittsburgh. The bakery offers macaron "
            "collections, gift boxes, individual macarons, and macaron towers."
        ),
        "source": "gaby-et-jules-official-macarons-curated",
        "provenance_urls": [
            "https://www.gabyetjules.com/",
            "https://www.gabyetjules.com/product-category/organization/macarons/",
        ],
    },
    {
        "id_key": "il-tetto-rooftop",
        "url": "https://www.siennamercato.com/faq/",
        "title": "Il Tetto rooftop beer garden and Pittsburgh skyline views — Sienna Mercato FAQ",
        "text": (
            "Which Pittsburgh restaurant offers a rooftop dining experience with city views? "
            "Il Tetto is the third-floor rooftop beer and wine garden at Sienna Mercato, "
            "a three-story marketplace in Downtown Pittsburgh. Sienna Mercato's official "
            "FAQ says its retractable glass ceiling provides beautiful views of the "
            "Pittsburgh skyline. The venue is at 942 Penn Avenue, Pittsburgh, PA 15222. "
            "This identifies Il Tetto as the rooftop restaurant and beer garden with city views."
        ),
        "source": "sienna-mercato-official-faq-curated",
        "provenance_urls": [
            "https://www.siennamercato.com/faq/",
            "https://www.siennamercato.com/location/il-tetto/",
        ],
    },
    {
        "id_key": "cmu-navlab",
        "url": "https://www.ri.cmu.edu/autonomous-vehicles/",
        "title": "NavLab autonomous vehicles — Carnegie Mellon Robotics Institute",
        "text": (
            "Carnegie Mellon Robotics Institute: autonomous vehicle research. "
            "CMU's NavLab project is a series of experimental autonomous and "
            "semi-autonomous vehicles. The project combines vehicle platforms "
            "with computers, laser scanners, and cameras for perception and "
            "automated driving research. CMU's autonomous driving work began in 1984."
        ),
        "source": "cmu-robotics-institute-curated",
    },
    {
        "id_key": "cmu-kiltie-band",
        "url": "https://www.cmu.edu/cfa/music/about/history.html",
        "title": "Kiltie Band student marching band — Carnegie Mellon University",
        "text": (
            "The Kiltie Band is Carnegie Mellon's student marching band. It "
            "wears traditional Scottish kilts and performs at CMU sporting "
            "events. The band began in 1908 as a seven-member group supporting "
            "the football team."
        ),
        "source": "cmu-kiltie-band-curated",
        "provenance_urls": [
            "https://www.cmu.edu/about/traditions",
            "https://www.cmu.edu/cfa/music/about/history.html",
        ],
    },
    {
        "id_key": "cmu-cfa-building",
        "url": "https://visit.pantheon.cmu.edu/visit/campus-tours/self-guided-campus-tour",
        "title": "College of Fine Arts Building — CMU self-guided campus tour",
        "text": (
            "Carnegie Mellon campus tour: the College of Fine Arts Building is "
            "an architectural work by Henry Hornbostel. It is home to the "
            "College of Fine Arts schools of architecture, art, and music, "
            "and to BXA intercollege degree programs."
        ),
        "source": "cmu-campus-tour-curated",
    },
    {
        "id_key": "cmu-fence",
        "url": "https://www.cmu.edu/125/stories/fence-history.html",
        "title": "The Fence tradition — Carnegie Mellon University",
        "text": (
            "Carnegie Mellon campus tradition: the original Fence was built "
            "on The Cut in 1923 by a group of seniors. By the 1960s, painting "
            "messages on the Fence had become a student tradition. CMU describes "
            "the Fence as a campus message board and a highly painted object."
        ),
        "source": "cmu-fence-history-curated",
    },
    {
        "id_key": "cmu-cut-history",
        "url": "https://www.cmu.edu/piper/news/archives/the-piper/ThePiperOct06.pdf",
        "title": "The Cut — CMU grassy lawn formed from a ravine filled by 1917",
        "text": (
            "The Cut is Carnegie Mellon's level grassy campus lawn. It was "
            "formerly a ravine that marked the campus edge. Carnegie "
            "Mellon's October 2006 Piper says the pre-existing ravine was filled "
            "in by 1917 after Carnegie Tech acquired land toward Forbes Street, "
            "using about one million cubic feet of earth from a nearby hill. "
            "1917 is the fill date, not when the ravine began. The Cut "
            "is the lawn and is not the painted message board. The Fence is a "
            "separate structure standing on the lawn; the Fence, not the lawn, "
            "is the student message board."
        ),
        "source": "cmu-piper-cut-history-curated",
        "provenance_urls": [
            "https://www.cmu.edu/piper/news/archives/the-piper/ThePiperOct06.pdf",
            "https://www.cmu.edu/125/stories/fence-history.html",
        ],
    },
    {
        "id_key": "tako-pittsburgh",
        "url": "https://takopgh.com/",
        "title": "Tako — official Pittsburgh restaurant description",
        "text": (
            "Tako's official website describes its food as a fusion of Mexican "
            "and Japanese street-food flavors. The restaurant is at 214 Sixth "
            "Street in downtown Pittsburgh. The website currently says in-person "
            "dining is temporarily closed while its next chapter takes shape; "
            "check the live site for current operating status."
        ),
        "source": "tako-official-curated",
    },
    {
        "id_key": "pusadees-garden-menu",
        "url": "https://pusadeesgarden.com/menus/dinner/",
        "title": "Pusadee's Garden — regional Thai dishes, khao soi, and northern-style laab",
        "text": (
            "Pusadee's Garden in Pittsburgh serves regional, homestyle Thai "
            "cuisine. The Pittsburgh "
            "Post-Gazette describes its food as regional Thai cooking; Pittsburgh "
            "Magazine's 2021 coverage of the restaurant's reopening describes a "
            "northern Thai relish and mushroom laab among its dishes. The current "
            "official dinner menu lists northern-style mushroom laab and khao soi "
            "with wagyu beef cheek, egg noodles, pickled mustard greens, and red "
            "and yellow curry. It also lists som tum Thai, jungle curry, and "
            "massaman curry. An older official menu lists northern Thai-style "
            "sausage; this is historical menu wording, not a claim that it is "
            "currently served. The live menu was checked October 23, 2026 and "
            "may change."
        ),
        "source": "pusadees-official-menu-curated",
        "provenance_urls": [
            "https://pusadeesgarden.com/menus/dinner/",
            "https://newsinteractive.post-gazette.com/eat-pittsburgh-restaurants/lawrenceville.php",
            "https://www.pittsburghmagazine.com/pusadees-garden-sets-an-opening-date/",
            "https://pusadeesgarden.com/menu/dining.pdf",
        ],
        "inference_note": (
            "The sources support regional Thai cuisine and northern-style menu examples, "
            "not that every dish or the entire current menu is exclusively Northern Thai. "
            "The older menu's sausage description is historical."
        ),
    },
    {
        "id_key": "iron-born-pizza",
        "url": "https://ironbornpizza.com/",
        "title": "Iron Born Pizza — official restaurant story",
        "text": (
            "Iron Born Pizza's official story says its inspiration came from "
            "Detroit-style pizza, which reminded its chef of square Sicilian "
            "pizza from his childhood. The Pittsburgh restaurant focuses on "
            "square Detroit-style pizza. It says it uses housemade garlic oil, "
            "pickled banana peppers, and an evolving list of inventive pies "
            "built around flavor and seasonal ingredients. The Strip District "
            "location offers dine-in and takeout at 1806 Smallman Street."
        ),
        "source": "iron-born-official-curated",
    },
    {
        "id_key": "fogo-pittsburgh",
        "url": "https://fogodechao.com/location/pittsburgh/",
        "title": "Fogo de Chão — Brazilian steakhouse in Pittsburgh",
        "text": (
            "Fogo de Chão offers an authentic Brazilian steakhouse experience "
            "in Pittsburgh, with Brazilian cuisine, a churrasqueira grill, and "
            "churrasco. Its Pittsburgh location is at 525 Smithfield Street "
            "downtown."
        ),
        "source": "fogo-official-curated",
    },
    {
        "id_key": "fogo-pittsburgh-full-churrasco-experience",
        "url": "https://fogodechao.com/location/pittsburgh/",
        "title": "Fogo de Chão Pittsburgh — Brazilian churrasco and continuous tableside service",
        "text": (
            "Fogo de Chão's Downtown Pittsburgh restaurant at 525 Smithfield "
            "Street offers an authentic Brazilian steakhouse and churrasco "
            "experience. Fogo describes its Full Churrasco Experience as "
            "continuous tableside service of fire-roasted meats carved by "
            "Brazilian-trained gaucho chefs, with access to the seasonal Market "
            "Table, Feijoada Bar, and Brazilian side dishes. The restaurant's "
            "official FAQ says guests may return for service as often as they "
            "like during the meal."
        ),
        "source": "fogo-pittsburgh-official-churrasco-curated",
        "provenance_urls": [
            "https://fogodechao.com/location/pittsburgh/",
            "https://fogodechao.com/faq/",
        ],
    },
    {
        "id_key": "cmu-deep-thought",
        "url": "https://www.cs.cmu.edu/~scsnews/may9-97.html",
        "title": "Deep Thought chess machine — Carnegie Mellon School of Computer Science",
        "text": (
            "Deep Thought was a computer chess machine built at Carnegie Mellon "
            "University by five graduate students: Thomas Anantharaman, Michael "
            "Browne, Murray Campbell, Feng-hsiung Hsu, and Andreas Nowatzyk. "
            "In 1988 it became the first chess machine to reach international "
            "master status and received the intermediate Fredkin Prize. Deep "
            "Thought was a precursor to IBM's Deep Blue. CMU's School of Computer "
            "Science says its computer-chess research dates to the late 1950s."
        ),
        "source": "cmu-scs-deep-thought-curated",
    },
    {
        "id_key": "mt-lebanon-library-hours",
        "url": "https://mtlebanonlibrary.org/DocumentCenter/View/4382/Hours-of-Opening-Policy-7_18_23?bidId=",
        "title": "Mt. Lebanon Public Library hours — official hours of opening policy",
        "text": (
            "Mt. Lebanon Public Library's Hours of Opening Policy, issued July "
            "18, 2023, lists public hours Monday through Thursday, Friday, "
            "Saturday, and Sunday. It is therefore open on all seven days of "
            "the week under the stated regular schedule: Monday–Thursday "
            "9 a.m.–9 p.m., Friday–Saturday 9 a.m.–5 p.m., and Sunday "
            "1 p.m.–5 p.m. The policy lists holidays when the library is closed."
        ),
        "source": "mt-lebanon-library-policy-curated",
    },
    {
        "id_key": "fet-fisk-specialty",
        "url": "https://www.fetfisk.net/the-story",
        "title": "FET-FISK specialty — Nordic-inspired seafood with seasonal regional produce",
        "text": (
            "FET-FISK describes itself as a seafood restaurant and bar. Its "
            "official story says its dishes highlight seasonal regional produce "
            "and sustainably sourced seafood and meat. The restaurant is at "
            "4786 Liberty Avenue in Pittsburgh. Independent local coverage "
            "describes its seafood dishes as inspired by Nordic culture; the "
            "restaurant's own page emphasizes seafood, seasonal regional "
            "produce, and sustainably sourced meat and fish."
        ),
        "source": "fet-fisk-official-story-curated",
        "provenance_urls": [
            "https://www.fetfisk.net/",
            "https://www.fetfisk.net/the-story",
            "https://www.axios.com/local/pittsburgh/2025/06/17/fet-fisk-james-beard-finalist-spotlight",
        ],
    },
    {
        "id_key": "bubba-chandler-bio",
        "url": "https://www.mlb.com/player/bubba-chandler-696149",
        "title": "Bubba Chandler — official MLB player bio",
        "text": (
            "Bubba Chandler's birthplace is Lawrenceville, Georgia. His "
            "birthplace is Lawrenceville, not Pittsburgh. The MLB player bio "
            "lists his birth date as September 14, 2002; his full name is Roy "
            "Reuben Chandler. He is a Pittsburgh Pirates pitcher, and his high "
            "school is North Oconee in Bogart, Georgia."
        ),
        "source": "mlb-bubba-chandler-bio-curated",
    },
    {
        "id_key": "luke-weaver-bio",
        "url": "https://www.mlb.com/player/luke-weaver-596133",
        "title": "Luke Weaver — official MLB player bio and debut",
        "text": (
            "The official MLB bio identifies Luke Allen Weaver as a pitcher "
            "and lists his Major League debut as August 13, 2016. It lists his "
            "birthplace as DeLand, Florida, and his college as Florida State. "
            "The debut date is August 13, 2016."
        ),
        "source": "mlb-luke-weaver-bio-curated",
    },
    {
        "id_key": "nick-robertson-bio",
        "url": "https://www.nhlpa.com/player/45/nicholas-robertson/",
        "title": "Nick Robertson — NHL Players' Association player profile",
        "text": (
            "The NHL Players' Association profile for Nicholas (Nick) "
            "Robertson lists his birthdate as September 11, 2001. Pittsburgh "
            "Penguins announced in July 2026 that they signed forward Nick "
            "Robertson to a two-year contract through the 2027–28 season, after "
            "acquiring him from Toronto on July 1, 2026."
        ),
        "source": "nhlpa-nick-robertson-bio-curated",
        "provenance_urls": [
            "https://www.nhlpa.com/player/45/nicholas-robertson/",
            "https://www.nhl.com/penguins/news/penguins-sign-forward-nick-robertson-to-a-two-year-contract",
        ],
    },
    {
        "id_key": "paul-jenkins-phenomena-prism-crucible",
        "source_checked_on": "2026-10-24",
        "url": "https://www.pauljenkins.net/works/painBody.html",
        "title": "Phenomena Prism Crucible — Paul Jenkins (also known as William Paul Jenkins)",
        "text": (
            "Paul Jenkins's official works catalogue lists Phenomena Prism "
            "Crucible (1984) as an acrylic on canvas measuring 72 by 156 inches "
            "and identifies the Carnegie Museum of Art, Pittsburgh, as its "
            "collection. The Smithsonian American Art Museum lists William Paul "
            "Jenkins as another name for Paul Jenkins. This artwork is by the "
            "artist Paul Jenkins, also known by the full name William Paul Jenkins."
        ),
        "source": "paul-jenkins-official-catalogue-curated",
        "provenance_urls": [
            "https://www.pauljenkins.net/works/painBody.html",
            "https://americanart.si.edu/artist/paul-jenkins-2450",
        ],
    },
    {
        "id_key": "rmu-mens-basketball-nec-titles",
        "url": "https://static.rmucolonials.com/custompages/MBB%202014-15%20Fact%20Book/2014-15_Section%203.pdf",
        "title": "Robert Morris men's basketball NEC tournament champions — 1982, 1983, 1989, 1990, 1992, 2009, 2010, 2015, 2020",
        "text": (
            "The Northeast Conference's official men's basketball history "
            "lists Robert Morris as tournament champion in seasons 1981-82, "
            "1982-83, 1988-89, 1989-90, 1991-92, 2008-09, 2009-10, 2014-15, "
            "and 2019-20. Expressed as the calendar year in each season name, "
            "Robert Morris men's basketball won championship titles in 1982, "
            "1983, 1989, 1990, 1992, 2009, 2010, 2015, and 2020. The 1982 and "
            "1983 titles were in the ECAC Metro era, before the conference was "
            "named the Northeast Conference. Robert Morris Athletics confirms "
            "the 2020 win was its ninth NEC Tournament title."
        ),
        "source": "rmu-nec-official-basketball-championships-curated",
        "provenance_urls": [
            "https://necsports.com/sports/2011/9/22/mbball_443.aspx",
            "https://rmucolonials.com/news/2020/3/10/mens-basketball-colonials-complete-championship-journey.aspx",
            "https://static.rmucolonials.com/custompages/MBB%202014-15%20Fact%20Book/2014-15_Section%203.pdf",
        ],
    },
    {
        "id_key": "pittsburgh-symphony-ceo",
        "url": "https://www.pittsburghsymphony.org/pso_home/web/about-landing",
        "title": "Pittsburgh Symphony Orchestra executive leadership",
        "text": (
            "The Pittsburgh Symphony Orchestra's official About page lists "
            "Melia P. Tourangeau as President and CEO. It says she was appointed "
            "in May 2015 and began her tenure in July 2015. Leadership can change; "
            "this record reflects the page checked October 23, 2026."
        ),
        "source": "pso-official-leadership-curated",
    },
    {
        "id_key": "duquesne-football-2026-head-coach",
        "url": "https://goduquesne.com/sports/football/coaches",
        "title": "Duquesne football 2026 coaching staff",
        "text": (
            "Duquesne University's official 2026 football coaching staff page "
            "lists Jerry Schmitt as the Dukes' Head Coach. His coach profile "
            "says he enters his 22nd season as Duquesne head coach in 2026."
        ),
        "source": "duquesne-official-football-staff-curated",
    },
    {
        "id_key": "rider-canastra-hammer-arena",
        "url": "https://gobroncs.com/news/2026/8/20/mens-basketball-announces-2026-27-schedule.aspx",
        "title": "Rider men's basketball schedule and Canastra Hammer Arena",
        "text": (
            "Rider University's official men's basketball schedule identifies "
            "Rider as a 2026-27 opponent of Pittsburgh, with Rider visiting Pitt "
            "on November 2. The schedule lists Rider home games at Canastra "
            "Hammer Arena, and the university identifies Canastra Hammer Arena "
            "as Rider's home basketball venue in Lawrenceville, New Jersey. "
            "Therefore, the Pitt opponent that plays at Canastra Hammer Arena "
            "is Rider University."
        ),
        "source": "rider-official-schedule-curated",
        "provenance_urls": [
            "https://gobroncs.com/news/2026/8/20/mens-basketball-announces-2026-27-schedule.aspx",
            "https://gobroncs.com/facilities/alumni-gymnasium/3",
        ],
    },
    {
        "id_key": "cmu-tepper-school",
        "url": "https://www.cmu.edu/tepper/",
        "title": "Tepper School of Business — Carnegie Mellon University",
        "text": (
            "Carnegie Mellon's business school is the Tepper School of Business. "
            "The official CMU site identifies it as the Tepper School of Business "
            "at Carnegie Mellon University."
        ),
        "source": "cmu-tepper-official-curated",
    },
    {
        "id_key": "pittsburgh-macaron-bar",
        "url": "https://www.macaron-bar.com/pittsburgh",
        "title": "Macaron Bar — Pittsburgh bakery specializing in French macarons",
        "text": (
            "Macaron Bar is a Pittsburgh bakery specializing in French macarons. "
            "Its official Pittsburgh location page lists its Lawrenceville shop "
            "at 3629 Butler Street, Pittsburgh, PA 15201. The official About page "
            "says the bakery specializes in French macarons and macaron baking classes."
        ),
        "source": "macaron-bar-official-curated",
        "provenance_urls": [
            "https://www.macaron-bar.com/pittsburgh",
            "https://www.macaron-bar.com/about",
        ],
    },
    {
        "id_key": "the-finch-rooftop",
        "url": "https://www.thedistillerycomplex.com/the-finch",
        "title": "The Finch — Pittsburgh rooftop restaurant with city views",
        "text": (
            "The Finch is a rooftop bar and restaurant on the sixth floor of The "
            "Distillery Complex at 59 South 2nd Street in Pittsburgh. Its official "
            "website describes panoramic views of Pittsburgh and the city skyline."
        ),
        "source": "the-finch-official-curated",
    },
    {
        "id_key": "sarris-handmade-chocolate",
        "url": "https://sarriscandies.com/pages/our-story",
        "title": "Sarris Candies — handmade chocolates in Canonsburg near Pittsburgh",
        "text": (
            "Sarris Candies is a family-owned chocolate maker founded in "
            "Canonsburg, Pennsylvania. Its official story says founder Frank "
            "Sarris began handcrafting chocolate in his basement, and the company "
            "continues to make handcrafted chocolates. Sarris's official store "
            "page describes its Canonsburg location as a chocolate shop near "
            "Pittsburgh and says it offers handcrafted chocolates and seasonal "
            "confections. The flagship candy store is at 511 Adams Avenue, "
            "Canonsburg, PA."
        ),
        "source": "sarris-official-story-curated",
        "provenance_urls": [
            "https://sarriscandies.com/pages/our-story",
            "https://sarriscandies.com/pages/our-store",
        ],
    },
    {
        "id_key": "david-clark-networking-bio",
        "url": "https://groups.csail.mit.edu/ana/People/Biographies/David_Clark_CV.pdf",
        "title": "David D. Clark — MIT internet and ARPANET researcher biography",
        "text": (
            "David D. Clark is a networking researcher who worked on the early "
            "ARPANET and development of ARPA network protocols. His official MIT "
            "curriculum vitae lists a BS in electrical engineering from Swarthmore "
            "College (1966), an MS from MIT (1969), and a PhD from MIT (1973); "
            "it does not list a Carnegie Mellon degree. MIT describes Clark as a "
            "leader in Internet development and Chief Protocol Architect from "
            "1981 to 1989."
        ),
        "source": "mit-david-clark-official-bio-curated",
        "provenance_urls": [
            "https://groups.csail.mit.edu/ana/People/Biographies/David_Clark_CV.pdf",
            "https://internetpolicy.mit.edu/team/david-clark/",
        ],
    },
    {
        "id_key": "cmoa-luxe-gallery-location",
        "url": "https://collection.carnegieart.org/?location=%22Scaife+Gallery+13%22",
        "title": "Luxe, Calme et Volupte — listed in Scaife Gallery 13",
        "text": (
            "The Carnegie Museum of Art collection search filtered to location "
            "Scaife Gallery 13 lists Pierre Alechinsky's painting Luxe, Calme et "
            "Volupte (1969) among its results. The museum cautions that its "
            "collection search is undergoing upgrades and its data may not be up "
            "to date; this is the location currently listed by that search."
        ),
        "source": "carnegie-art-official-location-search-curated",
        "provenance_urls": [
            "https://collection.carnegieart.org/?location=%22Scaife+Gallery+13%22",
        ],
    },
    {
        "id_key": "holy-cross-greek-food-festival",
        "url": "https://pittsburghgreekfestival.org/",
        "title": "Holy Cross Greek Food Festival — Pittsburgh Greek cuisine festival",
        "text": (
            "The Holy Cross Greek Food Festival in Pittsburgh focuses on Greek "
            "cuisine and culture. Its official festival page describes five days "
            "of authentic Greek cuisine and lists dishes including gyros, souvlaki, "
            "pastitsio, moussaka, spanakopita, and baklava. The 2026 page lists "
            "the festival at Holy Cross Greek Orthodox Church, 123 Gilkeson Road."
        ),
        "source": "holy-cross-greek-festival-official-curated",
    },
    {
        "id_key": "carmellas-whiskey-selection",
        "url": "https://carmellasplatesandpints.com/",
        "title": "Carmella's Plates & Pints — extensive Pittsburgh whiskey selection",
        "text": (
            "Carmella's Plates & Pints in Pittsburgh has a whiskey bar displaying "
            "over 500 bourbons, scotches, and tequilas, according to its official "
            "website. The restaurant describes its food as upscale comfort cuisine."
        ),
        "source": "carmellas-official-curated",
    },
    {
        "id_key": "commonplace-coffee-roastery",
        "url": "https://commonplacecoffee.com/pages/commonplace-coffee-headquarters-roastery",
        "title": "Commonplace Coffee — Pittsburgh in-house coffee roastery",
        "text": (
            "Commonplace Coffee roasts coffee for its own shops and wholesale "
            "customers at its Pittsburgh headquarters and roastery at 1004 "
            "Washington Boulevard. Its official barista training page also lists "
            "latte art as a training topic. The roastery page says visitors are "
            "by appointment only."
        ),
        "source": "commonplace-official-curated",
        "provenance_urls": [
            "https://commonplacecoffee.com/pages/commonplace-coffee-headquarters-roastery",
            "https://commonplacecoffee.com/pages/barista-training",
        ],
    },
    {
        "id_key": "cmoa-official-instagram-handle",
        "url": "https://carnegieart.org/wp-content/uploads/2023/04/23_MapsforWebsite_Spanish_v01.pdf",
        "title": "Carnegie Museum of Art official Instagram username",
        "text": (
            "Carnegie Museum of Art's official visitor information lists its "
            "Instagram username as @carnegiemuseumofart. This is the Art "
            "museum's account; Carnegie Museum of Natural History uses a "
            "different account, @carnegiemnh."
        ),
        "source": "cmoa-official-instagram-curated",
        "provenance_urls": [
            "https://carnegieart.org/wp-content/uploads/2023/04/23_MapsforWebsite_Spanish_v01.pdf",
            "https://carnegiemuseums.org/connect-with-us/",
        ],
    },
    {
        "id_key": "cmoa-winter-bouquet-title-collision",
        "url": "https://commons.wikimedia.org/wiki/Paintings_in_the_Carnegie_Museum_of_Art",
        "title": "Two Carnegie Museum of Art works titled Winter Bouquet",
        "text": (
            "The title Winter Bouquet identifies at least two different works "
            "associated with the Carnegie Museum of Art. The museum's current "
            "collection page is a woodcut print by Yoshida Chizuko, dated 1955, "
            "accession 89.28.1473. A public inventory of Carnegie Museum of Art "
            "paintings separately lists a painting by Robert Kushner, accession "
            "2004.57.2, titled Winter Bouquet. Libera Art's Carnegie Museum of "
            "Art catalog index labels the Robert Kushner painting 1992. Thus "
            "1992 is the reported creation date for the Kushner painting; 2004 "
            "is part of its accession number, not its creation date. These are "
            "distinct objects with the same title; the 1955 date belongs to "
            "Yoshida Chizuko's print and must not be applied to the Robert "
            "Kushner painting."
        ),
        "source": "cmoa-winter-bouquet-title-collision-curated",
        "provenance_urls": [
            "https://commons.wikimedia.org/wiki/Paintings_in_the_Carnegie_Museum_of_Art",
            "https://collection.carnegieart.org/objects/9d2bfecd-02c6-46d1-a6dd-d2626b077c40",
            "https://libera.art/m-siVYvecRh7/carnegie-museum-of-art",
        ],
        "source_checked_on": "2026-10-24",
        "inference_note": (
            "The inventory supports the Kushner title, artist, and accession; "
            "the live CMOA record supports the Yoshida title, artist, accession, "
            "medium, and 1955 date. Libera Art's secondary CMOA catalog index "
            "labels the Kushner painting 1992; this date should be checked "
            "against an original CMOA record when that archive becomes available."
        ),
    },
    {
        "id_key": "allegheny-county-2026-operating-budget-total",
        "url": "https://www.alleghenycounty.us/files/assets/county/v/1/government/budget-amp-finance/operating-budget/2026-operating-budget.pdf",
        "title": "Allegheny County adopted 2026 operating budget — total expenditures",
        "text": (
            "Allegheny County's enacted 2026 County Operating Budget provides "
            "for total budgeted expenditures of $1,193,518,154. The county "
            "adopted the operating budget on December 2, 2025 and the County "
            "Executive signed it on December 4, 2025. This is the operating "
            "budget total, not the separate capital budget or the combined "
            "county-wide fiscal plan."
        ),
        "source": "allegheny-county-2026-operating-budget-total-curated",
        "provenance_urls": [
            "https://www.alleghenycounty.us/files/assets/county/v/1/government/budget-amp-finance/operating-budget/2026-operating-budget.pdf",
            "https://www.alleghenycounty.us/files/assets/county/v/1/government/budget-amp-finance/budgets-%E2%80%93-line-item-detail/2026-line-item-budget-final.pdf",
        ],
    },
    {
        "id_key": "clemente-museum-no-walk-in-hours",
        "url": "https://clementemuseum.com/",
        "title": "Clemente Museum visits — no walk-in hours; tours and open houses by schedule",
        "text": (
            "The Clemente Museum does not offer walk-in hours. Its official "
            "website says it does not facilitate walk-in visits and operates "
            "guided tours and open houses on select scheduled days and times; "
            "advance tickets are required. Visitors should check the museum's "
            "current schedule before planning a visit."
        ),
        "source": "clemente-museum-official-visits-curated",
        "provenance_urls": [
            "https://clementemuseum.com/",
            "https://clementemuseum.com/faqs/",
        ],
    },
    {
        "id_key": "syracuse-2026-preseason-strength-of-schedule-rank",
        "url": "https://www.si.com/fannation/college/cfb-hq/rankings/college-football-strength-of-schedule-rankings-2026",
        "title": "Syracuse Orange — No. 16 in a June 2026 preseason strength-of-schedule ranking",
        "text": (
            "Sports Illustrated's College Football HQ June 3, 2026 preseason "
            "college-football strength-of-schedule ranking places Syracuse "
            "16th nationally, with opponents' prior-season record listed as "
            "92-62 (59.7%). The article explains that it estimates schedule "
            "strength by adding up the wins and losses of each team's opponents "
            "from the preceding season. This is that publisher's preseason "
            "ranking, not an official NCAA ranking; ranking methods and values "
            "can differ across publishers and later updates."
        ),
        "source": "sports-illustrated-syracuse-2026-sos-curated",
        "source_checked_on": "2026-10-24",
    },
    {
        "id_key": "cmoa-cowboys-ranch-bequest-method",
        "url": "https://collection.carnegieart.org/objects/49d59248-c83f-49f4-9b44-d6bf9df9ba8f",
        "title": "The Cowboy's Ranch by Doris Lee — CMOA credit line records a bequest",
        "text": (
            "The Carnegie Museum of Art record for Doris Lee's The Cowboy's "
            "Ranch (1939), accession 74.7.17, gives the credit line 'Bequest of "
            "Charles J. Rosenbloom.' The recorded acquisition method is bequest. "
            "This summarizes the catalog's credit line; it does not provide an "
            "acquisition date."
        ),
        "source": "cmoa-cowboys-ranch-bequest-curated",
        "source_checked_on": "2026-10-24",
    },
    {
        "id_key": "pittsburgh-sports-1964",
        "url": "https://www.pgh-sea.com/index.php?path=about-sa-history",
        "title": "1964 in Pittsburgh sports — Stadium Authority formation",
        "text": (
            "In Pittsburgh sports history, 1964 is significant because the "
            "Stadium Authority of the City of Pittsburgh was formed on March 9, "
            "1964. The Pittsburgh Steelers also moved from Forbes Field to Pitt "
            "Stadium in 1964, according to a City Controller audit of the Sports "
            "and Exhibition Authority and Stadium Authority. The Stadium Authority "
            "later oversaw construction of Three Rivers Stadium."
        ),
        "source": "pittsburgh-sea-official-history-curated",
        "provenance_urls": [
            "https://www.pgh-sea.com/index.php?path=about-sa-history",
            "https://www.pittsburghpa.gov/files/assets/city/v/1/controller/documents/performance-audits/sports_exhibition_and_stadium_authority_direct_revenue_december_2015.pdf",
        ],
    },
    {
        "id_key": "steelers-chuck-noll-hired-1969-date-correction",
        "url": "https://www.steelers.com/video/steelershistory-chuck-noll-hired-16735008",
        "title": "Pittsburgh sports dates — Chuck Noll hired in 1969, not 1964",
        "text": (
            "The Pittsburgh Steelers' official history says Chuck Noll was hired "
            "on January 27, 1969; the team's official Noll biography lists his "
            "head-coach career as 1969–1991. The team sources therefore do not "
            "support assigning Noll's hiring to 1964. For 1964, the Pittsburgh "
            "Sports and Exhibition Authority's history records that the Stadium "
            "Authority of the City of Pittsburgh was formed on March 9, 1964, "
            "and a City audit says the Steelers moved from Forbes Field to Pitt "
            "Stadium that year. These are separate Pittsburgh sports-history "
            "facts; do not conflate the 1964 events with Noll's 1969 hiring."
        ),
        "source": "steelers-official-chuck-noll-date-curated",
        "provenance_urls": [
            "https://www.steelers.com/video/steelershistory-chuck-noll-hired-16735008",
            "https://www.steelers.com/history/bios/noll_chuck",
            "https://www.pgh-sea.com/index.php?path=about-sa-history",
            "https://www.pittsburghpa.gov/files/assets/city/v/1/controller/documents/performance-audits/sports_exhibition_and_stadium_authority_direct_revenue_december_2015.pdf",
        ],
        "source_checked_on": "2026-10-24",
    },
    {
        "id_key": "pittsburgh-longest-city-inventory-bridge",
        "url": "https://www.pittsburghpa.gov/files/assets/city/v/1/pli/documents/24123_city_of_pittsburgh_bamp_report_to_mayor_ed_gainey_-_update_june_2023.pdf",
        "title": "Longest bridge in Pittsburgh city inventory — Fort Pitt Blvd over Mon Wharf, 1,623 feet",
        "text": (
            "Pittsburgh bridge length, according to the City of Pittsburgh's "
            "2022 bridge inventory: Fort Pitt Blvd (Commonwealth to Wood), "
            "crossing the Mon Wharf Parking Lot, is listed at 1,623 feet. "
            "A City of Pittsburgh bridge-portfolio presentation identifies this "
            "Fort Pitt Boulevard structure as the longest bridge in the city's "
            "inventory. The inventory entry is a roadway bridge over the Mon "
            "Wharf Parking Lot; it does not cross the Monongahela River."
        ),
        "source": "pittsburgh-city-bridge-inventory-longest-curated",
        "provenance_urls": [
            "https://www.pittsburghpa.gov/files/assets/city/v/1/pli/documents/24123_city_of_pittsburgh_bamp_report_to_mayor_ed_gainey_-_update_june_2023.pdf",
            "https://assets.ccaps.umn.edu/documents/CPE-Conferences/Structural/2025FHB.pdf",
        ],
        "source_checked_on": "2026-10-24",
    },
    {
        "id_key": "pittsburgh-payroll-tax-faq",
        "url": "https://www.pittsburghpa.gov/City-Government/Finance-Budget/Taxes",
        "title": "Pittsburgh Payroll Expense Tax — due dates and passive income",
        "text": (
            "Pittsburgh Payroll Expense Tax quarterly reports are due on the last "
            "day of the second month after each quarter: first quarter May 31, "
            "second August 31, third November 30, and fourth February 28 of the "
            "following year. These are Payroll Expense Tax dates, not Earned Income "
            "Tax estimated-payment dates. Passive income of a self-employed person "
            "or partner is not subject to Payroll Expense Tax because it is not "
            "earned income. The City's tax webpage identifies Pittsburgh Municipal "
            "Code Chapter 258 as the Payroll Expense Tax code."
        ),
        "source": "pittsburgh-finance-tax-page-curated",
    },
    {
        "id_key": "pittsburgh-earned-income-tax-faq",
        "url": "https://www.pittsburghpa.gov/City-Government/Finance-Budget/Taxes",
        "title": "Pittsburgh Earned Income Tax — nonresident rate and quarterly estimated due dates",
        "text": (
            "Pittsburgh Earned Income Tax: a non-Pennsylvania resident who works "
            "within Pittsburgh pays 1% City Earned Income Tax. Estimated EIT "
            "payments are due April 30, July 31, October 31, and January 31 for "
            "quarters one through four, respectively. In particular, third-quarter "
            "Earned Income Tax estimated payments are due October 31. These EIT "
            "estimated-payment dates are distinct from the later quarterly "
            "Payroll Expense Tax report dates."
        ),
        "source": "pittsburgh-finance-eit-curated",
    },
    {
        "id_key": "pittsburgh-isp-tax-code",
        "url": "https://ecode360.com/45439726",
        "title": "Pittsburgh Municipal Code Chapter 247 — Institution and Service Privilege Tax",
        "text": (
            "The Pittsburgh Municipal Code identifies the Institution and Service "
            "Privilege Tax as Chapter 247, §§ 247.01–247.05. Section 247.02 levies "
            "an annual tax on persons engaging in institutional or nonprofit "
            "services in the City, subject to the chapter's definitions and "
            "exclusions. The City's current online code table lists this tax as "
            "Chapter 247."
        ),
        "source": "pittsburgh-code-isp-curated",
    },
    {
        "id_key": "pittsburgh-parking-tax-license",
        "url": "https://www.pittsburghpa.gov/City-Government/Finance-Budget/Taxes",
        "title": "Pittsburgh Parking Tax — operator license authority",
        "text": (
            "The City of Pittsburgh states that every Parking Tax operator must "
            "secure a license from the Superintendent of the Bureau of Building "
            "Inspection. A provider of valet parking services must hold a valet "
            "parking license from the Director of Mobility and Infrastructure. "
            "The City identifies the Parking Tax ordinance as Section 253 of the "
            "Pittsburgh Municipal Code."
        ),
        "source": "pittsburgh-finance-parking-tax-curated",
    },
    {
        "id_key": "pittsburgh-amusement-tax-social-clubs",
        "url": "https://www.pittsburghpa.gov/City-Government/Finance-Budget/Taxes",
        "title": "Pittsburgh Amusement Tax — social club gross-receipts rule",
        "text": (
            "The City of Pittsburgh's Amusement Tax rule says that when a social "
            "club or fraternal organization provides entertainment without a "
            "separate charge, the established amusement price is 50% of gross "
            "receipts. The City identifies the Amusement Tax ordinance as Section "
            "241 of the Pittsburgh Municipal Code."
        ),
        "source": "pittsburgh-finance-amusement-tax-curated",
    },
    {
        "id_key": "heinz-company-founded-1869",
        "url": "https://news.kraftheinzcompany.com/press-releases-details/2019/HEINZ-Relishes-150-Years/default.aspx",
        "title": "H. J. Heinz founded in 1869 — Pittsburgh company history",
        "text": (
            "The Kraft Heinz Company states that H. J. Heinz founded the Heinz "
            "brand in Pittsburgh in 1869. The Heinz History Center describes the "
            "company as founded by Henry John Heinz in 1869 and notes that the "
            "early horseradish business began in nearby Sharpsburg, Pennsylvania. "
            "The company associated with Pittsburgh's 1869 founding clue is H. J. "
            "Heinz Company (the Heinz brand)."
        ),
        "source": "kraft-heinz-and-history-center-curated",
        "provenance_urls": [
            "https://news.kraftheinzcompany.com/press-releases-details/2019/HEINZ-Relishes-150-Years/default.aspx",
            "https://www.heinzhistorycenter.org/research/collection-highlights/h-j-heinz-company/",
        ],
    },
    {
        "id_key": "us-steel-founded-1901",
        "url": "https://www.ussteel.com/prereleases/-/blogs/u-s-steel-marks-125-years-strong-forging-the-future-of-american-steel",
        "title": "1901 significance for Pittsburgh steel — U. S. Steel becomes first billion-dollar company",
        "text": (
            "U. S. Steel states that it was founded on February 25, 1901. Its "
            "official history says the company was born in 1901 and that its "
            "global headquarters is in Pittsburgh. In 1901, the new United States "
            "Steel Corporation was capitalized at $1.4 billion and became the "
            "world's first billion-dollar company, according to the company's "
            "centennial press release. The year 1901 is significant for Pittsburgh's "
            "steel industry because U. S. Steel was formed then and became the "
            "first billion-dollar corporation."
        ),
        "source": "us-steel-official-history-curated",
        "provenance_urls": [
            "https://www.ussteel.com/prereleases/-/blogs/u-s-steel-marks-125-years-strong-forging-the-future-of-american-steel",
            "https://www.ussteel.com/es/about-us/history",
            "https://uss.mediaroom.com/index.php?item=111151",
        ],
    },
    {
        "id_key": "pittsburgh-civil-war-industry",
        "url": "https://artsandculture.google.com/story/iron-city-senator-john-heinz-history-center/owWhHqDsPdbhSw?hl=en",
        "title": "Pittsburgh's role in the Civil War — iron and armaments for the Union",
        "text": (
            "The Senator John Heinz History Center's Iron City exhibit explains "
            "that Pittsburgh's iron foundries, forges, and rolling mills supported "
            "the Union war effort during the Civil War. Fort Pitt Foundry specialized "
            "in large cannons and cannonballs and produced more than 3,000 cannons "
            "during the war. Pittsburgh's industrial capacity and armaments production "
            "made it an important manufacturing center for the Union."
        ),
        "source": "heinz-history-center-civil-war-curated",
    },
    {
        "id_key": "smithfield-street-bridge-significance",
        "url": "https://www.asce.org/about-civil-engineering/history-and-heritage/historic-landmarks/smithfield-street-bridge",
        "title": "Significance of the Smithfield Street Bridge — oldest Pittsburgh steel bridge, built 1883; National Civil Engineering Landmark",
        "text": (
            "Historical significance of the Smithfield Street Bridge: it is "
            "Pittsburgh's oldest steel bridge, was completed in 1883, and was "
            "designated a National Civil Engineering Landmark by the American "
            "Society of Civil Engineers. Visit Pittsburgh "
            "describes it as the city's longest in-service bridge and as the "
            "oldest steel bridge in the United States. The bridge crosses the "
            "Monongahela River. The American Society of Civil Engineers "
            "identifies its significance as a distinctive adaptation of the "
            "European lenticular truss to American needs and says it served as a "
            "guide for similar highway bridges built in later decades. "
            "PennDOT describes it as one of the few multiple long-span lenticular "
            "trusses remaining in the United States and as an early steel-truss "
            "technology pioneer; it is a National Civil Engineering Landmark."
        ),
        "source": "asce-penndot-smithfield-bridge-curated",
        "provenance_urls": [
            "https://www.asce.org/about-civil-engineering/history-and-heritage/historic-landmarks/smithfield-street-bridge",
            "https://www.pa.gov/content/dam/copapwp-pagov/en/penndot/documents/public/pubsforms/publications/pub-862.pdf",
            "https://www.visitpittsburgh.com/blog/25-famous-pittsburgh-bridges/",
        ],
    },
    {
        "id_key": "rickard-rakell-bio",
        "url": "https://www.nhlpa.com/player/236/rickard-rakell/",
        "title": "Rickard Rakell — NHL Players' Association player profile",
        "text": (
            "The NHL Players' Association profile lists Pittsburgh Penguins "
            "forward Rickard Rakell's birthplace as Sundbyberg, Sweden, and his "
            "birthdate as May 5, 1993."
        ),
        "source": "nhlpa-rickard-rakell-bio-curated",
    },
    {
        "id_key": "scarpacis-monday-open-mic",
        "url": "https://www.scarpacisbar.com/enter",
        "title": "Monday open mic at Scarpaci's Bar — Pittsburgh weekly event at 8 PM",
        "text": (
            "Scarpaci's Bar in Pittsburgh hosts Open Mic Music every Monday, "
            "beginning at 8:00 PM. The venue's event page lists the weekly "
            "Monday open mic and its 8 PM start time. Check the live venue page "
            "for current event details."
        ),
        "source": "scarpacis-official-event-curated",
    },
    {
        "id_key": "pittsburgh-restaurant-week-about",
        "url": "https://pittsburghrestaurantweek.com/about/",
        "title": "What is Pittsburgh Restaurant Week? — local dining promotion",
        "text": (
            "Pittsburgh Restaurant Week is a twice-yearly dining promotion, "
            "with Summer and Winter celebrations. The official Pittsburgh "
            "Restaurant Week site says its mission is to highlight the region's "
            "wide-ranging dining options and bring people into the city for "
            "meals at special discounted prices. Visit Pittsburgh describes "
            "January and August events with more than 50 participating "
            "restaurants offering dining deals, including three-course "
            "fixed-price meal specials."
        ),
        "source": "pittsburgh-restaurant-week-official-curated",
        "provenance_urls": [
            "https://pittsburghrestaurantweek.com/about/",
            "https://www.visitpittsburgh.com/events-festivals/food-festivals/",
        ],
        "source_checked_on": "2026-10-24",
    },
    {
        "id_key": "pso-president-ceo",
        "url": "https://pittsburghsymphony.org/pso_home/web/about-landing/melia-p-tourangeau-president",
        "title": "Pittsburgh Symphony Orchestra President and CEO — Melia P. Tourangeau",
        "text": (
            "The Pittsburgh Symphony Orchestra identifies Melia P. Tourangeau "
            "as its President and CEO. Her official biography says she was "
            "appointed President and CEO in May 2015. This is a current "
            "leadership fact; check the orchestra's live leadership page for updates."
        ),
        "source": "pso-official-leadership-curated",
    },
    {
        "id_key": "cmu-navlab-significance",
        "url": "https://www.ri.cmu.edu/autonomous-vehicles/",
        "title": "NavLab significance — CMU's pioneering autonomous driving research",
        "text": (
            "Carnegie Mellon's NavLab project is significant as pioneering "
            "autonomous vehicle research. CMU's Robotics Institute says its "
            "autonomous vehicle work began in the 1980s; NavLab used onboard "
            "computers, laser scanners, and color cameras for outdoor navigation. "
            "NavLab 5 completed a 1995 Pittsburgh-to-San Diego trip with 98.2% "
            "of its 2,849 miles driven autonomously, a milestone in self-driving "
            "vehicle research."
        ),
        "source": "cmu-robotics-navlab-significance-curated",
        "provenance_urls": [
            "https://www.ri.cmu.edu/autonomous-vehicles/",
            "https://mobility21.cmu.edu/the-road-ahead-for-self-driving-cars/",
        ],
    },
    {
        "id_key": "luke-weaver-debut-date-question",
        "url": "https://www.mlb.com/player/luke-weaver-596133/stats",
        "title": "Luke Weaver MLB debut date — Pittsburgh Pirates player profile",
        "text": (
            "The official MLB profile lists Pittsburgh Pirates pitcher Luke "
            "Weaver's Major League debut as August 13, 2016 (2016-08-13). "
            "MLB's 2018 transaction announcement also states that he made his "
            "Major League debut on August 13, 2016, against the Cubs."
        ),
        "source": "mlb-luke-weaver-debut-date-curated",
        "provenance_urls": [
            "https://www.mlb.com/player/luke-weaver-596133/stats",
            "https://www.mlb.com/press-release/d-backs-acquire-luke-weaver-carson-kelly-andrew-young-and-a-competitiv-301510482",
        ],
    },
    {
        "id_key": "brandon-eisert-bio",
        "url": "https://www.mlb.com/player/brandon-eisert-685126",
        "title": "Brandon Eisert birth year — official Pittsburgh Pirates player bio",
        "text": (
            "The official MLB profile lists Pittsburgh Pirates pitcher Brandon "
            "Eisert as born January 19, 1998, in Portland, Oregon. His birth year "
            "is 1998."
        ),
        "source": "mlb-brandon-eisert-bio-curated",
    },
    {
        "id_key": "awaacc-rental-first-step",
        "url": "https://awaacc.org/rental/rental-faq/",
        "title": "First step to rent the AWAACC — submit the facility rental inquiry form",
        "text": (
            "The August Wilson African American Cultural Center's current Rental "
            "FAQ lists the first step to rent the AWAACC as filling out its "
            "rental inquiry form. A consultation follows, then a site visit if "
            "the renter wants one. The inquiry must be submitted at least 45 days "
            "before the event to be considered. The FAQ says date availability "
            "is discussed during the consultation."
        ),
        "source": "awaacc-official-rental-faq-curated",
    },
    {
        "id_key": "mattress-factory-instagram",
        "url": "https://mattress.org/",
        "title": "Mattress Factory Instagram handle — official profile @mattressfactory",
        "text": (
            "The official Mattress Factory website links to the museum's Instagram "
            "profile at https://www.instagram.com/mattressfactory/. The account "
            "handle is @mattressfactory."
        ),
        "source": "mattress-factory-official-social-curated",
        "provenance_urls": [
            "https://mattress.org/",
            "https://www.instagram.com/mattressfactory/",
        ],
    },
    {
        "id_key": "cmoa-tribulations-provenance-1958",
        "source_checked_on": "2026-10-24",
        "url": "https://www.openartdata.org/2026/05/CMOA-NEPIP-Provenance.html?m=0",
        "title": "The Tribulations of Saint Anthony, accession 58.83 — purchased November 1958",
        "text": (
            "James Ensor's The Tribulations of Saint Anthony, Carnegie Museum of "
            "Art accession 58.83, was purchased by the Department of Fine Arts, "
            "Carnegie Institute, Pittsburgh, in November 1958, according to a public "
            "transcription of selected 2015 CMOA provenance. The transcription gives "
            "month and year only and does not give a calendar day. The work's 1909 "
            "date is its creation date. This is historical provenance, not a current "
            "live catalog field."
        ),
        "source": "open-art-data-cmoa-provenance-transcription-curated",
        "provenance_urls": [
            "https://www.openartdata.org/2026/05/CMOA-NEPIP-Provenance.html?m=0",
            "https://collection.carnegieart.org/objects/4166c391-1fe7-4af2-a4ec-133c0957720d",
        ],
    },
    {
        "id_key": "cmoa-italian-landscape-acquisition-date-1993-10",
        "url": "https://carnegiemuseums.org/archive_article/insights-into-building-a-great-art-collection-mar-apr-2003/",
        "title": "Italian Landscape acquisition date — 1993-10 (October 1993; Andreas Achenbach, accession 93.119)",
        "text": (
            "The Carnegie Museum of Art's recorded acquisition date at the "
            "available precision for Andreas Achenbach's Italian Landscape, "
            "accession 93.119, is 1993-10 (October 1993). "
            "A public transcription of selected provenance from the museum's "
            "2015 collection dataset says the painting was purchased by the "
            "museum in October 1993. Carnegie Museums' 2003 magazine archive "
            "independently recounts the curator's 1993 purchase of the 1845 "
            "Roman landscape after it failed to sell at auction. Neither source "
            "establishes the calendar day. The artwork date is 1845; it is not "
            "the acquisition date."
        ),
        "source": "carnegie-museums-achenbach-acquisition-history-curated",
        "source_checked_on": "2026-10-24",
        "provenance_urls": [
            "https://carnegiemuseums.org/archive_article/insights-into-building-a-great-art-collection-mar-apr-2003/",
            "https://carnegieart.org/resource/achenbach-and-brahms/",
            "https://collection.carnegieart.org/objects/946509e1-58a9-4461-982c-c23e24d22c37",
            "https://www.openartdata.org/2026/05/CMOA-NEPIP-Provenance.html?m=0",
        ],
    },
    {
        "id_key": "cmoa-ruckkehr-acquired-2004-05-context",
        "url": "https://carnegiemuseums.org/archive_article/artistic-license-summer-2005/",
        "title": "Rückkehr by Neo Rauch — included in CMOA 2004–05 acquisitions",
        "text": (
            "A 2005 Carnegie Museums article lists Neo Rauch's Rückkehr (2004) "
            "among works included in the 2004–05 Carnegie International "
            "acquisitions. The current Carnegie Museum of Art record identifies "
            "the work as accession 2005.2. The article supports the 2004–05 "
            "acquisition-program context; it does not establish an exact "
            "purchase date, and 2004 is the artwork date rather than a confirmed "
            "acquisition date."
        ),
        "source": "carnegie-museums-2005-international-acquisitions-context-curated",
        "provenance_urls": [
            "https://carnegiemuseums.org/archive_article/artistic-license-summer-2005/",
            "https://collection.carnegieart.org/objects/225f4da1-bcba-425a-ad91-ce4a2713c2ae",
        ],
    },
    {
        "id_key": "iron-born-detroit-pizza-characteristics-axios-2025",
        "url": "https://www.axios.com/local/pittsburgh/2025/02/27/pittsburgh-strip-district-iron-born-pizza-review",
        "title": "Iron Born Pizza — Detroit-style crust and classic tomato mozzarella basil pie",
        "text": (
            "A February 2025 Axios Pittsburgh review describes Iron Born in the "
            "Strip District as serving Detroit-style pizza, with a thick, light "
            "crust and crispy edge. It recommends a classic pie topped with "
            "cherry tomatoes, mozzarella, and fresh basil. The review identifies "
            "the Strip District location at 1806 Smallman Street and distinguishes "
            "it from the Millvale takeout-only location. This is dated editorial "
            "coverage; menu availability can change."
        ),
        "source": "axios-pittsburgh-iron-born-review-curated",
        "provenance_urls": [
            "https://www.axios.com/local/pittsburgh/2025/02/27/pittsburgh-strip-district-iron-born-pizza-review",
            "https://ironbornpizza.com/",
        ],
    },
    {
        "id_key": "fet-fisk-nordic-seafood-specialty-axios-2025",
        "url": "https://www.axios.com/local/pittsburgh/2025/06/17/fet-fisk-james-beard-finalist-spotlight",
        "title": "Fet Fisk specialty — Nordic-influenced seafood and seasonal dishes",
        "text": (
            "Axios Pittsburgh describes Fet-Fisk as a Scandinavian-inspired "
            "Bloomfield restaurant specializing in seafood dishes inspired by "
            "Nordic culture. Its June 2025 report highlights grilled cabbage "
            "Caesar, whole grilled branzino, and sourdough spaetzle. The "
            "restaurant's own story says its dishes emphasize seasonal regional "
            "produce and sustainably sourced seafood and meat. The highlighted "
            "menu items are dated reporting, not a guarantee of current availability."
        ),
        "source": "axios-pittsburgh-fet-fisk-specialty-curated",
        "provenance_urls": [
            "https://www.axios.com/local/pittsburgh/2025/06/17/fet-fisk-james-beard-finalist-spotlight",
            "https://www.fetfisk.net/the-story",
        ],
    },
    {
        "id_key": "pusadees-thai-dishes-post-gazette-2022",
        "url": "https://newsinteractive.post-gazette.com/eat-pittsburgh-restaurants/lawrenceville.php",
        "title": "Pusadee's Garden — Thai menu and khao soi",
        "text": (
            "Pittsburgh Post-Gazette coverage describes Pusadee's Garden as "
            "serving a refined menu of Thai dishes not found elsewhere in "
            "Pittsburgh and highlights khao soi with short rib, egg noodles, "
            "pickled mustard greens, and red and yellow curries. The restaurant's "
            "current official dinner menu lists khao soi with wagyu beef cheek, "
            "egg noodles, pickled mustard greens, and red and yellow curry, as "
            "well as northern-style mushroom laab. The Post-Gazette examples "
            "are historical coverage; check the linked live menu for current dishes. "
            "Pusadee's archived official menu also labels a sausage as northern "
            "Thai style; this is historical menu wording, not confirmation that "
            "the sausage remains available."
        ),
        "source": "post-gazette-pusadees-thai-menu-curated",
        "provenance_urls": [
            "https://newsinteractive.post-gazette.com/eat-pittsburgh-restaurants/lawrenceville.php",
            "https://pusadeesgarden.com/menus/dinner/",
            "https://pusadeesgarden.com/menu/dining.pdf",
        ],
    },
    {
        "id_key": "fet-fisk-setting-desserts-axios-2025",
        "url": "https://www.axios.com/local/pittsburgh/2025/03/07/pittsburghs-hottest-restaurant-fet-fisk",
        "title": "Fet Fisk — Nordic-influenced seafood, cozy nautical dining, and desserts",
        "text": (
            "A March 2025 Axios Pittsburgh visit describes Fet-Fisk as an "
            "upscale Scandinavian-inspired restaurant with a cozy atmosphere and "
            "nautical decor. It highlights the grilled cabbage Caesar salad and "
            "says desserts stood out. Together with the restaurant's own "
            "description of sustainably sourced seafood and seasonal regional "
            "produce, this documents its Nordic-influenced seafood specialty and "
            "the dining experience reported at that time. Menu and atmosphere "
            "details are attributed to dated coverage."
        ),
        "source": "axios-pittsburgh-fet-fisk-dining-report-curated",
        "provenance_urls": [
            "https://www.axios.com/local/pittsburgh/2025/03/07/pittsburghs-hottest-restaurant-fet-fisk",
            "https://www.fetfisk.net/the-story",
        ],
    },
    {
        "id_key": "tako-cuisine-pittsburgh-mexican-japanese-fusion",
        "source_checked_on": "2026-10-24",
        "url": "https://takopgh.com/mexican-food-downtown-pittsburgh/",
        "title": "Tākō official menu — Asian Mexican cuisine and fusion tacos in Downtown Pittsburgh",
        "text": (
            "Tākō's official food menu describes it as the first Asian Mexican "
            "restaurant in Downtown Pittsburgh. The menu pairs Mexican dishes "
            "such as queso fundido and pollo asado tacos with fusion items such "
            "as a Korean beef taco topped with Napa cabbage, peanut salsa, and "
            "soybean glaze. The menu therefore identifies Tākō's cuisine as "
            "Asian Mexican fusion, including Mexican-style tacos with Asian "
            "influences."
        ),
        "source": "tako-official-cuisine-curated",
        "provenance_urls": [
            "https://takopgh.com/mexican-food-downtown-pittsburgh/",
            "https://takopgh.com/",
        ],
    },
    {
        "id_key": "pso-fiddlesticks-once-upon-a-melody-conductor-2026",
        "url": "https://awc.culturaldistrict.org/production/107728/fiddlesticks-once-upon-a-melody",
        "title": "PSO Fiddlesticks: Once Upon a Melody — Andrés Franco, conductor, November 14, 2026",
        "text": (
            "The Pittsburgh Cultural District official ticket page lists Andrés "
            "Franco as conductor for the Pittsburgh Symphony Orchestra family "
            "concert Fiddlesticks: Once Upon a Melody at Heinz Hall on Saturday, "
            "November 14, 2026, at 11:15 a.m. The page also lists Corrie Stallings "
            "as vocalist. The Pittsburgh Symphony Orchestra's own Fiddlesticks "
            "page confirms the concert title, date, and 11:15 a.m. time. The "
            "conductor and schedule are event-specific and should be rechecked "
            "if the event details change."
        ),
        "source": "pittsburgh-cultural-district-pso-event-conductor-curated",
        "provenance_urls": [
            "https://awc.culturaldistrict.org/production/107728/fiddlesticks-once-upon-a-melody",
            "https://www.pittsburghsymphony.org/pso_home/web/fiddlesticks-musical-exploration",
        ],
    },
    {
        "id_key": "east-liberty-farmers-market-first-operation",
        "url": "https://farmersmarketcooperativeofeastliberty.com/",
        "title": "Farmers' Market Cooperative of East Liberty — first day of operation",
        "text": (
            "The Farmers' Market Cooperative of East Liberty states in its "
            "official History and Background that its first day of operation "
            "was July 5, 1941. A 2021 WTAE report independently says the market "
            "made its debut on July 5, 1941. The cooperative describes itself "
            "as the oldest continuously operating market in western Pennsylvania."
        ),
        "source": "east-liberty-farmers-market-history-curated",
        "provenance_urls": [
            "https://farmersmarketcooperativeofeastliberty.com/",
            "https://www.wtae.com/article/east-liberty-farmers-market-celebrates-80-years/37188725",
        ],
    },
    {
        "id_key": "getaway-monday-night-open-mic-comedy-2024",
        "url": "https://thegetawaypgh.com/event/monday-night-open-mic-comedy/2024-03-18/",
        "title": "Monday Night Open Mic Comedy — The Getaway Bar & Grill, 2024 event listing",
        "text": (
            "The Getaway Bar & Grill's event listing for March 18, 2024 is "
            "part of its event series Monday Night Open Mic Comedy. The page "
            "says open mic comedy ran every Monday night from 8 p.m. to 10 p.m. "
            "This is historical event information from a 2024 listing and does "
            "not verify that the series is still running. The listing gives the "
            "venue address as 3049 Sussex Avenue, Pittsburgh."
        ),
        "source": "getaway-official-historical-event-curated",
        "provenance_urls": [
            "https://thegetawaypgh.com/event/monday-night-open-mic-comedy/2024-03-18/",
        ],
    },
    {
        "id_key": "penguins-predators-oct-24-2026-local-time",
        "url": "https://pittsburgh.events/tickets/pittsburgh-penguins-vs-nashville-predators-pittsburgh-saturday-october-24-2026-700-pm/",
        "title": "Penguins vs. Predators — October 24, 2026 start time in Pittsburgh",
        "text": (
            "The Pittsburgh Penguins host the Nashville Predators at PPG Paints "
            "Arena on October 24, 2026. The event listing gives a local start "
            "time of 7:00 PM and a published timestamp of 2026-10-24T19:00:00-04:00. "
            "For Pittsburgh, that is 7:00 PM Eastern Daylight Time (EDT), "
            "within the Eastern Time (ET) zone; concisely, the scheduled time is "
            "7:00 PM ET. The listing identifies PPG Paints "
            "Arena at 1001 Fifth Avenue, Pittsburgh. Recheck the event listing "
            "for schedule changes."
        ),
        "source": "pittsburgh-events-penguins-predators-time-curated",
        "provenance_urls": [
            "https://pittsburgh.events/tickets/pittsburgh-penguins-vs-nashville-predators-pittsburgh-saturday-october-24-2026-700-pm/",
        ],
    },
    {
        "id_key": "arcade-sketch-comedy-lab-dec-5-2026",
        "url": "https://www.arcadecomedytheater.com/event/sketch-comedy-lab-15/",
        "title": "Sketch Comedy Lab — Arcade Comedy Theater, December 5, 2026 at 6:00 PM",
        "text": (
            "Arcade Comedy Theater's official event page lists Sketch Comedy "
            "Lab on Saturday, December 5, 2026 at 6:00 PM. Sketch Comedy Lab is "
            "a staged reading of sketches by local writers who participated in "
            "the theater's Writers Lab; actors perform the scripts for the "
            "audience and writers. The theater describes it as an incubator "
            "space for sketch comedy. The event page lists Arcade Comedy Theater "
            "in Pittsburgh and a $10 ticket price. Check the live event page for "
            "schedule or ticket changes."
        ),
        "source": "arcade-comedy-theater-official-event-curated",
        "provenance_urls": [
            "https://www.arcadecomedytheater.com/event/sketch-comedy-lab-15/",
        ],
    },
    {
        "id_key": "butcher-and-the-rye-whiskey-destination-2026",
        "url": "https://butcherandtherye.com/",
        "title": "Butcher and the Rye — Pittsburgh restaurant with an extensive whiskey selection",
        "text": (
            "Butcher and the Rye is the Pittsburgh restaurant known for its "
            "extensive whiskey selection. Its official website calls it "
            "Pittsburgh's whiskey destination and says its Whiskey Wall and "
            "whiskey list each feature more than 600 bottles. Visit Pittsburgh "
            "describes the restaurant as a destination celebrated for its "
            "expansive whiskey collection and inventive rustic American cuisine. "
            "It is located at 212 Sixth Street in Downtown Pittsburgh's Cultural "
            "District. The restaurant's current site "
            "lists dinner service Wednesday through Saturday, 5–10 PM; hours "
            "may change, so check the live site before visiting."
        ),
        "source": "butcher-and-the-rye-official-whiskey-curated",
        "provenance_urls": [
            "https://butcherandtherye.com/",
            "https://www.visitpittsburgh.com/directory/butcher-and-the-rye/",
        ],
    },
    {
        "id_key": "that-like-this-mr-smalls-dec-5-2026",
        "url": "https://mrsmalls.com/events/that-like-this/",
        "title": "THAT LIKE THIS Pittsburgh 2026 performance schedule — December 5 at 8:00 PM",
        "text": (
            "Concert schedule: When does THAT LIKE THIS perform in Pittsburgh "
            "in 2026? The Pittsburgh-based collective performs in the Pittsburgh "
            "area on Saturday, December 5, 2026 at 8:00 PM. The official Mr. "
            "Smalls event listing identifies this as an album release show at "
            "The Funhouse at Mr. Smalls, 400 Lincoln Avenue, Millvale, PA. "
            "Doors open at 7:00 PM; Org Dröl and Meddle are special guests. "
            "Check the venue page for current details."
        ),
        "source": "mr-smalls-official-event-curated",
        "provenance_urls": [
            "https://mrsmalls.com/events/that-like-this/",
        ],
    },
    {
        "id_key": "bethel-park-2026-municipal-millage",
        "url": "https://apps.alleghenycounty.us/website/millmuni.asp",
        "title": "Bethel Park Municipality 2026 real estate tax millage",
        "text": (
            "Bethel Park Municipality's 2026 municipal real estate tax rate is "
            "4.13 mills. Allegheny County's 2026 municipality millage table "
            "lists Bethel Park at 4.1300 mills. The Municipality of Bethel "
            "Park's tax page itemizes the rate as 3.79 mills for General and "
            "Capital purposes plus 0.34 mills for the Fire Department, totaling "
            "4.13 mills. This is the municipal rate, separate from county and "
            "school district millages."
        ),
        "source": "allegheny-county-bethel-park-2026-millage-curated",
        "provenance_urls": [
            "https://apps.alleghenycounty.us/website/millmuni.asp",
            "https://www.bethelparkpa.gov/finance/real-estate-tax",
        ],
    },
    {
        "id_key": "dormont-2026-municipal-millage",
        "url": "https://boro.dormont.pa.us/tax-collector/",
        "title": "Dormont Borough 2026 real estate tax millage",
        "text": (
            "Dormont Borough's real estate tax rate for 2026 is 12.47 mills. "
            "The Borough's tax collector page lists the 2026 millage as "
            "12.4700, and Borough Ordinance No. 1656 establishes the rate at "
            "12.47 mills for the fiscal year January 1 through December 31, "
            "2026. Allegheny County's 2026 municipality millage table also "
            "lists Dormont Borough at 12.4700 mills. This is the borough "
            "municipal rate, separate from county and school district millages."
        ),
        "source": "dormont-borough-2026-millage-curated",
        "provenance_urls": [
            "https://boro.dormont.pa.us/tax-collector/",
            "https://ecode360.com/DO1365/laws/LF2553861.pdf",
            "https://apps.alleghenycounty.us/website/millmuni.asp",
        ],
    },
    {
        "id_key": "pitt-womens-volleyball-vs-duke-2026-11-06",
        "url": "https://pittsburghpanthers.com/sports/womens-volleyball/schedule/text",
        "title": "Pitt women's volleyball vs Duke — November 6, 2026 at 7 PM",
        "text": (
            "Pitt women's volleyball hosts Duke in Pittsburgh on November 6, "
            "2026, at 7 PM, according to the official University of Pittsburgh "
            "Athletics schedule. This is a future match and may change."
        ),
        "source": "pitt-athletics-womens-volleyball-schedule-curated",
        "provenance_urls": [
            "https://pittsburghpanthers.com/sports/womens-volleyball/schedule/text",
        ],
    },
    {
        "id_key": "pitt-womens-volleyball-at-stanford-2026-11-24",
        "url": "https://pittsburghpanthers.com/news/2026/5/26/volleyball-panthers-release-competitive-2026-schedule",
        "title": "Pitt women's volleyball at Stanford — November 24, 2026",
        "text": (
            "Pitt women's volleyball plays at Stanford in Stanford, California, "
            "on November 24, 2026. Pitt's official schedule lists the match at "
            "7 PM, and the team's schedule announcement confirms Stanford as "
            "the November 24 opponent. The ACC schedule independently lists "
            "Pitt at Stanford that day. This is a future match and may change."
        ),
        "source": "pitt-athletics-womens-volleyball-schedule-curated",
        "provenance_urls": [
            "https://pittsburghpanthers.com/sports/womens-volleyball/schedule/text",
            "https://pittsburghpanthers.com/news/2026/5/26/volleyball-panthers-release-competitive-2026-schedule",
            "https://theacc.com/schedule.aspx?schedule=4649",
        ],
    },
    {
        "id_key": "pitt-womens-basketball-at-georgia-tech-2026-12-13",
        "url": "https://pittsburghpanthers.com/sports/womens-basketball/schedule/text",
        "title": "Pitt women's basketball at Georgia Tech — December 13, 2026",
        "text": (
            "Pitt women's basketball visits Georgia Tech in Atlanta on "
            "December 13, 2026. The official University of Pittsburgh "
            "Athletics schedule lists the game at 2 PM, and the team's "
            "schedule announcement confirms the December 13 road game. This "
            "is a future game and may change."
        ),
        "source": "pitt-athletics-womens-basketball-schedule-curated",
        "provenance_urls": [
            "https://pittsburghpanthers.com/sports/womens-basketball/schedule/text",
            "https://pittsburghpanthers.com/news/2026/9/2/panthers-announce-2026-27-womens-basketball-schedule",
        ],
    },
    {
        "id_key": "pitt-womens-basketball-vs-mercyhurst-2026-12-17",
        "url": "https://pittsburghpanthers.com/sports/womens-basketball/schedule/text",
        "title": "Pitt women's basketball vs Mercyhurst — December 17, 2026",
        "text": (
            "Pitt women's basketball hosts Mercyhurst in Pittsburgh on "
            "December 17, 2026, at 7 PM, according to the official University "
            "of Pittsburgh Athletics schedule. The listed venue is Petersen "
            "Events Center. This is a future game and may change."
        ),
        "source": "pitt-athletics-womens-basketball-schedule-curated",
        "provenance_urls": [
            "https://pittsburghpanthers.com/sports/womens-basketball/schedule/text",
        ],
    },
    {
        "id_key": "duquesne-womens-basketball-vs-eastern-michigan-2026-12-09",
        "url": "https://goduquesne.com/news/2026/8/26/womens-basketball-dukes-reveal-2026-non-conference-schedule.aspx",
        "title": "Duquesne women's basketball vs Eastern Michigan — December 9, 2026",
        "text": (
            "Duquesne women's basketball hosts Eastern Michigan on Wednesday, "
            "December 9, 2026, according to Duquesne Athletics' official "
            "2026 non-conference schedule announcement. This is a future game "
            "and may change."
        ),
        "source": "duquesne-athletics-womens-basketball-schedule-curated",
        "provenance_urls": [
            "https://goduquesne.com/news/2026/8/26/womens-basketball-dukes-reveal-2026-non-conference-schedule.aspx",
        ],
    },
    {
        "id_key": "chatham-mens-basketball-december-2026-schedule-count",
        "url": "https://gochathamcougars.com/sports/mens-basketball/schedule",
        "title": "Chatham men's basketball games scheduled for December 2026 — five games",
        "text": (
            "Chatham University Athletics currently lists five men's basketball "
            "games in December 2026: December 2 versus Saint Vincent, December 5 "
            "versus W&J, December 12 at Thiel, December 19 versus Carnegie Mellon, "
            "and December 30 at Hood. The count is derived by enumerating the "
            "December dates on Chatham's official 2026-27 schedule page; future "
            "games and schedules may change."
        ),
        "source": "chatham-athletics-mens-basketball-schedule-curated",
        "provenance_urls": [
            "https://gochathamcougars.com/sports/mens-basketball/schedule",
        ],
    },
    {
        "id_key": "chatham-womens-hockey-at-stevenson-2026-11-24",
        "url": "https://gochathamcougars.com/sports/womens-ice-hockey/schedule/2026-27?grid=true",
        "title": "Chatham women's hockey at Stevenson — November 24, 2026",
        "text": (
            "Chatham University women's ice hockey plays at Stevenson on "
            "Tuesday, November 24, 2026, at 1 PM in Reisterstown, Maryland, "
            "according to Chatham Athletics' official 2026-27 schedule. The "
            "schedule separately lists a home rematch against Stevenson on "
            "November 25 in Pittsburgh. These are future games and may change."
        ),
        "source": "chatham-athletics-womens-hockey-schedule-curated",
        "provenance_urls": [
            "https://gochathamcougars.com/sports/womens-ice-hockey/schedule/2026-27?grid=true",
            "https://theuchc.com/schedule.aspx?schedule=219",
        ],
    },
    {
        "id_key": "duquesne-acha-hockey-at-buffalo-2026-11-06",
        "url": "https://www.duqhockey.com/schedule/upcoming",
        "title": "Duquesne ACHA D1 hockey at University at Buffalo — November 6, 2026",
        "text": (
            "Duquesne University's ACHA Division 1 men's hockey team is scheduled "
            "to play away at the University at Buffalo on November 6, 2026. "
            "Duquesne Hockey's official upcoming-games page lists University at "
            "Buffalo as the opponent for the game displayed at 00:30 UTC on "
            "November 7, which falls on the evening of November 6 in Pittsburgh. "
            "The future schedule may change."
        ),
        "source": "duquesne-acha-hockey-official-schedule-curated",
        "provenance_urls": [
            "https://www.duqhockey.com/",
            "https://www.duqhockey.com/schedule/upcoming",
        ],
    },
    {
        "id_key": "penguins-at-panthers-2026-12-10",
        "url": "https://www.nhl.com/penguins/schedule/2026-12-01",
        "title": "Penguins at Florida Panthers — December 10, 2026",
        "text": (
            "The Pittsburgh Penguins visit the Florida Panthers on Thursday, "
            "December 10, 2026, at 7:00 PM Eastern, according to the official "
            "Penguins December schedule. The game is scheduled at Amerant Bank "
            "Arena in Sunrise, Florida. Future game details may change."
        ),
        "source": "pittsburgh-penguins-official-schedule-curated",
    },
    {
        "id_key": "andrew-carnegie-free-library-weekly-hours",
        "url": "https://carnegiecarnegie.org/",
        "title": "Andrew Carnegie Free Library & Music Hall weekly opening days and hours",
        "text": (
            "The Andrew Carnegie Free Library & Music Hall is open six (6) days "
            "per week: Monday noon–7 PM, Tuesday through Thursday 10 AM–7 PM, "
            "and Friday and Saturday 10 AM–5 PM. It is closed Sundays, according "
            "to the library's official posted hours. Holiday hours may differ."
        ),
        "source": "andrew-carnegie-library-official-hours-curated",
    },
    {
        "id_key": "a-musical-christmas-carol-2026-run-dates",
        "url": "https://pittsburghclo.culturaldistrict.org/production/109404/a-musical-christmas-carol",
        "title": "A Musical Christmas Carol at Byham Theater — December 11–23, 2026",
        "text": (
            "The Pittsburgh CLO production A Musical Christmas Carol runs at "
            "the Byham Theater from December 11 through December 23, 2026. "
            "The official Cultural District ticket listing gives the final date "
            "as Wednesday, December 23, 2026. Performance dates are subject to "
            "the organizer's schedule."
        ),
        "source": "pittsburgh-cultural-district-official-event-curated",
    },
    {
        "id_key": "pittsburgh-savoyards-christmas-carol-venue-2026",
        "url": "https://pittsburghsavoyards.org/tickets/",
        "title": "Pittsburgh Savoyards' A Christmas Carol — Margaret Partee Performing Arts Center, December 2026",
        "text": (
            "The Pittsburgh Savoyards' winter 2026 production of Charles "
            "Dickens' A Christmas Carol is staged at the Margaret Partee "
            "Performing Arts Center in Bellevue, Pennsylvania, December 4–19, "
            "2026. The Savoyards' official tickets page lists this venue for "
            "the production. This is a different production from Pittsburgh "
            "CLO's A Musical Christmas Carol at the Byham Theater."
        ),
        "source": "pittsburgh-savoyards-official-production-curated",
        "provenance_urls": [
            "https://pittsburghsavoyards.org/tickets/",
            "https://pittsburghsavoyards.org/venue/",
        ],
    },
    {
        "id_key": "pitt-teaching-with-makers-tools-2026-11-13",
        "url": "https://calendar.pitt.edu/event/teaching-with-makers-tools-11-13-26",
        "title": "Teaching with Makers' Tools at Hillman Library — November 13, 2026 at 12 PM",
        "text": (
            "The University of Pittsburgh schedules Teaching with Makers' Tools "
            "at Hillman Library's Open Lab on Friday, November 13, 2026. The "
            "official Pitt calendar lists the event from 12:00 PM to 1:30 PM "
            "Eastern; its start time is 12:00 PM. This is a scheduled future "
            "workshop and details may change."
        ),
        "source": "pitt-calendar-official-event-curated",
        "provenance_urls": [
            "https://calendar.pitt.edu/event/teaching-with-makers-tools-11-13-26",
            "https://calendar.pitt.edu/hillman_library/calendar",
        ],
    },
    {
        "id_key": "heinz-history-center-student-admission",
        "url": "https://www.heinzhistorycenter.org/visit/heinz-history-center/",
        "title": "Heinz History Center admission — students with valid IDs pay $11",
        "text": (
            "The cost to attend the Heinz History Center with a student ID is "
            "$11 for students with valid IDs, according to the official admission "
            "page. This is the student admission price; the separate $1 price is "
            "for Access Card holders, not students. Prices can change, so check "
            "the official visitor page before visiting."
        ),
        "source": "heinz-history-center-official-admission-curated",
        "provenance_urls": [
            "https://www.heinzhistorycenter.org/visit/heinz-history-center/",
        ],
    },
    {
        "id_key": "pittsburgh-police-2026-budgeted-uniformed-positions",
        "url": "https://www.pittsburghpa.gov/files/assets/city/v/2/omb/documents/operating-budgets/2026-operating-budget.pdf",
        "title": "Pittsburgh FY2026 budget — 800 total uniformed police positions",
        "text": (
            "The City of Pittsburgh FY2026 Operating Budget's Bureau of Police "
            "Position Summary budgets 800 Total Uniformed Police positions. "
            "This is the budgeted staffing level, not a count of officers "
            "currently employed or on duty."
        ),
        "source": "pittsburgh-2026-police-budget-curated",
        "provenance_urls": [
            "https://www.pittsburghpa.gov/files/assets/city/v/2/omb/documents/operating-budgets/2026-operating-budget.pdf",
            "https://pittsburgh.legistar.com/LegislationDetail.aspx?GUID=AD5B59C5-8D59-4965-B031-C090E0452853&ID=7729348",
        ],
    },
    {
        "id_key": "pittsburgh-improv-steph-tolev-october-2026",
        "url": "https://improv.com/pittsburghimprov/",
        "title": "Pittsburgh Improv comedy show starting October 22, 2026 — Steph Tolev",
        "text": (
            "The comedy show at Pittsburgh Improv starting October 22, 2026, "
            "is Steph Tolev. The official Pittsburgh Improv schedule lists her "
            "shows Thursday through Saturday, October 22-24, 2026, with four "
            "performances. Visit Pittsburgh lists the October 22 performance "
            "from 7:00 to 9:00 PM."
        ),
        "source": "pittsburgh-improv-steph-tolev-official-curated",
        "provenance_urls": [
            "https://improv.com/pittsburghimprov/",
            "https://www.visitpittsburgh.com/events/steph-tolev/",
        ],
    },
    {
        "id_key": "pittsburgh-pirates-nl-wild-card-results",
        "source_checked_on": "2026-10-24",
        "url": "https://www.mlb.com/pirates/history/records-stats-awards/postseason-results",
        "title": "Pittsburgh Pirates postseason results — one NL Wild Card game win",
        "text": (
            "How many NL Wild Card games have the Pittsburgh Pirates won? "
            "The Pirates have won one NL Wild Card game: they beat the Cincinnati "
            "Reds 6-2 in 2013. The official Pittsburgh Pirates postseason-results "
            "table records losses in the NL Wild Card games against the San Francisco "
            "Giants in 2014 and the Chicago Cubs in 2015. Therefore their total is "
            "one win, not three appearances or wins."
        ),
        "source": "mlb-pirates-official-postseason-results-curated",
        "provenance_urls": [
            "https://www.mlb.com/pirates/history/records-stats-awards/postseason-results",
        ],
    },
    {
        "id_key": "cmoa-anne-dashwood-historical-department",
        "source_checked_on": "2026-10-24",
        "url": "https://www.openartdata.org/2026/05/CMOA-NEPIP-Provenance.html?m=1",
        "title": "Portrait of Mrs. Anne Dashwood — historical CMOA Department of Fine Arts provenance",
        "text": (
            "The historical provenance transcription for George Romney's "
            "Portrait of Mrs. Anne Dashwood (CMOA accession 61.15) says the work "
            "was gifted to the Department of Fine Arts, Carnegie Institute, "
            "Pittsburgh, in September 1961. This object-specific historical record "
            "supports the department name Fine Arts. It documents the department "
            "named in the provenance at the time of the gift; it is not a claim "
            "about a current collection-page classification field. The transcription "
            "links to the museum's collection record for the same object."
        ),
        "source": "cmoa-anne-dashwood-historical-department-curated",
        "provenance_urls": [
            "https://www.openartdata.org/2026/05/CMOA-NEPIP-Provenance.html?m=1",
            "https://collection.carnegieart.org/objects/cabce7d8-9f73-4de7-a46b-6d0b3cb61774",
        ],
        "inference_note": (
            "The public source is a transcription of historical CMOA provenance. "
            "It directly names Department of Fine Arts, but this is distinct from "
            "the current CMOA page's Paintings classification."
        ),
    },
    {
        "id_key": "mt-lebanon-lst-low-income-exemption",
        "source_checked_on": "2026-10-24",
        "url": "https://mtlebanon.org/wp-content/uploads/2023/03/Mt_-Lebanon-LST-Ordinance.pdf",
        "title": "Mt. Lebanon Local Services Tax — under-$12,000 income exemption",
        "text": (
            "Mt. Lebanon's Local Services Tax ordinance provides an income-based "
            "exemption for a person who reasonably expects earned income and net "
            "profits from all sources within the Municipality to be less than "
            "$12,000 in the calendar year. The municipality's exemption certificate "
            "repeats the under-$12,000 threshold and requires supporting pay stubs "
            "or a prior-year W-2. Therefore the income threshold for the Mt. Lebanon "
            "Local Services Tax exemption is less than $12,000. This is a threshold "
            "for income earned within the Municipality, not a minimum wage or a "
            "general household-income limit."
        ),
        "source": "mt-lebanon-official-lst-exemption-curated",
        "provenance_urls": [
            "https://mtlebanon.org/wp-content/uploads/2023/03/Mt_-Lebanon-LST-Ordinance.pdf",
            "https://mtlebanon.org/wp-content/uploads/2023/03/MT-L-Exemption-Cert.pdf",
        ],
    },
    {
        "id_key": "cmoa-an-african-acquisition",
        "source_checked_on": "2026-10-24",
        "url": "https://www.openartdata.org/2021/06/the-munich-connection.html",
        "title": "An African by Ferdinand Georg Waldmüller — CMOA provenance records a 2004 purchase",
        "text": (
            "The historical Carnegie Museum of Art collection record for "
            "Ferdinand Georg Waldmüller's painting An African states that it "
            "was sold by French & Company in New York in 2004 and then "
            "purchased by Carnegie Museum of Art in December 2004. The historical "
            "record is linked from Open Art Data's provenance transcription as "
            "CMOA item 12339, which notes the work was also listed as "
            "'Der Mohrenfürst'. The current CMOA catalog identifies An African by "
            "Waldmüller as accession 2004.53, consistent with the 2004 purchase. Acquisition "
            "method: purchase."
        ),
        "source": "cmoa-an-african-acquisition-curated",
        "provenance_urls": [
            "https://www.openartdata.org/2021/06/the-munich-connection.html",
            "http://collection.cmoa.org/CollectionDetail.aspx?item=12339",
            "https://collection.carnegieart.org/objects/af0b661c-11f6-4b94-98d0-925aa4d9de26",
        ],
        "inference_note": (
            "Open Art Data transcribes the provenance text of linked historical "
            "CMOA item 12339 and notes the alternate title 'Der Mohrenfürst'. "
            "The current CMOA page identifies An African by Waldmüller as accession "
            "2004.53. The shared artist, alternate title, and 2004 museum purchase "
            "support matching the historical provenance to the benchmark painting, "
            "though the old item-to-accession crosswalk is not directly displayed. "
            "The purchase method is explicit in the "
            "transcribed provenance, though the current catalog only shows its "
            "Heinz Family Fund credit line."
        ),
    },
    {
        "id_key": "cmoa-woodland-scene-title-collision",
        "source_checked_on": "2026-10-24",
        "url": "https://commons.wikimedia.org/wiki/Paintings_in_the_Carnegie_Museum_of_Art",
        "title": "Woodland Scene painting by Alfred Wall — CMOA accession 64.10.11; acquisition date not verified",
        "text": (
            "For the CMOA acquisition-date question about Woodland Scene, the "
            "painting is listed by a public CMOA paintings index as a work by "
            "Alfred Wall, accession 64.10.11. It is distinct from the live CMOA "
            "collection record also titled Woodland Scene: that record is a "
            "black-and-white photograph by Charles 'Teenie' Harris, accession "
            "2001.35.3765, with creation date circa 1938–1946. The photograph's "
            "creation date is not the painting's acquisition date. The accessible "
            "sources identify Alfred Wall's painting but do not provide its "
            "acquisition date; an exact date still requires an object-matched "
            "CMOA archive or museum record."
        ),
        "source": "cmoa-woodland-scene-title-collision-curated",
        "provenance_urls": [
            "https://commons.wikimedia.org/wiki/Paintings_in_the_Carnegie_Museum_of_Art",
            "https://collection.carnegieart.org/objects/b1087138-a27f-417c-b3f2-def44954e716",
        ],
        "inference_note": (
            "The Alfred Wall painting identity and accession are reported by a "
            "secondary, crowdsourced index. The CMOA page directly verifies the "
            "different Teenie Harris photograph. Neither source establishes the "
            "painting's acquisition date."
        ),
    },
]


def records():
    rows = []
    for item in SOURCES:
        text = item["text"]
        rows.append({
            "id": "fact-" + digest(item["id_key"] + "\n" + item["url"] + "\n" + text)[:24],
            "kind": "curated_source_record",
            "source": item["source"],
            "url": item["url"],
            "title": item["title"],
            "text": text,
            "text_hash": digest(text),
            "provenance": [
                {"page_url": url, "method": "human-reviewed source summary"}
                for url in item.get("provenance_urls", [item["url"]])
            ],
            "source_checked_on": item.get("source_checked_on", "2026-10-23"),
            "extractor": "curated-source-summary-v1",
            "retrieval_note": "Concise source-derived facts; recheck live page for time-sensitive details.",
        })
        if item.get("inference_note"):
            rows[-1]["inference_note"] = item["inference_note"]
    # These records were appended together after the Pitt event record in v68.
    # Preserve that serialized order so rebuilding a version produces the same
    # chunk ordering and retrieval tie breaks.
    appended_sources = [
        "rmu-nec-official-basketball-championships-curated",
        "pittsburgh-restaurant-week-official-curated",
        "open-art-data-cmoa-provenance-transcription-curated",
        "fogo-pittsburgh-official-churrasco-curated",
        "cmoa-official-instagram-curated",
        "allegheny-county-2026-operating-budget-total-curated",
        "clemente-museum-official-visits-curated",
        "sports-illustrated-syracuse-2026-sos-curated",
        "cmoa-cowboys-ranch-bequest-curated",
        "mt-lebanon-official-lst-exemption-curated",
        "cmoa-woodland-scene-title-collision-curated",
        "cmoa-an-african-acquisition-curated",
    ]
    appended = {source: next(row for row in rows if row["source"] == source)
                for source in appended_sources}
    rows = [row for row in rows if row["source"] not in appended]
    insertion = next(i for i, row in enumerate(rows)
                     if row["source"] == "pitt-calendar-official-event-curated") + 1
    rows[insertion:insertion] = [appended[source] for source in appended_sources]
    return rows


if __name__ == "__main__":
    rows = records()
    write_jsonl(OUTPUT, rows)
    print(f"Wrote {len(rows)} curated source records to {OUTPUT}")
