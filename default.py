# -*- coding: utf-8 -*-

import os, sys, dateutil, time, urllib2, unicodedata, random, string
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import json

#import dateutil.parser
from datetime import datetime
from dateutil import tz
from dateutil import parser



ADDON		= xbmcaddon.Addon()
ADDONNAME	= ADDON.getAddonInfo('name')
ADDONID		= ADDON.getAddonInfo('id')
CWD		= ADDON.getAddonInfo('path').decode("utf-8")
ADDONVERSION	= ADDON.getAddonInfo('version')
LANGUAGE	= ADDON.getLocalizedString
RESOURCE	= xbmc.translatePath( os.path.join( CWD, 'resources', 'lib' ).encode("utf-8") ).decode("utf-8")
PROFILE		= xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

sys.path.append(RESOURCE)

from utils import *

#APPID		= ADDON.getSetting('API')
#BASE_URL	= 'https://api.weather.gov/'
#LATLON		= ADDON.getSetting('LatLon')
#WEEKEND	= ADDON.getSetting('Weekend')
#STATION	= ADDON.getSetting('Station')
#MAPS		= ADDON.getSetting('WMaps')
#ZOOM		= str(int(ADDON.getSetting('Zoom')) + 2)
WEATHER_ICON	= xbmc.translatePath('%s.png').decode("utf-8")
DATEFORMAT	= xbmc.getRegion('dateshort')
TIMEFORMAT	= xbmc.getRegion('meridiem')
KODILANGUAGE	= xbmc.getLanguage().lower()
MAXDAYS		= 10


def clear():
	set_property('Current.Condition'	, 'N/A')
	set_property('Current.Temperature'	, '0')
	set_property('Current.Wind'		, '0')
	set_property('Current.WindDirection'	, 'N/A')
	set_property('Current.Humidity'		, '0')
	set_property('Current.FeelsLike'	, '0')
	set_property('Current.UVIndex'		, '0')
	set_property('Current.DewPoint'		, '0')
	set_property('Current.OutlookIcon'	, 'na.png')
	set_property('Current.FanartCode'	, 'na')
	for count in range (0, MAXDAYS+1):
		set_property('Day%i.Title'	% count, 'N/A')
		set_property('Day%i.HighTemp'	% count, '0')
		set_property('Day%i.LowTemp'	% count, '0')
		set_property('Day%i.Outlook'	% count, 'N/A')
		set_property('Day%i.OutlookIcon' % count, 'na.png')
		set_property('Day%i.FanartCode'	% count, 'na')

def refresh_locations():
	locations = 0
	for count in range(1, 6):
		loc_name = ADDON.getSetting('Location%s' % count)
		if loc_name != '':
			locations += 1
		else:
			ADDON.setSetting('Location%sID' % count, '')
			ADDON.setSetting('Location%sdeg' % count, '')

		set_property('Location%s' % count, loc_name)

	set_property('Locations', str(locations))
	log('available locations: %s' % str(locations))

def get_initial(loc):
	url = 'https://api.weather.gov/points/%s' % loc
	log("url:"+url)
	try:
		req = urllib2.urlopen(url)
		response = req.read()
		req.close()
	except:
		response = ''
	return response
	
def code_from_icon(icon):
		icon=icon.rsplit('?', 1)[0]
		code=icon.rsplit('/',1)[1]
		thing=code.split(",")
		if len(thing) > 1:
			rain=thing[1]
			code=thing[0]
			return code, rain
		else:
			code=thing[0]
			return code, ''
		

def get_data(url):
	#url = BASE_URL % search_string
	try:
		req = urllib2.urlopen(url)
		response = req.read()
		req.close()
	except:
		response = ''
	return response

def get_timestamp(datestr):
	#"2019-04-29T16:00:00-04:00"
	#iso_fmt = '%Y-%m-%dT%H:%M:%S%z'
	#newtext = datestr[:21] + datestr[23:]
	#datestamp=datetime.datetime.strptime(datestr,iso_fmt)
	datestamp=dateutil.parser.parse(datestr)
	return time.mktime(datestamp.timetuple())


def convert_date(stamp):
	if str(stamp).startswith('-'):
		return ''
	date_time = time.localtime(stamp)
	if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
		localdate = time.strftime('%d-%m-%Y', date_time)
	elif DATEFORMAT[1] == 'm' or DATEFORMAT[0] == 'M':
		localdate = time.strftime('%m-%d-%Y', date_time)
	else:
		localdate = time.strftime('%Y-%m-%d', date_time)

	if TIMEFORMAT != '/':
		localtime = time.strftime('%I:%M%p', date_time)
	else:
		localtime = time.strftime('%H:%M', date_time)
	return localtime + '	' + localdate

def get_time(stamp):
	date_time = time.localtime(stamp)
	if TIMEFORMAT != '/':
		localtime = time.strftime('%I:%M%p', date_time)
	else:
		localtime = time.strftime('%H:%M', date_time)
	return localtime

def get_weekday(stamp, form):
	date_time = time.localtime(stamp)
	weekday = time.strftime('%w', date_time)
	if form == 's':
		return xbmc.getLocalizedString(WEEK_DAY_SHORT[weekday])
	elif form == 'l':
		return xbmc.getLocalizedString(WEEK_DAY_LONG[weekday])
	else:
		return int(weekday)

def get_month(stamp, form):
	date_time = time.localtime(stamp)
	month = time.strftime('%m', date_time)
	day = time.strftime('%d', date_time)
	if form == 'ds':
		label = day + ' ' + xbmc.getLocalizedString(MONTH_NAME_SHORT[month])
	elif form == 'dl':
		label = day + ' ' + xbmc.getLocalizedString(MONTH_NAME_LONG[month])
	elif form == 'ms':
		label = xbmc.getLocalizedString(MONTH_NAME_SHORT[month]) + ' ' + day
	elif form == 'ml':
		label = xbmc.getLocalizedString(MONTH_NAME_LONG[month]) + ' ' + day
	return label

def geoip():
	try:
		req = urllib2.urlopen('http://freegeoip.net/json/')
		response = req.read()
		req.close()
	except:
		response = ''
		log('failed to retrieve geoip location')
	if response:
		data = json.loads(response)
		if data and data.has_key('city') and data.has_key('country_name'):
			city, country = data['city'], data['country_name']
			return '%s, %s' % (city, country)

def location(locstr,prefix):
	log('searching for location: %s' % locstr)
	query = get_initial(locstr)
	log('location data: %s' % query)
	if not query:
		log('failed to retrieve location data')
		return None
	try:
		data = json.loads(query)
	except:
		log('failed to parse location data')
		return None
	if data != '' and 'properties' in data:
		#radarStation = data['properties']['radarStation']
		city	=	data['properties']['relativeLocation']['properties']['city']
		state =		data['properties']['relativeLocation']['properties']['state']
		locationName=	city+" "+state
		lat =		str(data['geometry']['coordinates'][1])
		lon =		str(data['geometry']['coordinates'][0])
		locationLatLong=lat+','+lon

		cwa=			data['properties']['cwa']
		#forecastZone=		data['properties']['forecastZone']
		forecastZone=		data['properties']['county']
		zone=forecastZone.rsplit('/',1)[1]
		forecastGridData_url =	data['properties']['forecastGridData']
		forecastHourly_url =	data['properties']['forecastHourly']
		forecast_url =		data['properties']['forecast']
		stations_url =		data['properties']['observationStations']
		
		
		ADDON.setSetting(prefix+'Name',			locationName)
		ADDON.setSetting(prefix,			locationLatLong)
		ADDON.setSetting(prefix+'cwa',				cwa)
		ADDON.setSetting(prefix+'Zone',			zone)
		ADDON.setSetting(prefix+'forecastGrid_url',	forecastGridData_url)
		ADDON.setSetting(prefix+'forecastHourly_url', forecastHourly_url)
		ADDON.setSetting(prefix+'forecast_url',	forecast_url)
		#ADDON.setSetting(prefix+'radarStation',	radarStation)
		query = get_data(stations_url)
		log('location data: %s' % query)
		if not query:
			log('failed to retrieve location data')
			return None
		try:
			odata = json.loads(query)
		except:
			log('failed to parse location data')
			return None
		if odata != '' and 'features' in odata:
			stations={}
			stationlist=[]
			
			for count, item in enumerate(odata['features']):
				stationId=item['properties']['stationIdentifier']
				stationName=item['properties']['name']
				stationlist.append(stationName)
				stations[stationName]=stationId

			#xbmc.log('stationlist: %s' % stationlist,level=xbmc.LOGNOTICE)
			#xbmc.log('stations: %s' % stations,level=xbmc.LOGNOTICE)

			dialog = xbmcgui.Dialog()
			i=dialog.select("Select local weather station for current weather",stationlist)
			#xbmc.log('selected station name: %s' % stationlist[i],level=xbmc.LOGNOTICE)
			#xbmc.log('selected station: %s' % stations[stationlist[i]],level=xbmc.LOGNOTICE)

			ADDON.setSetting(prefix+'Station',stations[stationlist[i]])
			ADDON.setSetting(prefix+'StationName',stationlist[i])


def dailyforecast(num):
#
#	if MAPS == 'true' and xbmc.getCondVisibility('System.HasAddon(script.openweathermap.maps)'):
#		lat = float(eval(locationdeg)[0])
#		lon = float(eval(locationdeg)[1])
#		xbmc.executebuiltin('XBMC.RunAddon(script.openweathermap.maps,lat=%s&lon=%s&zoom=%s&api=%s&debug=%s)' % (lat, lon, ZOOM, APPID, DEBUG))
#	else:
#		set_property('Map.IsFetched', '')
#		for count in range (1, 6):
#			set_property('Map.%i.Layer' % count, '')
#			set_property('Map.%i.Area' % count, '')
#			set_property('Map.%i.Heading' % count, '')
#			set_property('Map.%i.Legend' % count, '')
#	try:
#		lang = LANG[KODILANGUAGE]
#		if lang == '':
#			lang = 'en'
#	except:
#		lang = 'en'
#	query = locid
#	if not locid.startswith('lat'):
#		query = 'id=' + locid
#	if STATION == 'true':
#		station_id = ADDON.getSetting('StationID')
#		station_string = 'station?id=%s&lang=%s&APPID=%s&units=metric' % (station_id, lang, APPID)

	forecast_url=ADDON.getSetting('Location'+str(num)+'forecast_url')		
	log('forecast url: %s' % forecast_url)
			
	##current_props(current_weather,loc)

	daily_data = get_data(forecast_url)
	log('daily data: %s' % daily_data)
	try:
		daily_weather = json.loads(daily_data)
	except:
		log('parsing daily data failed')
		daily_weather = ''
	if daily_weather and daily_weather != '' and 'properties' in daily_weather:
		data=daily_weather['properties']
	else:
		return None

	for count, item in enumerate(data['periods']):
		#code = str(item['weather'][0].get('id',''))
		icon = item['icon']
		#https://api.weather.gov/icons/land/night/ovc?size=small
		icon=icon.rsplit('?', 1)[0]
		code, rain=code_from_icon(icon)
		#xbmc.log('icon %s' % icon,level=xbmc.LOGNOTICE)
		#xbmc.log('code %s' % code,level=xbmc.LOGNOTICE)

		weathercode = WEATHER_CODES.get(code)
		starttime=item['startTime']
		startstamp=get_timestamp(starttime)
		set_property('Day%i.isDaytime'		% (count),str(item['isDaytime']))
		set_property('Day%i.Title'		% (count), item['name'])
		if item['isDaytime'] == True:
			set_property('Day%i.HighTemp'	% (count), str(FtoC(item['temperature'])))
			set_property('Day%i.LowTemp'	% (count), str(FtoC(item['temperature'])))
		if item['isDaytime'] == False:
			set_property('Day%i.HighTemp'	% (count), str(FtoC(item['temperature'])))
			set_property('Day%i.LowTemp'	% (count), str(FtoC(item['temperature'])))

		set_property('Day%i.Outlook'		% (count), item['shortForecast'])

		#set_property('Day%i.Details'		% (count+1), item['detailedForecast'])
		set_property('Day%i.OutlookIcon'	% (count), weathercode)
		set_property('Day%i.RemoteIcon'		% (count), icon)
		# NOTE: Day props are 0 based, but Daily/Hourly are 1 based
		set_property('Daily.%i.isDaytime'	% (count+1),str(item['isDaytime']))
		set_property('Daily.%i.Outlook'		% (count+1), item['detailedForecast'])
		set_property('Daily.%i.ShortOutlook'	% (count+1), item['shortForecast'])
		
		set_property('Daily.%i.RemoteIcon'	% (count+1), icon)
		set_property('Daily.%i.OutlookIcon'	% (count+1), WEATHER_ICON % weathercode)
		set_property('Daily.%i.FanartCode'	% (count+1), weathercode)
		set_property('Daily.%i.WindDirection'	% (count+1), item['windDirection'])
		set_property('Daily.%i.WindSpeed'	% (count+1), item['windSpeed'])

		if item['isDaytime'] == True:
			set_property('Daily.%i.LongDay'		% (count+1), item['name'])
			set_property('Daily.%i.ShortDay'	% (count+1), get_weekday(startstamp,'s')+" (d)")
			set_property('Daily.%i.TempDay'		% (count+1), str(item['temperature'])+item['temperatureUnit'])
			set_property('Daily.%i.HighTemperature'	% (count+1), str(item['temperature'])+item['temperatureUnit'])
			set_property('Daily.%i.TempNight'	% (count+1), '')
			set_property('Daily.%i.LowTemperature'	% (count+1), '')
		if item['isDaytime'] == False:
			set_property('Daily.%i.LongDay'		% (count+1), item['name'])
			set_property('Daily.%i.ShortDay'	% (count+1), get_weekday(startstamp,'s')+" (n)")
			set_property('Daily.%i.TempDay'		% (count+1), '')
			set_property('Daily.%i.HighTemperature'	% (count+1), '')
			set_property('Daily.%i.TempNight'	% (count+1), str(item['temperature'])+item['temperatureUnit'])
			set_property('Daily.%i.LowTemperature'	% (count+1), str(item['temperature'])+item['temperatureUnit'])
		#set_property('Daily.%i.LongDay'		% (count+1), get_weekday(startstamp, 'l'))
		#set_property('Daily.%i.ShortDay'		% (count+1), get_weekday(startstamp,'s'))
		if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
			set_property('Daily.%i.LongDate'	% (count+1), get_month(startstamp, 'dl'))
			set_property('Daily.%i.ShortDate'	% (count+1), get_month(startstamp, 'ds'))
		else:
			set_property('Daily.%i.LongDate'	% (count+1), get_month(startstamp, 'ml'))
			set_property('Daily.%i.ShortDate'	% (count+1), get_month(startstamp, 'ms'))
		if (rain !=''):
			set_property('Daily.%i.Precipitation'	% (count+1), rain + '%')
		else:
			set_property('Daily.%i.Precipitation'	% (count+1), '')
			
#		set_property('Daily.%i.WindDegree'	% (count+1), str(item.get('deg','')) + u'°')
#		set_property('Daily.%i.Humidity'	% (count+1), str(item.get('humidity','')) + '%')
#		set_property('Daily.%i.TempMorn'	% (count+1), TEMP(item['temp']['morn']) + TEMPUNIT)
#		set_property('Daily.%i.TempDay'		% (count+1), TEMP(item['temp']['day']) + TEMPUNIT)
#		set_property('Daily.%i.TempEve'		% (count+1), TEMP(item['temp']['eve']) + TEMPUNIT)
#		set_property('Daily.%i.TempNight'	% (count+1), TEMP(item['temp']['night']) + TEMPUNIT)
#		set_property('Daily.%i.HighTemperature' % (count+1), TEMP(item['temp']['max']) + TEMPUNIT)
#		set_property('Daily.%i.LowTemperature'	% (count+1), TEMP(item['temp']['min']) + TEMPUNIT)
#		set_property('Daily.%i.FeelsLike'	% (count+1), FEELS_LIKE(item['temp']['day'], item['speed'] * 3.6, item['humidity']) + TEMPUNIT)
#		set_property('Daily.%i.DewPoint'	% (count+1), DEW_POINT(item['temp']['day'], item['humidity']) + TEMPUNIT)


def currentforecast(num):
	station=ADDON.getSetting('Location'+str(num)+'Station')
	url="https://api.weather.gov/stations/%s/observations/latest" %station	
	current_data=get_data(url)
	#xbmc.log('current data: %s' % current_data,level=xbmc.LOGNOTICE)
	try:
		current = json.loads(current_data)
	except:
		xbmc.log('parsing current data failed' ,level=xbmc.LOGNOTICE)
		current = ''
	if current and current != '' and 'properties' in current:
		data=current['properties']
		#xbmc.log('data: %s' % data,level=xbmc.LOGNOTICE)
	else:
		xbmc.log('Failed to find current data' ,level=xbmc.LOGNOTICE)
		return None
	
	#xbmc.log('data %s' % data,level=xbmc.LOGNOTICE)
	icon = data['icon']
	#https://api.weather.gov/icons/land/night/ovc?size=small
	icon=icon.rsplit('?', 1)[0]
	code, rain=code_from_icon(icon)
	weathercode = WEATHER_CODES.get(code)
	#set_property('Current.Location', loc)
	set_property('Current.RemoteIcon',icon) 
	set_property('Current.OutlookIcon', '%s.png' % weathercode) # xbmc translates it to Current.ConditionIcon
	set_property('Current.FanartCode', weathercode)
	set_property('Current.Condition', FORECAST.get(data.get('textDescription'), data.get('textDescription')))
	try:
		set_property('Current.Humidity'	, str(round(data.get('relativeHumidity').get('value'))))
	except:
		set_property('Current.Humidity'		, '')
				
	try:
		temp=int(round(data.get('temperature').get('value')))
		#xbmc.log('raw temp %s' % data.get('temperature').get('value'),level=xbmc.LOGNOTICE)
		#xbmc.log('temp %s' % temp,level=xbmc.LOGNOTICE)
		set_property('Current.Temperature',str(temp)) # api values are in C
	except:
		set_property('Current.Temperature','') 
	try:
		set_property('Current.Wind', str(int(round(data.get('windSpeed').get('value') * 3.6))))
	except:
		set_property('Current.Wind','')

	try:
		set_property('Current.WindDirection', xbmc.getLocalizedString(WIND_DIR(int(round(data.get('windDirection').get('value'))))))
	except:
		set_property('Current.WindDirection', '')

	#set_property('Current.Precipitation',	str(round(data.get('precipitationLast3Hours').get('value') *	0.04 ,2)) + ' in')
	if (rain != ''):
		set_property('Current.ChancePrecipitaion', str(rain)+'%');
	else :
		set_property('Current.ChancePrecipitaion'		, '');

	try:
		set_property('Current.FeelsLike', FEELS_LIKE(data.get('temperature').get('value'), data.get('windSpeed').get('value') * 3.6, data.get('relativeHumidity').get('value'), False))
	except:
		set_property('Current.FeelsLike', '')

#	if 'calc' in data['last'] and 'dewpoint' in data['last']['calc']:
#		if data['last']['main']['temp'] - data['last']['calc']['dewpoint'] > 100:
	try:
		set_property('Current.DewPoint', str(int(round(data.get('relativeHumidity').get('value'))))) # api values are in C
	except:
		set_property('Current.DewPoint', '') 

#		else:
#			set_property('Current.DewPoint'	, str(int(round(data['last']['calc']['dewpoint'])) - 273)) # api values are in K
#	else:
#		try:
#			set_property('Current.DewPoint'	, DEW_POINT(data['last']['main']['temp'] -273, data['last']['main']['humidity'], False)) # api values are in K
#		except:
#			pass
#	#set_property('Current.UVIndex'			, '') # no idea how the api returns it, use data from current_props()
# # extended properties
#	if 'clouds' in data['last']:
#		set_property('Current.Cloudiness'	, data['last']['clouds'][0].get('condition',''))
#	if 'wind' in data['last'] and 'gust' in data['last']['wind']:

	try:
		set_property('Current.WindGust'	, SPEED(data.get('windGust').get('value',0)) + SPEEDUNIT)
	except:
		set_property('Current.WindGust'	, '')
		
#	if 'rain' in data['last'] and '1h' in data['last']['rain']:
#		if 'F' in TEMPUNIT:
#			set_property('Current.Precipitation', str(round(data['last']['rain']['1h'] *	0.04 ,2)) + ' in')
#		else:
#			set_property('Current.Precipitation', str(int(round(data['last']['rain']['1h']))) + ' mm')
#	if 'main' in data['last'] and 'pressure' in data['last']['main']:
#		if 'F' in TEMPUNIT:
#			set_property('Current.Pressure'	, str(round(data['last']['main']['pressure'] / 33.86 ,2)) + ' in')
#		else:
#			set_property('Current.Pressure'	, str(data['last']['main']['pressure']) + ' mb')




# def current_props(data,loc):
#	if not 'weather' in data:
#		return
# # standard properties
#	code = str(data['weather'][0].get('id',''))
#	icon = data['weather'][0].get('icon','')
#	if icon.endswith('n'):
#		code = code + 'n'
#	weathercode = WEATHER_CODES[code]
#	set_property('Current.Location'			, loc)
#	set_property('Current.Condition'			, FORECAST.get(data['weather'][0].get('description',''), data['weather'][0].get('description','')))
#	if 'temp' in data['main']:
#		set_property('Current.Temperature'	, str(int(round(data['main']['temp']))))
#		set_property('Current.DewPoint'		, DEW_POINT(data['main']['temp'], data['main']['humidity'], False))
#	else:
#		set_property('Current.Temperature'	, '')
#		set_property('Current.DewPoint'		, '')
#	if 'speed' in data['wind']:
#		set_property('Current.Wind'			, str(int(round(data['wind']['speed'] * 3.6))))
#		if 'temp' in data['main']:
#			set_property('Current.FeelsLike'	, FEELS_LIKE(data['main']['temp'], data['wind']['speed'] * 3.6, data['main']['humidity'], False))
#		else:
#			set_property('Current.FeelsLike'	, '')
#	else:
#		set_property('Current.Wind'			, '')
#		set_property('Current.FeelsLike'		, '')
#	if 'deg' in data['wind']:
#		set_property('Current.WindDirection'	, xbmc.getLocalizedString(WIND_DIR(int(round(data['wind']['deg'])))))
#	else:
#		set_property('Current.WindDirection'	, '')
#	set_property('Current.Humidity'			, str(data['main'].get('humidity','')))
#	set_property('Current.UVIndex'			, '') # not supported by openweathermap
#	set_property('Current.OutlookIcon'		, '%s.png' % weathercode) # xbmc translates it to Current.ConditionIcon
#	set_property('Current.FanartCode'		, weathercode)
#	set_property('Location'					, loc)
#	set_property('Updated'					, convert_date(data.get('dt','')))
# # extended properties
#	set_property('Current.Cloudiness'		, str(data['clouds'].get('all','')) + '%')
#	set_property('Current.ShortOutlook'		, FORECAST.get(data['weather'][0].get('main',''), data['weather'][0].get('main','')))
#	if 'temp_min' in data['main']:
#		set_property('Current.LowTemperature'	, TEMP(data['main']['temp_min']) + TEMPUNIT)
#	else:
#		set_property('Current.LowTemperature'	, '')
#	if 'temp_max' in data['main']:
#		set_property('Current.HighTemperature'	, TEMP(data['main']['temp_max']) + TEMPUNIT)
#	else:
#		set_property('Current.HighTemperature'	, '')
#	if 'F' in TEMPUNIT:
#		set_property('Current.Pressure'		, str(round(data['main']['pressure'] / 33.86 ,2)) + ' in')
#		if 'sea_level' in data['main']:
#			set_property('Current.SeaLevel'	, str(round(data['main']['sea_level'] / 33.86 ,2)) + ' in')
#		else:
#			set_property('Current.SeaLevel'	, '')
#		if 'grnd_level' in data['main']:
#			set_property('Current.GroundLevel'	, str(round(data['main']['grnd_level'] / 33.86 ,2)) + ' in')
#		else:
#			set_property('Current.GroundLevel'	, '')
#		rain = 0
#		snow = 0
#		if 'rain' in data:
#			if '1h' in data['rain']:
#				rain = data['rain']['1h']
#			elif '3h' in data['rain']:
#				rain = data['rain']['3h']
#			set_property('Current.Rain'		, str(round(rain *	0.04 ,2)) + ' in')
#		else:
#			set_property('Current.Rain'		, '')
#		if 'snow' in data:
#			if '1h' in data['snow']:
#				snow = data['snow']['1h']
#			elif '3h' in data['snow']:
#				snow = data['snow']['3h']
#			set_property('Current.Snow'		, str(round(snow *	0.04 ,2)) + ' in')
#		else:
#			set_property('Current.Snow'		, '')
#		precip = rain + snow
#		set_property('Current.Precipitation'	, str(round(precip *	0.04 ,2)) + ' in')
#	else:
#		set_property('Current.Pressure'		, str(data['main'].get('pressure','')) + ' mb')
#		set_property('Current.SeaLevel'		, str(data['main'].get('sea_level','')) + ' mb')
#		set_property('Current.GroundLevel'	, str(data['main'].get('grnd_level','')) + ' mb')
#		rain = 0
#		snow = 0
#		if 'rain' in data:
#			if '1h' in data['rain']:
#				rain = data['rain']['1h']
#			elif '3h' in data['rain']:
#				rain = data['rain']['3h']
#			set_property('Current.Rain'		, str(int(round(rain))) + ' mm')
#		else:
#			set_property('Current.Rain'		, '')
#		if 'snow' in	data:
#			if '1h' in data['snow']:
#				snow = data['snow']['1h']
#			elif '3h' in data['snow']:
#				snow = data['snow']['3h']
#			set_property('Current.Snow'		, str(int(round(snow))) + ' mm')
#		else:
#			set_property('Current.Snow'		, '')
#		precip = rain + snow
#		set_property('Current.Precipitation'	, str(int(round(precip))) + ' mm')
#	if 'gust' in data['wind']:
#		set_property('Current.WindGust'		, SPEED(data['wind']['gust']) + SPEEDUNIT)
#	else:
#		set_property('Current.WindGust'		, '')
#	if 'var_beg' in data['wind']:
#		set_property('Current.WindDirStart'	, xbmc.getLocalizedString(WIND_DIR(data['wind']['var_beg'])))
#	else:
#		set_property('Current.WindDirStart'	, '')
#	if 'var_end' in data['wind']:
#		set_property('Current.WindDirEnd'	, xbmc.getLocalizedString(WIND_DIR(data['wind']['var_end'])))
#	else:
#		set_property('Current.WindDirEnd'	, '')
#	set_property('Forecast.City'				, data.get('name',''))
#	set_property('Forecast.Country'			, data['sys'].get('country',''))
#	set_property('Forecast.Latitude'			, str(data['coord'].get('lat','')))
#	set_property('Forecast.Longitude'		, str(data['coord'].get('lon','')))
#	set_property('Forecast.Updated'			, convert_date(data.get('dt','')))
#	try:
#		set_property('Today.Sunrise'			, convert_date(data['sys'].get('sunrise','')).split('	')[0])
#	except:
#		set_property('Today.Sunrise'			, '')
#	try:
#		set_property('Today.Sunset'			, convert_date(data['sys'].get('sunset','')).split('	')[0])
#	except:
#		set_property('Today.Sunset'			, '')

#def full_daily_props():
#	mastermap = {}
#	#https://api.weather.gov/gridpoints/OKX/57,70
#	forecast_url=ADDON.getSetting('Location'+str(num)+'forecastGrid_url')		
#	log('forecast url: %s' % forecast_url)
#			
#	##current_props(current_weather,loc)
#
#	grid_data = get_data(forecast_url)
#	#log('daily data: %s' % daily_data)
#	try:
#		grid_weather = json.loads(grid_data)
#	except:
#		log('parsing daily data failed')
#		_weather = ''
#	if grid_weather and grid_weather != '' and 'properties' in grid_weather:
#		data=grid_weather['properties']
#	else:
#		return None
#
#	for count, item in enumerate(data['periods']):
	

#	if not 'periods' in data:
#		return
# # standard properties
#	
#	for count, item in enumerate(data['periods']):
#		#code = str(item['weather'][0].get('id',''))
#		icon = item['icon']
#		#https://api.weather.gov/icons/land/night/ovc?size=small
#		icon=icon.rsplit('?', 1)[0]
#		code=icon.rsplit('/',1)[1]
#		weathercode = WEATHER_CODES.get(code)
#		set_property('Day%i.Title'			% (count+1), item['name'])
#		if item['isDaytime'] == True:
#			set_property('Day%i.HighTemp'	% (count+1), str(FtoC(item['temperature'])))
#		if item['isDaytime'] == False:
#			set_property('Day%i.LowTemp'		% (count+1), str(FtoC(item['temperature'])))
#		set_property('Day%i.Outlook'			% (count+1), item['shortForecast'])
#		#set_property('Day%i.Details'			% (count+1), item['detailedForecast'])
#		set_property('Day%i.OutlookIcon'		% (count+1), weathercode)
# 
#		set_property('Daily.%i.Outlook'		% (count+1), item['detailedForecast'])
#		set_property('Daily.%i.ShortOutlook'	% (count+1), item['shortForecast'])
#		
#		set_property('Daily.%i.RemoteIcon'	% (count+1), icon)
#		set_property('Daily.%i.OutlookIcon'	% (count+1), WEATHER_ICON % weathercode)
#		set_property('Daily.%i.FanartCode'	% (count+1), weathercode)
#		set_property('Daily.%i.WindDirection'	% (count+1), item['windDirection'])
#		set_property('Daily.%i.WindSpeed'	% (count+1), item['windSpeed'])
#		if item['isDaytime'] == True:
#			set_property('Daily.%i.TempDay'			% (count+1), str(item['temperature'])+item['temperatureUnit'])
#			set_property('Daily.%i.HighTemperature'	% (count+1), str(item['temperature'])+item['temperatureUnit'])
#		if item['isDaytime'] == False:
#			set_property('Daily.%i.TempNight'		% (count+1), str(item['temperature'])+item['temperatureUnit'])
#			set_property('Daily.%i.LowTemperature'	% (count+1), str(item['temperature'])+item['temperatureUnit'])
#		starttime=item['startTime']
#		startstamp=get_timestamp(starttime)
#		set_property('Daily.%i.LongDay'		% (count), get_weekday(startstamp, 'l'))
#		set_property('Daily.%i.ShortDay'		% (count), get_weekday(startstamp,'s'))
#		if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
#			set_property('Daily.%i.LongDate'	% (count), get_month(startstamp, 'dl'))
#			set_property('Daily.%i.ShortDate'	% (count), get_month(startstamp, 'ds'))
#		else:
#			set_property('Daily.%i.LongDate'	% (count), get_month(startstamp, 'ml'))
#			set_property('Daily.%i.ShortDate'	% (count), get_month(startstamp, 'ms'))
#			
#		set_property('Daily.%i.WindDegree'	% (count+1), str(item.get('deg','')) + u'°')
#		set_property('Daily.%i.Humidity'		% (count+1), str(item.get('humidity','')) + '%')
#		set_property('Daily.%i.TempMorn'		% (count+1), TEMP(item['temp']['morn']) + TEMPUNIT)
#		set_property('Daily.%i.TempDay'		% (count+1), TEMP(item['temp']['day']) + TEMPUNIT)
#		set_property('Daily.%i.TempEve'		% (count+1), TEMP(item['temp']['eve']) + TEMPUNIT)
#		set_property('Daily.%i.TempNight'	% (count+1), TEMP(item['temp']['night']) + TEMPUNIT)
#		set_property('Daily.%i.HighTemperature' % (count+1), TEMP(item['temp']['max']) + TEMPUNIT)
#		set_property('Daily.%i.LowTemperature'	% (count+1), TEMP(item['temp']['min']) + TEMPUNIT)
#		set_property('Daily.%i.FeelsLike'	% (count+1), FEELS_LIKE(item['temp']['day'], item['speed'] * 3.6, item['humidity']) + TEMPUNIT)
#		set_property('Daily.%i.DewPoint'		% (count+1), DEW_POINT(item['temp']['day'], item['humidity']) + TEMPUNIT)


#		if count == MAXDAYS:
#			break
# extended properties
#	for count, item in enumerate(data['list']):
#		code = str(item['weather'][0].get('id',''))
#		icon = item['weather'][0].get('icon','')
#		if icon.endswith('n'):
#			code = code + 'n'
#		weathercode = WEATHER_CODES[code]
#		starttime=item['startTime']
#		startstamp=get_timestamp(starttime)
#		set_property('Daily.%i.LongDay'		% (count), get_weekday(startstamp, 'l'))
#		set_property('Daily.%i.ShortDay'		% (count), get_weekday(startstamp,'s'))
#		if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
#			set_property('Daily.%i.LongDate'	% (count), get_month(startstamp, 'dl'))
#			set_property('Daily.%i.ShortDate'	% (count), get_month(startstamp, 'ds'))
#		else:
#			set_property('Daily.%i.LongDate'	% (count), get_month(startstamp, 'ml'))
#			set_property('Daily.%i.ShortDate'	% (count), get_month(startstamp, 'ms'))
##		set_property('Daily.%i.Outlook'		% (count+1), FORECAST.get(item['weather'][0].get('description',''), item['weather'][0].get('description','')))
##		set_property('Daily.%i.ShortOutlook'	% (count+1), FORECAST.get(item['weather'][0].get('main',''), item['weather'][0].get('main','')))
#		set_property('Daily.%i.OutlookIcon'	% (count+1), WEATHER_ICON % weathercode)
#		set_property('Daily.%i.FanartCode'	% (count+1), weathercode)
#		set_property('Daily.%i.WindDirection'	% (count+1), xbmc.getLocalizedString(int(round(WIND_DIR(item['deg'])))))
#		set_property('Daily.%i.WindDegree'	% (count+1), str(item.get('deg','')) + u'°')
#		set_property('Daily.%i.Humidity'		% (count+1), str(item.get('humidity','')) + '%')
#		set_property('Daily.%i.TempMorn'		% (count+1), TEMP(item['temp']['morn']) + TEMPUNIT)
#		set_property('Daily.%i.TempDay'		% (count+1), TEMP(item['temp']['day']) + TEMPUNIT)
#		set_property('Daily.%i.TempEve'		% (count+1), TEMP(item['temp']['eve']) + TEMPUNIT)
#		set_property('Daily.%i.TempNight'	% (count+1), TEMP(item['temp']['night']) + TEMPUNIT)
#		set_property('Daily.%i.HighTemperature' % (count+1), TEMP(item['temp']['max']) + TEMPUNIT)
#		set_property('Daily.%i.LowTemperature'	% (count+1), TEMP(item['temp']['min']) + TEMPUNIT)
#		set_property('Daily.%i.FeelsLike'	% (count+1), FEELS_LIKE(item['temp']['day'], item['speed'] * 3.6, item['humidity']) + TEMPUNIT)
#		set_property('Daily.%i.DewPoint'		% (count+1), DEW_POINT(item['temp']['day'], item['humidity']) + TEMPUNIT)
#		if 'F' in TEMPUNIT:
#			set_property('Daily.%i.Pressure'		% (count+1), str(round(item['pressure'] / 33.86 ,2)) + ' in')
#			rain = 0
#			snow = 0
#			if 'rain' in item:
#				rain = item['rain']
#				set_property('Daily.%i.Rain'		% (count+1), str(round(rain * 0.04 ,2)) + ' in')
#			else:
#				set_property('Daily.%i.Rain'		% (count+1), '')
#			if 'snow' in item:
#				snow = item['snow']
#				set_property('Daily.%i.Snow'		% (count+1), str(round(snow * 0.04 ,2)) + ' in')
#			else:
#				set_property('Daily.%i.Snow'		% (count+1), '')
#			precip = rain + snow
#			set_property('Daily.%i.Precipitation'	% (count+1), str(round(precip * 0.04 ,2)) + ' in')
#		else:
#			set_property('Daily.%i.Pressure'		% (count+1), str(item.get('pressure','')) + ' mb')
#			rain = 0
#			snow = 0
#			if 'rain' in item:
#				rain = item['rain']
#				set_property('Daily.%i.Rain'		% (count+1), str(int(round(rain))) + ' mm')
#			else:
#				set_property('Daily.%i.Rain'		% (count+1), '')
#			if 'snow' in item:
#				snow = item['snow']
#				set_property('Daily.%i.Snow'		% (count+1), str(int(round(snow))) + ' mm')
#			else:
#				set_property('Daily.%i.Snow'		% (count+1), '')
#			precip = rain + snow
#			set_property('Daily.%i.Precipitation'	% (count+1), str(int(round(precip))) + ' mm')
#		set_property('Daily.%i.WindSpeed'		% (count+1), SPEED(item['speed']) + SPEEDUNIT)
#		if 'gust' in item: 
#			set_property('Daily.%i.WindGust'		% (count+1), SPEED(item['gust']) + SPEEDUNIT)
#		else:
#			set_property('Daily.%i.WindGust'		% (count+1), '')
#		set_property('Daily.%i.Cloudiness'		% (count+1), str(item.get('clouds','')) + '%')
#	if WEEKEND == '2':
#		weekend = [4,5]
#	elif WEEKEND == '1':
#		weekend = [5,6]
#	else:
#		weekend = [6,0]
#	count = 0
#	for item in (data['list']):
#		if get_weekday(item.get('dt',''), 'x') in weekend:
#			code = str(item['weather'][0].get('id',''))
#			icon = item['weather'][0].get('icon','')
#			if icon.endswith('n'):
#				code = code + 'n'
#			weathercode = WEATHER_CODES[code]
#			set_property('Weekend.%i.LongDay'		% (count+1), get_weekday(item.get('dt',''), 'l'))
#			set_property('Weekend.%i.ShortDay'		% (count+1), get_weekday(item.get('dt',''), 's'))
#			if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
#				set_property('Weekend.%i.LongDate'	% (count+1), get_month(item.get('dt',''), 'dl'))
#				set_property('Weekend.%i.ShortDate'	% (count+1), get_month(item.get('dt',''), 'ds'))
#			else:
#				set_property('Weekend.%i.LongDate'	% (count+1), get_month(item.get('dt',''), 'ml'))
#				set_property('Weekend.%i.ShortDate'	% (count+1), get_month(item.get('dt',''), 'ms'))
#			set_property('Weekend.%i.Outlook'		% (count+1), FORECAST.get(item['weather'][0].get('description',''), item['weather'][0].get('description','')))
#			set_property('Weekend.%i.ShortOutlook'	% (count+1), FORECAST.get(item['weather'][0].get('main',''), item['weather'][0].get('main','')))
#			set_property('Weekend.%i.OutlookIcon'	% (count+1), WEATHER_ICON % weathercode)
#			set_property('Weekend.%i.FanartCode'	% (count+1), weathercode)
#			set_property('Weekend.%i.WindDirection'	% (count+1), xbmc.getLocalizedString(int(round(WIND_DIR(item['deg'])))))
#			set_property('Weekend.%i.WindDegree'	% (count+1), str(item.get('deg','')) + u'°')
#			set_property('Weekend.%i.Humidity'		% (count+1), str(item.get('humidity','')) + '%')
#			set_property('Weekend.%i.Cloudiness'	% (count+1), str(item.get('clouds','')) + '%')
#			set_property('Weekend.%i.TempMorn'		% (count+1), TEMP(item['temp']['morn']) + TEMPUNIT)
#			set_property('Weekend.%i.TempDay'		% (count+1), TEMP(item['temp']['day']) + TEMPUNIT)
#			set_property('Weekend.%i.TempEve'		% (count+1), TEMP(item['temp']['eve']) + TEMPUNIT)
#			set_property('Weekend.%i.TempNight'	% (count+1), TEMP(item['temp']['night']) + TEMPUNIT)
#			set_property('Weekend.%i.HighTemperature' % (count+1), TEMP(item['temp']['max']) + TEMPUNIT)
#			set_property('Weekend.%i.LowTemperature'	% (count+1), TEMP(item['temp']['min']) + TEMPUNIT)
#			set_property('Weekend.%i.DewPoint'		% (count+1), DEW_POINT(item['temp']['day'], item['humidity']) + TEMPUNIT)
#			set_property('Weekend.%i.FeelsLike'	% (count+1), FEELS_LIKE(item['temp']['day'], item['speed'] * 3.6, item['humidity']) + TEMPUNIT)
#			if 'F' in TEMPUNIT:
#				set_property('Weekend.%i.Pressure'		% (count+1), str(round(item['pressure'] / 33.86 ,2)) + ' in')
#				rain = 0
#				snow = 0
#				if 'rain' in item:
#					rain = item['rain']
#					set_property('Weekend.%i.Rain'		% (count+1), str(round(rain * 0.04 ,2)) + ' in')
#				else:
#					set_property('Weekend.%i.Rain'		% (count+1), '')
#				if 'snow' in item:
#					snow = item['snow']
#					set_property('Weekend.%i.Snow'		% (count+1), str(round(snow * 0.04 ,2)) + ' in')
#				else:
#					set_property('Weekend.%i.Snow'		% (count+1), '')
#				precip = rain + snow
#				set_property('Weekend.%i.Precipitation'	% (count+1), str(round(precip * 0.04 ,2)) + ' in')
#			else:
#				set_property('Weekend.%i.Pressure'		% (count+1), str(item['pressure']) + ' mb')
#				rain = 0
#				snow = 0
#				if'rain' in	item:
#					rain = item['rain']
#					set_property('Weekend.%i.Rain'		% (count+1), str(int(round(rain))) + ' mm')
#				else:
#					set_property('Weekend.%i.Rain'		% (count+1), '')
#				if 'snow' in item:
#					snow = item['snow']
#					set_property('Weekend.%i.Snow'		% (count+1), str(int(round(snow))) + ' mm')
#				else:
#					set_property('Weekend.%i.Snow'		% (count+1), '')
#				precip = rain + snow
#				set_property('Weekend.%i.Precipitation'	% (count+1), str(int(round(precip))) + ' mm')
#			set_property('Weekend.%i.WindSpeed'		% (count+1), SPEED(item['speed']) + SPEEDUNIT)
#			if 'gust' in item: 
#				set_property('Weekend.%i.WindGust'		% (count+1), SPEED(item['gust']) + SPEEDUNIT)
#			else:
#				set_property('Weekend.%i.WindGust'		% (count+1), '')
#			count += 1
#			if count == 2:
#				break
#	count = 0
#	for item in (data['list']):
#		if count == 1:
#			count = 2
#		code = str(item['weather'][0].get('id',''))
#		icon = item['weather'][0].get('icon','')
#		if icon.endswith('n'):
#			code = code + 'n'
#		weathercode = WEATHER_CODES[code]
#		set_property('36Hour.%i.LongDay'		% (count+1), get_weekday(item.get('dt',''), 'l'))
#		set_property('36Hour.%i.ShortDay'		% (count+1), get_weekday(item.get('dt',''), 's'))
#		if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
#			set_property('36Hour.%i.LongDate'	% (count+1), get_month(item.get('dt',''), 'dl'))
#			set_property('36Hour.%i.ShortDate'	% (count+1), get_month(item.get('dt',''), 'ds'))
#		else:
#			set_property('36Hour.%i.LongDate'	% (count+1), get_month(item.get('dt',''), 'ml'))
#			set_property('36Hour.%i.ShortDate'	% (count+1), get_month(item.get('dt',''), 'ms'))
#		set_property('36Hour.%i.Outlook'		% (count+1), FORECAST.get(item['weather'][0].get('description',''), item['weather'][0].get('description','')))
#		set_property('36Hour.%i.ShortOutlook'	% (count+1), FORECAST.get(item['weather'][0].get('main',''), item['weather'][0].get('main','')))
#		set_property('36Hour.%i.OutlookIcon'	% (count+1), WEATHER_ICON % weathercode)
#		set_property('36Hour.%i.FanartCode'	% (count+1), weathercode)
#		set_property('36Hour.%i.WindDirection'	% (count+1), xbmc.getLocalizedString(int(round(WIND_DIR(item['deg'])))))
#		set_property('36Hour.%i.WindDegree'	% (count+1), str(item.get('deg','')) + u'°')
#		set_property('36Hour.%i.Humidity'		% (count+1), str(item.get('humidity','')) + '%')
#		set_property('36Hour.%i.Temperature'	% (count+1), TEMP(item['temp']['day']) + TEMPUNIT)
#		set_property('36Hour.%i.HighTemperature' % (count+1), TEMP(item['temp']['max']) + TEMPUNIT)
#		set_property('36Hour.%i.LowTemperature'	% (count+1), TEMP(item['temp']['min']) + TEMPUNIT)
#		set_property('36Hour.%i.FeelsLike'	% (count+1), FEELS_LIKE(item['temp']['day'], item['speed'] * 3.6, item['humidity']) + TEMPUNIT)
#		set_property('36Hour.%i.DewPoint'		% (count+1), DEW_POINT(item['temp']['day'], item['humidity']) + TEMPUNIT)
#		if 'F' in TEMPUNIT:
#			set_property('36Hour.%i.Pressure'		% (count+1), str(round(item['pressure'] / 33.86 ,2)) + ' in')
#			rain = 0
#			snow = 0
#			if 'rain' in item:
#				rain = item['rain']
#				set_property('36Hour.%i.Rain'		% (count+1), str(round(rain * 0.04 ,2)) + ' in')
#			else:
#				set_property('36Hour.%i.Rain'		% (count+1), '')
#			if 'snow' in item:
#				snow = item['snow']
#				set_property('36Hour.%i.Snow'		% (count+1), str(round(snow * 0.04 ,2)) + ' in')
#			else:
#				set_property('36Hour.%i.Snow'		% (count+1), '')
#			precip = rain + snow
#			set_property('36Hour.%i.Precipitation'	% (count+1), str(round(precip * 0.04 ,2)) + ' in')
#		else:
#			set_property('36Hour.%i.Pressure'		% (count+1), str(item.get('pressure','')) + ' mb')
#			rain = 0
#			snow = 0
#			if 'rain' in item:
#				rain = item['rain']
#				set_property('36Hour.%i.Rain'		% (count+1), str(int(round(rain))) + ' mm')
#			else:
#				set_property('36Hour.%i.Rain'		% (count+1), '')
#			if 'snow' in item:
#				snow = item['snow']
#				set_property('36Hour.%i.Snow'		% (count+1), str(int(round(snow))) + ' mm')
#			else:
#				set_property('36Hour.%i.Snow'		% (count+1), '')
#			precip = rain + snow
#			set_property('36Hour.%i.Precipitation'	% (count+1), str(int(round(precip))) + ' mm')
#		set_property('36Hour.%i.WindSpeed'		% (count+1), SPEED(item['speed']) + SPEEDUNIT)
#		if 'gust' in item: 
#			set_property('36Hour.%i.WindGust'		% (count+1), SPEED(item['gust']) + SPEEDUNIT)
#		else:
#			set_property('36Hour.%i.WindGust'		% (count+1), '')
#		set_property('36Hour.%i.Cloudiness'		% (count+1), str(item.get('clouds','')) + '%')
#		if count == 0:
#			set_property('36Hour.%i.Heading'		% (count+1), xbmc.getLocalizedString(33006))
#		else:
#			set_property('36Hour.%i.Heading'		% (count+1), xbmc.getLocalizedString(33007))
#		set_property('36Hour.%i.TemperatureHeading'	% (count+1), xbmc.getLocalizedString(393))
#		count += 1
#		if count >= 2:
#			daynum = get_month(item['dt'], 'ds').split(' ')[0]
#			return daynum

#https://api.weather.gov/alerts/active/zone/CTZ006
#https://api.weather.gov/alerts/active/zone/CTC009
def alerts(num):
	
	a_zone=ADDON.getSetting('Location'+str(num)+'Zone')
	url="https://api.weather.gov/alerts/active/zone/%s" %a_zone	
	alert_data=get_data(url)
	#xbmc.log('current data: %s' % current_data,level=xbmc.LOGNOTICE)
	for count in range (1, 10):
		set_property('Alerts.%i.event'	% (count),'')	
	
	try:
		alerts = json.loads(alert_data)
	except:
		xbmc.log('parsing alert data failed' ,level=xbmc.LOGNOTICE)
		alerts = ''
	if alerts and alerts != '' and 'features' in alerts:
		data=alerts['features']
		#xbmc.log('data: %s' % data,level=xbmc.LOGNOTICE)
		set_property('Alerts.IsFetched'		, 'true')

	else:
		set_property('Alerts.IsFetched'		, 'false')
		xbmc.log('Failed to find alert data' ,level=xbmc.LOGNOTICE)
		return None
	for count, item in enumerate(data):
		
		thisdata=item['properties']
		
		
		set_property('Alerts.%i.status'		% (count+1), str(thisdata['status']))	
		set_property('Alerts.%i.messageType'	% (count+1), str(thisdata['messageType']))	
		set_property('Alerts.%i.category'	% (count+1), str(thisdata['category']))	
		set_property('Alerts.%i.severity'	% (count+1), str(thisdata['severity']))	
		set_property('Alerts.%i.certainty'	% (count+1), str(thisdata['certainty']))	
		set_property('Alerts.%i.urgency'	% (count+1), str(thisdata['urgency']))	
		set_property('Alerts.%i.event'		% (count+1), str(thisdata['event']))	
		set_property('Alerts.%i.headline'	% (count+1), str(thisdata['headline']))	
		set_property('Alerts.%i.description'	% (count+1), str(thisdata['description']))	
		set_property('Alerts.%i.instruction'	% (count+1), str(thisdata['instruction']))	
		set_property('Alerts.%i.description'	% (count+1), str(thisdata['description']))	
		set_property('Alerts.%i.response'	% (count+1), str(thisdata['response']))	

	




def hourlyforecast(num):
		
	forecastHourly_url=ADDON.getSetting('Location'+str(num)+'forecastHourly_url')		
		
	hourly_data = get_data(forecastHourly_url)
	#xbmc.log('hourly data: %s' % hourly_data,level=xbmc.LOGNOTICE)
	try:
		hourly_weather = json.loads(hourly_data)
	except:
		log('parsing hourly data failed')
		hourly_weather = ''
	if hourly_weather and hourly_weather != '' and 'properties' in hourly_weather:
		data=hourly_weather['properties']
	else:
		return

# extended properties
	for count, item in enumerate(data['periods']):
		
		icon=item['icon']
		#https://api.weather.gov/icons/land/night/ovc?size=small
		icon=icon.rsplit('?', 1)[0]
		code, rain=code_from_icon(icon)
		set_property('Hourly.%i.RemoteIcon'	% (count+1), icon)	
		
		weathercode = WEATHER_CODES.get(code)
		starttime=item['startTime']
		startstamp=get_timestamp(starttime)
		if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
			set_property('Hourly.%i.LongDate'	% (count+1), get_month(startstamp, 'dl'))
			set_property('Hourly.%i.ShortDate'	% (count+1), get_month(startstamp, 'ds'))
		else:
			set_property('Hourly.%i.LongDate'	% (count+1), get_month(startstamp, 'ml'))
			set_property('Hourly.%i.ShortDate'	% (count+1), get_month(startstamp, 'ms'))
	
		set_property('Hourly.%i.Time'			% (count+1), get_time(startstamp))
		if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
			set_property('Hourly.%i.LongDate'	% (count+1), get_month(startstamp, 'dl'))
			set_property('Hourly.%i.ShortDate'	% (count+1), get_month(startstamp, 'ds'))
		else:
			set_property('Hourly.%i.LongDate'	% (count+1), get_month(startstamp, 'ml'))
			set_property('Hourly.%i.ShortDate'	% (count+1), get_month(startstamp, 'ms'))
		outlook=FORECAST.get(item['detailedForecast'],item['detailedForecast'])
		if len(outlook) < 3 :
			outlook=FORECAST.get(item['shortForecast'],item['shortForecast'])
		set_property('Hourly.%i.Outlook'		% (count+1),	outlook)
		set_property('Hourly.%i.ShortOutlook'	% (count+1), FORECAST.get(item['shortForecast'], item['shortForecast']))
		set_property('Hourly.%i.OutlookIcon'	% (count+1), WEATHER_ICON % weathercode)
		set_property('Hourly.%i.FanartCode'	% (count+1), weathercode)
		#set_property('Hourly.%i.Humidity'		% (count+1), str(item['main'].get('humidity','')) + '%')
		set_property('Hourly.%i.WindDirection'	% (count+1), item['windDirection'])
		set_property('Hourly.%i.WindSpeed'	% (count+1), item['windSpeed'])
		#set_property('Hourly.%i.WindDegree'	% (count+1), str(item['wind'].get('deg','')) + u'°')
		#	else:
		#		set_property('Hourly.%i.WindDirection'	% (count+1), '')
		#		set_property('Hourly.%i.WindDegree'	% (count+1), '')
		#	if 'speed' in item['wind']:
		#		set_property('Hourly.%i.WindSpeed'	% (count+1), SPEED(item['wind']['speed']) + SPEEDUNIT)
		#		set_property('Hourly.%i.FeelsLike'	% (count+1), FEELS_LIKE(item['main']['temp'], item['wind']['speed'] * 3.6, item['main']['humidity']) + TEMPUNIT)
		#	else:
		#		set_property('Hourly.%i.WindSpeed'	% (count+1), '')
		#		set_property('Hourly.%i.FeelsLike'	% (count+1), '')
		#	if 'gust' in item['wind']:
		#		set_property('Hourly.%i.WindGust'		% (count+1), SPEED(item['wind']['gust']) + SPEEDUNIT)
		#	else:
		#		set_property('Hourly.%i.WindGust'		% (count+1), '')
		#set_property('Hourly.%i.Cloudiness'		% (count+1), str(item['clouds'].get('all','')) + '%')

		set_property('Hourly.%i.Temperature'		% (count+1),	str(item['temperature'])+item['temperatureUnit'])
		
		#set_property('Hourly.%i.HighTemperature'	% (count+1), TEMP(item['main']['temp_max']) + TEMPUNIT)
		#set_property('Hourly.%i.LowTemperature'	% (count+1), TEMP(item['main']['temp_min']) + TEMPUNIT)
		#set_property('Hourly.%i.DewPoint'			% (count+1), DEW_POINT(item['main']['temp'], item['main']['humidity']) + TEMPUNIT)
		#if 'F' in TEMPUNIT:
		#	set_property('Hourly.%i.Pressure'		% (count+1), str(round(item['main']['pressure'] / 33.86 ,2)) + ' in')
		#	if 'sea_level' in item['main']:
		#		set_property('Hourly.%i.SeaLevel'	% (count+1), str(round(item['main']['sea_level'] / 33.86 ,2)) + ' in')
		#	else:
		#		set_property('Hourly.%i.SeaLevel'	% (count+1), '')
		#	if 'grnd_level' in item['main']:
		#		set_property('Hourly.%i.GroundLevel' % (count+1), str(round(item['main']['grnd_level'] / 33.86 ,2)) + ' in')
		#	else:
		#		set_property('Hourly.%i.GroundLevel' % (count+1), '')
		#	rain = 0
		#	snow = 0
		#	if 'rain' in item and '3h' in item['rain']:
		#		rain = item['rain']['3h']
		#		set_property('Hourly.%i.Rain'		% (count+1), str(round(rain *	0.04 ,2)) + ' in')
		#	else:
		#		set_property('Hourly.%i.Rain'		% (count+1), '')
		#	if 'snow' in item and '3h' in item['snow']:
		#		snow = item['snow']['3h']
		#		set_property('Hourly.%i.Snow'		% (count+1), str(round(snow *	0.04 ,2)) + ' in')
		#	else:
		#		set_property('Hourly.%i.Snow'		% (count+1), '')
		#	precip = rain + snow

		if rain !='':
			set_property('Hourly.%i.Precipitation'	% (count+1), rain + '%')
			set_property('Hourly.%i.ChancePrecipitation'	% (count+1), rain + '%')
		else:
			set_property('Hourly.%i.Precipitation'	% (count+1), '')
			set_property('Hourly.%i.ChancePrecipitation'	% (count+1), '')
			
		#else:
		#	set_property('Hourly.%i.Pressure'		% (count+1), str(item['main'].get('pressure','')) + ' mb')
		#	if 'sea_level' in item['main']:
		#		set_property('Hourly.%i.SeaLevel'	% (count+1), str(item['main'].get('sea_level','')) + ' mb')
		#	else:
		#		set_property('Hourly.%i.SeaLevel'	% (count+1), '')
		#	if 'grnd_level' in item['main']:
		#		set_property('Hourly.%i.GroundLevel' % (count+1), str(item['main'].get('grnd_level','')) + ' mb')
		#	else:
		#		set_property('Hourly.%i.GroundLevel' % (count+1), '')
		#	rain = 0
		#	snow = 0
		#	if 'rain' in item and '3h' in item['rain']:
		#		rain = item['rain']['3h']
		#		set_property('Hourly.%i.Rain'		% (count+1), str(int(round(rain))) + ' mm')
		#	else:
		#		set_property('Hourly.%i.Rain'		% (count+1), '')
		#	if 'snow' in item and '3h' in item['snow']:
		#		snow = item['snow']['3h']
		#		set_property('Hourly.%i.Snow'		% (count+1), str(int(round(snow))) + ' mm')
		#	else:
		#		set_property('Hourly.%i.Snow'		% (count+1), '')
		#	precip = rain + snow
		#	set_property('Hourly.%i.Precipitation'	% (count+1), str(int(round(precip))) + ' mm')
	
	count = 1

#	if daynum == '':
#		return
#	for item in (data['list']):
#		day_num = get_month(item.get('dt',''), 'ds').split(' ')[0]
#		if day_num == daynum:
#			day_time = get_time(item.get('dt',''))[0:2].lstrip('0').rstrip(':')
#			if day_time == '':
#				day_time = 0
#			if int(day_time) > 2:
#				code = str(item['weather'][0].get('id',''))
#				icon = item['weather'][0].get('icon','')
#				if icon.endswith('n'):
#					code = code + 'n'
#				weathercode = WEATHER_CODES[code]
#				set_property('36Hour.%i.Time'			% (count+1), get_time(item.get('dt','')))
#				if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
#					set_property('36Hour.%i.LongDate'	% (count+1), get_month(item.get('dt',''), 'dl'))
#					set_property('36Hour.%i.ShortDate'	% (count+1), get_month(item.get('dt',''), 'ds'))
#				else:
#					set_property('36Hour.%i.LongDate'	% (count+1), get_month(item.get('dt',''), 'ml'))
#					set_property('36Hour.%i.ShortDate'	% (count+1), get_month(item.get('dt',''), 'ms'))
#				set_property('36Hour.%i.Outlook'		% (count+1), FORECAST.get(item['weather'][0].get('description',''), item['weather'][0].get('description','')))
#				set_property('36Hour.%i.ShortOutlook'	% (count+1), FORECAST.get(item['weather'][0].get('main',''), item['weather'][0].get('main','')))
#				set_property('36Hour.%i.OutlookIcon'	% (count+1), WEATHER_ICON % weathercode)
#				set_property('36Hour.%i.FanartCode'	% (count+1), weathercode)
#				set_property('36Hour.%i.Humidity'		% (count+1), str(item['main'].get('humidity','')) + '%')
#				set_property('36Hour.%i.Cloudiness'	% (count+1), str(item['clouds'].get('all','')) + '%')
#				set_property('36Hour.%i.Temperature'	% (count+1), TEMP(item['main']['temp']) + TEMPUNIT)
#				set_property('36Hour.%i.HighTemperature' % (count+1), TEMP(item['main']['temp_max']) + TEMPUNIT)
#				set_property('36Hour.%i.LowTemperature'	% (count+1), TEMP(item['main']['temp_min']) + TEMPUNIT)
#				set_property('36Hour.%i.DewPoint'		% (count+1), DEW_POINT(item['main']['temp'], item['main']['humidity']) + TEMPUNIT)
#				if 'deg' in item['wind']:
#					set_property('36Hour.%i.WindDirection'	% (count+1), xbmc.getLocalizedString(WIND_DIR(int(round(item['wind']['deg'])))))
#					set_property('36Hour.%i.WindDegree'	% (count+1), str(item['wind'].get('deg','')) + u'°')
#				else:
#					set_property('36Hour.%i.WindDegree'	% (count+1), '')
#				if 'speed' in item['wind']:
#					set_property('36Hour.%i.WindSpeed'	% (count+1), SPEED(item['wind']['speed']) + SPEEDUNIT)
#					set_property('36Hour.%i.FeelsLike'	% (count+1), FEELS_LIKE(item['main']['temp'], item['wind']['speed'] * 3.6, item['main']['humidity']) + TEMPUNIT)
#				else:
#					set_property('36Hour.%i.WindSpeed'	% (count+1), '')
#					set_property('36Hour.%i.FeelsLike'	% (count+1), '')
#				if 'gust' in item['wind']:
#					set_property('36Hour.%i.WindGust'		% (count+1), SPEED(item['wind']['gust']) + SPEEDUNIT)
#				else:
#					set_property('36Hour.%i.WindGust'		% (count+1), '')
#				if 'F' in TEMPUNIT:
#					set_property('36Hour.%i.Pressure'		% (count+1), str(round(item['main']['pressure'] / 33.86 ,2)) + ' in')
#					rain = 0
#					snow = 0
#					if 'rain' in item and '3h' in item['rain']:
#						rain = item['rain']['3h']
#						set_property('36Hour.%i.Rain'		% (count+1), str(round(rain *	0.04 ,2)) + ' in')
#					else:
#						set_property('36Hour.%i.Rain'		% (count+1), '')
#					if 'snow' in item and '3h' in item['snow']:
#						snow = item['snow']['3h']
#						set_property('36Hour.%i.Snow'		% (count+1), str(round(snow *	0.04 ,2)) + ' in')
#					else:
#						set_property('36Hour.%i.Snow'		% (count+1), '')
#					precip = rain + snow
#					set_property('36Hour.%i.Precipitation'	% (count+1), str(round(precip *	0.04 ,2)) + ' in')
#				else:
#					set_property('36Hour.%i.Pressure'		% (count+1), str(item['main'].get('pressure','')) + ' mb')
#					rain = 0
#					snow = 0
#					if 'rain' in item and '3h' in item['rain']:
#						rain = item['rain']['3h']
#						set_property('36Hour.%i.Rain'		% (count+1), str(int(round(rain))) + ' mm')
#					else:
#						set_property('36Hour.%i.Rain'		% (count+1), '')
#					if 'snow' in item and '3h' in item['snow']:
#						snow = item['snow']['3h']
#						set_property('36Hour.%i.Snow'		% (count+1), str(int(round(snow))) + ' mm')
#					else:
#						set_property('36Hour.%i.Snow'		% (count+1), '')
#					precip = rain + snow
#					set_property('36Hour.%i.Precipitation'	% (count+1), str(int(round(precip))) + ' mm')
#				set_property('36Hour.%i.Heading'			% (count+1), xbmc.getLocalizedString(33018))
#				set_property('36Hour.%i.TemperatureHeading'	% (count+1), xbmc.getLocalizedString(391))
#				break





class MyMonitor(xbmc.Monitor):
	def __init__(self, *args, **kwargs):
		xbmc.Monitor.__init__(self)

log('version %s started with argv: %s' % (ADDONVERSION, sys.argv[1]))

MONITOR = MyMonitor()
set_property('Forecast.IsFetched'	, 'true')
set_property('Current.IsFetched'	, 'true')
set_property('Today.IsFetched'		, '')
set_property('Daily.IsFetched'		, 'true')
set_property('Detailed.IsFetched'	, 'true')
set_property('Weekend.IsFetched'	, '')
set_property('36Hour.IsFetched'		, '')
set_property('Hourly.IsFetched'		, 'true')
set_property('NOAA.IsFetched'		, 'true')
set_property('WeatherProvider'		, 'NOAA')
set_property('WeatherProviderLogo', xbmc.translatePath(os.path.join(CWD, 'resources', 'graphics', 'banner.png')))


#if not APPID:
#	log('no api key provided')
#elif sys.argv[1].startswith('Location'):

if sys.argv[1].startswith('Location'):
	log("argument: %s" % (sys.argv[1]))
	text = ADDON.getSetting(sys.argv[1])
	if text == '' :
		keyboard = xbmc.Keyboard('', 'Enter Latitude,Longitude', False)
		keyboard.doModal()
		if (keyboard.isConfirmed() and keyboard.getText() != ''):
			text = keyboard.getText()
	if text != '':
		log("calling location with %s and %s" % (text, sys.argv[1]))
		location(text,sys.argv[1])
		
else:

	#locationname = ADDON.getSetting('LocationName%s' % sys.argv[1])
	num=sys.argv[1]
	locationLatLong = ADDON.getSetting('Location%s' % num)
	if (locationLatLong == '') and (sys.argv[1] != '1'):
		num=1
		locationLatLong = ADDON.getSetting('Location%s' % num)
		log('trying location 1 instead')
	if not locationLatLong == '':
		dailyforecast(num)
		hourlyforecast(num)
		currentforecast(num)
		alerts(num)
	else:
		log('no location provided')
		clear()
	#refresh_locations()

log('finished')
