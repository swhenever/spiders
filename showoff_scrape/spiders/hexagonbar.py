import scrapy
from scrapy.spider import BaseSpider
import arrow
import json
from showoff_scrape.items import ShowItem
from scrapy.shell import inspect_response

class HexagonBarSpider(BaseSpider):

	name = 'hexagonbar'
	venueIdentifyingUrl = 'https://www.facebook.com/hexagonbarlivemusic'
	venueLabel = 'Hexagon Bar'
	allowed_domains = ['facebook.com']
	app_access_token = 'CAAGPqlSTsU8BAGBtUx6ZBuKuC9SqZBvmW8yMKkdfGNau7pZAOSYZAWq5FCi89XoLEfUuR0SAoK3lGOvO3WZAmMDI7845sND1G99f8uD9BAvXQ0ZA8wnlBxUTUkUkPInkntk2XdB68zlwxZCmxof3wMevWKKUhfHp9iFo7OGV4I6oyVNwohqRohqyHxCKqGOovuvrsZCzrMElwn7im67rgXbme89S2rivhxAZD'
	start_urls = ['https://graph.facebook.com/hexagonbarlivemusic/feed?access_token=' + app_access_token]

	def parse(self, response):
		#inspect_response(response, self)
		items = []
		dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
		defaultTime = '9:00pm' # Hexagon facebook posts often omit start time, but it seems like usually 9pm
		jsonresponse = json.loads(response.body_as_unicode())
		for feedItem in jsonresponse["data"]:
			if 'message' in feedItem:
				if feedItem["message"].find("UPCOMING BANDS") > -1:
					item = False
					# we have a post that might contain events
					# which might look like:
					# "WELCOME TO THE FRONT PAGE OF\nHEXAGON LIVE MUSIC AND SPORTS BAR\n2600 27th AVE South, Minneapolis MN 55406\nEstablished in 1934\nUPCOMING BANDS and EVENTS!\n\n FRIDAY MARCH 13th\n\"Cold Colours\"\n\"Attalla (WI)\"\n\"Go Go Slow\"\n\"Wicked Inquisition\"\n\n SATURDAY MARCH 14th\n\"Teenage Moods\"\n\"Heavy Hand (Mke)\"\n\"Rabbit Holes\"\n\"Color TV\"",

					# split by newline
					lines = feedItem["message"].split('\n')
					createdDate = arrow.get(feedItem["created_time"])
					for line in lines:
						# is this a date?
						dateFound = False
						lowerLine = line.lower()
						for dayName in dayNames:
							if (lowerLine.find(dayName) > -1):
								dateFound = True

						if dateFound:
							# if a showItem exists, then it's time to close it out
							if item != False:
								item["title"] = ', '.join(item["performers"])
								items.append(item)

							# start a new show, give it base properties
							item = ShowItem()
							item["performers"] = []
							# create a string that is trimmed, drops the last two chars ("th", "rd" etc) and adds year/default time
							dateString = lowerLine.strip()[:-2] + " " + createdDate.format("YYYY") + " " + defaultTime
							try:
								item['start'] = arrow.get(dateString, 'dddd MMMM D YYYY h:mma')
								item['url'] = self.venueIdentifyingUrl + "/#" + feedItem["id"] + "_" + item["start"].format("YYYY-MM-DD")
							except arrow.parser.ParserError:
								# we couldn't parse the date :( maybe a spelling error (frbruary lol)
								item = False
								# @todo - log this failure
						elif item != False:
							# an item is open, so we expect this line is a performer
							item["performers"].append(line.strip(' \n\r\t"'))
					
					# we're done with a message/post, so let's save any showitem that exists
					if item != False:
						item["title"] = ', '.join(item["performers"])
						items.append(item)
					# clear out the showItem, if any exists
					item = False;

					#print video["media$group"]["yt$videoid"]["$t"]
					#print video["media$group"]["media$description"]["$t"]
					#item ["title"] = video["title"]["$t"]
					#print video["author"][0]["name"]["$t"]
					#print video["category"][1]["term"]
				
				
		return items