import sqlite3
from bs4 import BeautifulSoup as bs4
import requests, random, logging

def get_page():
    # Get random wikiHow page using their own Random Page feature
    page = None

    while not page:
        page = bs4(requests.get("http://www.wikihow.com/Special:Randomizer").text)

    try:
        logging.info("Getting page: " + page.find("link", {"rel": "canonical"})['href'])
    except:
        page = get_page()

    return page

def get_source(page):
    h1 = page.find("h1", {"class": "firstHeading"})

    return {'link': unicode(h1.a['href']), 'title': unicode(h1.text)}

def get_needs(page):
    needsection = page.find("div", {"id": "thingsyoullneed"})
    if needsection:
        allneeds = needsection.find("ul").findChildren("li", recursive = False)
    else:
        logging.info("No materials listed for this how-to.")
        return ""

    needs = []
    count = len(allneeds)
    count = count if count < 3 else 3

    # If we grab all materials, the pool will be mostly recipe ingredients since they have so many.
    # So, only grab a few from each to maximize variability.
    for i in xrange(0, count):
        needs.append(allneeds[random.randint(0, len(allneeds) - 1)])
        allneeds.remove(needs[i])

    return needs

def get_warnings(page):
    warningsection = page.find("div", {"id": "warnings"})
    if warningsection:
        allwarnings = warningsection.find("ul").findChildren("li", recursive = False)
    else:
        logging.info("No warnings listed for this how-to.")
        return ""

    warnings = []
    count = len(allwarnings)
    count = count if count < 4 else 4

    # Again, only grab a limited number from each page to promote variety
    for i in xrange(0, count):
        warnings.append(allwarnings[random.randint(0, len(allwarnings) - 1)])
        allwarnings.remove(warnings[i])

    return warnings

def get_steps(page):
    stepsection = page.find("div", {"id": "steps_1"})
    if not stepsection: # Only one 'method'
        allsteps = stepsection.find("ol").findChildren("li", recursive = False)
    else: # Multiple 'methods', each with their own list of steps
        logging.info("Multiple methods on page, searching for one with list items.")
        for x in range(1, 5):
            try:
                stepsection  = page.find("div", {"id": "steps_%d" % x})
                try:
                    # Possible for a Method to have no actual steps, just a paragraph, so check for the list
                    allsteps = stepsection.find("ol").findChildren("li", recursive = False)
                    logging.info("Found list items under Method %d" % x)
                    break
                except:
                    continue
            except:
                logging.info("Failed to find any list section")
                allsteps = ""
                break

    return allsteps

def process_img(step):
    if step.find("img") is not None:
        img = step.find("div", {"class": "mwimg"}).extract()
        img.a.unwrap()
    else:
        img = None

    return img

def process_step(step):
    if step.find("div", {"class": "wh_ad_inner"}):
        step.find("div", {"class": "wh_ad_inner"}).extract()
        step.find("div", {"class": "ad_label"}).extract()
        step.find("div", {"class": "adclear"}).extract()

    html = unicode(step)
    num = step.find("div", {"class": "step_num"}).extract()
    boldtext = step.find("b").extract()

    return {'boldtext': unicode(boldtext), 'number': int(num.text), 'html': html}

def get_rand_step(steplist):
    return steplist[random.randint(0, len(steplist) - 1)]

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dupecount = 0

    with sqlite3.connect("static/wh.db") as db:
        c = db.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY,
            url TEXT,
            title TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY,
            source INTEGER,
            html TEXT,
            boldtext TEXT,
            number INTEGER,
            imgid INTEGER,
            FOREIGN KEY(source) REFERENCES urls(id),
            FOREIGN KEY(imgid) REFERENCES images(id)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY,
            source INTEGER,
            html TEXT,
            FOREIGN KEY(source) REFERENCES urls(id)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY,
            source INTEGER,
            html TEXT,
            FOREIGN KEY(source) REFERENCES urls(id)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            source INTEGER,
            html TEXT,
            FOREIGN KEY(source) REFERENCES urls(id)
        )""")

        for i in range(0, 50):
            page = get_page()
            source = get_source(page)

            c.execute("SELECT * FROM urls WHERE url=?", (source['link'],))

            if c.fetchone():
                dupecount += 1
                logging.info("Duplicate page fetched, skipping.")
            else:
                c.execute("""
                INSERT INTO urls (url, title)
                VALUES (?, ?)
                """, (source['link'], source['title']))

                sourceid = int(c.lastrowid)
                logging.info("Inserted url ID: %d" % sourceid)

                needs = get_needs(page)
                for need in needs:
                    c.execute("""
                    INSERT INTO materials (source, html)
                    VALUES (?, ?)
                    """, (sourceid, unicode(need)))

                warnings = get_warnings(page)
                for warning in warnings:
                    c.execute("""
                    INSERT INTO warnings (source, html)
                    VALUES (?, ?)
                    """, (sourceid, unicode(warning)))

                steps = get_steps(page)
                for step in steps:
                    img = process_img(step)
                    if img:
                        c.execute("""
                        INSERT INTO images (source, html)
                        VALUES (?, ?)
                        """, (sourceid, unicode(img)))
                        imgid = int(c.lastrowid)
                    else:
                        imgid = None

                    proc = process_step(step)
                    c.execute("""
                    INSERT INTO steps (source, html, boldtext, number, imgid)
                    VALUES (?, ?, ?, ?, ?)
                    """, (sourceid, proc['html'], proc['boldtext'], proc['number'], imgid))
                db.commit()
        logging.info("DONE. Found %d duplicates." % dupecount)
