import time
from python3_anticaptcha import ImageToTextTask
import vk_api
from vklibary import database
from datetime import datetime

def captcha_handler(captcha):
    key = ImageToTextTask.ImageToTextTask(anticaptcha_key="f0d1147d67df6a70b77ccf1e41372dc1", save_format='const') \
        .captcha_handler(captcha_link=captcha.get_url())

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key['solution']['text'])


def UploadInfo():
    database.Clear("ads")
    database.Clear("static")
    database.Clear("account_monitor")
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
            resp = vk.ads.getAds(account_id=ac["account_id"], include_deleted=1, campaign_ids="[{0}]".format(cm["id"]))
            adIds = {}
            for ad in resp:
                database.Insert("ads", "'{0}', '{1}', '{2}','{3}', '{4}', '{5}'".format(ad["id"], ad["name"], cm["id"],
                                                                                        ac["account_id"],
                                                                                        cm["name"], ac["account_name"]))
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


def CreateAcc(name, login, password, spent, critik, join):
    database.Insert("account", "'{0}', '{1}','{2}','{3}','{4}','{5}'".format(name,
                                                                             login,
                                                                             password,
                                                                             spent,
                                                                             critik,
                                                                             join))


def GetMonitor(start, end):
    info = {"day": 0, 'info': {}}
    c = 0
    for ac in database.GetInfo("account"):
        c += 1
        for acv in database.GetInfo("account_monitor", sorting="office_login='{0}'".format(ac['login'])):
            start_d = datetime.strptime(start, "%Y-%m-%d")
            print(start_d)
            end_d = datetime.strptime(end, "%Y-%m-%d")
            day = start_d - end_d
            day = -day.days
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

            max_per = ac["max_waste_per_month"] / 30 * day
            info['day'] = day
            info['info'].update({c: [{"name":ac["name"],"spent": spent, "join": join, "summ": summ,
                                  "minimal": minimal, "pale_join": pale_join, "max_per": max_per}]})

    return info