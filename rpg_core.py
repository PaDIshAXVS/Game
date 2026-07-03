import sqlite3


def save_all_changes(table, id, **kwargs):
    con = sqlite3.connect('Data_base.db')
    cursor = con.cursor()

    keys = list(kwargs.keys())

    values = list(kwargs.values())
    values.append(id)
    values = tuple(values)

    keys = ', '.join([f'{k} = ?' for k in keys])
    sql = f'UPDATE {table} SET {keys} WHERE id = ?'

    cursor.execute(sql, values)

    con.commit()
    con.close()

def remove_module(table, module_id):
    con = sqlite3.connect('Data_base.db')
    cursor = con.cursor()

    if table == 'Nodes':
        cursor.execute("DELETE FROM Nodes WHERE id = ?", (module_id, ))
    else:
        cursor.execute("DELETE FROM Nodes WHERE island_id = ?", (module_id, ))
        cursor.execute("DELETE FROM Islands WHERE id = ?", (module_id, ))

    con.commit()
    con.close()


class Skill():
    def __init__(self, name):
        self._id = None
        self._cur_xp = 0
        self._next_level_xp = 100
        self._level = 1
        self._name = name
        self._islands = []


    @classmethod
    def load(cls, name):
        con = sqlite3.connect('Data_base.db')
        cursor = con.cursor()

        cursor.execute("SELECT id, level, cur_xp, next_level_xp FROM Skills WHERE name = ?", (name, ))
        row = cursor.fetchone()

        if not row:
            cursor.execute("INSERT INTO Skills (name, level, cur_xp, next_level_xp) VALUES (?, 1, 0, 100)", (name,))
            con.commit()
            
            cursor.execute("SELECT id, level, cur_xp, next_level_xp FROM Skills WHERE name = ?", (name, ))
            row = cursor.fetchone()
        
        cursor.execute(f"SELECT name FROM Islands WHERE skill_id = {row[0]}")
        islands = cursor.fetchall()
        
        con.close()
        
        skill = cls(name)
        skill._id = row[0]
        skill._level = row[1]
        skill._cur_xp = row[2]
        skill._next_level_xp = row[3]
        
        skill._islands = []
        for island in islands:
            island_object = Island.load(island[0])

            skill._islands.append(island_object)

        return skill


    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, new_name):
        self._name = new_name
        save_all_changes('Skills', self._id, name=self._name)
    

    @property
    def level(self):
        return self._level
    
    @property
    def next_level_xp(self):
        return self._next_level_xp
    
    @property
    def xp(self):
        return self._cur_xp
    
    @property
    def islands(self):
        return self._islands
    

    def minus_xp(self, xp):
        while xp > 0:
            if self._level == 1 and self._cur_xp <= xp:
                self._cur_xp = 0
                break
                
            if self._cur_xp >= xp:
                self._cur_xp -= xp
                break
            else:
                xp -= self._cur_xp 
                self._level -= 1
                self._next_level_xp = round(self._next_level_xp / 1.2)
                self._cur_xp = self._next_level_xp
    

    def add_node_to_island(self, island, node):
        if island.check_island_completion():
            self.minus_xp(1000)

            save_all_changes('Skills', self._id, level=self._level, cur_xp=self._cur_xp, next_level_xp=self._next_level_xp)

        island._nodes.append(node)
        node._island_id = island._id

        save_all_changes('Nodes', node._id, island_id=island._id)
    

    def add_island(self, island):
        self._islands.append(island)
        island._skill_id = self._id

        save_all_changes('Islands', island._id, skill_id=self._id)


    def remove_island(self, island):
        self._islands.remove(island)

        remove_module('Islands', island._id)
    

    def get_info(self):
        return (self._name, self._level, self._cur_xp, self._next_level_xp, self._islands)
    
    
    def check_xp(self):
        while self._cur_xp >= self._next_level_xp:
            self._cur_xp -= self._next_level_xp
            self._next_level_xp = round(self._next_level_xp * 1.2)
            self._level += 1

        save_all_changes('Skills', self._id, cur_xp=self._cur_xp, level=self._level, next_level_xp=self._next_level_xp)


    def add_xp(self, xp):
        self._cur_xp += xp

        self.check_xp()


    def completed_modules(self, island, node):
        node.complete()
        self.add_xp(100)

        if island.check_island_completion():
            self.add_xp(1000)


class Island():
    def __init__(self, name):
        self._id = None
        self._skill_id = None
        self._name = name
        self._nodes = []


    @classmethod
    def load(cls, name):
        con = sqlite3.connect('Data_base.db')
        cursor = con.cursor()

        cursor.execute("SELECT id, skill_id FROM Islands WHERE name = ?", (name, ))
        row = cursor.fetchone()

        if not row:
            cursor.execute("INSERT INTO Islands (name) VALUES (?)", (name,))
            con.commit()
            
            cursor.execute("SELECT id, skill_id FROM Islands WHERE name = ?", (name, ))
            row = cursor.fetchone()

        cursor.execute(f'SELECT name FROM Nodes WHERE island_id = {row[0]}')
        nodes = cursor.fetchall()

        con.close()
        
        island = cls(name)
        island._id = row[0]
        island._skill_id = row[1]

        island._nodes = []
        for node in nodes:
            node_object = Node.load(node[0])

            island._nodes.append(node_object)

        return island

    
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, new_name):
        self._name = new_name

        save_all_changes('Islands', self._id, name=self._name)

    @property
    def nodes(self):
        return self._nodes
    
    
    def remove_node(self, node):
        self._nodes.remove(node)

        remove_module('Nodes', node._id)
        
    
    def check_island_completion(self):
        if len(self._nodes) == 0:
            return False

        for node in self._nodes:
            if not node.is_completed:
                return False
        
        return True


class Node():
    def __init__(self, name):
        self._id = None
        self._island_id = None
        self._name = name
        self._is_completed = False


    @classmethod
    def load(cls, name):
        con = sqlite3.connect('Data_base.db')
        cursor = con.cursor()

        cursor.execute("SELECT id, is_completed, island_id FROM Nodes WHERE name = ?", (name, ))
        row = cursor.fetchone()

        if not row:
            cursor.execute("INSERT INTO Nodes (name) VALUES (?)", (name,))
            con.commit()
            
            cursor.execute("SELECT id, is_completed, island_id FROM Nodes WHERE name = ?", (name, ))
            row = cursor.fetchone()
        
        con.close()
        
        node = cls(name)
        node._id = row[0]
        node._is_completed = row[1]
        node._island_id = row[2]

        return node
    

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, new_name):
        self._name = new_name

        save_all_changes('Nodes', self._id, name=self._name)

    @property
    def is_completed(self):
        return self._is_completed
    

    def complete(self):
        self._is_completed = True

        save_all_changes('Nodes', self._id, is_completed=self._is_completed)
    

if __name__ == '__main__':
    pass