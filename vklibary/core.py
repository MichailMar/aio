import time
from python3_anticaptcha import ImageToTextTask
import vk_api
from vklibary import database
from datetime import datetime
from vklibary import utils

def captcha_handler(captcha):
    key = ImageToTextTask.ImageToTextTask(anticaptcha_key="f0d1147d67df6a70b77ccf1e41372dc1", save_format='const') \
        .captcha_handler(captcha_link=captcha.get_url())

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key['solution']['text'])


# region Upload
def UploadInfo():
    database.Clear("ads")
    database.Clear("static")
    database.Clear("account_monitor")
    database.Clear("company")
    for ac in database.GetInfo("account"):
        vk_session = vk_api.VkApi('{0}'.format(ac["login"]), '{0}'.format(ac["pass"]), captcha_handler=captcha_handler)
        vk_session.auth()
        ac_l = ac["login"]
        vk = vk_session.get_api()
        ac = vk.ads.getAccounts()[0]
        camp = vk.ads.getCampaigns(account_id=ac['account_id'])
        budgect = vk.ads.getBudget(account_id=ac['account_id'])
        database.Insert("account_monitor", "'{0}', '{1}', '{2}', '{3}'".format(ac["account_id"], budgect, ac["account_name"],
                                                                               ac_l))
        time.sleep(1)
        for cm in camp:
            database.Insert("company", "'{0}', '{1}', '{2}', '{3}'".format(cm['id'],ac["account_id"],
                                                                           cm["name"], ac["account_name"]))
            resp = vk.ads.getAds(account_id=ac["account_id"], include_deleted=1, campaign_ids="[{0}]".format(cm["id"]))
            adIds = {}
            for ad in resp:
                database.Insert("ads", "'{0}', '{1}', '{2}','{3}', '{4}', '{5}', {6}, {7}".format(ad["id"], ad["name"], cm["id"],
                                                                                        ac["account_id"],
                                                                                        cm["name"], ac["account_name"],
                                                                                        ad['status'], ad['all_limit']))
                adIds.update({str(ad["id"]): 0})
            StaticLoad(vk, ac["account_id"], adIds)
            time.sleep(1)


def StaticLoad(api, acid, adids):
    resp = api.ads.getStatistics(account_id=acid, ids_type="ad", period="day",
                                 ids=",".join(adids),
                                 date_from=0, date_to=0)
    for res in resp:
        static = []
        id = res["id"]
        if "stats" in res:
            for stat in res["stats"]:
                join = 0
                clicks = 0
                spent = 0
                reach = 0
                if "join_rate" in stat:
                    join = stat["join_rate"]
                if "clicks" in stat:
                    clicks = stat["clicks"]
                if "spent" in stat:
                    spent = stat["spent"]
                if "reach" in stat:
                    reach = stat["reach"]

                static.append((id, stat["day"], join, clicks, reach, 0, 0, 0, spent))
        database.InsertStatic(static)

# endregion

#region Account
def CreateAcc(name, login, password, spent, critik, join):
    database.Insert("account", "'{0}', '{1}','{2}','{3}','{4}','{5}'".format(name,
                                                                             login,
                                                                             password,
                                                                             spent,
                                                                             critik,
                                                                             join))
#endregion

# region Monitor
def GetMonitor(start, end):
    info = {"day": 0, 'info': {}}
    c = 0
    for ac in database.GetInfo("account"):
        c += 1
        for acv in database.GetInfo("account_monitor", sorting="office_login='{0}'".format(ac['login'])):
            start_d = datetime.strptime(start, "%Y-%m-%d")
            end_d = datetime.strptime(end, "%Y-%m-%d")
            day = start_d - end_d
            day = -day.days
            last_day = end_d.replace(day=end_d.day - 1).strftime("%Y-%m-%d")
            last = {'spent':0, 'join':0}
            spent = 0
            join = 0
            summ = acv["summ"]
            minimal = ac["minimal_budjet"]
            pale_join = ac["plane_join"]

            for ad in database.GetInfo("ads", sorting="id_ads_office='{0}'".format(acv["id"])):
                id = ad["id"]
                for static_ad in database.GetAds(start, end, "id_ads = '{0}'".format(id)):
                    spent += static_ad["spent"]
                    join += static_ad["join"]
                    if last_day == static_ad["date"]:
                        last['spent'] += static_ad["spent"]
                        last['join'] += static_ad["join"]

            max_per = ac["max_waste_per_month"] / 30 * day
            info['day'] = day
            info['info'].update({c: {"office": acv['id'], "name":ac["name"],"spent": spent, "join": join, "summ": summ,
                                  "minimal": minimal, "pale_join": pale_join, "max_per": max_per, "last": last}})


    return info

def GetStats(start, end):
    static = {}
    for ad in database.GetInfo("ads"):
        day = 0
        join = 0
        clicks = 0
        spent = 0
        reach = 0
        traffic = 0
        sale = 0
        join_message = 0
        id = ad["id"]
        for static_ad in database.GetAds(start, end, "id_ads = '{0}'".format(id)):
            day += 1
            clicks += static_ad["clicks"]
            spent += static_ad["spent"]
            reach += static_ad["reach"]
            traffic += static_ad["traffic"]
            sale += static_ad["sale"]
            join_message += static_ad["join_message"]
            join += static_ad["join"]

        if day != 0:
            static.update({id: {'day':day,'join': join,'clicks': clicks,'traffic': traffic,'reach': reach,
                                'join_message':join_message, 'name_ad':ad['name'], 'name_camp':ad['name_camp'],
                               'name_office':ad['name_office'], 'sale':sale}})

    return static

# endregion

# region Company
def GetCamp(start, end, type, office):
    static = {}
    c = 0
    start_d = datetime.strptime(start, "%Y-%m-%d")
    end_d = datetime.strptime(end, "%Y-%m-%d")
    day = start_d - end_d
    last_day = end_d.replace(day=end_d.day-1).strftime("%Y-%m-%d")
    day = -day.days
    for aci in database.GetInfo("account"):
        for ac in database.GetInfo("account_monitor", sorting="id='{0}'".format(office)):
            join = 0
            clicks = 0
            spent = 0
            reach = 0
            traffic = 0
            sale = 0
            join_message = 0
            name = ""
            office = ""
            last = {'spent':0, 'join':0}
            for ad in database.GetInfo("ads", "id_ads_office='{0}'".format(ac['id'])):
                if type.lower() in ad["name_camp"].lower():
                    id = ad["id"]
                    for static_ad in database.GetAds(start, end, "id_ads = '{0}'".format(id)):
                        if last_day == static_ad["date"]:
                            last['spent'] += static_ad["spent"]
                            last['join'] += static_ad["join"]
                        clicks += static_ad["clicks"]
                        spent += static_ad["spent"]
                        reach += static_ad["reach"]
                        traffic += static_ad["traffic"]
                        sale += static_ad["sale"]
                        join_message += static_ad["join_message"]
                        join += static_ad["join"]
                    office = ad['name_office']
                    name = ad["name_camp"]

            if name != "":
                static.update({c: {'day': day,'office': ac['id'],  'spent': spent,'join': join, 'clicks': clicks, 'traffic': traffic, 'reach': reach,
                                            'max_per': aci['max_waste_per_month'], 'join_message': join_message, 'name_camp': name,
                                            'name_office': office, 'sale': sale, 'last': last}})
            c += 1
    return static


def GetCampDet(start, end, office, type):
    c = 0
    end_d = datetime.strptime(end, "%Y-%m-%d")
    one_day = utils.Data(end_d, 1)
    seven_day = utils.Data(end_d, 7)
    day_30 = end_d.replace(month=end_d.month - 1).strftime("%Y-%m-%d")

    stats = {}

    for ac in database.GetInfo("account_monitor", "id='{0}'".format(office)):
        for cm in database.GetInfo("company", sorting="office_id='{0}'".format(ac['id'])):
            if type.lower() in cm['name_camp'].lower():
                join = 0
                spent = 0
                stat1 = {'join': 0, 'spent': 0, 'plane_join': 0, 'join_one': 0}
                stat7 = {'join': 0, 'spent': 0, 'plane_join': 0, 'join_one': 0}
                stat30 = {'join': 0, 'spent': 0, 'plane_join': 0, 'join_one': 0}
                stat = utils.getStats(start, end, "id_campagins='{0}'".format(cm['id']), type)
                join += stat['join']
                spent += stat['spent']
                stat = utils.getStats(one_day, end, "id_campagins='{0}'".format(cm['id']), type)
                stat1['join'] += stat['join']
                stat1['spent'] += stat['spent']
                stat = utils.getStats(seven_day, end, "id_campagins='{0}'".format(cm['id']), type)
                stat7['join'] += stat['join']
                stat7['spent'] += stat['spent']
                stat = utils.getStats(day_30, end, "id_campagins='{0}'".format(cm['id']), type)
                stat30['join'] += stat['join']
                stat30['spent'] += stat['spent']
                if stat1['join'] != 0:
                    stat1['join_one'] = stat1['spent'] / stat1['join']
                if stat7['join'] != 0:
                    stat7['join_one'] = stat7['spent'] / stat7['join']
                if stat30['join'] != 0:
                    stat30['join_one'] = stat30['spent'] / stat30['join']

                stats.update({c:{'name': cm['name_camp'], 'id': cm['id'], 'type': type,'join': join, 'spent': spent, 'period':{
                    '30': stat30,
                    '7': stat7,
                    '1': stat1
                }}})
                c += 1

    return stats
# endregion

# region Ads
def GetAds(start, end, camp_id):
    # region var
    stats = {}
    c = 0
    start_d = datetime.strptime(start, "%Y-%m-%d")
    end_d = datetime.strptime(end, "%Y-%m-%d")
    day = start_d - end_d
    last_day = end_d.replace(day=end_d.day-1).strftime("%Y-%m-%d")
    day = -day.days
    # endregion

    for ad in database.GetInfo('ads', sorting="id_campagins='{0}'".format(camp_id)):
        join = 0
        clicks = 0
        spent = 0
        reach = 0
        last = {'spent': 0, 'join': 0}
        for static_ad in database.GetAds(start, end, "id_ads = '{0}'".format(ad['id'])):
            if last_day == static_ad["date"]:
                last['spent'] += static_ad["spent"]
                last['join'] += static_ad["join"]
            clicks += static_ad["clicks"]
            spent += static_ad["spent"]
            reach += static_ad["reach"]
            join += static_ad["join"]

        joinsumm = 0

        if join != 0 and spent != 0:
            joinsumm = spent / join
        stats.update({c:{'status':ad['status'], 'join': join, 'name': ad['name'], 'join_summ': joinsumm,
                         'spent': spent, 'limit': ad['limit'], 'plane_join_summ': 10}})
        c += 1

    return stats


def GetAllAds(start, end, type):
    stats = {}
    c = 0

    join = 0
    spent = 0
    for ac in database.GetInfo("account_monitor"):
        stat = utils.getStats(start, end, "id_ads_office='{0}'".format(ac['id']), type)
        join += stat['join']
        spent += stat['spent']

        stats.update({c:{'name': ac['name'], 'idof': ac['id'], 'type':type,'join': join, 'spent': spent}})
        c += 1
    return stats

# endregion
