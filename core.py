from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship


sqlite_database = "sqlite:///Data_base.db"
engine = create_engine(sqlite_database, echo=True)
Session = sessionmaker(autoflush=False, bind=engine)    


class Base(DeclarativeBase): 
    pass


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    telegram_id = Column(BigInteger, unique=True)

    skills = relationship('Skill', backref='user', cascade='all, delete-orphan')


    @classmethod
    def load(cls, session, telegram_id):
        user = session.query(cls).filter_by(telegram_id=telegram_id).first()

        if not user:
            user = cls(telegram_id=telegram_id)
            session.add(user)

            session.commit()

        return user
    

    def add_skill(self, skill, session):
        self.skills.append(skill)

        session.commit()


    def remove_skill(self, skill, session):
        self.skills.remove(skill)

        session.commit()


class Skill(Base):
    __tablename__ = 'skills'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String)
    level = Column(Integer, default=1)
    cur_xp = Column(Integer, default=0)
    next_level_xp = Column(Integer, default=100)

    user_id = Column(Integer, ForeignKey('users.id'))
    islands = relationship('Island', backref='skill', cascade='all, delete-orphan')


    @classmethod
    def load(cls, session, name, user_id):
        skill = session.query(cls).filter_by(name=name, user_id=user_id).first()

        if not skill:
            skill = cls(name=name, user_id=user_id)
            session.add(skill)
            
            session.commit()

        return skill
    

    def minus_xp(self, xp, session):
        while xp > 0:
            if self.level == 1 and self.cur_xp <= xp:
                self.cur_xp = 0
                break
                
            if self.cur_xp >= xp:
                self.cur_xp -= xp
                break
            else:
                xp -= self.cur_xp 
                self.level -= 1
                self.next_level_xp = round(self.next_level_xp / 1.2)
                self.cur_xp = self.next_level_xp
        
        session.commit()
    

    def add_island(self, island, session):
        self.islands.append(island)
        
        session.commit()


    def remove_island(self, island, session):
        self.islands.remove(island)

        session.commit()
    

    def get_info(self, session):
        return (self.name, self.level, self.cur_xp, self.next_level_xp, self.islands)
    
    
    def check_xp(self, session):
        while self.cur_xp >= self.next_level_xp:
            self.cur_xp -= self.next_level_xp
            self.next_level_xp = round(self.next_level_xp * 1.2)
            self.level += 1

        session.commit()


    def add_xp(self, xp, session):
        self.cur_xp += xp

        self.check_xp(session)


    def completed_modules(self, island, node, session):
        node.complete(session)
        self.add_xp(100, session)

        if island.check_island_completion(session):
            self.add_xp(1000, session)


class Island(Base):
    __tablename__ = 'islands'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String)
    
    skill_id = Column(Integer, ForeignKey('skills.id'))
    nodes = relationship('Node', backref='island', cascade='all, delete-orphan')


    @classmethod
    def load(cls, session, name, skill_id):
        island = session.query(cls).filter_by(name=name, skill_id=skill_id).first()

        if not island:
            island = cls(name=name, skill_id=skill_id)
            session.add(island)
            
            session.commit()
        
        return island


    def remove_node(self, node, session):
        self.nodes.remove(node)

        session.commit()
        
    
    def check_island_completion(self, session):
        if len(self.nodes) == 0:
            return False

        for node in self.nodes:
            if not node.is_completed:
                return False
        
        return True


class Node(Base):
    __tablename__ = 'nodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String)
    is_completed = Column(Boolean, default=False)
    
    island_id = Column(Integer, ForeignKey('islands.id'))


    @classmethod
    def load(cls, session, name, island_id):
        node = session.query(cls).filter_by(name=name, island_id=island_id).first()

        if not node:
            node = cls(name=name, island_id=island_id)
            session.add(node)
            
            session.commit()

        return node
    

    def complete(self, session):
        self.is_completed = True

        session.commit()


def setup():
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    setup()