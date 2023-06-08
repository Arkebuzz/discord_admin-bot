import re

import aiohttp

from bs4 import BeautifulSoup


async def search_steam_games():
    url = 'https://store.steampowered.com/search/?l=russian&maxprice=free&supportedlang=any&specials=1'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            contents = await resp.text()

    soup = BeautifulSoup(contents, 'html.parser')
    contents = soup.find_all('a', {'class': 'search_result_row ds_collapse_flag'})

    res = []

    for game in contents:
        async with aiohttp.ClientSession() as session:
            async with session.get(game['href'] + '&l=russian') as resp:
                game_info = await resp.text()

        game_info = BeautifulSoup(game_info, 'html.parser')

        date = game_info.find('p', {'class': 'game_purchase_discount_quantity'}).text.split('	')[0]

        description = game_info.find('div', {'id': 'game_area_description'}).text[13:1000].lstrip()

        if game_info.find('div', {'class': 'game_area_bubble game_area_dlc_bubble'}) is not None:
            dlc = 1
        else:
            dlc = 0

        try:
            rating = (
                game.find(
                    'span', {'class': re.compile('search_review_summary')}
                ).get('data-tooltip-html').replace('<br>', ': ')
            )
        except AttributeError:
            rating = None

        # 'Платформы: ' +
        # ', '.join(a['class'][-1] for a in game.find_all('span', {'class': re.compile('platform_img')}))

        res += [[
            game.find('span', {'class': 'title'}).text + ' (' +  # Название
            game.find('div', {'class': 'col search_released responsive_secondrow'}).text + ')',  # Дата выхода

            dlc,  # Дополнение (0,1)?

            game['href'],  # Ссылка

            description,  # Описание

            rating,  # Рейтинг

            date,  # До какого момента можно забрать

            game.find('img').get('srcset').split()[-2],  # Картинка

            0  # Тип магазина
        ]]

    return res


async def search_epic_games():
    url = 'https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            contents = await resp.json()

    contents = contents['data']['Catalog']['searchStore']['elements']
    res = []

    for game in contents:
        if game['title'] == 'Mystery Game':
            continue

        try:
            date = 'Можно забрать до ' + '/'.join(
                game['promotions']['promotionalOffers'][0]['promotionalOffers'][0]['endDate'][:10].split('-')[::-1]
            ) + '.'
        except (IndexError, KeyError):
            continue

        img = [g['url'] for g in game['keyImages'] if g["type"] == "OfferImageWide"][0]

        res += [[
            game['title'],  # Название

            0,  # Дополнение?

            'https://store.epicgames.com/ru/p/' + game['productSlug'],  # Ссылка

            game['description'],  # Описание

            None,  # Рейтинга в эпике нет

            date,  # Дата

            img,  # Картинка

            1  # Тип магазина
        ]]

    return res


async def search_gog_games():
    url = 'https://www.gog.com/ru/games?priceRange=0,0&discounted=true'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            contents = await resp.text()

    soup = BeautifulSoup(contents, 'html.parser')
    contents = soup.find_all('a', {'class': 'product-tile product-tile--grid'})

    res = []

    for game in contents:
        async with aiohttp.ClientSession() as session:
            async with session.get(game['href']) as resp:
                game_info = await resp.text()

        game_info = BeautifulSoup(game_info, 'html.parser')

        if game.find('span', {'class': 'title-label small ng-star-inserted'}) is not None:
            dlc = 1
        else:
            dlc = 0

        rating = game_info.find('script', {'type': 'application/ld+json'}).text
        ind = rating.find('ratingValue')
        if ind != -1:
            rating = rating[ind + 15:rating.find('"', ind + 15)]
        else:
            rating = None

        res += [[
            game.find('div', {'class': 'product-tile__title'})['title'],  # Название

            dlc,  # Дополнение?

            game['href'],  # Ссылка

            game_info.find('div', {'class': 'description'}).text.split('\n')[0],  # Описание

            rating,  # Рейтинг

            None,  # Срок скидки в gog не известен

            game.find('source')['srcset'].split()[-2],  # Картинка

            2  # Тип магазина
        ]]

    return res


async def search_games():
    res = await search_steam_games()
    res += await search_gog_games()
    res += await search_epic_games()
    return res


if __name__ == '__main__':
    import asyncio

    loop = asyncio.new_event_loop()

    print('GOG')
    print(*loop.run_until_complete(search_gog_games()), sep='\n', end='\n\n')
    print('EPIC')
    print(*loop.run_until_complete(search_epic_games()), sep='\n', end='\n\n')
    print('STEAM')
    print(*loop.run_until_complete(search_steam_games()), sep='\n', end='\n\n')
