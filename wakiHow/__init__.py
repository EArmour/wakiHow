from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup as bs4
import random

app = Flask(__name__)

@app.route('/')
def disp():
    steps = get_steps()
    return render_template('template.html', steps = steps)

def get_steps(num = 3, brevity = True):
    steps = [None] * num

    for i in range(0, num):
        #Get random wikiHow page using their own Random Page feature
        page = bs4(requests.get("http://www.wikihow.com/Special:Randomizer").text)
        """:type : bs4.BeautifulSoup"""

        app.logger.debug("Getting page " + str(i) + ": " + page.find("link", {"rel": "canonical"})['href'])
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
                    app.logger.debug("Failed to find a list section")
                    break

        steps[i] = process_step(allsteps, i, brevity)

    return steps

def process_step(allsteps, stepnum, brevity):
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
