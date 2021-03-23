from pickle import load
from tkinter import *
from tkinter.ttk import Separator
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
import PIL.ImageTk
import PIL.Image
import googleapiclient.discovery
import requests
import bs4
from functools import partial
from pygame import mixer
from time import localtime, strptime, mktime, time


class ManagerWindow(Tk):

    def __init__(self):

        Tk.__init__(self)
        self.title("Stream Manager")
        self.configure(bg='#4E4E4E')

        self.MainFrame = SetupFrame(self, width=900, height=700, bg='#4E4E4E')
        self.StreamFrame = EditFrame(self, width=900, height=200, bg='#4E4E4E')

        self.MainFrame.grid(row=0, column=0)
        self.StreamFrame.grid(row=1, column=0)

        self.csv_links = []
        self.current_csv = 0
        self.afters = {"rotate": None, "free": None}
        self.after_blocked = {"rotate": False, "free": False}

        self.MatchWindow = None

    def launch_match(self, nb_matches, url_list, empty_text=""):

        if not self.MatchWindow:
            self.MatchWindow = MatchWindow(master=self, nb_matches=nb_matches, url_list=url_list, empty_text=empty_text)

            self.StreamFrame.load_edit(nb_matches)

        else:
            self.MatchWindow.change_match_number(nb_matches, url_list, empty_text=empty_text)
            self.StreamFrame.load_edit(nb_matches)

    def move(self, tag, direction):

        self.MatchWindow.move(tag, direction)

    def load_video(self, video_url):
        self.MatchWindow.load_video_stats(video_url)

    def launch_playback(self, filename):
        self.MatchWindow.playback(filename)

    def is_stream_on(self):
        return not (self.MatchWindow is None)

    def erase(self):
        self.MatchWindow = None

    def load_from_csv(self):

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
            url = file.readline().strip("\n").split(",")[0].strip("\ufeff")
            while url:
                match_page = requests.get(url)
                soup = bs4.BeautifulSoup(match_page.text, "html.parser")
                if soup.find("title").text != "Erreur 404":
                    if not([url, 0] in self.csv_links):
                        self.csv_links.append([url, 0])
                else:
                    error_urls.append(url)
                url = file.readline().strip("\n").split(",")[0].strip("\ufeff")

        if error_urls:
            showerror("Erreur 404", f"Le(s) match(s) que vous cherchez, {error_urls}, " +
                      "n'existe(nt) pas sur matchendirect.")

        self.timer()
        self.clean_list()
        self.csv_match()

    def csv_match(self):
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

        self.after_blocked["rotate"] = False
        self.after_blocked["free"] = False

    def rotate_matches(self):
        self.after_blocked["rotate"] = True
        self.afters["rotate"] = None
        self.csv_links[self.current_csv][1] = -1
        self.check_finished()
        self.csv_links.sort(key=lambda i: i[1])
        self.clean_list()
        self.csv_match()

    def free_matches(self):
        self.after_blocked["free"] = True
        self.afters["free"] = None
        old_list = self.csv_links.copy()
        self.check_finished()
        self.csv_links.sort(key=lambda i: i[1])
        self.clean_list()
        if self.csv_links != old_list:
            self.csv_match()
        else:
            self.waiter()  # self.after(300000, self.free_matches)

    def check_finished(self):

        for i in range(self.current_csv):
            link = self.csv_links[i]
            match_page = requests.get(link[0])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            minute_text = soup.find(class_="status").text
            if minute_text == "Match terminé":
                link[1] = -2

    def timer(self):

        time_conv = {"janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                     "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12}
        now = int(time() // 60)

        for link in self.csv_links:
            match_page = requests.get(link[0])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            minute_text = soup.find(class_="status").text
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
            elif minute_text == "Match terminé":
                link[1] = -2
            else:
                link[1] = -1  # match ongoing

        self.csv_links.sort(key=lambda i: i[1])

    def clean_list(self):

        if self.csv_links:
            while self.csv_links[0][1] == -2:
                self.csv_links.pop(0)
                if not self.csv_links:
                    return


class MatchWindow(Toplevel):

    def __init__(self, master: ManagerWindow, nb_matches, url_list=None, empty_text=""):

        Toplevel.__init__(self, master)
        self.youtube = self.authenticate()
        self.master = master
        self.title("Match Stream")
        self.match_urls = []
        self.nb_matches = -1
        self.gif = []
        self.stop_gif = False
        self.afters = {"scores": None, "timer": None, "commentaries": None, "gif": None}
        self.after_blocked = {"scores": False, "timer": False, "commentaries": False, "gif": False}
        self.videos_infos = {"video_id": None, "title": "", "description": [], "tags": []}
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

        self.load_gif()
        self.load_bases()
        self.load_channel_stats()
        self.change_match_number(nb_matches, url_list, empty_text)

    def update_videos(self):

        print(self.videos_infos)

        videos_list_response = self.youtube.videos().list(id=self.videos_infos["video_id"], part="snippet").execute()

        videos_list_snippet = videos_list_response["items"][0]["snippet"]

        videos_list_snippet["title"] = self.videos_infos["title"]
        videos_list_snippet["description"] = "\n".join(self.videos_infos["description"])
        videos_list_snippet["tags"] = list(set(self.videos_infos["tags"]))

        self.youtube.videos() \
            .update(part="snippet", body=dict(snippet=videos_list_snippet, id=self.videos_infos["video_id"])).execute()

    def update_video_infos(self, titre="", description=None, tags=None):
        self.videos_infos["title"] = titre
        if description:
            self.videos_infos["description"] = description
        if tags:
            self.videos_infos["tags"] = tags

    def load_bases(self):
        pil_image = PIL.Image.open("./ressources/images/fond_direct.jpg")
        pil_image2 = pil_image.resize((1536, 864))
        pil_image.close()
        self.displayed_bg = PIL.ImageTk.PhotoImage(pil_image2)

        self.MatchCanvas.create_image(770, 434, image=self.displayed_bg, tag="Background")

        pil_image2.close()
        pil_image = PIL.Image.open("./ressources/images/logo.png")
        pil_image2 = pil_image.resize((100, 100))
        pil_image.close()
        self.displayed_logo = PIL.ImageTk.PhotoImage(pil_image2)

        self.MatchCanvas.create_image(70, 70, image=self.displayed_logo, tag="Logo")

        pil_image2.close()

        self.load_black()

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

        pil_image = PIL.Image.open("./ressources/images/affiche_vierge.png")

        if self.nb_matches == 1:
            pil_image2 = pil_image.resize((1150, 234))
        elif self.nb_matches == 2:
            pil_image2 = pil_image.resize((875, 195))
        else:  # self.nb_matches == 3 or self.nb_matches == 4:
            pil_image2 = pil_image.resize((700, 156))
        pil_image.close()
        if pil_image2:
            self.displayed_black = PIL.ImageTk.PhotoImage(pil_image2)

        for i in range(self.nb_matches):
            if self.nb_matches == 1:
                self.MatchCanvas.create_image(770, 500, image=self.displayed_black, tag="Black" + str(i))

            elif self.nb_matches == 2:
                self.MatchCanvas.create_image(770, 270 * i + 350, image=self.displayed_black, tag="Black" + str(i))

            elif self.nb_matches == 3:
                self.MatchCanvas.create_image(770 - 375 * (i == 1) + 375 * (i == 2), 215 * (i > 0) + 350,
                                              image=self.displayed_black, tag="Black" + str(i))
            elif self.nb_matches == 4:
                self.MatchCanvas.create_image(770 - 375 * (i % 2 == 1) + 375 * (i % 2 == 0), 215 * (i > 1) + 350,
                                              image=self.displayed_black, tag="Black" + str(i))

    def load_gif(self):
        gifimg = PIL.Image.open("./ressources/images/gif-eye.gif")

        for i in range(55):
            gifimg.seek(i)
            self.gif.append(PIL.ImageTk.PhotoImage(gifimg.copy().resize((30, 30))))

        gifimg.close()

    def load_match_stats(self):

        # font_sizes = ((30, 40, 12, (12, 35)), (22, 40, 10, (10, 25)), (20, 35, 8, (7, 20)), (20, 35, 8, (7, 20)))

        for j in range(self.nb_matches):

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
                self.MatchCanvas.create_image(720, 448, tag="gif" + str(j))

            elif self.nb_matches == 2:
                for i in range(2):
                    self.MatchCanvas.create_text(333 * (1 - i) + (1 - 2 * i) * 220 + 1217 * i, 270 * j + 350,
                                                 font=["Ubuntu", 22],
                                                 fill="white", justify="center", tag="TeamName" + str(2 * j + i))

                for i in range(2):
                    self.MatchCanvas.create_text(325 * (1 - i) + (1 - 2 * i) * 383 + 1217 * i, 270 * j + 380,
                                                 font=["Ubuntu", 40],
                                                 fill="white", justify="center", tag="score" + str(2 * j + i))

                self.MatchCanvas.create_rectangle(360, 450 + 270 * j, 1180, 511 + 270 * j, width=0, tag="bg" + str(j))
                self.MatchCanvas.create_text(771, 483 + 270 * j,
                                             text="", font=["Arial", 10],
                                             fill="black", tag="commentaire" + str(j), width=800)

                for i in range(2):
                    self.MatchCanvas.create_image(333 * (1 - i) + (1 - 2 * i) * 80 + 1207 * i, 270 * j + 350,
                                                  tag="Teamlogo" + str(2 * j + i))

                self.MatchCanvas.create_text(771, 307 + 270 * j, justify="center", tag="timer" + str(j))
                self.MatchCanvas.create_image(725, 307 + 270 * j, tag="gif" + str(j))

            elif self.nb_matches == 3:
                for i in range(2):
                    self.MatchCanvas.create_text((420 - 375 * (j == 1) + 375 * (j == 2)) * (1 - i) + (1 - 2 * i) * 190 +
                                                 (1120 - 375 * (j == 1) + 375 * (j == 2)) * i, 215 * (j >= 1) + 350,
                                                 font=["Ubuntu", 20],
                                                 fill="white", justify="center", tag="TeamName" + str(2 * j + i))

                for i in range(2):
                    self.MatchCanvas.create_text((420 - 375 * (j == 1) + 375 * (j == 2)) * (1 - i) + (1 - 2 * i) * 300 +
                                                 (1122 - 375 * (j == 1) + 375 * (j == 2)) * i, 215 * (j >= 1) + 372,
                                                 font=["Ubuntu", 35],
                                                 fill="white", justify="center", tag="score" + str(2 * j + i))

                self.MatchCanvas.create_rectangle(50 + 375 * (j == 0) + 750 * (j == 2), 432 + 215 * (j >= 1),
                                                  740 + 375 * (j == 0) + 750 * (j == 2), 479 + 215 * (j >= 1),
                                                  width=0, tag="bg" + str(j))

                self.MatchCanvas.create_text((770 - 375 * (j == 1) + 375 * (j == 2)), 215 * (j >= 1) + 455,
                                             text="", font=["Arial", 8],
                                             fill="black", tag="commentaire" + str(j), width=680)

                for i in range(2):
                    self.MatchCanvas.create_image((420 - 375 * (j == 1) + 375 * (j == 2)) * (1 - i) + (1 - 2 * i) * 70 +
                                                  (1120 - 375 * (j == 1) + 375 * (j == 2)) * i, 215 * (j >= 1) + 350,
                                                  tag="Teamlogo" + str(2 * j + i))

                self.MatchCanvas.create_text(771 - 375 * (j == 1) + 375 * (j == 2), 313 + 215 * (j >= 1),
                                             justify="center", tag="timer" + str(j))
                self.MatchCanvas.create_image(730 - 375 * (j == 1) + 375 * (j == 2), 313 + 215 * (j >= 1),
                                              tag="gif" + str(j))

            elif self.nb_matches == 4:
                for i in range(2):
                    self.MatchCanvas.create_text(
                        (420 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                        190 + (1120 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * i, 215 * (j >= 2) + 350,
                        font=["Ubuntu", 20],
                        fill="white", justify="center", tag="TeamName" + str(2 * j + i))

                for i in range(2):
                    self.MatchCanvas.create_text(
                        (420 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                        300 + (1122 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * i, 215 * (j >= 2) + 372,
                        font=["Ubuntu", 35],
                        fill="white", justify="center", tag="score" + str(2 * j + i))

                self.MatchCanvas.create_rectangle(50 + 750 * (j % 2 == 1), 432 + 215 * (j >= 2),
                                                  740 + 750 * (j % 2 == 1), 479 + 215 * (j >= 2),
                                                  width=0, tag="bg" + str(j))

                self.MatchCanvas.create_text((770 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)),
                                             215 * (j >= 2) + 455,
                                             text="", font=["Arial", 8],
                                             fill="black", tag="commentaire" + str(j), width=680)

                for i in range(2):
                    self.MatchCanvas.create_image(
                        (420 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                        70 + (1120 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1)) * i, 215 * (j >= 2) + 350,
                        tag="Teamlogo" + str(2 * j + i))

                self.MatchCanvas.create_text(771 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1), 313 + 215 * (j >= 2),
                                             justify="center", tag="timer" + str(j))
                self.MatchCanvas.create_image(730 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1), 313 + 215 * (j >= 2),
                                              tag="gif" + str(j))
        self.load_match_teams()
        self.reload_match_score()
        self.reload_match_commentaries()
        self.reload_match_timer()

    def change_matches(self, new_urls):

        self.match_urls = new_urls
        self.load_match_teams()
        self.reload_match_score()
        self.reload_match_commentaries()
        self.reload_match_timer()

    def change_match_number(self, new_number, new_urls, empty_text=""):
        self.stop_gif = True
        for value in self.after_blocked.values():
            if value:
                self.after(500, self.change_match_number, new_number, new_urls)
                return
        self.stop_gif = False

        self.MatchCanvas.delete("Empty")
        self.MatchCanvas.delete("champ")

        if new_number != self.nb_matches:
            for after_id in self.afters.values():
                if after_id:
                    self.after_cancel(after_id)
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
            if self.nb_matches:
                self.load_black()
                self.load_match_stats()
            else:
                self.load_empty(empty_text)

        elif self.match_urls != new_urls:
            for after_id in self.afters.values():
                if after_id:
                    self.after_cancel(after_id)
            self.change_matches(new_urls)

        elif new_number == 0:
            self.load_empty(empty_text)

        # self.play_gif(0)

    def load_empty(self, empty_text=""):
        if not empty_text:
            self.MatchCanvas.create_rectangle(350, 400, 1190, 560, fill="white", tag="Empty", width=0)
            self.MatchCanvas.create_text(770, 480, width=800, text="C'est fini pour aujourd'hui.\n" +
                                                                   "Il n'y a plus de match prévus pour ce stream.\n" +
                                                                   "A plus la team!",
                                         justify="center", tag="Empty", font=["Ubuntu", 30])
            self.update_video_infos("Actu2Foot revient bientôt", self.base_description, self.base_tags)
            if self.videos_infos["video_id"]:
                self.update_videos()
        else:
            self.MatchCanvas.create_rectangle(350, 450, 1190, 510, fill="white", tag="Empty", width=0)
            self.MatchCanvas.create_text(770, 480, text="Prochain match prévu" + empty_text, tag="Empty",
                                         font=["Ubuntu", 30])
            self.update_video_infos("[Score en direct] Prochain match prévu" + empty_text, self.base_description,
                                    self.base_tags)
            if self.videos_infos["video_id"]:
                self.update_videos()

    def load_match_teams(self):

        self.displayed_teamlogos = []
        self.videos_infos["title"] = "[Score en direct]"
        self.displayed_championnat = None
        first_url_logo_champ = ""
        dict_head_description = {}
        hashtag_description = []
        list_tags = []

        for j in range(self.nb_matches):
            if j >= len(self.match_urls):
                return

            match_title = " "
            match_head_description = ""
            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            championnat = soup.find("div", class_="info1").text.split("|")[1][1:-1]
            if championnat not in dict_head_description:
                dict_head_description[championnat] = [""]
            hashtag = "#" + championnat.lower().replace(" ", "").replace("-", "")
            if not (hashtag in hashtag_description):
                hashtag_description.append(hashtag)
            tag = championnat.lower()
            if not (tag in list_tags):
                list_tags.append(tag)
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
                    match_title += "-"
                    match_head_description += " - "
                i += 1

            match_head_description += " | [Score en direct]"
            dict_head_description[championnat].append(match_head_description)

            if j != (self.nb_matches - 1):
                match_title += " |"

            if len(self.videos_infos["title"] + match_title) <= 100:
                self.videos_infos["title"] += match_title
            elif self.videos_infos["title"][0:18] == "[Score en direct]" and \
                    len(self.videos_infos["title"][18:] + match_title) <= 100:
                self.videos_infos["title"] = self.videos_infos["title"][18:] + match_title

            i = 0
            for div in soup.find_all("div", class_="col-xs-4 text-center"):
                full_url = "https://www.matchendirect.fr" + div.find("img")["src"].replace("/96/", "/128/")
                pil_image = PIL.Image.open(requests.get(full_url, stream=True).raw)
                self.displayed_teamlogos.append(PIL.ImageTk.PhotoImage(pil_image))
                self.MatchCanvas.itemconfigure("Teamlogo" + str(2 * j + i), image=self.displayed_teamlogos[2 * j + i])
                i += 1

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

        if self.videos_infos["video_id"]:
            self.update_videos()

    def display_championnat(self):
        if self.displayed_championnat:
            self.MatchCanvas.create_image(770, 120, image=self.displayed_championnat, tag="champ")

    def reload_match_score(self):
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
        self.after_blocked["timer"] = True
        for j in range(self.nb_matches):
            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            minute_text = soup.find(class_="status").text
            if minute_text.split(" ")[0] == "Coup":
                self.MatchCanvas.itemconfigure("timer" + str(j), text="Coup\nd'envoi",
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
                self.MatchCanvas.itemconfigure("timer" + str(j), text=minute_text.strip(" "),
                                               font=["Ubuntu", 20 + 5 * (self.nb_matches <= 2)
                                                     + 10 * (self.nb_matches == 1)])

        print("Timer mis à jour")
        self.afters["timer"] = self.after(60000, self.reload_match_timer)
        self.after_blocked["timer"] = False

    def load_channel_stats(self):
        self.MatchCanvas.create_text(1416, 45, font=["Ubuntu", 20], tag="Subs")
        self.reload_channel_stats()

    def reload_channel_stats(self):
        channel_list_response = self.youtube.channels().list(mine=True, part='statistics').execute()
        full_text = channel_list_response["items"][0]["statistics"]["subscriberCount"]
        self.MatchCanvas.itemconfigure("Subs", text=full_text)
        self.after(65000, self.reload_channel_stats)

    def load_video_stats(self, video_link=""):
        if video_link[:32] == "https://www.youtube.com/watch?v=":
            video_id = video_link.split("?v=")[1].split("&ab")[0]
        else:
            video_id = video_link.split(".be/")[1]
        infos = self.youtube.videos().list(id=video_id, part="snippet").execute()
        if infos['pageInfo']['totalResults'] != 0 and infos['snippet']['liveBroadcastContent'] == 'live':
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
        stats = self.youtube.videos().list(id=self.videos_infos["video_id"], part="statistics").execute()
        video = stats["items"][0]["statistics"]
        self.MatchCanvas.itemconfigure("Views", text=str(video["viewCount"]))
        self.MatchCanvas.itemconfigure("Likes", text=str(int(video["likeCount"]) + 1))

        self.after(60000, self.reload_video_stats)
        print("Stats mises à jour")

    def move(self, tag, direction: tuple):
        if direction[0] * direction[1] == 0:
            self.MatchCanvas.move(tag, 10 * direction[0], 10 * direction[1])
        else:
            current = self.MatchCanvas.itemcget(tag, "font").split(" ")
            self.MatchCanvas.itemconfigure(tag, font=[current[0], int(current[1]) + direction[0]])

    def play_gif(self, i=1):
        self.after_blocked["gif"] = True
        for j in range(self.nb_matches):
            timer_text = self.MatchCanvas.itemcget("timer" + str(j), "text")
            if timer_text[-1] == "'":
                self.MatchCanvas.itemconfigure("gif" + str(j), image=self.gif[i])
            elif timer_text == "Match terminé":
                self.MatchCanvas.delete("gif" + str(j))

        if not self.stop_gif:
            i += 1
            i %= 55
            self.afters["gif"] = self.after(2000 // 55, self.play_gif, i)
        else:
            self.afters["gif"] = None
        self.after_blocked["gif"] = False

    def playback(self, filename):
        mixer.init()
        mixer.music.load(filename)
        mixer.music.play(10)

    def destroy(self):
        if mixer.get_init():
            mixer.music.stop()
            mixer.quit()
        self.master.erase()
        Toplevel.destroy(self)

    def authenticate(self):
        with open("ressources/credentials", 'rb') as f:
            credentials = load(f)
        return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


class SetupFrame(Frame):

    def __init__(self, master: ManagerWindow, **kwargs):
        Frame.__init__(self, master, kwargs)
        self.master = master
        self.old_number = 0
        self.url_entries = []

        self.MatchButton = Button(self, text="Lancer le suivi", command=self.launch_match, bg='#4E4E4E', fg='white')
        self.NumberRoll = Spinbox(self, from_=1, to=4, bg='#4E4E4E', fg='white')
        self.NumberButton = Button(self, text="Valider", command=self.generate_urls, width=10, bg='#4E4E4E', fg='white')
        self.Schedule = Button(self, text="Schedule", command=self.launch_schedule, width=10, bg='#4E4E4E', fg='white')

        Label(self, text="Nombre de matches: ", width=20, bg='#4E4E4E', fg='white').grid(row=0, column=0)
        self.NumberRoll.grid(row=0, column=1, padx=10, pady=10)
        self.NumberButton.grid(row=0, column=2, padx=10, pady=10)
        self.Schedule.grid(row=0, column=3, padx=10, pady=10)

        self.generate_urls()

    def generate_urls(self, _event=None):

        number = int(self.NumberRoll.get())
        if self.old_number != number:
            self.MatchButton.grid_forget()
            if number > self.old_number:
                for i in range(number - self.old_number):
                    self.url_entries.append(Entry(self, width=70, bg='#6b6b6b', fg='white'))
                    self.url_entries[self.old_number + i].grid(row=self.old_number + 1 + i, column=1, padx=10, pady=10)
            else:
                for i in range(self.old_number - number):
                    self.url_entries[number + i].destroy()
                self.url_entries = self.url_entries[:number]

            self.old_number = number

            self.MatchButton.grid(row=self.old_number + 1, column=1)

    def launch_match(self, _event=None):

        if self.old_number:
            url_list = []
            for i in self.url_entries:
                if i.get() and i.get()[:40] == "https://www.matchendirect.fr/live-score/" and \
                        i.get()[-5:] == ".html":
                    if bs4.BeautifulSoup(requests.get(i.get()).text, "html.parser").find("title").text != "Erreur 404":
                        url_list.append(i.get())
                    else:
                        showerror("Erreur 404", f"Le match que vous cherchez, {i.get()}, " +
                                  "n'existe pas sur matchendirect.")
                        return
                else:
                    showerror("Mauvaises urls", "Vérifiez la validité des urls entrées.")
                    return
            self.master.launch_match(nb_matches=self.old_number, url_list=url_list)

    def launch_schedule(self):
        self.master.load_from_csv()


class EditFrame(Frame):

    def __init__(self, master: ManagerWindow, **kwargs):
        Frame.__init__(self, master, kwargs)
        self.nb_matches = 0
        self.master = master
        self.musicfile = ""

        self.VideoEntry = Entry(self, width=70, bg='#6b6b6b', fg='white')
        self.VideoButton = Button(self, text="Charger", command=self.load_video, width=10, bg='#4E4E4E',
                                  fg='white')

        self.MusicButton = Button(self, text="Choix Musique", command=self.select_playback, bg='#4E4E4E', fg='white')
        self.MusicPlay = Button(self, text="Jouer Musique", command=self.launch_playback, bg='#4E4E4E', fg='white')

        self.SubFrame = Frame(self, bg='#4E4E4E')

        Label(self, text="Url du stream: ", width=20, bg='#4E4E4E', fg='white').grid(row=0, column=0)
        self.VideoEntry.grid(row=0, column=1, padx=10, pady=10)
        self.VideoButton.grid(row=0, column=2, padx=10, pady=10)
        self.MusicButton.grid(row=1, column=0, padx=10, pady=10)
        self.MusicPlay.grid(row=1, column=1, padx=10, pady=10)
        self.SubFrame.grid(row=2, column=0, columnspan=3)

    def load_video(self):

        if self.master.is_stream_on():
            if self.VideoEntry.get() and (self.VideoEntry.get()[:32] == "https://www.youtube.com/watch?v=" or
                                          self.VideoEntry.get()[:21] == "https://www.youtu.be/"):
                self.master.load_video(self.VideoEntry.get())
            else:
                showerror("Mauvaise URL de vidéo.", f"L'url renseignée \"{self.VideoEntry.get()}\" " +
                          "n'est pas un lien youtube valable.")

    def move(self, tag, direction):

        self.master.move(tag, direction)

    def select_playback(self):
        self.musicfile = askopenfilename(initialdir="./ressources/", filetypes=[("Tout audio", (".mp3", ".ogg",
                                                                                                ".wav")),
                                                                                ("Fichier compressé", ".mp3"),
                                                                                ('Audio non compressé', ".wav")])

    def launch_playback(self):
        if self.master.is_stream_on():
            if self.musicfile:
                self.master.launch_playback(self.musicfile)

    def load_edit(self, val):
        self.nb_matches = val

        for i in self.SubFrame.grid_slaves():
            i.destroy()

        Separator(self.SubFrame, orient="horizontal").grid(row=0, column=0, columnspan=20,
                                                           sticky="we", pady=4)

        for i in range(self.nb_matches):
            Label(self.SubFrame, text="Match " + str(i + 1),
                  bg='#4E4E4E', fg='white').grid(row=3 * i + 1, column=1, rowspan=2, padx=10, pady=10)
            Separator(self.SubFrame, orient="vertical").grid(row=3 * i + 1, column=2, rowspan=2,
                                                             sticky="ns", padx=10, pady=4)
            Label(self.SubFrame, text="Timer :",
                  bg='#4E4E4E', fg='white').grid(row=3 * i + 1, column=3, rowspan=2, padx=10, pady=10)
            Button(self.SubFrame, text="\U000025C0", fg='white',
                   command=partial(self.move, "timer" + str(i), (-1, 0)),
                   bg='#4E4E4E').grid(row=3 * i + 1, column=4, rowspan=2, padx=5, pady=10, sticky='e')
            Button(self.SubFrame, text="\U000025B6", fg='white',
                   command=partial(self.move, "timer" + str(i), (1, 0)),
                   bg='#4E4E4E').grid(row=3 * i + 1, column=6, rowspan=2, padx=5, pady=10, sticky='w')
            Button(self.SubFrame, text="\U000025B2", fg='white',
                   command=partial(self.move, "timer" + str(i), (0, -1)),
                   bg='#4E4E4E').grid(row=3 * i + 1, column=5, padx=5, pady=10)
            Button(self.SubFrame, text="\U000025BC", fg='white',
                   command=partial(self.move, "timer" + str(i), (0, 1)),
                   bg='#4E4E4E').grid(row=3 * i + 2, column=5, padx=5, pady=10)
            Button(self.SubFrame, text="\U000025B2", fg='white',
                   command=partial(self.move, "timer" + str(i), (1, 1)),
                   bg='#4E4E4E').grid(row=3 * i + 1, column=7, padx=10, pady=10)
            Button(self.SubFrame, text="\U000025BC", fg='white',
                   command=partial(self.move, "timer" + str(i), (-1, -1)),
                   bg='#4E4E4E').grid(row=3 * i + 2, column=7, padx=10, pady=10)
            Separator(self.SubFrame, orient="horizontal").grid(row=3 * i + 3, column=0, columnspan=20,
                                                               sticky="we", pady=4)

            for j in range(2):
                Separator(self.SubFrame, orient="vertical").grid(row=3 * i + 1, column=6 * (j + 1) + 2, rowspan=2,
                                                                 sticky="ns", padx=10, pady=4)
                Label(self.SubFrame, text="Equipe " + str(j + 1) + " :",
                      bg='#4E4E4E', fg='white').grid(row=3 * i + 1, column=6 * (j + 1) + 3, rowspan=2, padx=10, pady=10)
                Button(self.SubFrame, text="\U000025C0", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (-1, 0)),
                       bg='#4E4E4E').grid(row=3 * i + 1, column=6 * (j + 1) + 4, rowspan=2, padx=5, pady=10)
                Button(self.SubFrame, text="\U000025B6", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (1, 0)),
                       bg='#4E4E4E').grid(row=3 * i + 1, column=6 * (j + 2), rowspan=2, padx=5, pady=10)
                Button(self.SubFrame, text="\U000025B2", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (0, -1)),
                       bg='#4E4E4E').grid(row=3 * i + 1, column=6 * (j + 1) + 5, padx=5, pady=10)
                Button(self.SubFrame, text="\U000025BC", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (0, 1)),
                       bg='#4E4E4E').grid(row=3 * i + 2, column=6 * (j + 1) + 5, padx=5, pady=10)
                Button(self.SubFrame, text="\U000025B2", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (1, 1)),
                       bg='#4E4E4E').grid(row=3 * i + 1, column=6 * (j + 2) + 1, padx=10, pady=10)
                Button(self.SubFrame, text="\U000025BC", fg='white',
                       command=partial(self.move, "TeamName" + str(2 * i + j), (-1, -1)),
                       bg='#4E4E4E').grid(row=3 * i + 2, column=6 * (j + 2) + 1, padx=10, pady=10)
