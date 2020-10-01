from aiohttp import web
import aiohttp_jinja2
import jinja2
from pathlib import Path
from vklibary import core

here = str(Path(__file__).resolve().parent) + "/templates"
routes = web.RouteTableDef()


@routes.get('/company')
@aiohttp_jinja2.template('clickbate.html')
async def company(req):
    q = req.rel_url.query
    dr = {}
    click = {}
    if "date_start" in q and "date_end" in q and "office" in q:
        dr = core.GetCamp(q["date_start"], q["date_end"], "ДР", q['office'])
        click = core.GetCamp(q["date_start"], q["date_end"], "Кликбейт", q['office'])
    return {"dr": dr, "click": click, 'type': 1,
            'info': {'start': q["date_start"], 'end': q["date_end"]}}


@routes.get('/details_company')
@aiohttp_jinja2.template('clickbate.html')
async def detcompany(req):
    q = req.rel_url.query
    stat = {}
    print(q)
    if "date_start" in q and "date_end" in q and "office" in q:
        stat = core.GetCampDet(q["date_start"], q["date_end"], q['office'], q['type'])
    return {'stat': stat, 'type': 2, 'info': {'start': q["date_start"], 'end': q["date_end"]}}


@aiohttp_jinja2.template('main.html')
async def monitor(req):
    q = req.rel_url.query
    if "start_date" in q and "end_date" in q:
        stat = core.GetMonitor(q["start_date"], q["end_date"])
        return {"resp": stat, 'loading': 1, 'info': {
            'start': q["start_date"], 'end': q["end_date"]}}
    return {'loading': 0}


@routes.get('/ads')
@aiohttp_jinja2.template('ads.html')
def ads(req):
    q = req.rel_url.query
    if "start_date" in q and "end_date" in q:
        stat = core.GetAds(q["start_date"], q["end_date"], q['camp'])
        return {"resp": stat, 'loading': 1, 'info': {
            'start': q["start_date"], 'end': q["end_date"]}}
    return {'loading': 0}


@routes.get('/company_type')
@aiohttp_jinja2.template('all.html')
def companytype(req):
    q = req.rel_url.query
    if "start_date" in q and "end_date" in q:
        stat = core.GetAllAds(q["start_date"], q["end_date"], q['type'])
        return {"resp": stat, 'loading': 1, 'info': {
            'start': q["start_date"], 'end': q["end_date"], 'type': q['type']}}


@routes.get('/acc')
@aiohttp_jinja2.template('acc.html')
def getacc(req):
    acc = core.GetAcc()
    print(acc)
    return {'acc': acc}


# region Utils
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


# endregion

# region Main
filters = {"smart_round": smart_round}
app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(here), filters=filters)
app.router.add_get('/', index_handler)
app.router.add_get('/monitoring', monitor)
app.router.add_get('/accadd', addacc)
app.router.add_get('/company', company)
app.router.add_get('/acc', getacc)
app.router.add_get('/company_type', companytype)
app.router.add_get('/ads', ads)
app.router.add_get('/details_company', detcompany)
app.router.add_post('/create', create)
web.run_app(app, host="91.210.168.170")
