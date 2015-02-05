from flask import Flask, render_template, request, g
import random, sqlite3

DB = 'static/wh.db'

app = Flask(__name__)
app.config.from_object(__name__)

@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DB'])

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db:
        db.close()

@app.route('/')
def main():
    return display()

@app.route('/display', methods = ['POST', 'GET'])
def display():
    if request.method == 'POST':
        step_count = int(request.form['count'])
    else:
        step_count = 3

    stepinfo = select_steps(step_count)
    steps = stepinfo[0]
    needs = select_rand('materials', 'html', step_count)
    warnings = select_rand('warnings', 'html', step_count)
    sources = select_sources(stepinfo[1])

    return render_template('template.html', steps = steps, needs = needs, warnings = warnings, needs_exist = not all(
        x is None for x in needs), warnings_exist = not all(y is None for y in warnings), sources = sources)

def select_steps(num):
    c = g.db.execute("SELECT boldtext, imgid, source FROM steps ORDER BY RANDOM() LIMIT %d" % num)
    rows= c.fetchall()

    steps, sourceids = [], []
    for i, row in enumerate(rows):
        imgid = g.db.execute("SELECT html FROM images WHERE id=?", (row[1],))
        html = imgid.fetchone()
        if imgid:
            assembled = '<li>' + html[0].decode('utf-8')
        else:
            assembled = '<li>'
        assembled += '<div class="step_num">%d</div>' % (i + 1) + row[0] + '</li>'
        steps.append(assembled)
        sourceids.append(row[2])
    return [steps, sourceids]

def select_rand(table, field, num=1):
    count = random.randint(0, num)
    c = g.db.execute("SELECT %s FROM %s ORDER BY RANDOM() LIMIT %d" % (field, table, count))
    rows = c.fetchall()
    return [row[0].decode('utf-8') for row in rows]

def select_sources(ids):
    sources = []

    for sourceid in ids:
        c = g.db.execute("SELECT url, title FROM urls WHERE id=?", (sourceid,))
        src = c.fetchone()
        sources.append('<li><a href="%s">%s</a></li>' % (src[0], src[1]))

    return sources

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
