# -*- charset: utf-8 -*-

import os

# Site config
config = {
    "name":        "Demo site",                     # Name for the site, displayed in the title bar
    "description": "Demo site for py-mCMS",         # Description of the site, contained in the site metadata
    "author":      "py-mCMS dev",                   # Author(s) of the site, contained in the site metadata
    "admin_user":  "REPLACE ME",                    # Username of the site admin
    "admin_pass":  "REPLACE ME",                    # SHA-256 hashed password of the admin
    "secret_key":  "REPLACE ME",                    # Secret key, you should generate this with "os.urandom(24)"
    "data_path":   os.path.dirname(os.path.abspath(__file__)),  # Absolute path of the folder containing the site root
    "db_name":     "site.db",                       # Name of the site database file
    "configured":  False,                           # Change to True when configured

    "main_page": "main",    # Short name of the main/index page (in database)

    # List of styles included in every page
    "styles": [
        "main.css",
        "mobile.css"
    ],

    # CKEditor preferences
    "ckeditor": {
        "js_url":       "//cdn.ckeditor.com/4.5.4/standard/ckeditor.js",    # URL/path of the CKEditor main JS file (CDN usage is recommended)
        "contents_css": "main.css",                                         # Style filename from the styles list
        "body_id":      "content",                                          # CSS ID for the content (used to render CKEditor content)
        "skin": {
            "name":   "moono-dark",                  # Name of the CKEditor skin
            "url":    "ckeditor/skins/moono-dark/"   # URL/path of the CKEditor skin
        }
    },

    # Debug settings
    "debug": {
        "bind_ip": "127.0.0.1",  # Use 0.0.0.0 if you're developing with other machine
        "port": 8080             # Usually something else than 80
    }
}
