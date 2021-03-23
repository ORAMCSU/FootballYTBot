from tkinter import *
from tkinter.messagebox import showerror
import requests
import bs4
from time import localtime, strptime, mktime, time
from MatchWin import MatchWindow
from SetFrame import SetupFrame
from EdFrame import EditFrame


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
