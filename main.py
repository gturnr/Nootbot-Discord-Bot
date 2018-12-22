#!python3.6
import discord, asyncio, os, ast, random, time, operator, logging, log_config
from time import gmtime, strftime
from urllib.request import Request, urlopen

discord_logger = log_config.setup_logger('discord', 'discordpy.log')
logger = log_config.setup_logger('noot', 'nootbot.log', logging.INFO, logging.INFO)

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')
    logger.info('Opus was not loaded. Launching now.')

client = discord.Client()

server_objects = []

class Server:
    def __init__(self, server):
        self.id = server.id
        self.joined_voice = False
        self.is_playing = False
        self.queue = []
        self.check_server_file_structure()
        self.player = None
        self.voice_obj = None
        self.playlists = {}  # add support for playlists! coming soon...


    def update_songs(self):
        path = 'servers/' + str(self.id) + '/songs.txt'
        if os.path.exists(path):
            f = open(path, 'r')
            songsStr = f.read().lower()
            f.close()

            try:
                self.songs = eval(songsStr)

            except Exception as e:
                logger.critical('Server songs file invalid format. server: ' + str(server.id) + '\n' + e)
                self.songs = []

        else:
            logger.critical('Server failed to validate and load data! server: ' + str(self.id))
            self.songs = []

    def check_server_file_structure(self, aggresive=False):
        server_path = 'servers/' + str(self.id)
        if not os.path.isdir(server_path):
            os.mkdir(server_path)
            logger.info('the server ' + str(self.id) + ' had no root dir, created now')

        if not os.path.isdir(server_path + '/songs'):
            os.mkdir(server_path + '/songs')
            logger.info('the server ' + str(self.id) + ' had no root/songs dir, created now')

        if not os.path.exists(server_path + '/songs.txt'):
            f = open(server_path + '/songs.txt', 'w')
            f.write('[]')
            f.close()
            logger.info('the server ' + str(self.id) + ' had no songs.txt file, created now')

        #check server data integrity
        self.update_songs()
        valid = []
        invalid = []
        for song in self.songs:
            if os.path.exists(server_path+'/songs/'+ song + '.mp3'):
                valid.append(song)
                logger.debug('track ' + song + 'on server ' + str(self.id) + 'is valid')
            else:
                invalid.append(song)
                logger.info('track ' + song + 'on server ' + str(self.id) + 'is invalid')

        self.songs = valid  # prevents any of the invalid commands from being run until they are resolved

        if len(invalid) > 0:
            logger.warning('found ' + str(len(invalid)) + ' entries in song.txt for server: ' + str(self.id))

            if aggresive:  # destroys references to mp3s that were not found. Optional!
                logger.warning('Invalid references are being destroyed \n ' + str(invalid))
                f = open('servers/' + str(self.id) + '/songs.txt', 'w')
                f.write(str(valid))
                f.close()

            else:
                logger.warning('consider running an aggresive cleanup or investigating further. ' + str(invalid))

        else:
            logger.info('the server ' + str(self.id) + ' has a valid song.txt file')

        ### consider adding validation for mp3 files in folder! ###

    def leave_voice(self):
        if self.joined_voice:
            if self.player.is_playing():
                self.player.stop()
            self.queue = []
            self.is_playing = False
            leave = self.voice_obj.disconnect()
            command = asyncio.run_coroutine_threadsafe(leave, client.loop)
            try:
                command.result()
                self.joined_voice = False
                self.voice_obj = None
            except Exception as e:
                logger.warning('issue with leaving voice channel in server ' + str(self.id) + ' - error: ' + e)


    def finished_song(self):
        if self.queue == []:
            self.leave_voice()
        else:
            self.is_playing = False

    def play_track(self):
        song = self.queue[0]
        songpath = 'servers/' + str(self.id) + '/songs/' + song + '.mp3'

        self.player = self.voice_obj.create_ffmpeg_player(filename=songpath, after = lambda: self.finished_song())
        self.player.start()
        self.queue.pop(0)


def getAuth():
    try:
        file = open('key.txt')
        key = file.readline()
        file.close()
        return key
    except:
        print('Failed to load key file... create a text file called "key.txt" and put your auth key inside.')
        logger.critical('Auth key could not be read. Most likely no key.txt file...')
        exit()

def get_server_obj(server):
    for server_obj in server_objects:
        if server.id == server_obj.id:
            return server_obj

################################

@client.event
async def on_ready():
    logger.info('Connected as ' + client.user.name + ' - ' + client.user.id)
    await client.change_presence(game=discord.Game(name='!nootcommands'))

    for active_server in client.servers:
        server_objects.append(Server(active_server))
        logger.info('Server ' + str(active_server.name) + ' (' + active_server.id + ') connected and ready for playback')

@client.event
async def on_server_join(server):
    logger.info('Joined server: ' + str(server.name) + ' (' + server.id + ')')
    server_objects.append(Server(active_server))
    logger.info('Server ' + str(active_server.name) + ' (' + active_server.id + ') connected and ready for playback')


@client.event
async def on_message(message):
    if message.author.bot == True:
        logger.debug('Another message detected by a bot - ' + str(message.author.name))
        return

    if message.content == '(╯°□°）╯︵ ┻━┻':
        await client.send_message(message.channel, ('┬─┬﻿ ノ( ゜-゜ノ)'))
        await client.send_message(message.channel, ('Calm down bruh'))
        logger.info('Table flip requested by user: ' + str(message.author.name) + ' from server: ' + str(message.server.name))

    if message.content.startswith('!nootreboot'):
        logger.warning('Server reboot requested by user: ' + str(message.author.name) + ' from server: ' + str(message.server.name))
        if str(message.author.id) == '158639538468683776':
            logger.info('Server reboot authorised.')
            await client.send_message(message.channel, ('Rebooting... be right back!'))
            os.system('python reboot.py')
            logger.critical('rebooting NOW')
            exit()


    if message.server is not None and message.content.startswith('!nootupdate'):
        get_server_obj(message.server).update_songs()
        await client.send_message(message.channel, ('Updated!'))


    if message.server is not None and message.content.startswith('!nootcommands'):
        output = 'Bot commands: \n ```1) !nootupdate - updates the track collection \n 2) !nootcommands - Lists all commands \n 3) !nootqueue - Lists the current queue \n 4) !nootclear - clears the current queue (the current track will finish playing) \n  5) !nootadd - to add a new song \n 6) !nootremove - used to remove command from server (restricted)``` \n Valid keywords:'
        await client.send_message(message.channel, (output))

        songstr = ''
        unordered = []
        for song in get_server_obj(message.server).songs:
            unordered.append(song)
           
        for song in sorted(unordered):
           songstr += song + ', '
           if len(songstr) > 1500:
               songstr = songstr[:-2]
               await client.send_message(message.channel, ('```' + songstr + '```'))
               songstr = ''

        songstr = songstr[:-2]
        await client.send_message(message.channel, ('```' + songstr + '```'))

        newest_commands = ''
        for song in unordered[-5:]:
            newest_commands += song + ', '
 
        await client.send_message(message.channel, ('Newest: \n ```' + newest_commands[:-2] + '```'))


    if message.server is not None and message.content.startswith('!nootclear'): ###Not working
        get_server_obj(message.server).queue = []


    if message.server is not None and message.content.startswith('!nootqueue'):
        if get_server_obj(message.server).queue != []:
            msg = message.author.mention + ' \n Upcoming queue: \n '
            for id, item in enumerate(get_server_obj(message.server).queue):
                msg += str(id+1) + ') ' + item + '\n'
            await client.send_message(message.channel, (msg))
        else:
            await client.send_message(message.channel, ('There is nothing currently queued!'))


    if message.server is not None and message.content.lower() in get_server_obj(message.server).songs:
            item = message.content.lower()
            current_server = get_server_obj(message.server)
            voice_channel = message.author.voice.voice_channel
            if voice_channel is None:
                pass

            else:
                voice_channel = message.author.voice.voice_channel
                if voice_channel is None:
                    pass

                else:
                    logger.info('played ' + item + ' by: ' + message.author.name + ' in server: ' + str(current_server.id))
                    current_server.queue.append(item)

                    while current_server.is_playing:
                        await asyncio.sleep(0.5)

                    if current_server.queue != []:
                        current_server.is_playing = True

                        if not current_server.joined_voice:
                            current_server.voice_obj = await client.join_voice_channel(voice_channel)
                            current_server.joined_voice = True

                        current_server.play_track()

    #################################

    if message.server is not None and message.content.startswith('!nootremove'):
        logger.info('!nootremove by ' + message.author.name + ' (' + str(message.author.id) +') in server ' + str(message.server.id))
        if message.author == message.server.owner or str(message.author.id) == '158639538468683776':
            current_server = get_server_obj(message.server)
            logger.info('!nootremove access granted to user ' + message.author.name + ' (' + str(message.author.id) +') in server ' + str(message.server.id))
            track = message.content[len('!nootremove '):].strip()
            for command in current_server.songs:
                if track.lower() == command.lower():
                    current_server.check_server_file_structure()
                    path = 'servers/' + str(current_server.id) + '/songs/' + command + '.mp3'
                    try:
                        os.remove(path)
                        logger.warning('File ' + path + ' has been permanently deleted.')
                    except:
                        logger.warning('File' + path + ' could not be deleted!')

                    commandPos = current_server.songs.index(str(command))
                    current_server.songs.pop(commandPos)
                    logger.warning('server local song list for server ' + str(current_server.id) + ' has had command '+ command + ' removed')

                    f = open('servers/' + str(current_server.id) + '/songs.txt', 'w')
                    f.write(str(current_server.songs))
                    f.close()
                    logger.warning('songs.txt file for server ' + str(current_server.id) + ' has had command '+ command + ' removed')
                    await client.send_message(message.author, "Removed command " + command)
                    break

            current_server.check_server_file_structure()

        else:
            await client.send_message(message.channel, ('You need to be the server owner to use this command!'))
            logger.info('!nootremove access DENIED to user ' + message.author.name + ' (' + str(message.author.id) +') in server ' + str(message.server.id))

    if message.server is not None and message.content.startswith('!nootadd'):
        logger.info('!nootadd by ' + message.author.name + ' (' + str(message.author.id) +') in server ' + str(message.server.id))
        current_server = get_server_obj(message.server)

        await client.send_message(message.channel, ('Check your DMs ' + message.author.mention))
        await client.send_message(message.author, "Send the name of the track:")

        msg = await client.wait_for_message(author=message.author)
        name = msg.content.lower()
        logger.info(name + ' was submitted by ' + message.author.name + ' (' + str(message.author.id) +') in server ' + str(message.server.id))

        if name in current_server.songs or "'" in name or "\"" in name:
            await client.send_message(message.author, "Invalid name, already a set command. Terminated - to retry remessage me with !nootadd")
            logger.warning(name + ' was found to be invalid in server ' + str(message.server.id))
        else:
            await client.send_message(message.author, "Upload an .mp3 file (filename does not matter as long as it is a .mp3):")
            fileMsg = await client.wait_for_message(author=message.author)
            logger.info('mp3 was uploaded by ' + message.author.name + ' (' + str(message.author.id) +') in server ' + str(message.server.id))
            url = fileMsg.attachments[0].get('url')
            url = 'http' + url[5:]
            filename = fileMsg.attachments[0].get('filename')
            filenameType = filename.split('.')[-1]

            if filenameType.upper() == 'MP3':
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                data = urlopen(req).read()
                logger.info('data for track '+ name + ' was downloaded')

                server_dir = 'servers/' + str(current_server.id) + '/'
                f = open(server_dir + 'songs/' + str(name) + '.mp3', 'wb')
                f.write(data)
                f.close()
                logger.info('data for track '+ name + ' was saved to dir songs/ in server ' + str(message.server.id))

                current_server.check_server_file_structure()
                current_server.songs.append(name)
                logger.info('current tracks were ammended for server ' + str(message.server.id))

                f = open(server_dir + 'songs.txt', 'w')
                f.write(str(current_server.songs))
                f.close()
                current_server.check_server_file_structure()
                logger.info('track file saved for server ' + str(message.server.id))

                await client.send_message(message.author, "Added ;)")

            else:
                await client.send_message(message.author, "Not a valid mp3! To retry remessage me with !nootadd")


client.run(getAuth())
