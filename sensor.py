from datetime import datetime
import json
import time
import logging
import json
from datetime import timedelta
import requests
from urllib.request import urlopen
import aiohttp
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY,CONF_NAME
from homeassistant.util import Throttle
import homeassistant.util.dt as dt_util

#https://github.com/home-assistant/example-custom-config/tree/master/custom_components
#https://github.com/home-assistant/core/blob/b6f432645d7bc6b4947a20afa28647eb1515e4f8/homeassistant/helpers/entity.py

__version__ = '1.0.0'
_LOGGER = logging.getLogger(__name__)

CONF_TRANSPORT_KIND="transport_kind"
CONF_DIRECTION="direction"
CONF_SITE_ID="site_id"
CONF_FETCH_COOLDOWN="api_fetch_cooldown"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY) : cv.string,
    vol.Required(CONF_TRANSPORT_KIND) : cv.string,
	vol.Required(CONF_DIRECTION) : cv.positive_int,
	vol.Required(CONF_SITE_ID) : cv.positive_int,
	vol.Optional(CONF_FETCH_COOLDOWN,default=60) : cv.positive_int,
	vol.Optional(CONF_NAME): cv.string,  
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor."""
    api_key = config.get(CONF_API_KEY)
    site_id = config.get(CONF_SITE_ID) 
    transport_kind = config.get(CONF_TRANSPORT_KIND)
    fetch_cooldown_sec = config.get(CONF_FETCH_COOLDOWN)
    direction = config.get(CONF_DIRECTION)
    name= config.get(CONF_NAME)
    api = StorstockolmLokaltrafikAPI(api_key=api_key,site_id=site_id,transport_kind=transport_kind,fetch_cooldown_sec=fetch_cooldown_sec,direction=direction)
    add_entities([StorstockolmLokaltrafikSensor(api, name)], True)

class StorstockolmLokaltrafikSensor(Entity):
    """Representation of sensor."""

    def __init__(self, api, name):
        """Initialize sensor."""
        self._api = api
        self._name = name
        self._icon = "mdi:alert"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._api.data['state']

    @property
    def state_attributes(self):
        """Return the state attributes of the sensor."""
        data = {
            'departures': self._api.departures,
            'spoken_departure': self._api.voice_string
        }
        return data

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._api.available

    def update(self):
        """Get the latest data from the StorstockolmLokaltrafik API."""
        self._api.update()

class StorstockolmLokaltrafikAPI:
	def __init__(self,api_key="659a6dd9855140bd8ee7c74ab4ef595f",site_id=9264,transport_kind="Metros",fetch_cooldown_sec=60,direction=1):
		self.departures=[]
		self.api_key=api_key
		self.site_id=site_id
		self.transport_kind=transport_kind
		self.last_update=self.get_now_sec()
		self.data={"state":None}
		self.available=False
		self.fetch_cooldown_sec=fetch_cooldown_sec
		self.voice_string="Något gick fel"
		self.direction=direction

	def make_object(self, index, element):
		pass

	def get_now_sec(self):
		return int(time.time())

	def build_voice_string(self):
		d0=self.departures[0]["departure_time"]-datetime.now()
		d1=self.departures[1]["departure_time"]-datetime.now()

		dest0=self.departures[0]["destination"]
		dest1=self.departures[1]["destination"]
		
		mm=(d0.seconds//60)%60
		ss0=d0.seconds%60
		mm1=(d1.seconds//60)%60
		ss1=d1.seconds%60

		def plurify(val,sing,mult):
			s=str(val)+" "
			if val==1:
				return s+sing
			return s+mult
		if mm<1:
			return "{} , därefter {} och {}".format(plurify(ss0,"sekund","sekunder"),plurify(mm1,"minut","minuter"),plurify(ss1,"sekund","sekunder"))
		return "{} och {}, därefter {}".format(plurify(mm,"minut","minuter"),plurify(ss0,"sekund","sekunder"),plurify(mm1,"minut","minuter"))

	def parse_timestamp_to_datetime(self,expected):
		return datetime.strptime(expected, '%Y-%m-%dT%H:%M:%S')

	def _fetch(self):
		url = "https://api.sl.se/api2/realtimedeparturesV4.json?key={api_key}&siteid={site_id}&timewindow=60".format(**{"api_key":self.api_key,"site_id":self.site_id})
		response = urlopen(url)
		data = response.read().decode('utf-8')
		d = json.loads(data)
		transports=d["ResponseData"][self.transport_kind]
		self.last_update=self.get_now_sec()
		self.departures=[]
		for m in transports:
			direction=m["JourneyDirection"]
			departure_time=self.parse_timestamp_to_datetime(m["ExpectedDateTime"])
			if direction==self.direction:
				o={"departure_time":departure_time,"destination":m["Destination"],"deviations":m["Deviations"]}
				self.departures.append(o)

	def update(self):
		now=self.get_now_sec()
		elapsed=now-self.last_update

		if elapsed>self.fetch_cooldown_sec or len(self.departures)==0:
			self._fetch()
			elapsed=0

		self.departures = list(filter(lambda x: (x["departure_time"]-datetime.now()).seconds>0, self.departures))
		try:
			self.data["state"]=self.departures[0]["departure_time"]
			self.available=True
		except:
			self.available=False
		self.voice_string=self.build_voice_string()








