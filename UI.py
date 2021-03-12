from tkinter import *
import PIL.ImageTk
import PIL.Image


class ManagerWindow(Tk):

    def __init__(self):

        Tk.__init__(self)
        self.title("Stream Manager")
        self.old_number = 0
        self.url_entries = []

        self.MainFrame = Frame(self, width=500, height=500)
        self.MatchButton = Button(self.MainFrame, text="Lancer le suivi", command=self.launch_match)
        self.NumberRoll = Spinbox(self.MainFrame, from_=1, to=4)
        self.NumberButton = Button(self.MainFrame, text="Valider", command=self.generate_urls)

        self.MainFrame.grid(row=0, column=0)
        Label(self.MainFrame, text="Nombre de matches").grid(row=0, column=0)
        self.NumberRoll.grid(row=0, column=1)
        self.NumberButton.grid(row=0, column=2)

        self.MatchWindow = None

        self.generate_urls()

    def launch_match(self, _event=None):

        self.MatchWindow = MatchWindow(master=self, nb_matches=int(self.NumberRoll.get()), url_list=[i.get() for
                                       i in self.url_entries])

    def generate_urls(self, _event=None):

        number = int(self.NumberRoll.get())
        if self.old_number != number:
            self.MatchButton.grid_forget()
            if number > self.old_number:
                for i in range(number-self.old_number):
                    self.url_entries.append(Entry(self.MainFrame))
                    self.url_entries[self.old_number+i].grid(row=self.old_number+1+i, column=1)
            else:
                for i in range(self.old_number-number):
                    self.url_entries[number+i].destroy()
                self.url_entries = self.url_entries[:number]

            self.old_number = number

            self.MatchButton.grid(row=self.old_number+1, column=1)


class MatchWindow(Toplevel):

    def __init__(self, master=None, nb_matches=1, url_list=None, video_url=None):

        Toplevel.__init__(self, master)
        self.title("Match Stream")
        self.match_urls = url_list
        print(self.match_urls)

        self.video_url = video_url
        self.MatchCanvas = Canvas(self, width=1536, height=864)
        self.MatchCanvas.grid(row=0, column=0)

        self.displayed_bg = None
        self.displayed_logo = None
        self.displayed_black = None
        self.displayed_icons = []

        self.load_bases(nb_matches)

    def load_bases(self, nb_matches=1):

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
        if nb_matches == 1:
            pil_image2 = pil_image.resize((1150, 234))
        elif nb_matches == 2:
            pil_image2 = pil_image.resize((875, 195))
        elif nb_matches == 3 or nb_matches == 4:
            pil_image2 = pil_image.resize((700, 156))
        pil_image.close()
        if pil_image2:
            self.displayed_black = PIL.ImageTk.PhotoImage(pil_image2)

        for i in range(nb_matches):
            if nb_matches == 1:
                self.MatchCanvas.create_image(770, 500, image=self.displayed_black, tag="Black"+str(i))

            elif nb_matches == 2:
                self.MatchCanvas.create_image(770, 250*i+350, image=self.displayed_black, tag="Black" + str(i))

            elif nb_matches == 3:
                self.MatchCanvas.create_image(770-375*(i == 1)+375*(i == 2), 215*(i > 0)+350,
                                              image=self.displayed_black, tag="Black" + str(i))
            elif nb_matches == 4:
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
        pass
