from vklibary import database


def getStats(start, end, sorting, type):
    join = 0
    spent = 0
    static = database.GetAds(start, end)
    for ad in database.GetInfo('ads', sorting):
        if type.lower() in ad["name_camp"].lower():
            for static_ad in static:
                if static_ad['id_ads'] == ad['id']:
                    join += static_ad['join']
                    spent += static_ad['spent']
                status = ad['status']

    return {'join':join, 'spent': spent}


num_days=(31,28,31,30,31,30,31,31,30,31,30,31)


def Data(dat, day):
  days = dat.day - day

  if days < 1:
    days = -days
    new = dat.replace(month=dat.month - 1,
    day=num_days[dat.month] - days)
    return new.strftime("%Y-%m-%d")
  new = dat.replace(day=dat.day-day)
  return new.strftime("%Y-%m-%d")
