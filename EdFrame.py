from tkinter import Entry, Button, Frame, Label
from tkinter.ttk import Separator
from tkinter.filedialog import askopenfilename
from functools import partial
from UI import ManagerWindow
from tkinter.messagebox import showerror


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
