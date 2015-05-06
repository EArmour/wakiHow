wakiHow
=======

Compiles random wikiHow instructions, materials, warnings, and images into a single absurd how-to.

Built on Flask with a simple Jinja2 template. First run the scraping script to populate a SQLite DB with steps 
(leveraging wikiHow's own [Random Page](http://www.wikihow.com/Special:Randomizer) functionality), then start the Flask server.
