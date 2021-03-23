from tkinter import Label, Button, Frame, Spinbox, Entry
import bs4
import requests
from UI import ManagerWindow
from tkinter.messagebox import showerror


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
