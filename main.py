# -*- coding: utf-8 -*-

from flask import Flask, render_template, g, request, session, abort, url_for, flash, redirect, Markup, send_from_directory
from functools import wraps
from config import config
import sqlite3
import hashlib
import os

"""
py-mCMS
Copyright (c) 2015 Mark Mäkinen
See LICENSE.md
"""

app = Flask(__name__)
app.config.from_object(__name__)


def get_config(obj_str):
    path = obj_str.split(".")
    value = None
    for obj in path:
        if value is None:
            value = config.get(obj)
        else:
            value = value.get(obj)
    if value is None:
        abort(500)
    return value

config_status = get_config("configured")
if config_status is None or not config_status:
    raise Exception("Non-configured installation! Please check config.py!")

app.secret_key = get_config("secret_key")


@app.context_processor
def utility_processor():
    def get_config_jinja(obj_str):
        return get_config(obj_str)
    return dict(get_config=get_config_jinja)


def login_required(f):
    """Decorator for login. Redirects non-logged in users to the login page"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logged_in = session.get("logged_in", None)
        if logged_in is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/robots.txt")
@app.route("/favicon.ico")
def meta():
    """Handle static metadata files."""
    return send_from_directory(os.path.join(app.root_path, "static"), request.path[1:])


@app.route("/")
def main_page():
    """Serve the main/index page."""
    return page("main")


@app.route("/<pagename>")
def page(pagename):
    """Serve page with the given name."""

    c_page = get_page(pagename)
    if c_page is not None:
        return render_template("page.html", pages=get_pages(), pagename=c_page["name"], content=c_page["content"])
    else:
        # If the page is nonexistent, return HTTP 404
        abort(404)


@app.route("/<pagename>/edit", methods=["GET", "POST"])
@login_required
def edit_page(pagename):
    """Save edited page to the database."""

    if request.method == "POST":
        # Save
        content = request.form["editor"]
        name = request.form["name"]
        shortname = request.form["shortname"]
        order = request.form["order"]

        current_page = get_page(pagename, True)

        # Perform some checks

        name_count = query_db("SELECT COUNT(*) FROM pages WHERE name = ?", (name,), True)[0]
        shortname_count = query_db("SELECT COUNT(*) FROM pages WHERE shortname = ?", (shortname,), True)[0]
        order_count = query_db("SELECT COUNT(*) FROM pages WHERE page_order = ?", (order,), True)[0]

        error = False
        if name != current_page["name"] and name_count == 1:
            flash("Page with given new name already exists!")
            error = True
        if shortname != current_page["shortname"] and shortname_count == 1:
            flash("Page with given new short name already exists!")
            error = True
        if int(order) != current_page["page_order"] and order_count == 1:
            flash("Page with given new order already exists!")
            error = True

        if not error:
            # If no errors, update
            # Update only if data has changed
            if content != current_page["content"]:
                # Content
                query_db("UPDATE pages SET content = ? WHERE shortname = ?", (content, pagename))
            if name != current_page["name"]:
                # Name
                query_db("UPDATE pages SET name = ? WHERE shortname = ?", (name, pagename))
            if shortname != current_page["shortname"]:
                # Short name
                query_db("UPDATE pages SET shortname = ? WHERE shortname = ?", (shortname, pagename))
            if order != current_page["page_order"]:
                # Order
                query_db("UPDATE pages SET page_order = ? WHERE shortname = ?", (order, shortname))

            # Finally, save
            commit_db()

            flash(Markup("Page '" + pagename + "' saved! (<a href='" + url_for("page", pagename=pagename) + "'>Show</a>)"))

        # Return to the edit page
        c_page = get_page(pagename, True)
        return render_template("edit.html", pagename=c_page["name"], shortname=pagename, content=c_page["content"], order=c_page["page_order"], pages=get_pages())
    else:
        c_page = get_page(pagename, True)
        if c_page is not None:
            return render_template("edit.html", pagename=c_page["name"], shortname=pagename, content=c_page["content"], order=c_page["page_order"], pages=get_pages())
        else:
            abort(404)


@app.route("/add_page", methods=["GET", "POST"])
@login_required
def add_page():
    """Save page to the database."""

    if request.method == "POST":
        # Gather info
        order = request.form["order"]
        name = request.form["name"]
        shortname = request.form["shortname"]
        content = request.form["editor"]
        try:
            # Browsers don't return checkboxes if they are unchecked
            # If we don't catch this, Flask will send back HTTP 400 Bad Request
            available = (request.form["available"] == "available")
        except KeyError:
            available = False

        # Check existency
        # Page order
        count = query_db("SELECT COUNT(*) FROM pages WHERE page_order = ?", (order,), True)[0]
        if count > 0:
            flash("Page with given order already exists!")
            return render_template("add.html", name=name, shortname=shortname, content=content, available=available)
        # Short name
        count = query_db("SELECT COUNT(*) FROM pages WHERE shortname = ?", (shortname,), True)[0]
        if count > 0 or shortname in ["add_page", "admin", "login", "logout"]:
            flash("Page with given short name already exists!")
            return render_template("add.html", name=name, content=content, order=order, available=available)
        # Page name
        count = query_db("SELECT COUNT(*) FROM pages WHERE name = ?", (name,), True)[0]
        if count > 0:
            flash("Page with given name already exists!")
            return render_template("add.html", shortname=shortname, content=content, order=order, available=available)

        # Add to the database
        query_db("INSERT INTO pages (page_order, shortname, name, content, available) VALUES (?, ?, ?, ?, ?)", (order, shortname, name, content, available))
        commit_db()
        flash(Markup("Page '" + name + "' saved! (<a href='" + url_for("page", pagename=shortname) + "'>Show</a>)"))
        return redirect(url_for("admin"))
    else:
        # Get the next available order number
        next_order_num = query_db("SELECT MAX(page_order) + 1 FROM pages", (), True)[0]
        return render_template("add.html", order=next_order_num, pages=get_pages())


@app.route("/<shortname>/delete")
@login_required
def delete_page(shortname):
    """Delete page from the database."""

    # Check page existency
    if get_page(shortname) is None:
        abort(404)
    if shortname is None:
        flash("No parameters for page deletion!")
        return redirect(url_for("admin"))
    else:
        query_db("DELETE FROM pages WHERE shortname = ?", (shortname,))
        commit_db()
        flash("Page '" + shortname + "' deleted!")
        return redirect(url_for("admin"))


@app.route("/<shortname>/hide")
@login_required
def hide_page(shortname):
    """Hide page from the site users (visible for the admin)."""

    if get_page(shortname) is None:
        abort(404)
    if shortname is None:
        flash("No parameters for page hiding!")
        return redirect(url_for("admin"))
    else:
        query_db("UPDATE pages SET available = 0 WHERE shortname = ?", (shortname,))
        commit_db()
        flash("Page '" + shortname + "' is now hidden!")
        return redirect(url_for("admin"))


@app.route("/<shortname>/show")
@login_required
def show_page(shortname):
    """Show page to the site users."""

    if get_page(shortname, True) is None:
        abort(404)
    if shortname is None:
        flash("No parameters for page showing!")
        return redirect(url_for("admin"))
    else:
        query_db("UPDATE pages SET available = 1 WHERE shortname = ?", (shortname,))
        commit_db()
        flash("Page '" + shortname + "' is now available!")
        return redirect(url_for("admin"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login"""

    error = None
    next_page = request.args.get("next", None)
    if request.method == "POST":
        if request.form["username"] == get_config("admin_user"):
            hashed = hashlib.sha256(request.form["password"]).hexdigest()
            if hashed == get_config("admin_pass"):
                # Login OK
                session["logged_in"] = True
                flash("Login successful!")
                if next_page is not None:
                    return redirect(next_page)
                else:
                    return redirect(url_for("admin"))
            else:
                error = "Wrong username or password!"
        else:
            error = "Wrong username or password!"
    return render_template("login.html", error=error, next=next_page, pages=get_pages())


@app.route("/logout")
def logout():
    """User logout"""

    session.pop("logged_in", None)
    flash("Logout successful!")
    return redirect(url_for("main_page"))


@app.route("/admin")
@login_required
def admin():
    """Admin page"""
    return render_template("admin.html", pages=get_pages())


@app.errorhandler(404)
def page_not_found(error):
    """HTTP 404 handler"""
    return render_template("error_404.html", pages=get_pages()), 404


@app.errorhandler(500)
def server_error(error):
    """HTTP 500 handler"""
    return render_template("error_500.html", pages=get_pages()), 500


def connect_to_database():
    return sqlite3.connect(os.path.join(get_config("data_path"), get_config("db_name")))


def get_db():
    """Get the database object."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = connect_to_database()
        db.row_factory = sqlite3.Row
    return db


def query_db(query, args=(), one=False):
    """Perform a database query."""
    try:
        cur = get_db().execute(query, args)
    except sqlite3.OperationalError:
        flash("Database query failed!")
        return None
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def commit_db():
    """Commit the database changes."""
    get_db().commit()


@app.teardown_appcontext
def close_db(exception):
    """Close the database connection."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def get_pages():
    """Select all pages and order them by page_order."""
    pages = query_db("SELECT page_order, name, shortname, available FROM pages ORDER BY page_order")
    return pages


def get_page(pagename, ignore_availability=False):
    """Select page by short name."""
    content = query_db("SELECT shortname, page_order, available, name, content FROM pages WHERE shortname = ?", (pagename,), True)
    if content is not None:
        if content["available"] == 0 and not ignore_availability:
            if session.get("logged_in", None) == True:
                flash("Admin notice: Requested page is hidden")
            return None
        else:
            return content
    else:
        return None


if __name__ == "__main__":
    """Serve the site in debug mode."""
    app.run(host=get_config("debug.bind_ip"), port=get_config("debug.port"), debug=True)
