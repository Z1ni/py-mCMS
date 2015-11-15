CREATE TABLE pages(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, shortname TEXT NOT NULL, content TEXT NOT NULL, page_order INTEGER NOT NULL, available INTEGER DEFAULT 1);
INSERT INTO pages (name, shortname, content, page_order) VALUES ("Main page", "main", "<h2>Main page!</h2><p>You should <a href='/main/edit'>edit</a> this page!</p>", 1);