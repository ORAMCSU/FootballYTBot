from tkinter import *
import PIL.ImageTk
import PIL.Image
import requests
import bs4
import json
from functools import partial

from pafy import new


class ManagerWindow(Tk):

    def __init__(self):

        Tk.__init__(self)
        self.title("Stream Manager")

        self.MainFrame = SetupFrame(self, width=900, height=700, bg='#4E4E4E')
        self.StreamFrame = EditFrame(self, width=900, height=200, bg='#4E4E4E')

        self.MainFrame.grid(row=0, column=0)
        self.StreamFrame.grid(row=1, column=0)

        self.MatchWindow = None

    def launch_match(self, nb_matches, url_list):

        self.MatchWindow = MatchWindow(master=self, nb_matches=nb_matches, url_list=url_list)

        self.StreamFrame.load_edit(nb_matches)

    def move(self, tag, direction):

        self.MatchWindow.move(tag, direction)

    def load_video(self, video_url):
        self.MatchWindow.load_video_stats(video_url)

    def is_stream_on(self):
        return not(self.MatchWindow is None)


class MatchWindow(Toplevel):

    def __init__(self, master=None, nb_matches=1, url_list=None, video_url=None):

        Toplevel.__init__(self, master)
        self.title("Match Stream")
        self.match_urls = url_list
        self.nb_matches = nb_matches

        self.video_url = video_url
        self.MatchCanvas = Canvas(self, width=1536, height=864)
        self.MatchCanvas.grid(row=0, column=0)

        self.displayed_bg = None
        self.displayed_logo = None
        self.displayed_black = None
        self.displayed_icons = []
        self.displayed_teamlogos = []

        self.load_bases()
        self.load_channel_stats()
        self.load_match_stats()

    def load_bases(self):

        pil_image = PIL.Image.open("ressources/images/fond_direct.jpg")
        pil_image2 = pil_image.resize((1536, 864))
        pil_image.close()
        self.displayed_bg = PIL.ImageTk.PhotoImage(pil_image2)

        self.MatchCanvas.create_image(770, 434, image=self.displayed_bg, tag="Background")

        pil_image2.close()
        pil_image = PIL.Image.open("ressources/images/logo.png")
        pil_image2 = pil_image.resize((100, 100))
        pil_image.close()
        self.displayed_logo = PIL.ImageTk.PhotoImage(pil_image2)

        self.MatchCanvas.create_image(70, 70, image=self.displayed_logo, tag="Logo")

        pil_image2.close()
        pil_image = PIL.Image.open("ressources/images/affiche_vierge.png")

        if self.nb_matches == 1:
            pil_image2 = pil_image.resize((1150, 234))
        elif self.nb_matches == 2:
            pil_image2 = pil_image.resize((875, 195))
        elif self.nb_matches == 3 or self.nb_matches == 4:
            pil_image2 = pil_image.resize((700, 156))
        pil_image.close()
        if pil_image2:
            self.displayed_black = PIL.ImageTk.PhotoImage(pil_image2)

        for i in range(self.nb_matches):
            if self.nb_matches == 1:
                self.MatchCanvas.create_image(770, 500, image=self.displayed_black, tag="Black"+str(i))

            elif self.nb_matches == 2:
                self.MatchCanvas.create_image(770, 250*i+350, image=self.displayed_black, tag="Black" + str(i))

            elif self.nb_matches == 3:
                self.MatchCanvas.create_image(770-375*(i == 1)+375*(i == 2), 215*(i > 0)+350,
                                              image=self.displayed_black, tag="Black" + str(i))
            elif self.nb_matches == 4:
                self.MatchCanvas.create_image(770-375*(i % 2 == 1)+375*(i % 2 == 0), 215*(i > 1)+350,
                                              image=self.displayed_black, tag="Black" + str(i))

        iconlist = ["ressources/images/youtube.png", "ressources/images/views.png", "ressources/images/likes.png"]
        for i in range(3):
            self.MatchCanvas.create_rectangle(1306, 20+70*i, 1486, 70+70*i, fill="white", outline="white")
            pil_image2.close()
            pil_image = PIL.Image.open(iconlist[i])
            pil_image2 = pil_image.resize((int((pil_image.size[0]/pil_image.size[1])*40), 40))
            pil_image.close()

            self.displayed_icons.append(PIL.ImageTk.PhotoImage(pil_image2))
            self.MatchCanvas.create_image(1341, 45 + 70 * i, image=self.displayed_icons[i], tag="Icon" + str(i))

        pil_image2.close()

    def load_match_stats(self):

        for j in range(self.nb_matches):
            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")

            if self.nb_matches == 1:
                i = 0
                for div in soup.find_all("div", class_="col-xs-4 text-center team"):
                    self.MatchCanvas.create_text(195*(1-i) + (1-2*i)*300 + 1347*i, 500,
                                                 text=div.text[1:-1].replace(" ", "\n"), font=["Ubuntu", 30],
                                                 fill="white", justify="center", tag="TeamName"+str(i))
                    i += 1
                i = 0
                for score in soup.find_all(class_="score"):
                    self.MatchCanvas.create_text(195 * (1 - i) + (1 - 2 * i) * 493 + 1347 * i, 535,
                                                 text=score.text, font=["Ubuntu", 40],
                                                 fill="white", justify="center", tag="score"+str(i))
                    i += 1

                i = 0
                for div in soup.find_all("div", class_="col-xs-4 text-center"):
                    full_url = "https://www.matchendirect.fr" + div.find("img")["src"].replace("96", "128")
                    pil_image = PIL.Image.open(requests.get(full_url, stream=True).raw)
                    self.displayed_teamlogos.append(PIL.ImageTk.PhotoImage(pil_image))
                    self.MatchCanvas.create_image(195 * (1 - i) + (1 - 2 * i) * 100 + 1347 * i, 500,
                                                  image=self.displayed_teamlogos[i], tag="Teamlogo" + str(i))
                    i += 1

                minute_text = soup.find(class_="status").text
                if minute_text == " Mi-temps":
                    self.MatchCanvas.create_text(767, 448, text=minute_text.strip(" ").replace("-", "-\n"),
                                                 font=["Ubuntu", 12], justify="center", tag="timer"+str(j))
                elif minute_text == "Match terminé":
                    self.MatchCanvas.create_text(767, 448, text=minute_text.replace(" ", "\n"), font=["Ubuntu", 12],
                                                 justify="center", tag="timer" + str(j))
                else:
                    self.MatchCanvas.create_text(767, 448, text=minute_text.strip(' '), font=["Ubuntu", 35],
                                                 justify="center", tag="timer" + str(j))

            elif self.nb_matches == 2:
                i = 0
                for div in soup.find_all("div", class_="col-xs-4 text-center team"):
                    self.MatchCanvas.create_text(333 * (1 - i) + (1 - 2 * i) * 220 + 1217 * i, 250*j+350,
                                                 text=div.text[1:-1].replace(" ", "\n"), font=["Ubuntu", 22],
                                                 fill="white", justify="center", tag="TeamName" + str(2*j+i))
                    i += 1
                i = 0
                for score in soup.find_all(class_="score"):
                    self.MatchCanvas.create_text(325 * (1 - i) + (1 - 2 * i) * 383 + 1217 * i, 250*j+380,
                                                 text=score.text, font=["Ubuntu", 40],
                                                 fill="white", justify="center", tag="score" + str(2*j+i))
                    i += 1

                i = 0
                for div in soup.find_all("div", class_="col-xs-4 text-center"):
                    full_url = "https://www.matchendirect.fr" + div.find("img")["src"].replace("96", "128")
                    pil_image = PIL.Image.open(requests.get(full_url, stream=True).raw)
                    self.displayed_teamlogos.append(PIL.ImageTk.PhotoImage(pil_image))
                    self.MatchCanvas.create_image(333 * (1 - i) + (1 - 2 * i) * 80 + 1217 * i, 250*j+350,
                                                  image=self.displayed_teamlogos[2*j+i], tag="Teamlogo" + str(2*j+i))
                    i += 1

                minute_text = soup.find(class_="status").text

                if minute_text == " Mi-temps":
                    self.MatchCanvas.create_text(767, 307+250*j, text=minute_text.strip(" ").replace("-", "-\n"),
                                                 font=["Ubuntu", 10], justify="center", tag="timer" + str(j))
                elif minute_text == "Match terminé":
                    self.MatchCanvas.create_text(767, 307 + 250 * j, text=minute_text.replace(" ", "\n"),
                                                 font=["Ubuntu", 10], justify="center", tag="timer" + str(j))
                else:
                    self.MatchCanvas.create_text(767, 307 + 250 * j, text=minute_text.strip(' '), font=["Ubuntu", 25],
                                                 justify="center", tag="timer" + str(j))

            elif self.nb_matches == 3:
                i = 0
                for div in soup.find_all("div", class_="col-xs-4 text-center team"):
                    self.MatchCanvas.create_text((420-375*(j == 1)+375*(j == 2)) * (1 - i) + (1 - 2 * i) * 190 +
                                                 (1120-375*(j == 1)+375*(j == 2)) * i, 215*(j >= 1)+350,
                                                 text=div.text[1:-1].replace(" ", "\n"), font=["Ubuntu", 20],
                                                 fill="white", justify="center", tag="TeamName" + str(2*j+i))
                    i += 1
                i = 0
                for score in soup.find_all(class_="score"):
                    self.MatchCanvas.create_text((420-375*(j == 1)+375*(j == 2)) * (1 - i) + (1 - 2 * i) * 300 +
                                                 (1122-375*(j == 1)+375*(j == 2)) * i, 215*(j >= 1)+372,
                                                 text=score.text, font=["Ubuntu", 35],
                                                 fill="white", justify="center", tag="score" + str(2*j+i))
                    i += 1

                i = 0
                for div in soup.find_all("div", class_="col-xs-4 text-center"):
                    full_url = "https://www.matchendirect.fr" + div.find("img")["src"].replace("96", "128")
                    pil_image = PIL.Image.open(requests.get(full_url, stream=True).raw)
                    self.displayed_teamlogos.append(PIL.ImageTk.PhotoImage(pil_image))
                    self.MatchCanvas.create_image((420-375*(j == 1)+375*(j == 2)) * (1 - i) + (1 - 2 * i) * 70 +
                                                  (1120-375*(j == 1)+375*(j == 2)) * i, 215*(j >= 1)+350,
                                                  image=self.displayed_teamlogos[2*j+i], tag="Teamlogo" + str(2*j+i))
                    i += 1

                minute_text = soup.find(class_="status").text
                if minute_text == " Mi-temps":
                    self.MatchCanvas.create_text(770-375*(j == 1)+375*(j == 2), 313+215*(j >= 1),
                                                 text=minute_text.strip(" ").replace("-", "-\n"),
                                                 font=["Ubuntu", 7], justify="center", tag="timer" + str(j))
                elif minute_text == "Match terminé":
                    self.MatchCanvas.create_text(770 - 375 * (j == 1) + 375 * (j == 2), 313 + 215 * (j >= 1),
                                                 text=minute_text.replace(" ", "\n"),
                                                 font=["Ubuntu", 7], justify="center", tag="timer" + str(j))
                else:
                    self.MatchCanvas.create_text(773 - 375 * (j == 1) + 375 * (j == 2), 313 + 215 * (j >= 1),
                                                 text=minute_text.strip(' '),
                                                 font=["Ubuntu", 20], justify="center", tag="timer" + str(j))

            elif self.nb_matches == 4:
                i = 0
                for div in soup.find_all("div", class_="col-xs-4 text-center team"):
                    self.MatchCanvas.create_text((420-375*(j % 2 == 0)+375*(j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                                                 190 + (1120-375*(j % 2 == 0)+375*(j % 2 == 1)) * i, 215*(j >= 2)+350,
                                                 text=div.text[1:-1].replace(" ", "\n"), font=["Ubuntu", 20],
                                                 fill="white", justify="center", tag="TeamName" + str(2*j+i))
                    i += 1
                i = 0
                for score in soup.find_all(class_="score"):
                    self.MatchCanvas.create_text((420-375*(j % 2 == 0)+375*(j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                                                 300 + (1122-375*(j % 2 == 0)+375*(j % 2 == 1)) * i, 215*(j >= 2)+372,
                                                 text=score.text, font=["Ubuntu", 35],
                                                 fill="white", justify="center", tag="score" + str(2*j+i))
                    i += 1

                i = 0
                for div in soup.find_all("div", class_="col-xs-4 text-center"):
                    full_url = "https://www.matchendirect.fr" + div.find("img")["src"].replace("96", "128")
                    pil_image = PIL.Image.open(requests.get(full_url, stream=True).raw)
                    self.displayed_teamlogos.append(PIL.ImageTk.PhotoImage(pil_image))
                    self.MatchCanvas.create_image((420-375*(j % 2 == 0)+375*(j % 2 == 1)) * (1 - i) + (1 - 2 * i) *
                                                  70 + (1120-375*(j % 2 == 0)+375*(j % 2 == 1)) * i, 215*(j >= 2)+350,
                                                  image=self.displayed_teamlogos[2*j+i], tag="Teamlogo" + str(2*j+i))
                    i += 1

                minute_text = soup.find(class_="status").text
                if minute_text == " Mi-temps":
                    self.MatchCanvas.create_text(767-375*(j % 2 == 0)+375*(j % 2 == 1), 313+215*(j >= 2),
                                                 text=minute_text.strip(" ").replace("-", "-\n"), font=["Ubuntu", 7],
                                                 justify="center", tag="timer" + str(j))
                elif minute_text == "Match terminé":
                    self.MatchCanvas.create_text(767 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1), 313 + 215 * (j >= 2),
                                                 text=minute_text.replace(" ", "\n"), font=["Ubuntu", 7],
                                                 justify="center", tag="timer" + str(j))
                else:
                    self.MatchCanvas.create_text(767 - 375 * (j % 2 == 0) + 375 * (j % 2 == 1), 313 + 215 * (j >= 2),
                                                 text=minute_text.strip(' '), font=["Ubuntu", 20],
                                                 justify="center", tag="timer" + str(j))

        self.after(10000, self.reload_match_score)
        self.after(60000, self.reload_match_timer)

    def reload_match_score(self):
        for j in range(self.nb_matches):
            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            i = 0
            for score in soup.find_all(class_="score"):
                self.MatchCanvas.itemconfigure("score"+str(2*j+i), text=score.text)
                i += 1
        print("Scores mis à jour")
        self.after(10000, self.reload_match_score)

    def reload_match_timer(self):
        for j in range(self.nb_matches):
            match_page = requests.get(self.match_urls[j])
            soup = bs4.BeautifulSoup(match_page.text, "html.parser")
            minute_text = soup.find(class_="status").text
            if minute_text == " Mi-temps":
                self.MatchCanvas.itemconfigure("timer"+str(j), text=minute_text.strip(" ").replace("-", "-\n"),
                                               font=["Ubuntu", 7 + 3*(self.nb_matches <= 2) + 2*(self.nb_matches == 1)])
            elif minute_text == "Match terminé":
                self.MatchCanvas.itemconfigure("timer" + str(j), text=minute_text.replace(" ", "\n"),
                                               font=["Ubuntu", 7 + 3*(self.nb_matches <= 2) + 2*(self.nb_matches == 1)])
            else:
                self.MatchCanvas.itemconfigure("timer" + str(j), text=minute_text.strip(" "), font=["Ubuntu", 20 +
                                               5*(self.nb_matches <= 2) + 10*(self.nb_matches == 1)])

        print("Timer mis à jour")
        self.after(58000, self.reload_match_timer)

    def load_channel_stats(self, _video_link=""):
        channel_page = requests.get("https://www.youtube.com/channel/UCvahkUIQv3F1eYh7BV0CmbQ")
        soup = bs4.BeautifulSoup(channel_page.text, "html.parser")
        script = str(soup.find_all("script")[-7])
        index = script.find("ytInitialData = ")
        script = script[index+len("ytInitialData = "):-10]
        full_text = json.loads(script)["header"]["c4TabbedHeaderRenderer"]["subscriberCountText"]["simpleText"]
        self.MatchCanvas.create_text(1416, 45, text=full_text.replace(" ", "\xa0").split("\xa0")[0],
                                     font=["Ubuntu", 20], tag="Subs")

    def load_video_stats(self, video_link=""):
        video = new(video_link)

        self.MatchCanvas.create_text(1416, 115, text=str(video.viewcount),
                                     font=["Ubuntu", 20], tag="Views")
        self.MatchCanvas.create_text(1416, 185, text=str(video.likes),
                                     font=["Ubuntu", 20], tag="Likes")

        self.after(60000, self.reload_video_stats, video_link)

    def reload_video_stats(self, video_link="", iteration=0):
        video = new(video_link)
        self.MatchCanvas.itemconfigure("Views", text=str(video.viewcount))
        self.MatchCanvas.itemconfigure("Likes", text=str(video.likes))

        if iteration == 6:
            channel_page = requests.get("https://www.youtube.com/channel/UCvahkUIQv3F1eYh7BV0CmbQ")
            soup = bs4.BeautifulSoup(channel_page.text, "html.parser")
            script = str(soup.find_all("script")[-7])
            index = script.find("ytInitialData = ")
            script = script[index + len("ytInitialData = "):-10]
            full_text = json.loads(script)["header"]["c4TabbedHeaderRenderer"]["subscriberCountText"]["simpleText"]
            self.MatchCanvas.itemconfigure("Subs", text=full_text.replace(" ", "\xa0").split("\xa0")[0])

        self.after(60000, self.reload_video_stats, video_link, iteration + 1)
        print("Stats mises à jour")

    def move(self, tag, direction: tuple):
        if direction[0]*direction[1] == 0:
            self.MatchCanvas.move(tag, 10*direction[0], 10*direction[1])
        else:
            current = self.MatchCanvas.itemcget(tag, "font").split(" ")
            self.MatchCanvas.itemconfigure(tag, font=[current[0], int(current[1])+direction[0]])


class SetupFrame(Frame):

    def __init__(self, master: ManagerWindow, **kwargs):
        Frame.__init__(self, master, kwargs)
        self.old_number = 0
        self.url_entries = []

        self.MatchButton = Button(self, text="Lancer le suivi", command=self.launch_match, bg='#4E4E4E',
                                  fg='white')
        self.NumberRoll = Spinbox(self, from_=1, to=4, bg='#4E4E4E', fg='white')
        self.NumberButton = Button(self, text="Valider", command=self.generate_urls, width=10, bg='#4E4E4E',
                                   fg='white')

        Label(self, text="Nombre de matches: ", width=20, bg='#4E4E4E', fg='white').grid(row=0, column=0)
        self.NumberRoll.grid(row=0, column=1, padx=10, pady=10)
        self.NumberButton.grid(row=0, column=2, padx=10, pady=10)

        self.generate_urls()

    def generate_urls(self, _event=None):

        number = int(self.NumberRoll.get())
        if self.old_number != number:
            self.MatchButton.grid_forget()
            if number > self.old_number:
                for i in range(number-self.old_number):
                    self.url_entries.append(Entry(self, width=70, bg='#6b6b6b', fg='white'))
                    self.url_entries[self.old_number+i].grid(row=self.old_number+1+i, column=1, padx=10, pady=10)
            else:
                for i in range(self.old_number-number):
                    self.url_entries[number+i].destroy()
                self.url_entries = self.url_entries[:number]

            self.old_number = number

            self.MatchButton.grid(row=self.old_number+1, column=1)

    def launch_match(self, _event=None):

        self.master.launch_match(nb_matches=int(self.NumberRoll.get()), url_list=[i.get() for
                                 i in self.url_entries])


class EditFrame(Frame):

    def __init__(self, master, **kwargs):
        Frame.__init__(self, master, kwargs)
        self.nb_matches = 0

        self.VideoEntry = Entry(self, width=70, bg='#6b6b6b', fg='white')
        self.VideoButton = Button(self, text="Charger", command=self.load_video, width=10, bg='#4E4E4E',
                                  fg='white')

        self.SubFrame = Frame(self)

        Label(self, text="Url du stream: ", width=20, bg='#4E4E4E', fg='white').grid(row=0, column=0)
        self.VideoEntry.grid(row=0, column=1, padx=10, pady=10)
        self.VideoButton.grid(row=0, column=2, padx=10, pady=10)
        self.SubFrame.grid(row=1, column=0, columnspan=3)

    def load_video(self):

        if self.master.is_stream_on():
            if self.VideoEntry.get():
                self.master.load_video(self.VideoEntry.get())

    def move(self, tag, direction):

        self.master.move(tag, direction)

    def load_edit(self, val):
        self.nb_matches = val

        for i in self.SubFrame.grid_slaves():
            i.destroy()

        for i in range(self.nb_matches):
            Label(self.SubFrame, text="Match " + str(i + 1) + " - Timer :").grid(row=2 * i, column=0, rowspan=2)
            Button(self.SubFrame, text="\U000025C4",
                   command=partial(self.move, "timer"+str(i), (-1, 0))).grid(row=2*i, column=1, rowspan=2)
            Button(self.SubFrame, text="\U000025BA",
                   command=partial(self.move, "timer"+str(i), (1, 0))).grid(row=2*i, column=3, rowspan=2)
            Button(self.SubFrame, text="\U000025B2",
                   command=partial(self.move, "timer"+str(i), (0, -1))).grid(row=2*i, column=2)
            Button(self.SubFrame, text="\U000025BC",
                   command=partial(self.move, "timer"+str(i), (0, 1))).grid(row=2*i+1, column=2)
            Button(self.SubFrame, text="\U000025B2",
                   command=partial(self.move, "timer" + str(i), (1, 1))).grid(row=2*i, column=4)
            Button(self.SubFrame, text="\U000025BC",
                   command=partial(self.move, "timer" + str(i), (-1, -1))).grid(row=2*i+1, column=4)

            for j in range(2):
                Label(self.SubFrame, text="Equipe "+str(j+1)+" :").grid(row=2*i, column=5*(j+1), rowspan=2)
                Button(self.SubFrame, text="\U000025C4",
                       command=partial(self.move, "TeamName" + str(2*i+j),
                                           (-1, 0))).grid(row=2*i, column=5*(j+1)+1, rowspan=2)
                Button(self.SubFrame, text="\U000025BA",
                       command=partial(self.move, "TeamName" + str(2*i+j),
                                           (1, 0))).grid(row=2*i, column=5*(j+1)+3, rowspan=2)
                Button(self.SubFrame, text="\U000025B2",
                       command=partial(self.move, "TeamName" + str(2*i+j),
                                           (0, -1))).grid(row=2*i, column=5*(j+1)+2)
                Button(self.SubFrame, text="\U000025BC",
                       command=partial(self.move, "TeamName" + str(2*i+j),
                                           (0, 1))).grid(row=2*i+1, column=5*(j+1)+2)
                Button(self.SubFrame, text="\U000025B2",
                       command=partial(self.move, "TeamName" + str(2*i+j), (1, 1))).grid(row=2*i, column=5*(j+1)+4)
                Button(self.SubFrame, text="\U000025BC",
                       command=partial(self.move, "TeamName" + str(2*i+j),
                                           (-1, -1))).grid(row=2*i+1, column=5*(j+1)+4)
