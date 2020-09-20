from aiohttp import web
import aiohttp_jinja2
import jinja2
from pathlib import Path
from vklibary import core


here = str(Path(__file__).resolve().parent) + "/templates"
routes = web.RouteTableDef()


@aiohttp_jinja2.template('main.html')
async def monitor(req):
    q = req.rel_url.query
    type = 0
    if "monitor" in q:
        type = 1
    elif "clickbate" in q:
        type = 2

    stat = ""
    if "start_date" in q and "end_date" in q and type == 2 and "type" in q:
        stat = core.GetCamp(q["start_date"], q["end_date"],q['type'])
    elif "start_date" in q and "end_date" in q and type == 1:
        stat = core.GetMonitor(q["start_date"], q["end_date"])
    return {"type": type, "resp": stat}


@routes.get('/')
@aiohttp_jinja2.template('login.html')
async def index_handler(request):
    return {}


@routes.post('/accadd')
@aiohttp_jinja2.template('addacc.html')
async def addacc(request):
    pass


@routes.post('/create')
@aiohttp_jinja2.template('loc.html')
async def create(req):
    q = await req.post()
    name = q["name"]
    login = q["login"]
    password = q["pass"]
    spent = q["spent"]
    critik = q["critik"]
    join = q["join"]
    core.CreateAcc(name, login, password, spent, critik, join)
    return


def smart_round(text: str, ndigits: int = 2) -> str:
    try:
        number = round(float(text), ndigits)
        if number == int(number):
            number = int(number)
        return str(number)
    except:  # строка не является float / int
        return ''


filters = {"smart_round": smart_round}
app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(here), filters=filters)
app.router.add_get('/', index_handler)
app.router.add_get('/monitoring', monitor)
app.router.add_get('/accadd', addacc)
web.run_app(app, host='91.210.168.170/')
