from flask import Flask, render_template, request
from bs4 import BeautifulSoup as bs4
import requests, random

WIMMY_DIDDLE = """<li>
<div class="mwimg  largeimage  floatcenter " style="max-width:670px"><img alt="Whittle a Wimmy Diddle Step 10.jpg" src="http://pad1.whstatic.com/images/thumb/e/e2/Whittle-a-Wimmy-Diddle-Step-10.jpg/670px-Whittle-a-Wimmy-Diddle-Step-10.jpg" width="670" height="503"></div>
<div class="step_num">%d</div><b class="whb">Make sure you can spin the propeller.</b>
</li>"""

app = Flask(__name__)

@app.route('/')
def main():
    return display()

@app.route('/display', methods = ['POST', 'GET'])
def display():
    if request.method == "POST":
        step_count = int(request.form['count'])
    else:
        step_count = 3

    steps = []
    needs = []
    warnings = []
    sources = []

    for i in range(0, step_count):
        try:
            page = get_page()
            steps.append(get_step(page, i))
            needs.extend(get_needs(page))
            warnings.extend(get_warnings(page))
            sources.append(get_source(page))
        except: #Failed for some reason, emergency wimmy diddle step placeholder
            app.logger.error("Failed to retrieve info from page #%d" % i)
            steps.append(WIMMY_DIDDLE % i)

    return render_template('template.html', steps = steps, needs = needs, warnings = warnings, needs_exist = not all(
        x is None for x in needs), warnings_exist = not all(y is None for y in warnings), sources = sources)

def get_page():
    #Get random wikiHow page using their own Random Page feature
    page = None

    while not page:
        page = bs4(requests.get("http://www.wikihow.com/Special:Randomizer").text)

    app.logger.debug("Getting page: " + page.find("link", {"rel": "canonical"})['href'])

    return page

def get_needs(page):
    needsection = page.find("div", {"id": "thingsyoullneed"})
    if needsection:
        allneeds = needsection.find("ul").findChildren("li", recursive = False)
    else:
        app.logger.debug("No materials listed for this how-to.")
        return ""

    needs = []
    count = len(allneeds)
    count = count if count < 2 else 2

    for i in xrange(0, random.randint(1, count)):
        needs.append(allneeds[random.randint(0, len(allneeds) - 1)])
        allneeds.remove(needs[i])

    return needs

def get_warnings(page):
    warningsection = page.find("div", {"id": "warnings"})
    if warningsection:
        allwarnings = warningsection.find("ul").findChildren("li", recursive = False)
    else:
        app.logger.debug("No warnings listed for this how-to.")
        return ""

    warnings = []
    count = len(allwarnings)
    count = count if count < 3 else 3

    for i in xrange(0, random.randint(1, count)):
        warnings.append(allwarnings[random.randint(0, len(allwarnings) - 1)])
        allwarnings.remove(warnings[i])

    return warnings

def get_step(page, num):
    stepsection = page.find("div", {"id": "steps"})
    if stepsection: # Only one 'method'
        allsteps = stepsection.find("ol").findChildren("li", recursive = False)
    else: # Multiple 'methods', each with their own list of steps
        app.logger.debug("Multiple methods on page, searching for one with list items.")
        for x in range(1, 5):
            try:
                stepsection  = page.find("div", {"id": "steps_%d" % x})
                try:
                    # Possible for a Method to have no actual steps, just a paragraph, so check for the list
                    allsteps = stepsection.find("ol").findChildren("li", recursive = False)
                    app.logger.debug("Found list items under Method %d" % x)
                    break
                except:
                    continue
            except:
                app.logger.debug("Failed to find any list section")
                break

    return process_step(allsteps, num)

def get_source(page):
    link = page.find("h1", {"class": "firstHeading"}).a

    return "<li>" + str(link) + "</li>"

def process_step(allsteps, stepnum):
    step = get_rand_step(allsteps)

    while step.find("img") is None:
        app.logger.debug("Selected step with no image, reselecting")
        step = get_rand_step(allsteps)

    img = step.find("div", {"class": "mwimg"}).extract()
    img.a.unwrap()
    num = step.find("div", {"class": "step_num"}).extract()
    num.string.replace_with(str(stepnum + 1))
    boldtext = step.find("b").extract()

    step = "<li>" + str(img).decode('utf-8') +str(num).decode('utf-8') + str(boldtext).decode('utf-8') + "</li>"
    return step

def get_rand_step(steplist):
    return steplist[random.randint(0, len(steplist) - 1)]

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
