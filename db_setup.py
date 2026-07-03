import sqlite3
import os


def setup():
    if os.path.exists('Data_base.db'):
        os.remove('Data_base.db')

    con = sqlite3.connect('Data_base.db')
    cursor = con.cursor()

    cursor.execute("""CREATE TABLE Skills
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT UNIQUE,
                   level INTEGER DEFAULT 1,
                   cur_xp INTEGER DEFAULT 0,
                   next_level_xp INTEGER DEFAULT 100)
                   """)
    
    cursor.execute("""CREATE TABLE Islands
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT,
                   skill_id INTEGER,
                   FOREIGN KEY (skill_id) REFERENCES Skills (id))
                    """)
    
    cursor.execute("""CREATE TABLE Nodes
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT,
                   is_completed BOOL DEFAULT FALSE,
                   island_id INTEGER,
                   FOREIGN KEY (island_id) REFERENCES Islands (id))
                    """)
    
    con.commit()
    con.close()


if __name__ == '__main__':
    setup()