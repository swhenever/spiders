# spiders
Spiders for performing arts events, running in the Scrapy framewok (http://scrapy.org/). Spiders make ShowBills that are assigned to items, and items are fed to a pipelne that POSTs them to the engine's /showbill endpoint.

## Spider status

### WORKING

* amsterdam: working! (needs refinement, some dates aren't matching)
* cabooze: working!
* fineline: working! (needs refinement, some dates aren't matching)
* firstave: working! (incl Turf Club and Palace Theatre)
* honey: working!
* icehouse: working!
* thecedar: working!
* triplerock: working! (but this venue is closing)
* turfclub: working! (but probably obsolete, since firstave covers this)
* skywaytheatre: working!

### NOT working

* varsitytheater: unknown problems<>
* threethirtyoneclub: website has changed, see http://331club.com/#calendar
* hexagonbar: needs manually-renewed facebook API key
* kittycatklub: website has changed, now a facebook page
* leesliquorlounge: website has changed, see http://www.leesliquorlounge.com/calendar.html

## Running spiders

* In the context of the full engine stack, because you want to test spiders/engine integration, or simply want to populate an engine environment with data. In that case, follow the [deploy repo's instructions for setting up the stack](https://github.com/theshowthing/deploy) and running spiders (the latter is in Initialization Steps).
* In the context of doing spider development, adding new spiders or improving them. Spiders don't need to know anything about engine (they just need to return valid ScrapyShowBillItem objects), so spider development can take place using just the docker-scrapy-dev container. See [that repo's instructions](https://github.com/theshowthing/docker-scrapy-dev).
