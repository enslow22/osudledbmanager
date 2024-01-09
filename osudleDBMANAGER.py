from sqlalchemy import create_engine, Column, String, Integer, Date, Float, BLOB, select, exists, URL, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import ossapi
import os
import subprocess
from config import *
from youtubehandler import YoutubeHandler

api = ossapi.Ossapi(client_id, client_secret)

class Base(DeclarativeBase):
    pass

class osuMap(Base):
    __tablename__ = 'osumapinfo'
    map_id = Column(Integer, primary_key=True)
    map_url = Column(String(100))
    MOTD = Column(Integer)

    # Song Details
    title = Column(String(255))
    artist = Column(String(255))
    language = Column(String(20))
    genre = Column(String(20))
    bpm = Column(Integer)

    # Beatmap Info
    map_length = Column(Integer)
    star_rating = Column(Float)
    diff_name = Column(String(255))
    play_count = Column(Integer)
    background = Column(String(100))
    release_date = Column(String(100))

    # Mapper Info
    mapper_name = Column(String(100))
    mapper_previous_names = Column(String(255))
    mapper_country = Column(String(30))
    mapper_url = Column(String(60))
    mapper_avatar = Column(String(60))
    gd = Column(TINYINT)

    # Media
    youtube_link_1 = Column(String(255))
    youtube_link_2 = Column(String(255))
    youtube_link_3 = Column(String(255))

    # Takes an osumap object and generates its videos into the videos folder
    def generate_media(self, number, start, length=15, music=False):

        print("Generating video number %s for: %s" % (str(number), str(self.title)))

        # Pick render settings
        settings = "HideBG"
        if music:
            settings = "HideBG+unmute"

        # File paths
        outfilename = "osudle! Day %d Video %d" % (self.MOTD, number)
        cwd = os.getcwd()
        danser_path = os.path.join(cwd, "danser")
        temp_path = os.path.join(cwd, "danser", "videos", outfilename+'.mp4')

        # Clear temp folder
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Danser saves files to danser/videos
        #danser-cli.exe -skip -id='2117132' -settings='HideBG' -start='8' -end='23' -out=temp
        clistring = 'danser-cli.exe -skip -id="%s" -settings="%s" -start="%d" -end="%d" -out="%s"' % (
            self.map_id, settings, start, start + length, outfilename)
        subprocess.run(clistring, cwd=danser_path, shell=True, check=True, stdout=subprocess.DEVNULL)

        if not os.path.exists(temp_path):
            print("Maybe map not downloaded")
            clistring = 'danser-cli.exe -skip -t="%s" -d="%s" -settings="%s" -start="%d" -end="%d" -out="%s"' % (
                self.title, self.diff_name, settings, start, start + length, outfilename)
            subprocess.run(clistring, cwd=danser_path, shell=True, check=True, stdout=subprocess.DEVNULL)

    # Find videos in videos folder to upload to youtube
    # We SHOULD check to see if the video is on youtube, but we have limited youtube api quota, so we wont
    def upload_all_media(self):

        uploader = YoutubeHandler()
        uploader.start_service()

        videos_folder = os.path.join(os.getcwd(), "danser", "videos")

        if self.youtube_link_1 is None:
            title = "osudle! Day %d Video 1" % self.MOTD
            filepath = os.path.join(videos_folder, title+'.mp4')
            print('Uploading video 1')
            self.youtube_link_1 = uploader.upload_video(filepath, title)

        if self.youtube_link_2 is None:
            title = "osudle! Day %d Video 2" % self.MOTD
            filepath = os.path.join(videos_folder, title+'.mp4')
            print('Uploading video 2')
            self.youtube_link_2 = uploader.upload_video(filepath, title)

        if self.youtube_link_3 is None:
            title = "osudle! Day %d Video 3" % self.MOTD
            filepath = os.path.join(videos_folder, title+'.mp4')
            print('Uploading video 3')
            self.youtube_link_3 = uploader.upload_video(filepath, title)

        return True

    # daily map number = -1 if not a daily map
    def __init__(self, map_id, daily_map_number):

        print("Accessing osu! api for map: %d" % map_id)

        try:
            bmsinfo = api.beatmapset(beatmap_id=map_id)
            beatmap = api.beatmap(map_id)
            mapper = api.user(beatmap.user_id)
        except Exception as e:
            print('something wrong with %d. GOOF LUCK' % map_id)
            print(e)
            return

        # If bmsinfo.user_id != beatmap.used_id, then the map is a gd

        # Identifiers
        self.map_id = map_id
        self.map_url = beatmap.url
        self.MOTD = daily_map_number

        # Song Details
        self.title = bmsinfo.title
        self.artist = bmsinfo.artist
        self.language = bmsinfo.language['name']
        self.genre = bmsinfo.genre['name']
        self.bpm = bmsinfo.bpm

        # Beatmap Details
        self.map_length = beatmap.total_length
        self.star_rating = beatmap.difficulty_rating
        self.diff_name = beatmap.version
        self.play_count = bmsinfo.play_count
        self.background = bmsinfo.covers.cover_2x
        self.release_date = str(bmsinfo.submitted_date)

        # Mapper Info
        self.mapper_name = mapper.username
        self.mapper_previous_names = str(mapper.previous_usernames)
        self.mapper_country = mapper.country.name
        self.mapper_url = "https://osu.ppy.sh/users/%s" % str(mapper.id)
        self.mapper_avatar = mapper.avatar_url
        self.gd = not (bmsinfo.user_id == beatmap.user_id)

def add_maps(maps):

    # type check for array
    if type(maps) is int:
        maps = [maps]

    for map_id in maps:
        print()
        # Check to see if map is not in db

        if get_map_in_db(map_id) is not None:
            print("%s already exists in database. Skipping" % str(map_id))
        else:
            print("Adding %s to database." % str(map_id))
            # Create an osuMap object and commit to db
            new_osu_map = osuMap(map_id, -1)
            session.add(new_osu_map)

            # Really, you should only commit after everything is added but i dont want to :    ^)
            session.commit()

def add_new_MOTD(map_id, starting_points):

    if len(starting_points) != 3:
        print('Please provide 3 starting points')
        return

    # CHECK 2 THINGS
    # IF MAP IS IN DB ALREADY AND IF IT IS A MOTD

    # IF IT IS MOTD, return nothing
    # IF IT IS IN THE DB BUT NOT MOTD, DELETE THE RECORD FROM DB

    temp = get_map_in_db(map_id)
    if temp is not None:
        if temp.MOTD != -1:
            print('%s is already a MOTD' % temp.title)
        else:
            ans = input('%s is already in the db. Overwrite? (y/n)' % temp.title)
            if (ans == 'y'):
                print('Okay, deleting..')
                delete_map_from_db(map_id)
            else:
                print('Okay Aborting..')

    next_daily = getNextDaily()
    new_osu_map = osuMap(map_id, next_daily)

    # Add confirmation here
    print('Are you sure you want %s - [%s] to be map number %d? (y/n/m)' % (new_osu_map.title, new_osu_map.diff_name, next_daily))
    check = input()
    if (check not in ['y', 'm']):
        return

    # Generate the videos for the object
    new_osu_map.generate_media(1, starting_points[0])
    new_osu_map.generate_media(2, starting_points[1])
    new_osu_map.generate_media(3, starting_points[2], music=True)

    # Maybe add another check here?

    if (check == 'm'):
        if (input('Are the videos good to upload? (y/n)') != 'y'):
            return

    #All videos should exist in danser/videos so we can upload them
    new_osu_map.upload_all_media()
    session.add(new_osu_map)
    session.commit()

def generate_map_videos(map_id, starting_points):
    if type(starting_points) is int:
        starting_points = [starting_points]
    map_data = session.get(osuMap, map_id)
    for i, times in enumerate(starting_points):
        map_data.generate_media(i+1, starting_points[i], music=(i == 2))

    return

# Returns the number corresponding to the next daily map
def getNextDaily():
    allMaps = session.query(osuMap).where(osuMap.MOTD >= 0).all()
    list_of_dailies = [x.MOTD for x in allMaps if x.MOTD != -1]
    a = sorted(set(range(1, list_of_dailies[-1])) - set(list_of_dailies))
    return max(list_of_dailies)+1 if a == [] else a[0]

# See if map exists in db
# Returns None if map dne
def get_map_in_db(map_id):
    map_record = session.query(osuMap).where(osuMap.map_id == map_id).scalar()
    return map_record

def delete_map_from_db(map_id):
    map_record = get_map_in_db(map_id)
    if map_record is not None:
        session.delete(map_record)
        session.commit()
    else:
        print('Tried to delete %d, but it is not in the database!' % map_id)

# A good example of how to access the db using the SQLAlchemy
def change_covers(map_id):
    map_data = session.get(osuMap, map_id)
    new_bg_link = map_data.background.replace("card", "cover@2x")
    map_data.background = new_bg_link
    session.commit()
    return


if __name__ == '__main__':
    engine = create_engine("mysql+pymysql://%s:%s@%s/%s" % (db_user, db_pass, db_host, db_name), future=True)

    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    #generate_map_videos(163054, [0, 122, 190])
    add_new_MOTD(165325, [0, 43, 60])
    #add_maps([2547713])
    #a = get_map_in_db(1946507)


    print("Finished!")
