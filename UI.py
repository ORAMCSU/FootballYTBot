import csv
from pickle import load
from tkinter import *
from tkinter import colorchooser
from tkinter.ttk import Separator
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
import PIL.ImageTk
import PIL.Image
import googleapiclient.discovery
import requests
import bs4
from functools import partial

from googleapiclient.http import MediaFileUpload
from pygame import mixer
from time import localtime, strptime, mktime, time


class ManagerWindow(Tk):
    """
    Window used to control the livestream.
    """

    def __init__(self):

        Tk.__init__(self)
        self.title("Stream Manager")
        self.configure(bg='#4E4E4E')

        self.MainFrame = SetupFrame(self, width=900, height=700, bg='#4E4E4E')
        self.YtFrame = YoutubeFrame(self, width=900, height=200, bg='#4E4E4E')
        self.StreamFrame = EditFrame(self, bg='#4E4E4E')

        self.MainFrame.grid(row=0, column=0)
        self.YtFrame.grid(row=1, column=0)
        self.StreamFrame.grid(row=0, column=2, rowspan=2)
        Separator(self, orient="vertical").grid(row=0, column=1, rowspan=2, sticky="ns", padx=4)

        self.csv_links = []
        self.current_csv = 0
        self.afters = {"rotate": None, "free": None}
        self.after_blocked = {"rotate": False, "free": False}

        self.MatchWindow = None

    def launch_match(self, nb_matches, url_list, empty_text=""):
        """
        Method that displays the stream window if it is not already on, updates it otherwise. Also updates the EditFrame
        :param nb_matches: int number of simultaneous matches to display (from 1 to 4)
        :param url_list: list containing the urls to the specific matches
        :param empty_text: text to display if no match is left
        :return: None
        """

        # if there is no MatchWindow, create one. Otherwise update the current one.
        if not self.MatchWindow:
            self.MatchWindow = MatchWindow(master=self, nb_matches=nb_matches, url_list=url_list, empty_text=empty_text)
            self.StreamFrame.load_edit(nb_matches)

        else:
            self.MatchWindow.change_match_number(nb_matches, url_list, empty_text=empty_text)
            self.StreamFrame.load_edit(nb_matches)

    def move(self, tag, direction):
        """
        Method used as a medium between EditFrame and MatchWindow for moving text parts of the stream.
        :param tag: string, tag of the item in the canvas.
        :param direction: tuple of 2 int indicating how to move the element on the 2D axes. Same numbers indicated font
        size change
        :return: None
        """
        self.MatchWindow.move(tag, direction)

    def define_user_comment(self, color="black", text=""):
        """
        Method used as a medium between YoutubeFrame and MatchWindow to generate the Defined User Text.
        :param color: string indicating the color of the text
        :param text: text to dislay. Empty indicates the text has to be erased.
        :return: None
        """
        self.MatchWindow.define_user_comment(color, text)

    def load_video(self, video_url):
        """
        Method used as a medium between YoutubeFrame and MatchWindow to load the likes and views of the video.
        :param video_url: url of the livestream
        :return: None
        """
        self.MatchWindow.load_video_stats(video_url)

    def launch_playback(self, filename):
        """
        Method used as a medium between YoutubeFrame and MatchWindow to play the music selected
        :param filename:
        :return: None
        """
        self.MatchWindow.playback(filename)

    def is_stream_on(self):
        """
        Method to indicate if the stream window is created
        :return: boolean indicating if the stream window is already created
        """
        return not (self.MatchWindow is None)

    def erase(self):
        """
        Method to erase the reference to the MatchWindow
        :return: None
        """
        self.MatchWindow = None

    def load_from_csv(self, launch=True):
        """
        Method called to load the content of the file named schedule.csv
        :param launch: boolean indicating whether one wants to call launch_match after running the method
        :return: None
        """
        for block in self.after_blocked.values():
            if block:
                self.after(500, self.load_from_csv)
                return

        for after in self.afters.values():
            if after:
                self.after_cancel(after)

        error_urls = []
        self.csv_links = []
        with open("./ressources/schedule.csv", "r", encoding="utf8") as file:
            reader = csv.reader(file, delimiter=",")
            for row in reader:
                match_page = requests.get(row[0])
                soup = bs4.BeautifulSoup(match_page.text, "html.parser")
                if soup.find("title").text != "Erreur 404":
                    if len(row) == 1:
                        row.append("2")
                    if not([row[0], 0, int(row[1])] in self.csv_links):
                        self.csv_links.append([row[0], 0, int(row[1])])
                else:
                    error_urls.append(row[0])

        if error_urls:
            showerror("Erreur 404", f"Le(s) match(s) que vous cherchez, {error_urls}, " +
                      "n'existe(nt) pas sur matchendirect.")

        if launch:
            self.timer()
            self.clean_list()
            self.csv_match()

    def load_to_csv(self, new_urls=None, empty=False):
        """
        Method called to refresh the content of the csv file
        :param new_urls: list of urls to add to the csv file
        :param empty: boolean indicating if csv_links is intentionnally empty (False indicates that it has never been
        loaded)
        :return: None
        """
        if not self.csv_links and not empty:
            self.load_from_csv(False)
        if new_urls:
            self.csv_links += new_urls
        with open("ressources/schedule.csv", 'w', newline="") as f:
            print("ui")
            writer = csv.writer(f, delimiter=',')
            for link in self.csv_links:
                writer.writerow(link[0::2])

    def csv_match(self):
        """
        Method called to prepare to launch a MatchWindow following the schedule.
        :return: None
        """
        print("Changement de matchs")
        i = 0
        url_list = []
        while i < 4 and i < len(self.csv_links) and self.csv_links[i][1] == -1:
            url_list.append(self.csv_links[i][0])
            i += 1

        self.current_csv = i
        message = ""
        if self.current_csv == 0 and self.csv_links:
            cast_time = localtime(self.csv_links[0][1] * 60)
            now = localtime()
            if now.tm_mday != cast_time.tm_mday or now.tm_mon != cast_time.tm_mon or now.tm_year != cast_time.tm_year:
                message = " le " + str(cast_time.tm_mday) + "/" + "{0:0=2d}".format(cast_time.tm_mon)
            message += " à " + str(cast_time.tm_hour) + "h" + "{0:0=2d}".format(cast_time.tm_min) + "."

        self.launch_match(i, url_list, message)
        self.waiter()

    def waiter(self):
        """
        Method called to shedule future actions concerning the refresh of displayed matches.
        :return: None
        """
        now = int(time() // 60)
        if self.current_csv < len(self.csv_links) and self.current_csv < 4:
            if self.csv_links[self.current_csv][1] - now - 5 < 0:
                self.rotate_matches()
            else:
                if not self.afters["rotate"]:
                    self.afters["rotate"] = self.after((self.csv_links[self.current_csv][1] - now - 5) * 60000,
                                                       self.rotate_matches)
                if self.csv_links[self.current_csv][1] - now > 10:
                    self.afters["free"] = self.after(300000, self.free_matches)
        else:
            self.afters["free"] = self.after(300000, self.free_matches)

        # only liberate the blockers when after calls to either free_matches or rotate_matches are scheduled
        self.after_blocked["rotate"] = False
        self.after_blocked["free"] = False

    def rotate_matches(self):
        """
        Method called when a new match begins.
        :return: None
        """
        # turn the blocker on to indicate that not cancellation can be made right away
        self.after_blocked["rotate"] = True
        self.afters["rotate"] = None
        self.csv_links[self.current_csv][1] = -1
        self.check_finished()
        self.csv_links.sort(key=self.sortlinks_key)
        self.clean_list()
        self.csv_match()

    def free_matches(self):
        """
        Method called regularly to remove finished matches from the MatchWindow.
        :return: None
        """
        # turn the blocker on to indicate that not cancellation can be made right away
        self.after_blocked["free"] = True
        self.afters["free"] = None
        old_list = self.csv_links.copy()
        self.check_finished()
        self.csv_links.sort(key=self.sortlinks_key)
        self.clean_list()
        if self.csv_links != old_list:
            self.csv_match()
        else:
            self.waiter()  # even if no modification is done to the stream, it is necessary to loop back for checks

    def check_finished(self):
        """
        Method that checks whether there are finished matches into the csv_links list.
        :return: None
        """
        for i in range(self.current_csv):
            link = self.csv_links[i]
            match_page = requests.get(link[0])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            minute_text = soup.find(class_="status").text
            if minute_text == "Match terminé":
                link[1] = -2

    def timer(self):
        """
        Method used to calculate when the matches of csv_links will start. Gives them the time status -1 if the match is
        ongoing, -2 if it is finished/cancelled.
        :return: None
        """
        time_conv = {"janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                     "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12}
        now = int(time() // 60)  # current time in minutes

        for link in self.csv_links:
            match_page = requests.get(link[0])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            minute_text = soup.find(class_="status").text
            print(minute_text)
            print("oui")
            if minute_text.split(" ")[0] == "Coup":
                start = soup.find("div", class_="info1").text.split("|")[0]
                start = start.split(" ")[1:4] + [start.split(" ")[-2]]
                start[1] = time_conv[start[1]]
                cast_time = strptime(str(start), "['%d', %m, '%Y', '%Hh%M']")
                cast_time = int(mktime(cast_time) // 60)
                if cast_time - 5 < now:
                    link[1] = -1
                else:
                    link[1] = cast_time
            elif minute_text == " Mi-temps":
                link[1] = -1  # match ongoing
            elif minute_text in ["Match terminé", "Match annulé", "0"] or minute_text[:6] in [" (déla", "Report"]:
                link[1] = -2
            else:
                link[1] = -1  # match ongoing

        self.csv_links.sort(key=self.sortlinks_key)

    def sortlinks_key(self, link):
        """
        Method called when sorting the csv_links attribute list
        :param link: element of the list to move
        :return: int to use to sort (link[2] is always inferior to link[1] if link[1] is positive)
        """
        if link[1] == -1:
            return link[2]
        else:
            return link[1]

    def clean_list(self):
        """
        Method called to remove all finished/cancelled matches from the list of matches to display.
        :return: None
        """
        if self.csv_links:
            while self.csv_links[0][1] == -2:
                self.csv_links.pop(0)
                if not self.csv_links:
                    self.load_to_csv(empty=True)
                    return

            self.load_to_csv()

    def destroy(self):
        """
        Method handling some problems happening when destroying the Stream Manager before the MatchWindow.
        :return: None
        """
        if self.MatchWindow:
            self.MatchWindow.destroy()
        Tk.destroy(self)


class MatchWindow(Toplevel):
    """
    Window used for the youtube livestream.
    """

    def __init__(self, master: ManagerWindow, nb_matches: int, url_list=None, empty_text=""):
        Toplevel.__init__(self, master)
        self.youtube = self.authenticate()
        self.master = master
        self.title("Match Stream")
        self.match_urls = []
        self.nb_matches = -1
        self.stop_gif = False
        self.afters = {"scores": None, "timer": None, "commentaries": None, "gif": None}
        self.after_blocked = {"scores": False, "timer": False, "commentaries": False, "gif": False}
        self.videos_infos = {"video_id": None, "title": "", "description": [], "tags": [],
                             "thumbnail": MediaFileUpload("./ressources/images/thumbnail.jpg")}
        self.base_description = ["", "Subscribe! /Abonne-toi!",
                                 "https://www.youtube.com/channel/UCvahkUIQv3F1eYh7BV0CmbQ?sub_confirmation=1", ""]
        self.base_tags = ["foot", "match foot", "foot en direct", "Actu2Foot", "uefa", "match en direct", "direct",
                          "football", "buts", "goals", "actu2foot", "actu foot", "score", "score direct", "match",
                          "multiplex", "live", "score en direct", "stream", "communauté foot"]

        self.MatchCanvas = Canvas(self, width=1536, height=864)
        self.MatchCanvas.grid(row=0, column=0)

        self.displayed_bg = None
        self.displayed_logo = None
        self.displayed_black = None
        self.displayed_icons = []
        self.displayed_teamlogos = []
        self.displayed_championnat = None

        self.load_bases()
        self.load_channel_stats()
        self.change_match_number(nb_matches, url_list, empty_text)

    def update_videos(self):
        """
        Method called to trigger the online update of all video info.
        :return: None
        """
        print(self.videos_infos)

        # get all the information related to the livestream
        videos_list_response = self.youtube.videos().list(id=self.videos_infos["video_id"], part="snippet").execute()
        videos_list_snippet = videos_list_response["items"][0]["snippet"]

        # update only the relevant parts
        videos_list_snippet["title"] = self.videos_infos["title"]
        videos_list_snippet["description"] = "\n".join(self.videos_infos["description"])
        videos_list_snippet["tags"] = list(set(self.videos_infos["tags"]))

        # to avoid any bugs, push the whole modified thing
        self.youtube.videos() \
            .update(part="snippet", body=dict(snippet=videos_list_snippet, id=self.videos_infos["video_id"])).execute()
        self.youtube.thumbnails().set(videoId=self.videos_infos["video_id"],
                                      media_body=self.videos_infos["thumbnail"]).execute()

    def update_video_info(self, titre="", description=None, tags=None):
        """
        Method called to update the informations of the livestream
        :param titre: new title for the livestream
        :param description: description to set below the video
        :param tags: tags to put into the video
        :return: None
        """
        self.videos_infos["title"] = titre
        if description:
            self.videos_infos["description"] = description
        if tags:
            self.videos_infos["tags"] = tags

    def load_bases(self):
        """
        Method to load the very bases of the Canvas (called only at initiation).
        :return: None
        """
        # Main background
        pil_image = PIL.Image.open("./ressources/images/fond_direct.jpg")
        pil_image2 = pil_image.resize((1536, 864))
        pil_image.close()
        self.displayed_bg = PIL.ImageTk.PhotoImage(pil_image2)

        self.MatchCanvas.create_image(770, 434, image=self.displayed_bg, tag="Background")

        pil_image2.close()  # Close to make sure memory is free

        # Logo of the channel
        pil_image = PIL.Image.open("./ressources/images/logo.png")
        pil_image2 = pil_image.resize((100, 100))
        pil_image.close()
        self.displayed_logo = PIL.ImageTk.PhotoImage(pil_image2)

        self.MatchCanvas.create_image(70, 70, image=self.displayed_logo, tag="Logo")

        pil_image2.close()

        # load all the icons related to youtube statistics
        iconlist = ["./ressources/images/youtube.png", "./ressources/images/views.png", "./ressources/images/likes.png"]
        for i in range(3):
            self.MatchCanvas.create_rectangle(1306, 20 + 70 * i, 1486, 70 + 70 * i, fill="white", outline="white")
            pil_image2.close()
            pil_image = PIL.Image.open(iconlist[i])
            pil_image2 = pil_image.resize((int((pil_image.size[0] / pil_image.size[1]) * 40), 40))
            pil_image.close()

            self.displayed_icons.append(PIL.ImageTk.PhotoImage(pil_image2))
            self.MatchCanvas.create_image(1341, 45 + 70 * i, image=self.displayed_icons[i], tag="Icon" + str(i))

        pil_image2.close()

    def load_black(self):
        """
        Method called to draw the black background
        :return: None
        """
        pil_image = PIL.Image.open("./ressources/images/affiche_vierge.png")

        # different sizes depending on the number of matches
        if self.nb_matches == 1:
            pil_image2 = pil_image.resize((1150, 234))
        elif self.nb_matches == 2:
            pil_image2 = pil_image.resize((875, 195))
        else:
            pil_image2 = pil_image.resize((700, 156))
        pil_image.close()
        if pil_image2:
            self.displayed_black = PIL.ImageTk.PhotoImage(pil_image2)

        # placement is different according to the number of matches
        for i in range(self.nb_matches):
            if self.nb_matches == 1:
                self.MatchCanvas.create_image(770, 500, image=self.displayed_black, tag="Black" + str(i))

            elif self.nb_matches == 2:
                self.MatchCanvas.create_image(770, 300 * i + 320, image=self.displayed_black, tag="Black" + str(i))

            elif self.nb_matches == 3:
                self.MatchCanvas.create_image(770 - 375 * (i == 1) + 375 * (i == 2), 265 * (i > 0) + 300,
                                              image=self.displayed_black, tag="Black" + str(i))
            elif self.nb_matches == 4:
                self.MatchCanvas.create_image(770 - 375 * (i % 2 == 0) + 375 * (i % 2 == 1), 265 * (i > 1) + 300,
                                              image=self.displayed_black, tag="Black" + str(i))

    def load_match_stats(self):
        """
        Method called to set all the places where things are displayed on the stream. Used every time the number of
        matches is different.
        :return: None
        """
        # font_sizes = ((30, 40, 12, (12, 35)), (22, 40, 10, (10, 25)), (20, 35, 8, (7, 20)), (20, 35, 8, (7, 20)))

        for j in range(self.nb_matches):
            # sizes and coordinates depend on the number of matches, and are set through experimentation
            if self.nb_matches == 1:
                for i in range(2):
                    self.MatchCanvas.create_text(195 * (1 - i) + (1 - 2 * i) * 300 + 1347 * i, 500, font=["Ubuntu", 30],
                                                 fill="white", justify="center", tag="TeamName" + str(i))

                for i in range(2):
                    self.MatchCanvas.create_text(195 * (1 - i) + (1 - 2 * i) * 493 + 1347 * i, 535, font=["Ubuntu", 40],
                                                 fill="white", justify="center", tag="score" + str(i))

                self.MatchCanvas.create_rectangle(221, 625, 1321, 720, tag="bg" + str(j), width=0)
                self.MatchCanvas.create_text(771, 672, font=["Arial", 12],
                                             fill="black", tag="commentaire" + str(j), width=1100)

                for i in range(2):
                    self.MatchCanvas.create_image(195 * (1 - i) + (1 - 2 * i) * 100 + 1347 * i, 500, tag="Teamlogo" +
                                                                                                         str(2 * j + i))

                self.MatchCanvas.create_text(771, 448, justify="center", tag="timer" + str(j))
                self.MatchCanvas.create_oval(710, 438, 730, 458, fill="green", tag="gif" + str(j))

            elif self.nb_matches == 2:
                for i in range(2):
                    self.MatchCanvas.create_text(333 * (1 - i) + (1 - 2 * i) * 240 + 1217 * i, 300 * j + 320,  # -30
                                                 font=["Ubuntu", 22],
                                                 fill="white", justify="center", tag="TeamName" + str(2 * j + i))

                for i in range(2):
                    self.MatchCanvas.create_text(325 * (1 - i) + (1 - 2 * i) * 383 + 1217 * i, 300 * j + 350,
                                                 font=["Ubuntu", 40],
                                                 fill="white", justify="center", tag="score" + str(2 * j + i))

                self.MatchCanvas.create_rectangle(360, 420 + 300 * j, 1180, 506 + 300 * j, width=0, tag="bg" + str(j))
                self.MatchCanvas.create_text(771, 463 + 300 * j,
                                             text="", font=["Arial", 10],
                                             fill="black", tag="commentaire" + str(j), width=800)

                for i in range(2):
                    self.MatchCanvas.create_image(333 * (1 - i) + (1 - 2 * i) * 80 + 1207 * i, 300 * j + 320,
                                                  tag="Teamlogo" + str(2 * j + i))

                self.MatchCanvas.create_text(771, 277 + 300 * j, justify="center", tag="timer" + str(j))
                self.MatchCanvas.create_oval(715, 267 + 300 * j, 735, 287 + 300 * j, fill="green", tag="gif" + str(j))

            elif self.nb_matches == 3:
                for i in range(2):
                    self.MatchCanvas.create_text((420 - 375 * (j == 1) + 375 * (j == 2)) * (1 - i) + (1 - 2 * i) * 190 +
                                                 (1120 - 375 * (j == 1) + 375 * (j == 2)) * i, 265 * (j >= 1) + 300,
                                                 font=["Ubuntu", 20],
                                                 fill="white", justify="center", tag="TeamName" + str(2 * j + i))

                for i in range(2):
                    self.MatchCanvas.create_text((420 - 375 * (j == 1) + 375 * (j == 2)) * (1 - i) + (1 - 2 * i) * 300 +
                                                 (1122 - 375 * (j == 1) + 375 * (j == 2)) * i, 265 * (j >= 1) + 322,
                                                 font=["Ubuntu", 35],
                                                 fill="white", justify="center", tag="score" + str(2 * j + i))

                self.MatchCanvas.create_rectangle(50 + 375 * (j == 0) + 750 * (j == 2), 387 + 265 * (j >= 1),
                                                  740 + 375 * (j == 0) + 750 * (j == 2), 469 + 265 * (j >= 1),
                                                  width=0, tag="bg" + str(j))

                self.MatchCanvas.create_text((770 - 375 * (j == 1) + 375 * (j == 2)), 265 * (j >= 1) + 425,
                                             text="", font=["Arial", 8],
                                             fill="black", tag="commentaire" + str(j), width=680)

                for i in range(2):
                    self.MatchCanvas.create_image((420 - 375 * (j == 1) + 375 * (j == 2)) * (1 - i) + (1 - 2 * i) * 70 +
                                                  (1120 - 375 * (j == 1) + 375 * (j == 2)) * i, 265 * (j >= 1) + 300,
                                                  tag="Teamlogo" + str(2 * j + i))

                self.MatchCanvas.create_text(771 - 375 * (j == 1) + 375 * (j == 2), 263 + 265 * (j >= 1),
                                             justify="center", tag="timer" + str(j))
                self.MatchCanvas.create_oval(710 - 375 * (j == 1) + 375 * (j == 2), 253 + 265 * (j >= 1),
                                             730 - 375 * (j == 1) + 375 * (j == 2), 273 + 265 * (j >= 1),
                                             fill="green", tag="gif" + str(j))

            elif self.nb_matches == 4:
                for i in range(2):
                    self.MatchCanvas.create_text(
                        (420 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                        190 + (1120 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * i, 265 * (j >= 2) + 300,
                        font=["Ubuntu", 20],
                        fill="white", justify="center", tag="TeamName" + str(2 * j + i))

                for i in range(2):
                    self.MatchCanvas.create_text(
                        (420 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                        300 + (1122 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * i, 265 * (j >= 2) + 322,  # -50, +50
                        font=["Ubuntu", 35],
                        fill="white", justify="center", tag="score" + str(2 * j + i))

                self.MatchCanvas.create_rectangle(50 + 750 * (j % 2 == 1), 385 + 265 * (j >= 2),  # -45
                                                  740 + 750 * (j % 2 == 1), 469 + 265 * (j >= 2),  # -10
                                                  width=0, tag="bg" + str(j))

                self.MatchCanvas.create_text((770 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)),
                                             265 * (j >= 2) + 425,  # -30
                                             text="", font=["Arial", 8],
                                             fill="black", tag="commentaire" + str(j), width=680)

                for i in range(2):
                    self.MatchCanvas.create_image(
                        (420 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                        70 + (1120 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * i, 265 * (j >= 2) + 300,
                        tag="Teamlogo" + str(2 * j + i))

                self.MatchCanvas.create_text(771 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1), 263 + 265 * (j >= 2),
                                             justify="center", tag="timer" + str(j))
                self.MatchCanvas.create_oval(720 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1), 253 + 265 * (j >= 2),
                                             740 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1), 273 + 265 * (j >= 2),
                                             fill="green", tag="gif" + str(j))

        # once places are set, load the actual data
        self.load_match_teams()
        self.reload_match_score()
        self.reload_match_commentaries()
        self.reload_match_timer()

    def change_matches(self, new_urls: list):
        """
        Method called when matches rotate without changing their numbers
        :param new_urls: list of urls with the new matches to display
        :return: None
        """
        self.match_urls = new_urls
        self.load_match_teams()
        self.reload_match_score()
        self.reload_match_commentaries()
        self.reload_match_timer()

    def change_match_number(self, new_number: int, new_urls: list, empty_text=""):
        """
        Method called when rotating matches
        :param new_number: new number of matches to be displayed
        :param new_urls: list of urls of the new matches to display
        :param empty_text:
        :return: None
        """
        # tell the gif process to stop
        self.stop_gif = True
        # make sure all after methods are currently waiting
        for value in self.after_blocked.values():
            if value:
                self.after(500, self.change_match_number, new_number, new_urls)
                return
        self.stop_gif = False

        # cancel all sheduled methods
        for after_id in self.afters.values():
            if after_id:
                self.after_cancel(after_id)

        # erase the championship logo and the message for empty screen
        self.MatchCanvas.delete("Empty")
        self.MatchCanvas.delete("champ")

        # if there is a different number of matches to be displayed, erase all elements not related to the video itself
        if new_number != self.nb_matches:
            for j in range(self.nb_matches):
                self.MatchCanvas.delete("bg" + str(j))
                self.MatchCanvas.delete("commentaire" + str(j))
                self.MatchCanvas.delete("timer" + str(j))
                self.MatchCanvas.delete("Black" + str(j))
                self.MatchCanvas.delete("gif" + str(j))
                for i in range(2):
                    self.MatchCanvas.delete("Teamlogo" + str(2 * j + i))
                    self.MatchCanvas.delete("TeamName" + str(2 * j + i))
                    self.MatchCanvas.delete("score" + str(2 * j + i))

            self.nb_matches = new_number
            self.match_urls = new_urls

            # if there is at least a match to display, call the regular setting functions
            if self.nb_matches:
                self.load_black()
                self.load_match_stats()
                self.play_gif()
            # if there is no match to display anymore, use the specific method
            else:
                self.load_empty(empty_text)

        # if only the urls are different, the process is lighter
        elif self.match_urls != new_urls:
            self.change_matches(new_urls)
            self.play_gif()

        # if there was no match, and there is still none, recreate an empty text with possibly new content
        elif new_number == 0:
            self.load_empty(empty_text)

    def load_empty(self, empty_text=""):
        """
        Method called when there is no match to display. Displays a specific text instead.
        :param empty_text: sentence to display
        :return: None
        """
        # if there is no text, it means there is no match scheduled anymore, display the specific message
        if not empty_text:
            self.MatchCanvas.create_rectangle(350, 400, 1190, 560, fill="white", tag="Empty", width=0)
            self.MatchCanvas.create_text(770, 480, width=800, text="C'est fini pour aujourd'hui.\n" +
                                                                   "Il n'y a plus de match prévus pour ce stream.\n" +
                                                                   "A plus la team!",
                                         justify="center", tag="Empty", font=["Ubuntu", 30])
            self.update_video_info("Actu2Foot revient bientôt", self.base_description, self.base_tags)
            # if the livestream was linked to the window, update its information
            if self.videos_infos["video_id"]:
                self.update_videos()
        else:
            self.MatchCanvas.create_rectangle(350, 450, 1190, 510, fill="white", tag="Empty", width=0)
            self.MatchCanvas.create_text(770, 480, text="Prochain match prévu" + empty_text, tag="Empty",
                                         font=["Ubuntu", 30])
            self.update_video_info("[Score en direct] Prochain match prévu" + empty_text, self.base_description,
                                   self.base_tags)
            # if the livestream was linked to the window, update its information
            if self.videos_infos["video_id"]:
                self.update_videos()

    def load_match_teams(self):
        """
        Method called to load all the information about the teams playing the match.
        :return: None
        """
        self.displayed_teamlogos = []
        self.videos_infos["title"] = "[Score en direct]"
        self.displayed_championnat = None
        first_url_logo_champ = ""
        dict_head_description = {}
        hashtag_description = []
        list_tags = []

        for j in range(self.nb_matches):
            # if the number of matches does not fit the number of urls, return (should not happen anyway)
            if j >= len(self.match_urls):
                return

            # initialise match title, description and hashtags
            match_title = " "
            match_head_description = ""

            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")

            # add championship hashtags
            championnat = soup.find("div", class_="info1").text.split("|")[1][1:-1]
            if championnat not in dict_head_description:
                dict_head_description[championnat] = [""]
            hashtag = "#" + championnat.lower().replace(" ", "").replace("-", "")

            # add team hashtags
            if not (hashtag in hashtag_description):
                hashtag_description.append(hashtag)
            tag = championnat.lower()
            if not (tag in list_tags):
                list_tags.append(tag)

            # display team names on the MatchWindow
            i = 0
            for div in soup.find_all("div", class_="col-xs-4 text-center team"):
                self.MatchCanvas.itemconfigure("TeamName" + str(2 * j + i), text=div.text[1:-1].replace(" ", "\n"))
                match_title += div.text[1:-1]
                match_head_description += div.text[1:-1]
                hashtag = "#" + div.text[1:-1].lower().replace(" ", "").replace("-", "")
                hashtag_description.append(hashtag)
                tag = div.text[1:-1].lower()
                list_tags.append(tag)
                if i == 0:
                    match_title += " - "
                    match_head_description += " - "
                i += 1

            # configure video description
            match_head_description += " | [Score en direct]"
            dict_head_description[championnat].append(match_head_description)

            # configure match title
            if j != (self.nb_matches - 1):
                match_title += " |"
            if len(self.videos_infos["title"] + match_title) <= 100:
                self.videos_infos["title"] += match_title
            elif self.videos_infos["title"][0:18] == "[Score en direct]" and \
                    len(self.videos_infos["title"][18:] + match_title) <= 100:
                self.videos_infos["title"] = self.videos_infos["title"][18:] + match_title

            # display team logos on the MatchWindow
            i = 0
            for div in soup.find_all("div", class_="col-xs-4 text-center"):
                full_url = "https://www.matchendirect.fr" + div.find("img")["src"].replace("/96/", "/128/")
                pil_image = PIL.Image.open(requests.get(full_url, stream=True).raw)
                self.displayed_teamlogos.append(PIL.ImageTk.PhotoImage(pil_image))
                self.MatchCanvas.itemconfigure("Teamlogo" + str(2 * j + i), image=self.displayed_teamlogos[2 * j + i])
                i += 1

            # check if all the matchs are from the same championship
            url_logo_champ = "https://www.matchendirect.fr" + \
                             soup.find("div", class_="col-xs-4 text-center imgfootball").find("img")["src"]

            if j == 0:
                first_url_logo_champ = url_logo_champ
                pil_image = PIL.Image.open(requests.get(url_logo_champ, stream=True).raw)
                logo = PIL.ImageTk.PhotoImage(pil_image)
                self.displayed_championnat = logo
            else:
                if first_url_logo_champ != url_logo_champ:
                    self.displayed_championnat = None

        self.display_championnat()

        # finish to configure video title, description and hashtags
        if self.videos_infos["title"][-1] == "|":
            self.videos_infos["title"] = self.videos_infos["title"][:-1]

        head_description = []
        for key in dict_head_description:
            head_description.append(key)
            for match in dict_head_description[key]:
                head_description.append(match)
            head_description.append("")

        self.videos_infos["description"] = head_description + self.base_description + hashtag_description
        self.videos_infos["tags"] = self.base_tags + list_tags

        # update video infos
        if self.videos_infos["video_id"]:
            self.update_videos()

    def display_championnat(self):
        """
        Method to display the championship of the matches, if all matches belong to the same championship
        :return: None
        """
        if self.displayed_championnat:
            self.MatchCanvas.create_image(770, 120, image=self.displayed_championnat, tag="champ")

    def define_user_comment(self, color="black", text=""):
        """
        Method called when it is needed to write a specific message on the stream
        :param color: string of a color
        :param text: string containing hte message to display. Empty means message will be erased
        :return: None
        """
        if text:
            self.MatchCanvas.create_rectangle(370, 820, 1170, 860, fill="white", width=0, tag="white_defined_bg")
            self.MatchCanvas.create_text(770, 840, text=text, fill=color, font=["Ubuntu", 18], tag="defined_text")
        else:
            self.MatchCanvas.delete("white_defined_bg")
            self.MatchCanvas.delete("defined_text")

    def reload_match_score(self):
        """
        Method called every ten seconds to reload the scores of the matches
        :return: None
        """
        self.after_blocked["scores"] = True
        for j in range(self.nb_matches):
            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            i = 0
            for score in soup.find_all(class_="score"):
                self.MatchCanvas.itemconfigure("score" + str(2 * j + i), text=score.text)
                i += 1
        print("Scores mis à jour")
        self.afters["scores"] = self.after(10000, self.reload_match_score)
        self.after_blocked["scores"] = False

    def reload_match_commentaries(self):
        """
        Method called every minute to reload the commentaries below the matches
        :return: None
        """
        self.after_blocked["commentaries"] = True
        for j in range(self.nb_matches):
            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            a = soup.find(class_="bg-primary")
            if a is not None:
                if not a.text:
                    a = "0'"
                else:
                    a = a.text + "'"
                b = soup.find(id="commentaire").find_all("td")[2].text
                self.MatchCanvas.itemconfigure("bg" + str(j), fill="#E5E4E1")
                self.MatchCanvas.itemconfigure("commentaire" + str(j), text=a + " : " + b)
        print("Commentaires mis à jour")
        self.afters["commentaries"] = self.after(60000, self.reload_match_commentaries)
        self.after_blocked["commentaries"] = False

    def reload_match_timer(self):
        """
        Method called every minute to actualize the timer.
        :return: None
        """
        self.after_blocked["timer"] = True
        for j in range(self.nb_matches):
            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            minute_text = soup.find(class_="status").text
            if minute_text.split(" ")[0] == "Coup":
                self.MatchCanvas.itemconfigure("timer" + str(j), text="Débute\nà " + minute_text.split(" ")[3],
                                               font=["Ubuntu",
                                                     7 + 3 * (self.nb_matches <= 2) + 2 * (self.nb_matches == 1)])
            elif minute_text == " Mi-temps":
                self.MatchCanvas.itemconfigure("timer" + str(j), text=minute_text.strip(" ").replace("-", "-\n"),
                                               font=["Ubuntu",
                                                     7 + 3 * (self.nb_matches <= 2) + 2 * (self.nb_matches == 1)])
            elif minute_text == "Match terminé":
                self.MatchCanvas.itemconfigure("timer" + str(j), text=minute_text.replace(" ", "\n"),
                                               font=["Ubuntu",
                                                     7 + 3 * (self.nb_matches <= 2) + 2 * (self.nb_matches == 1)])
            else:
                if self.MatchCanvas.itemcget("timer"+str(j), "text") and \
                        self.MatchCanvas.itemcget("timer"+str(j), "text")[-1] == "'":
                    timer_font = self.MatchCanvas.itemcget("timer", "font").split(" ")
                else:
                    timer_font = ["Ubuntu", 20 + 5 * (self.nb_matches <= 2) + 10 * (self.nb_matches == 1)]

                self.MatchCanvas.itemconfigure("timer" + str(j), text=minute_text.strip(" "), font=timer_font)

        print("Timer mis à jour")
        self.afters["timer"] = self.after(60000, self.reload_match_timer)
        self.after_blocked["timer"] = False

    def load_channel_stats(self):
        """
        Method called to display the number of subscribers to the channel.
        :return: None
        """
        self.MatchCanvas.create_text(1416, 45, font=["Ubuntu", 20], tag="Subs")
        self.reload_channel_stats()

    def reload_channel_stats(self):
        """
        Method called every 65 seconds to actualize the number of subscribers to the channel.
        :return: None
        """
        channel_list_response = self.youtube.channels().list(mine=True, part='statistics').execute()
        full_text = channel_list_response["items"][0]["statistics"]["subscriberCount"]
        self.MatchCanvas.itemconfigure("Subs", text=full_text)
        self.after(65000, self.reload_channel_stats)

    def load_video_stats(self, video_link=""):
        """
        Method called to assert if the video is a livestream, then update the number of likes and views.
        :param video_link: url of the livestream
        :return: None
        """
        if video_link[:32] == "https://www.youtube.com/watch?v=":
            video_id = video_link.split("?v=")[1].split("&ab")[0]
        else:
            video_id = video_link.split(".be/")[1]
        infos = self.youtube.videos().list(id=video_id, part="snippet").execute()
        print(infos)
        if infos['pageInfo']['totalResults'] != 0 and infos['items'][0]['snippet']['liveBroadcastContent'] == 'live':
            self.videos_infos["video_id"] = video_id
        else:
            showerror("Mauvaise URL de stream", "L'url que vous avez rentrée : \n" + video_link +
                      "\nne correspond pas à un live youtube.")
            return

        self.update_videos()

        stats = self.youtube.videos().list(id=self.videos_infos["video_id"], part="statistics").execute()
        video = stats["items"][0]["statistics"]

        self.MatchCanvas.create_text(1416, 115, text=str(video["viewCount"]),
                                     font=["Ubuntu", 20], tag="Views")
        self.MatchCanvas.create_text(1416, 185, text=str(video["likeCount"]),
                                     font=["Ubuntu", 20], tag="Likes")

        self.after(60000, self.reload_video_stats)

    def reload_video_stats(self):
        """
        Method called every minute to actualize the number of like and views of the livestream
        :return: None
        """
        stats = self.youtube.videos().list(id=self.videos_infos["video_id"], part="statistics").execute()
        video = stats["items"][0]["statistics"]
        self.MatchCanvas.itemconfigure("Views", text=str(video["viewCount"]))
        self.MatchCanvas.itemconfigure("Likes", text=str(int(video["likeCount"]) + 1))

        self.after(60000, self.reload_video_stats)
        print("Stats mises à jour")

    def move(self, tag: str, direction: tuple):
        """
        Method called to move text elements (timers and team names) and adjust the font size
        :param tag: tag given to the element to move
        :param direction: 2 int tuple indicating how to move the text on a 2D base
        :return: None
        """
        if direction[0] * direction[1] == 0:
            self.MatchCanvas.move(tag, 10 * direction[0], 10 * direction[1])
        else:
            current = self.MatchCanvas.itemcget(tag, "font").split(" ")
            self.MatchCanvas.itemconfigure(tag, font=[current[0], int(current[1]) + direction[0]])

    def play_gif(self, i=True):
        """
        Method called to play the timer gif
        :param i: boolean indicating if the image is displayed of hidden
        :return: None
        """
        self.after_blocked["gif"] = True
        for j in range(self.nb_matches):
            timer_text = self.MatchCanvas.itemcget("timer" + str(j), "text")
            if timer_text[-1] == "'" and i:
                self.MatchCanvas.tag_raise("gif"+str(j), "Black"+str(j))
            else:
                self.MatchCanvas.tag_lower("gif"+str(j), "Black"+str(j))
        if not self.stop_gif:
            self.afters["gif"] = self.after(1000, self.play_gif, not i)
        else:
            self.afters["gif"] = None
        self.after_blocked["gif"] = False

    def playback(self, filename: str):
        """
        Method called to play an audio file in the window. Loops it 10 times before stopping.
        :param filename: absolute path to the audio file
        :return: None
        """
        mixer.init()
        mixer.music.load(filename)
        mixer.music.play(10)

    def destroy(self):
        """
        Overriden method that makes sure the audio player is off before destroying self. Erases its reference in the
        master.
        :return: None
        """
        if mixer.get_init():
            mixer.music.stop()
            mixer.quit()
        self.master.StreamFrame.load_edit(0)
        self.master.erase()
        Toplevel.destroy(self)

    def authenticate(self):
        """
        Method called once to identify the application to youtube
        :return: identifiers to handle youtube-specific requests
        """
        with open("ressources/credentials", 'rb') as f:
            credentials = load(f)
        return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


class SetupFrame(Frame):
    """
    Frame to set up the MatchWindow and launch it.
    """
    def __init__(self, master: ManagerWindow, **kwargs):
        Frame.__init__(self, master, kwargs)
        self.master = master
        self.old_number = 0
        self.url_entries = []
        self.auto_on = False

        # number of matches and auto mode
        self.ModeButton = Checkbutton(self, text="Mode Automatique", command=self.change_mode, bg='#4E4E4E',
                                      activebackground='#4E4E4E', fg='white', activeforeground='white',
                                      selectcolor='#4E4E4E')
        self.MatchButton = Button(self, text="Lancer le suivi", command=self.launch_match, bg='#4E4E4E', fg='white')
        self.NumberRoll = Spinbox(self, from_=1, to=4, bg='#4E4E4E', fg='white', justify='center',
                                  buttonbackground='#4E4E4E')
        self.NumberButton = Button(self, text="Valider", command=self.generate_urls, width=10, bg='#4E4E4E', fg='white')
        self.Schedule = Button(self, text="Schedule", command=self.launch_schedule, width=10, bg='#4E4E4E', fg='white')

        self.ModeButton.grid(row=0, column=1, padx=10, pady=10)
        Label(self, text="Importance du match: ", width=20, bg='#4E4E4E', fg='white').grid(row=1, column=0)
        self.NumberRoll.grid(row=1, column=1, padx=10, pady=10)
        self.NumberButton.grid(row=1, column=2, padx=10, pady=10)

        self.generate_urls()

    def change_mode(self):
        """
        Method called to switch between automatic scheduled display mode and manual display mode.
        :return: None
        """
        if not self.auto_on:
            self.auto_on = True
            self.MatchButton.configure(text="Ajouter au csv", command=self.load_to_csv)
            self.NumberRoll.config(to=10)
            self.generate_urls()
            self.Schedule.grid(row=self.old_number + 2, column=2)
        else:
            self.auto_on = False
            self.MatchButton.config(text="Lancer le suivi", command=self.launch_match)
            self.NumberRoll.config(to=4)
            self.generate_urls()
            self.Schedule.grid_forget()

    def load_to_csv(self):
        """
        Method used to add match urls to the current csv file.
        :return: None
        """
        if self.old_number:
            url_list = []
            for i in self.url_entries:
                # verify that the url leads to the right website. Otherwise, add it to the list of wrong urls
                if i[0].get() and i[0].get()[:40] == "https://www.matchendirect.fr/live-score/" and \
                        i[0].get()[-5:] == ".html":
                    if bs4.BeautifulSoup(requests.get(i[0].get()).text, "html.parser").find("title")\
                            .text != "Erreur 404":
                        url_list.append([i[0].get(), 0, i[1].get()])  # [url, 0, priority]
                    else:
                        showerror("Erreur 404", f"Le match que vous cherchez, {i[0].get()}, " +
                                  "n'existe pas sur matchendirect.")
                        return
                else:
                    showerror("Mauvaises urls", "Vérifiez la validité des urls entrées.")
                    return

            # call the master method to add the urls to the csv
            self.master.load_to_csv(url_list)

    def generate_urls(self, _event=None):
        """
        Method that generates the entries for the match urls.
        :param _event: in case method is called from a bind method.
        :return: None
        """
        number = int(self.NumberRoll.get())
        if self.old_number != number:
            self.MatchButton.grid_forget()
            if number > self.old_number:
                for i in range(number - self.old_number):
                    self.url_entries.append([Entry(self, width=70, bg='#6b6b6b', fg='white'),
                                             Scale(self, orient="horizontal", from_=2, to=0,
                                                   length=50, showvalue='no', sliderlength=20, background="#4E4E4E",
                                                   bd=0, fg="red", highlightbackground="#4E4E4E",
                                                   bg="#4E4E4E", borderwidth=0, activebackground='#4E4E4E')])
                    self.url_entries[self.old_number + i][0].grid(row=self.old_number + 2 + i, column=1, padx=10,
                                                                  pady=10)
                    self.url_entries[self.old_number + i][1].grid(row=self.old_number + 2 + i, column=0)
                    self.url_entries[self.old_number + i][1].set(2)
            else:
                for i in range(self.old_number - number):
                    self.url_entries[number + i][0].destroy()
                    self.url_entries[number + i][1].destroy()
                self.url_entries = self.url_entries[:number]

            self.old_number = number

            self.MatchButton.grid(row=self.old_number + 2, column=1, padx=10, pady=10)

            # if automatic mode is enabled, display the button to schedule matches
            if self.auto_on:
                self.Schedule.grid(row=self.old_number + 2, column=2, padx=10, pady=10)

    def launch_match(self, _event=None):
        """
        Method that directly launches a MatchWindow with specific matches
        :param _event: in case method is called by a bind method
        :return: None
        """
        if self.old_number:
            url_list = []
            for i in self.url_entries:
                # Check if url is valid and prepares to launch it. Otherwise raise an error window.
                if i[0].get() and i[0].get()[:40] == "https://www.matchendirect.fr/live-score/" and \
                        i[0].get()[-5:] == ".html":
                    if bs4.BeautifulSoup(requests.get(i[0].get()).text, "html.parser").find("title")\
                            .text != "Erreur 404":
                        url_list.append(i[0].get())
                    else:
                        showerror("Erreur 404", f"Le match que vous cherchez, {i[0].get()}, " +
                                  "n'existe pas sur matchendirect.")
                        return
                else:
                    showerror("Mauvaises urls", "Vérifiez la validité des urls entrées.")
                    return

            # launch the match with the specified urls
            self.master.launch_match(nb_matches=self.old_number, url_list=url_list)

    def launch_schedule(self):
        """
        Method that launches the scheduled display of matches. Calls the masters method loading the csv file
        :return: None
        """
        self.master.load_from_csv()


class YoutubeFrame(Frame):
    """
    Frame that handles all the parts of the MatchWindow related to the livestream.
    """

    def __init__(self, master: ManagerWindow, **kwargs):
        Frame.__init__(self, master, kwargs)
        self.nb_matches = 0
        self.master = master  # master is set again to assert its type as ManagerWindow

        # Widgets and attributes for the User Defined Text
        self.color = 'black'
        self.displayed = False  # whether the User Defined Text is already defined
        self.ColorPicker = Button(self, text="Couleur", command=self.choose_color, bg='#4E4E4E', fg='white')
        self.DefinedText = Entry(self, width=70, bg='#6b6b6b', fg='white')
        self.DisplayButton = Button(self, text="Afficher Message", command=self.display_text, bg='#4E4E4E', fg='white')

        # Widgets for the videostream url
        Label(self, text="Url du stream: ", width=20, bg='#4E4E4E', fg='white').grid(row=2, column=0)
        self.VideoEntry = Entry(self, width=70, bg='#6b6b6b', fg='white')
        self.VideoButton = Button(self, text="Charger", command=self.load_video, width=10, bg='#4E4E4E',
                                  fg='white')

        # Widgets and attribute for the audio playback
        self.musicfile = ""  # name of the audio file
        self.MusicButton = Button(self, text="Choix Musique", command=self.select_playback, bg='#4E4E4E', fg='white')
        self.MusicPlay = Button(self, text="Jouer Musique", command=self.launch_playback, bg='#4E4E4E', fg='white')

        Separator(self, orient="horizontal").grid(row=0, column=0, columnspan=3, sticky="we", pady=4, padx=2)
        self.ColorPicker.grid(row=1, column=0, padx=10, pady=10)
        self.DefinedText.grid(row=1, column=1, padx=10, pady=10)
        self.DisplayButton.grid(row=1, column=2, padx=10, pady=10)
        self.VideoEntry.grid(row=2, column=1, padx=10, pady=10)
        self.VideoButton.grid(row=2, column=2, padx=10, pady=10)
        self.MusicButton.grid(row=3, column=0, padx=10, pady=10)
        self.MusicPlay.grid(row=3, column=1, padx=10, pady=10)

    def display_text(self):
        """
        Method that takes the string written in DefinedText to display it on the MatchWindow as the User Defined Text.
        :return: None
        """

        # check that stream is active and the user has something to say
        if self.master.is_stream_on() and self.DefinedText.get() != "" and not self.displayed:
            self.DisplayButton.config(text="Supprimer message")
            self.master.define_user_comment(self.color, self.DefinedText.get())
            self.displayed = True

        # if message is already displayed, ask to remove it
        elif self.displayed:
            self.DisplayButton.config(text="Afficher message")
            self.master.define_user_comment()
            self.displayed = False

    def choose_color(self):
        """
        Method to select the color of the User Defined Commentary.
        :return: None
        """
        self.color = colorchooser.askcolor(title="Choose color")[1]

    def load_video(self):
        """
        Method that takes the url of the current stream written in VideoEntry and passes it to the MatchWindow
        :return: None
        """

        if self.master.is_stream_on():
            # Verify if the given url is a youtube link. Otherwise, display an error window.
            if self.VideoEntry.get() and (self.VideoEntry.get()[:32] == "https://www.youtube.com/watch?v=" or
                                          self.VideoEntry.get()[:17] == "https://youtu.be/"):
                self.master.load_video(self.VideoEntry.get())
            else:
                showerror("Mauvaise URL de vidéo.", f"L'url renseignée \"{self.VideoEntry.get()}\" " +
                          "n'est pas un lien youtube valable.")

    def select_playback(self):
        """
        Method to choose the audio file to play on the stream.
        :return: None
        """
        self.musicfile = askopenfilename(initialdir="./ressources/", filetypes=[("Tout audio", (".mp3", ".ogg",
                                                                                                ".wav")),
                                                                                ("Fichier compressé", ".mp3"),
                                                                                ('Audio non compressé', ".wav")])

    def launch_playback(self):
        """
        Method that gives the order to start playing the audio file chosen with select_playback.
        :return: None
        """
        if self.master.is_stream_on():
            if self.musicfile:
                self.master.launch_playback(self.musicfile)


class EditFrame(Frame):
    """
    Frame for the handling of specific critical textual parts in the MatchWindow
    """

    def __init__(self, master: ManagerWindow, **kwargs):
        """
        New __init__ function, more precise about the master attribute, alike on other aspects
        :param master: Widget containing this widget
        :param kwargs: all typical Frame arguments
        """
        Frame.__init__(self, master, kwargs)
        self.nb_matches = 0  # number of matches currently displayed
        self.master = master

    def move(self, tag, direction):
        """
        Method triggered to move an element of the MatchCanvas of the MatchWindow
        :param tag: string, tag of the element to move
        :param direction: tuple of 2 int indicating how to move the element on the 2D axes. Same numbers indicated font
        size change
        :return: None
        """

        self.master.move(tag, direction)

    def load_edit(self, matches_number):
        """
        Method that loads all the buttons to move Team Names and Timers (and reduce font size). To call every time
        matches are changed.
        :param matches_number: number of matches to be displayed on the MatchWindow
        :return: None
        """
        self.nb_matches = matches_number

        # clean everything
        for i in self.grid_slaves():
            i.destroy()

        Separator(self, orient="horizontal").grid(row=0, column=0, columnspan=20, sticky="we", pady=4)

        for i in range(self.nb_matches):
            # for each match, display the buttons to adjust the timer
            Label(self, text="Match " + str(i + 1),
                  bg='#4E4E4E', fg='white').grid(row=3 * i + 1, column=1, rowspan=2, padx=10, pady=10)
            Separator(self, orient="vertical").grid(row=3 * i + 1, column=2, rowspan=2,
                                                    sticky="ns", padx=10, pady=4)
            Label(self, text="Timer :",
                  bg='#4E4E4E', fg='white').grid(row=3 * i + 1, column=3, rowspan=2, padx=10, pady=10)
            Button(self, text="\U000025C0", fg='white',
                   command=partial(self.move, "timer" + str(i), (-1, 0)),
                   bg='#4E4E4E').grid(row=3 * i + 1, column=4, rowspan=2, padx=5, pady=10, sticky='e')
            Button(self, text="\U000025B6", fg='white',
                   command=partial(self.move, "timer" + str(i), (1, 0)),
                   bg='#4E4E4E').grid(row=3 * i + 1, column=6, rowspan=2, padx=5, pady=10, sticky='w')
            Button(self, text="\U000025B2", fg='white',
                   command=partial(self.move, "timer" + str(i), (0, -1)),
                   bg='#4E4E4E').grid(row=3 * i + 1, column=5, padx=5, pady=10)
            Button(self, text="\U000025BC", fg='white',
                   command=partial(self.move, "timer" + str(i), (0, 1)),
                   bg='#4E4E4E').grid(row=3 * i + 2, column=5, padx=5, pady=10)
            Button(self, text="\U000025B2", fg='white',
                   command=partial(self.move, "timer" + str(i), (1, 1)),
                   bg='#4E4E4E').grid(row=3 * i + 1, column=7, padx=10, pady=10)
            Button(self, text="\U000025BC", fg='white',
                   command=partial(self.move, "timer" + str(i), (-1, -1)),
                   bg='#4E4E4E').grid(row=3 * i + 2, column=7, padx=10, pady=10)
            Separator(self, orient="horizontal").grid(row=3 * i + 3, column=0, columnspan=20,
                                                      sticky="we", pady=4)

            for j in range(2):
                # for each team of the match, display the buttons to adjust the name of the team
                Separator(self, orient="vertical").grid(row=3 * i + 1, column=6 * (j + 1) + 2, rowspan=2,
                                                        sticky="ns", padx=10, pady=4)
                Label(self, text="Equipe " + str(j + 1) + " :",
                      bg='#4E4E4E', fg='white').grid(row=3 * i + 1, column=6 * (j + 1) + 3, rowspan=2, padx=10, pady=10)
                Button(self, text="\U000025C0", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (-1, 0)),
                       bg='#4E4E4E').grid(row=3 * i + 1, column=6 * (j + 1) + 4, rowspan=2, padx=5, pady=10)
                Button(self, text="\U000025B6", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (1, 0)),
                       bg='#4E4E4E').grid(row=3 * i + 1, column=6 * (j + 2), rowspan=2, padx=5, pady=10)
                Button(self, text="\U000025B2", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (0, -1)),
                       bg='#4E4E4E').grid(row=3 * i + 1, column=6 * (j + 1) + 5, padx=5, pady=10)
                Button(self, text="\U000025BC", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (0, 1)),
                       bg='#4E4E4E').grid(row=3 * i + 2, column=6 * (j + 1) + 5, padx=5, pady=10)
                Button(self, text="\U000025B2", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (1, 1)),
                       bg='#4E4E4E').grid(row=3 * i + 1, column=6 * (j + 2) + 1, padx=10, pady=10)
                Button(self, text="\U000025BC", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (-1, -1)),
                       bg='#4E4E4E').grid(row=3 * i + 2, column=6 * (j + 2) + 1, padx=10, pady=10)
