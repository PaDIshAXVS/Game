from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from core import Session, User, Skill, Island, Node
from pydantic import BaseModel


app = FastAPI(title="Game API")
templates = Jinja2Templates(directory="templates")


class New_SKill(BaseModel):
    name: str

class New_Island(BaseModel):
    name: str

class New_Node(BaseModel):
    name: str


#GET-----------------------------------------------------------------------------------------------------------------------------------------------------------
@app.get('/')
async def root():
    return {"message": "Добро пожаловать в API."}


@app.get('/user/{telegram_id}')
async def get_user_profile(request: Request, telegram_id: int):
    session = Session()

    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        session.close()
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    skills_data = []
    for skill in user.skills:
        percent = int((skill.cur_xp / skill.next_level_xp) * 100) if skill.next_level_xp > 0 else 0
        
        skills_data.append({
            "id": skill.id,
            "name": skill.name,
            "level": skill.level,
            "xp_text": f"{skill.cur_xp} / {skill.next_level_xp}",
            "xp_percent": percent
        })
        
    session.close()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "telegram_id": telegram_id,
            "skills_count": len(user.skills),
            "skills": skills_data
        }
    )


@app.get('/user/{telegram_id}/skill/{skill_id}')
async def get_user_skill(request: Request, telegram_id: int, skill_id: int):
    session = Session()

    skill = session.query(Skill).filter_by(id=skill_id).first()
    if not skill:
        session.close()
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    percent = int((skill.cur_xp / skill.next_level_xp) * 100) if skill.next_level_xp > 0 else 0

    islands_data = []
    for island in skill.islands:
        islands_data.append({
            'id': island.id,
            'name': island.name,
            'is_completed': island.check_island_completion(session),
            'nodes_count': len(island.nodes)
        })

    context = {
        'user_id': skill.user_id,
        "telegram_id": telegram_id,
        "skill_id": skill.id,
        "skill_name": skill.name,
        "level": skill.level,
        "xp_text": f"{skill.cur_xp} / {skill.next_level_xp}",
        "xp_percent": percent,
        "islands": islands_data
    }

    session.close()

    return templates.TemplateResponse(
        request=request,
        name='skill.html',
        context=context
    )


@app.get('/user/{telegram_id}/skill/{skill_id}/island/{island_id}')
async def get_user_island(request: Request, telegram_id: int, skill_id: int, island_id: int):
    session = Session()

    island = session.query(Island).filter_by(id=island_id).first()
    if not island:
        session.close()
        raise HTTPException(status_code=404, detail="Остров не найден")
    
    node_data = []
    for node in island.nodes:
        node_data.append({
            'id': node.id,
            'name': node.name,
            'is_completed': node.is_completed,
            'island_id': island.id
        })
    
    context = {
        'telegram_id': telegram_id,
        'skill_id': skill_id,
        'island_id': island.id,
        'name': island.name,
        'nodes': node_data
    }

    session.close()

    return templates.TemplateResponse(
        request=request,
        name='island.html',
        context=context
    )


#POST-----------------------------------------------------------------------------------------------------------------------------------------------------------
@app.post('/user/{telegram_id}/add_skill')
async def add_skill(telegram_id: int, skill:New_SKill):
    session = Session()

    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        session.close()
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    Skill.load(session=session, name=skill.name, user_id=user.id)

    session.close()
    return {'status': 'success'}


@app.post('/user/{telegram_id}/skill/{skill_id}/add_island')
async def add_island(telegram_id: int, skill_id: int, new_island:New_Island):
    session = Session()

    skill = session.query(Skill).filter_by(id=skill_id).first()
    if not skill:
        session.close()
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    Island.load(session, new_island.name, skill.id)

    session.close()

    return {'status': 'success'}


@app.post('/user/{telegram_id}/skill/{skill_id}/add_xp')
async def add_xp(telegram_id: int, skill_id: int):
    session = Session()

    skill = session.query(Skill).filter_by(id=skill_id).first()
    if not skill:
        session.close()
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    skill.add_xp(10, session)
    session.close()

    return {'status': 'success'}


@app.post('/user/{telegram_id}/skill/{skill_id}/island/{island_id}/add_node')
async def add_node(telegram_id: int, skill_id: int, island_id: int, new_node:New_Node):
    session = Session()

    skill = session.query(Skill).filter_by(id=skill_id).first()
    if not skill:
        session.close()
        raise HTTPException(status_code=404, detail="Навык не найден")

    island = session.query(Island).filter_by(id=island_id).first()
    if not island:
        session.close()
        raise HTTPException(status_code=404, detail="Остров не найден")
    
    completed = island.check_island_completion(session)
    
    Node.load(session, new_node.name, island.id)

    if completed:
        skill.minus_xp(1000, session)

    session.close()

    return {'status': 'success'}


@app.post('/user/{telegram_id}/skill/{skill_id}/island/{island_id}/node/{node_id}/complete')
async def complete(telegram_id: int, skill_id: int, island_id: int, node_id: int):
    session = Session()

    skill = session.query(Skill).filter_by(id=skill_id).first()
    if not skill:
        session.close()
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    island = session.query(Island).filter_by(id=island_id).first()
    if not island:
        session.close()
        raise HTTPException(status_code=404, detail="Остров не найден")

    node = session.query(Node).filter_by(id=node_id).first()
    if not node:
        session.close()
        raise HTTPException(status_code=404, detail="Node не найдена")
    
    skill.completed_modules(island, node, session)
    session.close()

    return {'status': 'success'}


#delete-------------------------------------------------------------------------------------------------------------------------------------------------------
@app.delete('/user/{telegram_id}/skill/{skill_id}')
async def delete_skill(telegram_id: int, skill_id: int):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        session.close()
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    skill = session.query(Skill).filter_by(id=skill_id, user_id=user.id).first()

    if not skill:
        session.close()
        raise HTTPException(status_code=404, detail="Навык не найден")
    
    user.remove_skill(skill, session)
    session.close()

    return {'status': 'success'}


@app.delete('/user/{telegram_id}/skill/{skill_id}/island/{island_id}')
async def delete_island(telegram_id: int, skill_id: int, island_id: int):
    session = Session()

    skill = session.query(Skill).filter_by(id=skill_id).first()
    island = session.query(Island).filter_by(id=island_id).first()
    
    if not skill or not island:
        session.close()
        raise HTTPException(status_code=404, detail="Не найдено")
    
    xp_to_remove = 0
    if island.check_island_completion(session):
        xp_to_remove += 1000
        
    for node in island.nodes:
        if node.is_completed:
            xp_to_remove += 100

    skill.remove_island(island, session)
    
    if xp_to_remove > 0:
        skill.minus_xp(xp_to_remove, session)

    session.close()
    return {'status': 'success'}


@app.delete('/user/{telegram_id}/skill/{skill_id}/island/{island_id}/node/{node_id}')
async def delete_node(telegram_id: int, skill_id: int, island_id: int, node_id: int):
    session = Session()

    skill = session.query(Skill).filter_by(id=skill_id).first()
    island = session.query(Island).filter_by(id=island_id).first()
    node = session.query(Node).filter_by(id=node_id).first()
    
    if not skill or not island or not node:
        session.close()
        raise HTTPException(status_code=404, detail="Не найдено")
    
    was_completed = island.check_island_completion(session)

    if node.is_completed:
        skill.minus_xp(100, session)

    island.remove_node(node, session)
    is_completed_now = island.check_island_completion(session)

    if was_completed and not is_completed_now:
        skill.minus_xp(1000, session)
    elif not was_completed and is_completed_now:
        skill.add_xp(1000, session)

    session.close()
    return {'status': 'success'}