# newsman-matrix
An AI news and weather reporter for Matrix chat protocol which reports news by category in the style of a tv news report.  Powered by NewsAPI, WeatherAPI and OpenAI gpt-3.5-turbo.

IRC version available at [newsman-irc](https://github.com/h1ddenpr0cess20/newsman-irc)

## Setup
```
pip3 install openai matrix-nio
```
Fill in your [OpenAI API](https://platform.openai.com/signup) key, [NewsAPI](https://newsapi.org/account) key, [WeatherAPI](https://www.weatherapi.com/my/) key.

Set up a [Matrix account](https://app.element.io/) for your bot.  Fill in your Matrix server, channels, username, and password.

## Use
```
python3 newsman.py
```

### Commands:
.weather _location_

.news

.business

.entertainment

.general

.health

.science

.sports

.technology

.politics

