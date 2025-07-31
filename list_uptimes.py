#!/usr/bin/env python
"""Telegram bot to list nicely formated data from a REST API"""

from datetime import datetime
import logging
import re

import requests

from telethon import events, Button
from utils.telethon_utils import start_bot, get_logger

logger_log, logger_error = get_logger(logging_level=logging.INFO)

bot, rest_api, params = start_bot('TOKEN_LIST_UPTIMES_BOT', logger_log, logger_error)

p = re.compile(r'Start time .unixtime . utc_datetime.: \d+ .')
pz = re.compile(r'(.\d{6}Z|.\d{6}\+00:00)$')
pz_year = re.compile(r'^\d{4}\-')
p_ext = re.compile(r'\..*$')

keyboard = [
    Button.inline('Post a report', b'5'),
    Button.inline('List recent uptimes (/list)', b'6'),
]

def format_dict(result_dict):
    results = ''
    for ea in result_dict.keys():
        results = results + '**{}**\n'.format(ea)
        counter = 0
        result_dict[ea].reverse()
        for ea_ea in result_dict[ea]:
            results = results + '  {}\n'.format(ea_ea)
            counter += 1
            if counter == 1:
                break
        results = results + '\n'

    # max telegram len is 4096
    return results[:4096-128]

def fix_temp(value=None):
    if not value:
        return ''
    else:
        return f'{float(value):.1f}C/{(float(value)*9/5)+32:.0f}F'

def check_which_file(value=None):
    if value:
        value = f"""
    {value}"""
    else:
        value = ""

    return value

def get_body_time(body_time):
    if body_time:
        return f"/pz_year.sub('', body_time)"
    else:
        return ''

def fix_coord(coord):
    try:
        return str(round(float(coord), 5))
    except Exception as e:
        return f'{e}'

def get_t_when(t_when):
    if t_when:
        return pz_year.sub('', t_when)
    else:
        return ""

def check_voltage(value=None):
    if value:
        return f'/{float(value):.2f}v'
    else:
        return ''

def check_uptime(value=None):
    if 'days' in value:
        ss = value.split()

        return f'uptime: {ss[2]}'

    ss = value.split("'")
    for index, ea in enumerate(ss):
        if ea == 'status':
            return f'{ea}: {ss[index+2]}'

    if len(ss) > 2:
        return f'{ss[1]} {ss[2]}'
    else:
        return 'hm ...'

def get_location_type(uptime, loc_type, loc_time):
    if loc_type:
        return f"""
    best: {loc_type}/{pz_year.sub('', loc_time)}"""

    else:
        if "location(gps)" in uptime:
            return f"""
    best: gps"""

        elif "location(tower)" in uptime:
            return f"""
    best: tower"""

        else:
            return f"""
    best: probably gps"""

def get_uptime_report():
    """query the REST API"""
    results = {}
    r = requests.get(url=rest_api, params=params)
    if r.ok:
        data = r.json()
        for ea in data['results']:
            if ea['arduino_name'] not in results:
                results[ea['arduino_name']] = [] 

            results[ea['arduino_name']].insert(0, f"""created: {pz_year.sub('', pz.sub('', ea["created_at"]))}
    {pz.sub('', p.sub('uptime: ', check_uptime(ea["uptime"])))}{check_which_file(p_ext.sub('', ea["which_file"]))}{check_voltage(ea["voltage"])}
    {str(round(float(ea["latitude"]), 5))},{str(round(float(ea["longitude"]), 5))}
    {fix_temp(ea["temperature"])} {ea["humidity"]}%H {pz_year.sub('', ea["when_captured_by_device"])}{get_body_time(ea["body_time"])}{get_location_type(ea["uptime"], ea["best_location_type"], ea["best_location_when"])}
    tow: {ea["t_loc"]},{ea["t_country"]}/{get_t_when(ea["t_when"])}/{fix_coord(ea["t_lat"])},{fix_coord(ea["t_lon"])}""")

    results = format_dict(results)
    results = results + f"""**Currently:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"""

    logger_log.debug(results)
    return f'{results}'


@bot.on(events.CallbackQuery(data=re.compile(r'5')))
async def handler(event):
    logger_log.debug('{}'.format(dir(event)))
    logger_log.debug('{}'.format(event.stringify()))
    await event.respond('__Coming soon!__', parse_mode='md')

@bot.on(events.CallbackQuery(data=re.compile(r'6')))
async def handler(event):
    logger_log.debug('{}'.format(dir(event)))
    logger_log.debug('{}'.format(event.stringify()))
    await event.respond(get_uptime_report())
    await event.respond('Choose an option', buttons=keyboard)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """https://stackoverflow.com/questions/61184048/how-to-position-and-resize-button-in-telegram-using-telethon"""
    await bot.send_message(event.chat_id, "Choose an option:", buttons=keyboard)

@bot.on(events.NewMessage(pattern='/list'))
async def list(event):
    await event.respond(get_uptime_report())
    await event.respond('Choose an option', buttons=keyboard)
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='/help'))
async def help(event):
    await event.respond('Use /start to show choices')
    await event.respond('Use /list to show uptimes')
    raise events.StopPropagation

def main():
    """Start the bot."""
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()

# vim: ai et ts=4 sw=4 sts=4 nu
