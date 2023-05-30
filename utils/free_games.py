import re

import aiohttp

from bs4 import BeautifulSoup


async def search_free_games():
    url = 'https://store.steampowered.com/search/?maxprice=free&specials=1&ndl=1'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            contents = await resp.text()

    soup = BeautifulSoup(contents, 'html.parser')
    contents = soup.find_all('a', {'class': 'search_result_row ds_collapse_flag'})

    res = []

    for game in contents:
        res += [
            (game.find('span', {'class': 'title'}).text + ' (' +  # Название
                game.find('div', {'class': 'col search_released responsive_secondrow'}).text + ')',  # Год выхода
                'Платформы: ' +
                ', '.join(a['class'][-1] for a in game.find_all('span', {'class': re.compile('platform_img')})),
                game['href'])  # Ссылка
        ]

    return res
