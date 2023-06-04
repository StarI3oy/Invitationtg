import os, time, csv
import shutil
from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API, UseCurrentSession
import asyncio
# Авторизация
from telethon import TelegramClient
from telethon import functions, types
# Получение чатов
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel
import telethon.errors
from dotenv import load_dotenv
# Бот для управления
from telethon import events
from telethon.tl.types import PeerUser


load_dotenv()
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
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
        assert tdesk.isLoaded()
        client = await tdesk.ToTelethon(session=f"{filename}.session", flag=UseCurrentSession)
        print(client)
        await client.connect()
        try:
            await client.PrintSessions()
        except Exception as e:
            print("Ошибка ",e)
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
    for filename in os.listdir(os.path.join(os.getcwd(), directory)):
        purefilename = os.path.splitext(os.path.basename(filename))[0]
        async with TelegramClient(purefilename, api_id, api_hash, system_version="4.16.30-vxCUSTOM",
                                  proxy=proxys[purefilename]) as client:
            await client.connect()
            time.sleep(30)
            result = await client(functions.channels.JoinChannelRequest(channel=chat1))
            time.sleep(14)
            result = await client(functions.channels.JoinChannelRequest(channel=chat2))
            time.sleep(14)
            await client.disconnect()


async def scanchat(url1: str, url2: str, proxys: dict[str, list]) -> list[str]:
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
    async with TelegramClient(purefilename, api_hash=api_hash, api_id=api_id, system_version="4.16.30-vxCUSTOM",proxy=proxys[purefilename]) as client:
        await client.connect()
        time.sleep(14)
        offset_msg = 0
        limit_msg  = 100
        flag = 0
        messages_id = []
        flag_ = 0
        while len(accountsinvite) < 40*4:
            time.sleep(30)
            history = await client(GetHistoryRequest(
                peer=url1,
                offset_id=offset_msg,
                offset_date=None, add_offset=0,
                limit=limit_msg, max_id=0, min_id=0,
                hash=0))
            if not history.messages:
                break
            messages = history.messages
            if flag:
                break
            for i in messages:
                message = i.to_dict()
                print(message)
                try:
                    user = int(message['from_id']['user_id'])
                except:
                    continue
                print(user)
                if message['id'] in messages_id:
                    if flag_:
                        flag = True
                        break
                    else:
                        flag_ = True
                else:
                    messages_id.append(message['id'])
                if not user in accountsinvite:
                    accountsinvite.append(user)
        await client.disconnect()
    return accountsinvite


async def sendinvitation(chat: str, users: list[str],proxys: dict[str, list]):
    '''
        Функция для рассылки приглашений в целевой чат.
        Бот банится в течение минуты, если человек, которого пригласили не написал в чат ничего - он исключается из чата в течение 12 часов

        Возможные проблемы:
            -Плохо сформированные аккаунты (пустышки, без фото и нормального имени, с окол двух недель)

        Исключенные проблемы:
            -Бот не написал в один из чатов - не играет роли
            -Слишком дешевый бот, или слишком много репортов
            -Плохая группа - БАНИТ ГРУППУ, А НЕ ЮЗЕРБОТА
    '''
    directory = 'sessions'
    counter = 1
    sessionsarray = os.listdir(os.path.join(os.getcwd(), directory))
    breakCounter = len(sessionsarray)*40
    for user in users:
        purefilename = os.path.splitext(os.path.basename(sessionsarray[(len(sessionsarray)%counter) -1]))[0]
        counter +=1
        async with TelegramClient(purefilename, api_hash=api_hash, api_id=api_id, system_version="4.16.30-vxCUSTOM", proxy=proxys[purefilename]) as client:
            await client.connect()
            time.sleep(10)
            try:
                result = await client(functions.channels.InviteToChannelRequest(
                    channel=chat,
                    users=[(await client.get_entity(PeerUser(user))).username]
                ))
                time.sleep(10)
            except telethon.errors.FloodWaitError as e:
                print('Have to sleep', e.seconds, 'seconds')
                time.sleep(e.seconds)
            except Exception as e:
                print(e)
                continue
            print(result.stringify())
            await client.disconnect()

        if counter == breakCounter:
            break



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

async def sendmessage(users: list[str], proxys):
    directory = 'sessions'
    counter = 1
    sessionsarray = os.listdir(os.path.join(os.getcwd(), directory))
    for user in users:
        purefilename = os.path.splitext(os.path.basename(sessionsarray[(len(sessionsarray) % counter) - 1]))[0]
        counter += 1
        async with TelegramClient(purefilename, api_id, api_hash, system_version="4.16.30-vxCUSTOM",
                                  proxy=proxys[purefilename]) as client:
            await client.connect()
            time.sleep(30)
            try:
                entity = await client.get_entity(user)
                time.sleep(30)
                await client.send_message(entity=entity, message="How are you")
            except Exception as error:
                print(error)
            time.sleep(30)
            await client.disconnect()


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
# - Отчет об успешности
#       - Отчет об успешности
#




async def mains():
    a = input("Введите канал откуда приглашать (ввод вида t.me/channelname, \n!обязательно публичный! (на приватных не тестился): ")
    b = input("Введите канал куда приглашать (ввод вида t.me/channelname, \n!обязательно публичный! (на приватных не тестился): ")
    sessions = await preparesessions()
    proxysdict = await createproxydict(sessions)
    await joinallbots(a, b, proxysdict)
    users = await scanchat(a, b, proxysdict)
    print(users[:20])
    users = list(filter(lambda item: item is not None, users))
    await sendinvitation(b, users, proxysdict)

#t.me/XzxXasccq
#t.me/jojobasa
#t.me/casinochat_cbonus
#t.me/zanosicasinochat
if __name__ == "__main__":
    asyncio.run(mains())


