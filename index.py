import os, time, csv
import shutil
from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API, UseCurrentSession
import asyncio
# Авторизация
from telethon.sync import TelegramClient
from telethon import functions, types
# Получение чатов
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel


api_id = 12345
api_hash = "0123456789abcdef0123456789abcdef"


async def preparesessions() -> list[str]:
    '''
            Генерация файлов сессии через Opentele (для просмотра используйте SQLite)
    '''
    directory = 'tdata'
    sessions = []
    for file in os.listdir(os.path.join(os.getcwd(), "sessions")):
        path = os.path.join(os.path.join(os.getcwd(), "sessions"), file)
        try:
            shutil.rmtree(path)
        except OSError:
            os.remove(path)
    for filename in os.listdir(os.path.join(os.getcwd(), directory)):
        tdatafolder = r"{}".format(
            os.path.join(os.getcwd(), directory, filename, "tdata" if filename != "tdata" else ""))
        tdesk = TDesktop(tdatafolder)
        # Check if we have loaded any accounts
        assert tdesk.isLoaded()
        client = await tdesk.ToTelethon(session=f"{filename}.session", flag=UseCurrentSession)
        await client.connect()
        try:
            await client.PrintSessions()
        except:
            shutil.rmtree(os.path.join(os.getcwd(), directory,filename))
            continue
        await client.disconnect()
        sessions.append(filename)
        shutil.copy(os.path.join(os.getcwd(), f"{filename}.session"), os.path.join(os.getcwd(), "sessions"))
    return sessions


async def joinallbots(chat1: str, chat2: str, proxys: dict[str, list]):
    '''
        Функция для подключения всех ботов к чатам (исходный и конечный)
    '''
    directory = 'sessions'
    print(proxys)
    for filename in os.listdir(os.path.join(os.getcwd(), directory)):
        purefilename = os.path.splitext(os.path.basename(filename))[0]
        async with TelegramClient(purefilename, api_id, api_hash, system_version="4.16.30-vxCUSTOM",
                                  proxy=proxys[purefilename]) as client:
            await client.connect()
            result = await client(functions.channels.JoinChannelRequest(channel=chat1))
            time.sleep(3)
            result = await client(functions.channels.JoinChannelRequest(channel=chat2))
            time.sleep(3)
            await client.disconnect()


async def scanchat(url: str, proxys: dict[str, list[str]]) -> list[str]:
    '''
            Функция для рассылки приглашений в целевой чат.
            Бот банится в течение минуты, если человек, которого пригласили не написал в чат ничего - он исключается из чата в течение 12 часов

            Возможные проблемы:
                -Плохо сформированные аккаунты (пустышки, без фото и нормального имени, с окол двух недель)

            Исключенные проблемы:
                -Бот не написал в один из чатов - не играет роли
                -Юзер не написал в чат, а его пригласили - БАН МГНОВЕННО
                -Все действия бота воспроизводятся слишком быстро - БАН МГНОВЕННО
                -Плохая группа - БАНИТ ГРУППУ, А НЕ ЮЗЕРБОТА
        '''
    directory = 'sessions'
    filename = os.listdir(os.path.join(os.getcwd(), directory))[0]
    purefilename = os.path.splitext(os.path.basename(filename))[0]
    accountsinvite = []
    async with TelegramClient(purefilename, api_id, api_hash, system_version="4.16.30-vxCUSTOM",
                              proxy=proxys[purefilename]) as client:
        await client.connect()
        result = await client.get_participants(url)  # Просканировали
        if result:
            for i in result:
                counter = sum([1 * isinstance(j, types.Message) async for j in
                               client.iter_messages(url, from_user=i.id)])  # Посчитали
                if counter > 0:
                    accountsinvite.append(i.username)
                    # send invite
        await client.disconnect()
    return accountsinvite


async def sendinvitation(chat: str, proxys: dict[str, list], users: list[str]):
    '''
        Функция для рассылки приглашений в целевой чат.
        Бот банится в течение минуты, если человек, которого пригласили не написал в чат ничего - он исключается из чата в течение 12 часов

        Возможные проблемы:
            -Плохо сформированные аккаунты (пустышки, без фото и нормального имени, с окол двух недель)

        Исключенные проблемы:
            -Бот не написал в один из чатов - не играет роли
            -Юзер не написал в чат, а его пригласили - БАН МГНОВЕННО
            -Все действия бота воспроизводятся слишком быстро - БАН МГНОВЕННО
            -Плохая группа - БАНИТ ГРУППУ, А НЕ ЮЗЕРБОТА
    '''
    directory = 'sessions'
    counter = 1
    sessionsarray = os.listdir(os.path.join(os.getcwd(), directory))
    for user in users:
        purefilename = os.path.splitext(os.path.basename(sessionsarray[(len(sessionsarray)%counter) -1]))[0]
        counter +=1
        async with TelegramClient(purefilename, api_id, api_hash, system_version="4.16.30-vxCUSTOM",
                                  proxy=proxys[purefilename]) as client:
            await client.connect()
            time.sleep(3)
            try:
                await client(functions.channels.InviteToChannelRequest(
                    channel=chat,
                    users=[user]
                ))
            except Exception as error:
                print(error)
            time.sleep(3)
            await client.disconnect()



async def createproxydict(sessions: list[str]) -> dict:
    '''
        Функция для создания словаря с русскими прокси вида -  proxys = {sessionname(string) : [protocol(string), ip(string), port(int)]}.
        Алгоритм пользования:
            1) Переместите в папку с проектом csv-файл со списком прокси с сайта https://geonode.com/free-proxy-list
            (название файла должно содержать в названии "proxy"и должно быть с расширением CSV)
            2) Запустите функцию передав в качестве аргумента список с названиями сессий - sessions: list[str]
            3) Передайте результат в нужную переменную
    '''
    filewithproxy = ""
    proxys: dict[list[str], list[str | int]] = {}
    for filename in os.listdir(os.getcwd()):
        if "proxy" in os.path.splitext(os.path.basename(filename))[0] and "csv" in \
                os.path.splitext(os.path.basename(filename))[1]:
            filewithproxy = filename
            break
    with open(filewithproxy, newline='') as csvfile:
        counter = len(sessions)-1
        proxylist = csv.reader(csvfile)
        next(proxylist)
        for proxy in proxylist:
            if proxy[3] == "RU" and proxy[7].isnumeric() and counter != -1:
                ip, port, protocol = proxy[0], proxy[7], proxy[8]
                proxys[sessions[counter]] = [protocol, ip, int(port)]
                counter-=1
            else:
                continue

    return proxys


#TODO list:
# - Авторизация нескольких аккаунтов                      ✔
#       -Итерация по папкам                                 ✔
#       -Создание сессий                                    ✔
#       -Запись сессий в массив                             ✔
#       -Проверка сессий                                    ✔
# - Заход в целевой чат                                   ✔
#       -Присоединение по ссылке                            ✔
#       -Скан участников одним ботом                        ✔
#       -Подсчет количества сообщений каждого               ✔
#       -Запись айди в текстовый файл                       ✔
# - Прогрев аккаунта - ОБЯЗАТЕЛЬНО ИНАЧЕ БАН               ✔
# - Отправка приглашения                                   ✔
#       -Считывания файла                                   ✔
#       -Проход по строкам и отправка приглашения по айди  ✔
# - Отчет об успешности                                    ×
#       - Отчет об успешности                               ×
#




async def main():
    a = input("Введите канал откуда приглашать (ввод вида t.me/channelname, \n!обязательно публичный! (на приватных не тестился): ")
    b = input("Введите канал куда приглашать (ввод вида t.me/channelname, \n!обязательно публичный! (на приватных не тестился): ")
    sessions = await preparesessions()
    proxysdict = await createproxydict(sessions)
    await joinallbots(a,b, proxysdict)
    users = await scanchat(a, proxysdict)
    await sendinvitation(b, proxysdict, users)


if __name__ == "__main__":
    asyncio.run(main())


