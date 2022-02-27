# weather.noaa a Kodi Plugin for weather.gov (NOAA) weather forecasts


This Kodi plugin fetches weather reports from the National Weather Service https://www.weather.gov (eg NOAA). 

The best source for the latest release is to pull from my repo, (using either the Matrix or the Leia version)

* https://github.com/randallspicher/randalls-repo/tree/Leia/repository.randalls.repo
* https://github.com/randallspicher/randalls-repo/tree/Matrix/repository.randalls.repo

Note weather.gov only provides weather forecasts for USA.  The forecasts can be extremely localized (use the map-click feature from the weather.gov web site to get the latitude/longitude for the exact location you want the forecast for.)

weather.gov provides separate forecasts for Days and Nights, rather than just one per day. It also provides much more verbose forecasts.  It requires skin support to make use of the additional features.
https://github.com/randallspicher/skin.lyrebird.rmod is a skin that makes use of the additional features.  (including an option to use the weather.gov icons instead of the default kodi icons)


Skinners:

Note that weather.gov does not supply forecasts as one-per-day.  It instead provides separate forecasts for Daytime and Overnight.  Hard-coding the text "Today" and "Tomorrow" will not be accurate, (since first 2 actual forecasts may be for "This Afternoon" and "Tonight" depending on the current time-of-day.  The "Title" property is best to use.  Since the forecast for Day and Night are separate records, the daytime forecast does not provide a "LowTemperature", and the night-time forecast does not provide a "HighTemperature"  The respective non-relevant properties will be left blank in the Daily.n.xxx properties (you will get either Daily.n.HighTemperature, or Daily.n.LowTemperature, depending on if it's a day or night forecast.)  Since Day0.HighTemp and Day0.LowTemp are raw numbers that Kodi insists on calculating, the same temperature is populated and returned in both, to keep kodi happy.  It is recommended that the skin only make use of the Daily properties.

Weather.gov has much more verbose descriptive forecasts (can be paragraphs of info, instead of just a couple words).  A new screen (or pop-up dialog) is recommended to display the overview.

The plugin provied the following properties:

 - WeatherProvider  #name of provider
 - WeatherProviderLogo # url to logo
 - Forecast.IsFetched

Day forecast (0-13) -- 7 Days
Note, there are separate forcasts for daytime an nighttime

 - Day%i.isDaytime
 - Day%i.Title
Note, because weather.gov provieds a sperate Day and Night forecast, only
These will both return the same temperature, use "isDaytime" to determine which to show
 - Day%i.HighTemp       
 - Day%i.LowTemp         
 - Day%i.Outlook
 - Day%i.OutlookIcon
 - Day%i.OutlookIcon


Daily forecast (1-14) -- 7 Days
Note, there are separate forcasts for daytime an nighttime
Each item will be eaither a Daytime forcast with a HighTemperature, or it will be a Nighttime forecast with a LowTemperature

 - Daily.IsFetched    
 - Detailed.IsFetched       # indicates that this plugin is populating Daily.%i.DetailedOutlook 
 - Daily.%i.isDaytime       # True or False, if current item is for day or night forecast
 - Daily.%i.Outlook         # brief (couple of words) description of the forecast
 - Daily.%i.ShortOutlook    # same as outlook
 - Daily.%i.DetailedOutlook # Verbose detailed forcast. (can be multiple paragraphs)
 - Daily.%i.RemoteIcon      # url to weather.gov icon image (many more types of icons than kodi's built-in list)
 - Daily.%i.OutlookIcon     # kodi built-in icon code (eg, "12.png" ) 
 - Daily.%i.FanartCode      # kodi weather code (eg, "12")
 - Daily.%i.WindDirection
 - Daily.%i.WindSpeed
 - Daily.%i.LongDay         # long title for this item
 - Daily.%i.ShortDay        # short title for this item
 - Daily.%i.TempDay         # Daytime temperature (only populated when isDaytime='True')
 - Daily.%i.HighTemperature # same as TempDay
 - Daily.%i.TempNight       # Nighttime temperature (only populated when isDaytime='False')
 - Daily.%i.LowTemperature  #same as TempNight

Current Weather: 

 - Current.IsFetched
 - Current.Location      # name of current location
 - Current.RemoteIcon    # url to weather.gov weather icon
 - Current.OutlookIcon   # weather coded icon (eg  "12.png" 
 - Current.ConditionIcon # url that Kodi will return based on Current.OutlookIcon code
 - Current.FanartCode    # weather code raw value (eg, "12")
 - Current.Condition	 # current conditions (short weather description)
 - Current.Humidity
 - Current.DewPoint
 - Current.Temperature
 - Current.Wind
 - Current.WindDirection
 - Current.WindGust
 - Current.ChancePrecipitaion
 - Current.FeelsLike
 - Current.SeaLevel    # pressure at sealevel
 - Current.GroundLevel # pressure at groundlevel

Weather Alerts (1-10): number varies depending on number of alerts currently issued

 - Alerts.IsFetched  # true if there are current weather alerts for location, empty if not 
 - Alerts.%i.status
 - Alerts.%i.messageType
 - Alerts.%i.category	
 - Alerts.%i.severity
 - Alerts.%i.certainty	
 - Alerts.%i.urgency	
 - Alerts.%i.event	
 - Alerts.%i.headline
 - Alerts.%i.description	
 - Alerts.%i.instruction	
 - Alerts.%i.response


Hourly Weather (1-156):

 - Hourly.IsFetched
 - Hourly.%i.LongDate
 - Hourly.%i.ShortDate
 - Hourly.%i.Outlook
 - Hourly.%i.ShortOutlook
 - Hourly.%i.OutlookIcon
 - Hourly.%i.FanartCode
 - Hourly.%i.WindDirection
 - Hourly.%i.WindSpeed
 - Hourly.%i.Temperature

Radar and Satellite maps (1-5):

 - Map.%i.Area      # URL to radar or satellite image
 - Map.%i.Heading   # Title of radar or satellite image






















