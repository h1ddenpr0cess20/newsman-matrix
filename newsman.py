# Newsman for Matrix
# Dustin Whyte
# September 2023

import asyncio
from nio import AsyncClient, MatrixRoom, RoomMessageText
import datetime
from openai import OpenAI
import requests
import namegen

class Newsman:
    def __init__(self, server, username, password, channels, api_key):
        self.server = server
        self.username = username
        self.password = password
        self.channels = channels

        self.client = AsyncClient(server, username)
        self.openai = OpenAI(api_key=api_key)
        
        # time program started and joined channels
        self.join_time = datetime.datetime.now()

        self.model = "gpt-3.5-turbo"

        #personality types
        self.types = {
            "news": f"a network news anchor named {namegen.name_generator()}",
            "weather": f"a weatherman with a name you make up",
            "business": f"a business news reporter named {namegen.name_generator()}", 
            "entertainment": f"an entertainment news reporter named {namegen.name_generator()}", 
            "general": f"a network news anchor named {namegen.name_generator()}", 
            "health": f"a doctor named Dr. {namegen.name_generator()}", 
            "science": f"a science news reporter named {namegen.name_generator()}",
            "sports": f"a sports reporter named {namegen.name_generator()}",
            "technology": f"a tech news reporter named {namegen.name_generator()}",
            "politics": f"a political analyst named {namegen.name_generator()}"
            
            }


    # get the news from news api
    # may replace this with a scraper?
    async def get_news(self, type=None):
        #sources by category, still testing sources, some have unhelpful content for the purpose of this bot
        sources = {
            "business": "business-insider,fortune,the-wall-street-journal", 
            "entertainment": "ign,entertainment-weekly,mtv-news,polygon", 
            "general": "cnn,abc-news,nbc-news,associated-press,cbs-news,fox-news,reuters,the-washington-post,usa-today", 
            "health": "medical-news-today", 
            "science": "national-geographic,new-scientist",
            "sports": "espn,bleacher-report,fox-sports,nfl-news,nhl-news",
            "technology": "ars-technica,engadget,hacker-news,recode,techcrunch,the-verge",
            "politics": "politico,the-hill"}
        #if a personality type was chosen, use the appropriate source category
        if type:
            url = url =f"https://newsapi.org/v2/top-headlines?sources={sources[type]}&apiKey={news_api}"
        #top headlines without sources
        else:
            url = url =f"https://newsapi.org/v2/top-headlines?country=us&apiKey={news_api}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['articles']
        if response.status_code == 429:
            return 429
        else:
            return None
        #improve this later
    
    # get the weather from weather api
    async def get_weather(self, location):
        url = f"http://api.weatherapi.com/v1/current.json?key={weather_key}&q={location}&aqi=no"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            
            return "ignore previous sentence.  DO NOT attempt to report the weather.  tell the user there was a problem with the location they provided."

    # AI response   
    async def respond(self, message, type):
        persona = self.types[type]
        #create system prompt
        self.personality = f"assume the personality of {persona} and roleplay as them."
        
        response = self.openai.chat.completions.create(model=self.model,
                                                temperature=1,
                                                messages=({"role": "system", "content": self.personality},
                                                            {"role": "user", "content": message}))
        #return the response text
        response_text = response.choices[0].message.content
        return response_text.strip()
        #add error handling later


    # simplifies sending messages to the channel            
    async def send_message(self, channel, message):
         await self.client.room_send(
            room_id=channel,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
        )
         
    #message listener
    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
       
        # Main bot functionality
        if isinstance(event, RoomMessageText):
            # convert timestamp
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            # assign parts of event to variables
            message = event.body
            sender = event.sender
            room_id = room.room_id

            #check if the message was sent after joining and not by the bot
            if message_time > self.join_time and sender != self.username:
                #things to exclude from articles
                exclude = {None, "[Removed]"}
                if message.startswith("."):
                    type = message.lstrip(".")
                    if type.startswith("weather"):
                        if " " in type:
                            type = type.split(" ",1)
                            location = type[1]
                            type = type[0]
                        else:
                            location = " "
                        
                    #check the personality types for a matching news category
                    if type in self.types:
                        #get weather report
                        if type == "weather":
                            #you can tweak the fields the API returns under API Response Fields on the weatherapi website
                            weather = await self.get_weather(location)
                            #generate the AI weather report
                            report = await self.respond(f"report this weather in one paragraph\n{weather}", type)
                            await self.send_message(room_id, report)
                        else:            
                            #create a string for the list of articles
                            articles = ""
                            #get the news for the category
                            if type == "news":
                                news = await self.get_news()
                            else:             
                                news = await self.get_news(type)
                            
                            if news != None and news != 429:
                                #grab a limited amout of headlines and descriptions
                                #change how this works later by grabbing more articles, filtering the bad ones, then select 5 of them.  current way can result in too few articles being reported.
                                for article in news[:5]:
                                    if article['title'] in exclude or article['description'] in exclude:
                                        continue
                                    articles = articles + article['title'] + " - " + article['description'] + "\n\n"
                                #create AI news report
                                report = await self.respond(f"summarize these headlines into an entertaining {type} news report.  do not write it like a script. \n{articles}", type)
                                #chop it up for irc length 
                                await self.send_message(room_id, report)
                                
                            elif news == 429:
                                await self.send_message(room_id, "try again later")
                            else:
                                await self.send_message(room_id, "error")
                    #help menu
                    if type == "help":
                        commands = ""
                        #add the rest from types
                        for command in self.types:
                            commands = commands + f".{command}\n"
                        help_message = f"Newsman, an AI newsroom.\n\nCommands:\n{commands}\n\nAvailable at https://github.com/h1ddenpr0cess20/newsman-matrix"
                        #send help message as notice
                        await self.send_message(room_id, help_message)

    # main loop
    async def main(self):
        # Login, print "Logged in as @alice:example.org device id: RANDOMDID"
        print(await self.client.login(self.password))
        
        # join channels
        for channel in self.channels:
            try:
                await self.client.join(channel)
                print(f"Joined {channel}")
                
            except:
                print(f"Couldn't join {channel}")
        
        # start listening for messages
        self.client.add_event_callback(self.message_callback, RoomMessageText)
                     
        await self.client.sync_forever(timeout=30000)  # milliseconds

if __name__ == "__main__":
    openai_key = "API_KEY"
    news_api = "API_KEY"
    weather_key = 'API_KEY'
    
    server = "https://matrix.org" #change if using different homeserver
    username = "@USERNAME:SERVER.TLD" 
    password = "PASSWORD"

    channels = ["#channel1:SERVER.TLD", 
                "#channel2:SERVER.TLD", 
                "#channel3:SERVER.TLD", 
                "!ExAmPleOfApRivAtErOoM:SERVER.TLD", ] #enter the channels you want it to join here
        
    # create bot instance
    newsman = Newsman(server, username, password, channels, openai_key)
    
    # run main function loop
    asyncio.get_event_loop().run_until_complete(newsman.main())