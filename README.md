py-mCMS
===========

Intro
-----

This is a simple single-user CMS which stores the pages in a SQLite database.

Created with Python & [Flask](http://flask.pocoo.org/).

For an example site, see my website: [Mark Mäkinen](http://markmakinen.net)

Installation
------------

  1. Clone the repo
  * Optional: Install virtualenv
    
    Linux:
    ```
    $ sudo apt-get install python-virtualenv
    $ cd repo/
    $ virtualenv venv
    $ . venv/bin/activate
    ```

  2. Install Flask

     ```pip install Flask```
  3. Create the database 
  
     ```sqlite3 site.db < schema.sql```
  4. Configure by editing `config.py`
     * Remember to generate the secret key by using ```os.urandom(24)```!
     * Also remember to set ```configured``` to ```True```
  5. Run in debug mode with ```python main.py```
     OR
     configure WSGI by editing `site.wsgi` and your webserver configuration.
