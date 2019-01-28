import requests
import json
import argparse 
import time

if __name__ == '__main__': # Initialize the parser 

    parser = argparse.ArgumentParser( description="SE Power consumption" )
    parser.add_argument('-u','--user', help="Password")
    parser.add_argument('-p','--password', help="Password")
    parser.add_argument('-d','--date', help="date 1990-01-31")
    arguments = parser.parse_args()

    pattern = '%Y-%m-%d %H:%M:%S'

    #x = time.strptime(arguments.date + " 00:00:00", pattern)

    start_time = str(int(time.mktime(time.strptime(arguments.date + " 00:00:00", pattern)))*1000)
    stop_time = str((int(time.mktime(time.strptime(arguments.date + " 00:00:00", pattern)) )+60*60*24)*1000)


    with requests.Session() as s:
        s.get('http://webtools3.se.dk')
        payload = {'username': arguments.user, 'password': arguments.password , 'rememberLogin': 'false'}
        r = s.post("http://webtools3.se.dk/wts/login", data=payload)

        xx = json.loads(r.text)
        sessionx = xx.get('sessionId')
        v = s.get('http://webtools3.se.dk/wts/itemGroups',headers={"Session-Id":sessionx})#  /wts/itemGroups')
        yy = json.loads(v.text)
        to_readout = []
        for item in yy:
            if item.get('userId') == xx.get('id'):
                items = item.get('items')
                for channel in items:
                    if channel.get('active') == True:
                        dataxx = {}
                        data={"id":channel.get('id'), "set":dataxx}
                    
                        for series in channel.get('series'):
                            if series.get('seriesType') == 'usageConsumptionBought':
                                dataxx["usageConsumptionBought"] =  series.get('id')
                            if series.get('seriesType') == 'usageConsumptionNet':
                                dataxx["usageConsumptionNet"] =  series.get('id')
                            if series.get('seriesType') == 'usageConsumptionSold':
                                dataxx["usageConsumptionSold"] =  series.get('id')
                        if len(dataxx) == 3:  # Checks all 3 is there - maybe change to detection of types...
                            to_readout.append(data)

        payload = {'itemCategory': 'SonWinMeter', 
                   'start': start_time, 
                   'end': stop_time} 

        data_out = {}
        for count, data_set in enumerate(to_readout):
            payload['itemId'] = data_set.get('id')
            x=0
            for key,value in  data_set.get('set').items() :
                kl={"id":key}
                payload['series['+ str(x) + '][seriesId]'] = value
                payload['series['+ str(x) + '][prescaleUnitId]'] = 'kilo@energy_watt'
                payload['series['+ str(x) + '][zoomLevelId]'] = 'day_by_hours'
                x +=1
                data_out[key] = kl

        l = s.post("http://webtools3.se.dk/wts/seriesData", data=payload,headers={"Session-Id":sessionx})
        mm = json.loads(l.text)
        for item,data_in in zip(data_out,mm):
            data_out[item]['total'] = data_in['total']
            data_out[item]['average'] = data_in['average']
            data_usage = {}
            for bn in data_in['datapoints']:
                data_usage[bn['end']] = bn['value']
            data_out[item]['data'] = data_usage
        print(json.dumps(data_out))
