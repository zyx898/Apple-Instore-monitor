import asyncio
import aiohttp
import uuid
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed    
from ProxyManager import ProxyManager
WEBHOOK_URL = ""
productsJson = {
    "phones": {
        "iphone16_pro_max_256GB_desert": "MYW53LL/A",
        "iphone16_pro_max_256GB_natural": "MYW63LL/A",
        "iphone16_pro_max_256GB_white": "MYW43LL/A",
        "iphone16_pro_max_256GB_black": "MYW33LL/A",
        
        "iphone16_pro_max_512GB_natural": "MYWA3LL/A",
        "iphone16_pro_max_512GB_white": "MYW83LL/A",
        "iphone16_pro_max_512GB_black": "MYW73LL/A",
        "iphone16_pro_max_512GB_desert": "MYW93LL/A",

        "iphone16_pro_128GB_desert": "MYMC3LL/A",
        "iphone16_pro_128GB_natural": "MYMD3LL/A",
        "iphone16_pro_128GB_white": "MYMA3LL/A",
        "iphone16_pro_128GB_black": "MYM93LL/A",

        "iphone16_pro_256GB_desert": "MYMJ3LL/A",
        "iphone16_pro_256GB_natural": "MYMK3LL/A",
        "iphone16_pro_256GB_white": "MYMH3LL/A",
        "iphone16_pro_256GB_black": "MYMG3LL/A",
    },
    "geoLocations": [
        {
            "location": "97229",
            "storeName": "Pioneer Place",
            "storeNumber": "R077"
        },
        {
            "location": "97224",
            "storeName": "Bridgeport Village",
            "storeNumber": "R134"
        },
        {
            "location": "97223",
            "storeName": "Washington Square",
            "storeNumber": "R090"
        },
    ]
}


class AppleMonitor:
    def __init__(self,proxyManager) -> None:
        self.proxyManager = proxyManager
    
    async def fetch(self,taskInfo):
        # print(taskInfo)
        last_status = False
        while True:
            headers = {
                "Pragma": "no-cache",
                "Referer": f"https://www.apple.com/iphone",
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
            }
            try:
                async with aiohttp.ClientSession() as session:
                    self.taskInfo = taskInfo
                    self.url = f'https://www.apple.com/shop/fulfillment-messages?pl=true&mts.0=regular&cppart=UNLOCKED/US&parts.0={self.taskInfo["part"]}&location={self.taskInfo["location"]}&e={str(uuid.uuid4())}'
                    async with session.get(self.url,headers=headers,proxy=self.proxyManager.random_proxy().get_dict()['http']) as response:
                        current_status = False
                        respJson = await response.json()
                        if respJson['body']['content']['pickupMessage'].get('stores',{}) == {}:
                            pass
                        else:
                            for store in respJson['body']['content']['pickupMessage']['stores']:
                                if (self.taskInfo['storeNumber'] == store['storeNumber']):
                                    if store['partsAvailability'][self.taskInfo['part']]['messageTypes']['regular']['storeSelectionEnabled'] == True:
                                        current_status = True
                                        print(f"{datetime.now()} - INSTOCK!!! | Location:{self.taskInfo['location']} | Store:{store['storeName']} |  Store Number:{self.taskInfo['storeNumber']} | Phone:{self.taskInfo['phone'].upper()} |Build:{self.taskInfo['part']} RESTOCKED!!!")
                                        print(f"{datetime.now()} - INSTOCK!!! --------Location:{self.taskInfo['location']} | Store:{store['storeName']} | Store Number:{self.taskInfo['storeNumber']}----------- RESTOCKED!!!")
                                    break
                            if last_status != current_status:
                                if current_status == True:
                                    date = store['partsAvailability'][self.taskInfo['part']]['pickupSearchQuote']
                                    print(f"{datetime.now()} - INSTOCK!!! | Location:{self.taskInfo['location']} | Store:{store['storeName']} | Store Number:{self.taskInfo['storeNumber']} | Phone:{self.taskInfo['phone'].upper()} | Build:{self.taskInfo['part']} RESTOCKED!!!")
                                    print(f"{datetime.now()} - INSTOCK!!! --------Location:{self.taskInfo['location']} | Store:{store['storeName']} | Store Number:{self.taskInfo['storeNumber']}----------- RESTOCKED!!!")
                                    self.notifyDiscord(taskInfo,date)
                                last_status = current_status
                        print(f"{datetime.now()}  MONITORING ------------ | Location:{self.taskInfo['location']} | Store:{self.taskInfo['storeName']} | Store Number:{self.taskInfo['storeNumber']} | Phone:{self.taskInfo['phone'].upper()} | Build:{self.taskInfo['part']} Current_Status:{current_status} | Last_Status:{last_status}")
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(5)

    def notifyDiscord(self,taskInfo,date):
        #post orderLInk to discord
        webhook = DiscordWebhook(url=WEBHOOK_URL, username="Apple Restocked!",rate_limit_retry=True)
        embed = DiscordEmbed(title=f"Apple Restock - {taskInfo['storeName']}", url=f"https://www.apple.com/shop/buy-iphone/iphone-16-pro/{taskInfo['part']}", description=f"Name:{taskInfo['phone'].upper()} | Build:{taskInfo['part']}", color=242424)
        embed.add_embed_field(name="Name", value=taskInfo['phone'],inline=True)
        embed.add_embed_field(name="Build", value=taskInfo['part'],inline=True)
        embed.add_embed_field(name="Date", value=date, inline=False)
        embed.add_embed_field(name="Address", value=taskInfo['location'], inline=True)
        embed.add_embed_field(name="Store Number", value=taskInfo['storeNumber'], inline=True)
        embed.add_embed_field(name="Link", value=f"https://www.apple.com/shop/buy-iphone/iphone-16-pro/{taskInfo['part']}", inline=False)
        embed.set_footer(text='@Lucas - Apple Restock Monitor')
        webhook.add_embed(embed)
        response = webhook.execute()


if __name__ == '__main__':

    
    proxy_manager = ProxyManager('proxy.txt')
    #print each location with product
    tasks = []

    for location in productsJson['geoLocations']:
        for phone, part in productsJson['phones'].items():
            new_location = location.copy()
            new_location['part'] = part
            new_location["phone"] = phone
            monitor = AppleMonitor(proxy_manager)
            tasks.append(monitor.fetch(new_location))


    # # Run all tasks in one event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
