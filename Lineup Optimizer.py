import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
from pulp import LpProblem, LpMaximize, LpVariable, LpBinary, lpSum, value
import sys
from PIL import Image
import os
import ctypes

# Pfad zur OpenBLAS-Bibliothek
openblas_path = '/Users/el_niiino90/opt/anaconda3/envs/Kickbase_Championship_optimizer/lib/libopenblasp-r0.3.21.dylib'

def set_openblas_path(path):
    """Setze den OpenBLAS-Pfad für den Solver."""
    if os.path.exists(path):
        try:
            print(f"Versuche, OpenBLAS-Bibliothek von {path} zu laden...")
            ctypes.CDLL(path)
            os.environ["OPENBLAS"] = path
            print("OpenBLAS-Pfad erfolgreich gesetzt.")
            return True
        except Exception as e:
            print("Fehler beim Setzen des OpenBLAS-Pfads:", str(e))
    else:
        print(f"Der Pfad {path} existiert nicht.")
    return False

# Aufruf der Funktion mit dem OpenBLAS-Pfad
if set_openblas_path(openblas_path):
    print("OpenBLAS-Pfad erfolgreich gesetzt.")
else:
    print("Fehler beim Setzen des OpenBLAS-Pfads.")

def resource_path(relative_path):
    """Erhalte den absoluten Pfad zu einer Ressource, funktioniert für Entwicklung und PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class OutputGUI:
    def __init__(self, lineup, spieler):
        self.root = ctk.CTk()
        self.root.configure(fg_color="#2a3c48")  # Hintergrundfarbe setzen
        self.lineup = lineup
        self.spieler = spieler

    def display_lineup(self):
        self.root.title("Optimales Lineup")
        self.root.geometry("1200x1100+571+0")

        positions = {'Torhüter': [], 'Abwehrspieler': [], 'Mittelfeldspieler': [], 'Stürmer': []}
        for Name, Position in self.lineup:
            positions[Position].append(Name)

        # Validiere das Lineup
        if not self.validate_lineup(positions):
            messagebox.showerror("Fehler", "Kein passendes Lineup verfügbar.")
            self.root.destroy()
            return

        lineup_frame = ctk.CTkFrame(self.root, fg_color="#2a3c48")
        lineup_frame.pack(fill=ctk.BOTH, padx=10, pady=5)

        lineup_text = "Optimale Lineup-Zusammenstellung:\n--------------------------------\n"
        self.create_position_frame(lineup_frame, "Torhüter", positions['Torhüter'], lineup_text)
        self.create_position_frame(lineup_frame, "Abwehrspieler", positions['Abwehrspieler'], lineup_text)
        self.create_position_frame(lineup_frame, "Mittelfeldspieler", positions['Mittelfeldspieler'], lineup_text)
        self.create_position_frame(lineup_frame, "Stürmer", positions['Stürmer'], lineup_text)

        self.display_budget_and_ratings(lineup_frame, positions)

        self.root.mainloop()

    def create_position_frame(self, parent_frame, position_name, players, lineup_text):
        frame = ctk.CTkFrame(parent_frame, fg_color="#2e3e4e", height=200)
        frame.pack(fill=ctk.BOTH, pady=3, expand=True)
        ctk.CTkLabel(frame, text=position_name, font=("Philly Sans Regular", 14, "bold"), text_color="#ffffff", fg_color="#2e3e4e").pack(anchor="center", padx=10)
        lineup_text += f"{position_name}:\n\n"

        row_frame = ctk.CTkFrame(frame, fg_color="#2e3e4e")
        row_frame.pack(anchor="center", pady=2)

        for player in players:
            player_frame = ctk.CTkFrame(row_frame, fg_color="#3a4c5e", border_color="#ffffff", border_width=2, height=150, width=200)
            player_frame.pack_propagate(False)  # Prevent the frame from resizing to fit its content
            player_frame.pack(side=ctk.LEFT, padx=10, pady=10)  # Vergrößere die Abstände

            label = ctk.CTkLabel(player_frame, text=player, justify="left", anchor="w", font=("Philly Sans Regular", 12, "bold"), text_color="#d8f448", fg_color="#3a4c5e")
            label.pack(pady=2)

            details_label = ctk.CTkLabel(player_frame, text=self.get_player_details(player), justify="left", anchor="w", font=("Philly Sans Regular", 12), text_color="#ffffff", fg_color="#3a4c5e")
            details_label.pack(anchor="w", padx=5)

            lineup_text += f"{player}\n"
            lineup_text += self.get_player_details(player)

        row_frame.pack(anchor="center")

    def display_budget_and_ratings(self, parent_frame, positions):
        budget_frame = ctk.CTkFrame(parent_frame, fg_color="#2e3e4e")
        budget_frame.pack(fill=ctk.BOTH, pady=2)

        used_budget = sum(self.spieler[player]['Marktwert'] for player, _ in self.lineup)
        total_rating = sum(self.spieler[player]['Rating'] for player, _ in self.lineup)

        budget_label = ctk.CTkLabel(budget_frame, text=f"Genutztes Budget: {self.format_number(used_budget)} Mio. €", font=("Philly Sans Regular", 12, "bold"), text_color="#d8f448", fg_color="#2e3e4e")
        budget_label.pack(anchor="center", pady=2)

        rating_label = ctk.CTkLabel(budget_frame, text=f"Gesamtrating: {self.format_number(total_rating)}", font=("Philly Sans Regular", 12, "bold"), text_color="#d8f448", fg_color="#2e3e4e")
        rating_label.pack(anchor="center", pady=2)

        position_count_text = "Formation: " + " ".join([f"{position}: {len(players)}" for position, players in positions.items()])
        position_count_label = ctk.CTkLabel(budget_frame, text=position_count_text, font=("Philly Sans Regular", 12), text_color="#ffffff", fg_color="#2e3e4e")
        position_count_label.pack(anchor="center", pady=2)

        verein_count = {}
        for player, _ in self.lineup:
            verein = self.spieler[player]['Verein']
            verein_count[verein] = verein_count.get(verein, 0) + 1

        verein_frame = ctk.CTkFrame(budget_frame, fg_color="#2e3e4e")
        verein_frame.pack(anchor="center", pady=2)

        anzahl_spieler_label = ctk.CTkLabel(verein_frame, text="Anzahl der Spieler pro Verein:", font=("Philly Sans Regular", 12, "bold"), text_color="#ffffff", fg_color="#2e3e4e")
        anzahl_spieler_label.pack(side=ctk.TOP, pady=2)

        for verein, count in verein_count.items():
            verein_label = ctk.CTkLabel(verein_frame, text=f"{verein}: {count} ", font=("Philly Sans Regular", 12), padx=5, text_color="#ffffff", fg_color="#2e3e4e")
            verein_label.pack(side=ctk.LEFT, padx=2)

    def get_player_details(self, player_name):
        details = f"Verein: {self.spieler[player_name]['Verein']}\n"
        details += f"Gegner: {self.spieler[player_name]['Gegner']}\n"
        details += f"Rating: {int(self.spieler[player_name]['Rating'])}\n"
        details += f"Punktewahrscheinlichkeit: {int(self.spieler[player_name]['Punktewahrscheinlichkeit']):,}%\n"
        details += f"Marktwert: {self.format_number(self.spieler[player_name]['Marktwert'])} Mio. €\n"
        details += f"Erwartete Spielzeit: {int(self.spieler[player_name]['Spielzeit'])} Min.\n"
        return details

    def format_number(self, number):
        return f"{int(number):,}".replace(",", ".")

    def validate_lineup(self, positions):
        min_spieler_pro_position = {'Torhüter': 1, 'Abwehrspieler': 3, 'Mittelfeldspieler': 2, 'Stürmer': 1}
        max_spieler_pro_position = {'Torhüter': 1, 'Abwehrspieler': 4, 'Mittelfeldspieler': 5, 'Stürmer': 3}
        for position, players in positions.items():
            count = len(players)
            if count < min_spieler_pro_position.get(position, 0) or count > max_spieler_pro_position.get(position, float('inf')):
                return False
        return True

class InputGUI:
    def __init__(self, root, spieler):
        self.root = root
        self.root.configure(bg="#2a3c48")  # Hintergrundfarbe setzen
        self.spieler = spieler
        self.file_path = None
        self.max_spieler_pro_verein = None
        self.team_logo_photos = []  # Initialisiere die Liste für die Team-Logos
        self.bg_color = "#2a3c48"  # Hintergrundfarbe

    def submit(self):
        try:
            budget = float(self.budget_entry.get())
            min_rating = float(self.min_rating_entry.get())
            min_spielzeit = float(self.min_spielzeit_entry.get())
            min_wahrscheinlichkeit = float(self.min_wahrscheinlichkeit_entry.get())
            max_spieler_pro_verein_values = [int(entry.get()) for entry in self.max_spieler_pro_verein_entries]
        except ValueError:
            messagebox.showerror("Fehler", "Bitte geben Sie gültige Zahlenwerte ein.")
            return

        max_spieler_pro_verein = dict(zip(self.max_spieler_pro_verein.keys(), max_spieler_pro_verein_values))
        lineup = optimize_lineup(self.file_path, budget, min_rating, min_spielzeit, min_wahrscheinlichkeit, max_spieler_pro_verein)
        print("Lineup:", lineup)
        if lineup and len(lineup) == 11:
            OutputGUI(lineup, self.spieler).display_lineup()
        else:
            messagebox.showerror("Fehler", "Kein passendes Lineup verfügbar.")

    def create_gui(self):
        self.root.title("Grundeinstellungen")
        self.root.geometry("570x1100+0+0")  # Angepasste Größe des Fensters

        # Abstand zwischen den Elementen
        padding = {'padx': 10, 'pady': 5}
        text_color = "#ffffff"  # Textfarbe definieren
        font = ("Philly Sans Regular", 12)  # Schriftart definieren
        button_color = "#2a3c48"  # Button-Farbe definieren
        button_border_color = "#ffffff"  # Rahmenfarbe definieren

        main_frame = ctk.CTkFrame(self.root, fg_color=self.bg_color)
        main_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(main_frame, text="Budget:", anchor="w", text_color=text_color, font=font, bg_color=self.bg_color).grid(row=0, column=0, sticky="w", **padding)
        self.budget_entry = ctk.CTkEntry(main_frame, font=font)
        self.budget_entry.grid(row=0, column=1, **padding)
        self.budget_entry.insert(0, '250000000')  # Beispielwert

        ctk.CTkLabel(main_frame, text="Minimales Rating pro Spieler:", anchor="w", text_color=text_color, font=font, bg_color=self.bg_color).grid(row=1, column=0, sticky="w", **padding)
        self.min_rating_entry = ctk.CTkEntry(main_frame, font=font)
        self.min_rating_entry.grid(row=1, column=1, **padding)

        ctk.CTkLabel(main_frame, text="Minimale Spielzeit pro Spieler:", anchor="w", text_color=text_color, font=font, bg_color=self.bg_color).grid(row=2, column=0, sticky="w", **padding)
        self.min_spielzeit_entry = ctk.CTkEntry(main_frame, font=font)
        self.min_spielzeit_entry.grid(row=2, column=1, **padding)

        ctk.CTkLabel(main_frame, text="Minimale 100 Punkte Wahrscheinlichkeit pro Spieler:", anchor="w", text_color=text_color, font=font, bg_color=self.bg_color).grid(row=3, column=0, sticky="w", **padding)
        self.min_wahrscheinlichkeit_entry = ctk.CTkEntry(main_frame, font=font)
        self.min_wahrscheinlichkeit_entry.grid(row=3, column=1, **padding)

        header_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, bg_color=self.bg_color)
        header_frame.grid(row=4, column=0, columnspan=2, sticky="w")
        ctk.CTkLabel(header_frame, text="maximale Spieler pro Verein: ", padx=10, anchor="w", text_color=text_color, font=font, fg_color=self.bg_color, bg_color=self.bg_color).pack(side="left", **padding)

        team_info_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, bg_color=self.bg_color)
        team_info_frame.grid(row=5, column=0, columnspan=2, sticky="w")

        self.max_spieler_pro_verein_entries = []
        for i, verein in enumerate(self.max_spieler_pro_verein):
            row_frame = ctk.CTkFrame(team_info_frame, fg_color=self.bg_color, bg_color=self.bg_color)
            row_frame.pack(fill="x", pady=2)

            logo_path = resource_path(f"{verein}.png")
            if os.path.exists(logo_path):
                team_logo_image = Image.open(logo_path)
                team_logo_image = team_logo_image.resize((30, 30), Image.Resampling.LANCZOS)
                team_logo_photo = ctk.CTkImage(dark_image=team_logo_image, size=(30, 30))
                ctk.CTkLabel(row_frame, image=team_logo_photo, text="", fg_color=self.bg_color, bg_color=self.bg_color).pack(side="left", padx=5)
                self.team_logo_photos.append(team_logo_photo)  # Um das Bild im Speicher zu halten

            ctk.CTkLabel(row_frame, text=verein, width=20, anchor="w", text_color=text_color, font=font, fg_color=self.bg_color, bg_color=self.bg_color).pack(side="left", padx=5)
            entry = ctk.CTkEntry(row_frame, width=5, font=font)
            entry.pack(side="right", padx=5)  # Rechtsbündig anordnen
            entry.insert(0, '3')
            self.max_spieler_pro_verein_entries.append(entry)

        button_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, bg_color=self.bg_color)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        submit_button = ctk.CTkButton(button_frame, text="Parameter übermitteln", command=self.submit, text_color=text_color, font=font, fg_color=button_color, bg_color=button_color, border_color=button_border_color, border_width=2)
        submit_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(button_frame, text="Beenden", command=self.exit_program, text_color=text_color, font=font, fg_color=button_color, bg_color=button_color, border_color=button_border_color, border_width=2)
        exit_button.pack(side="left", padx=5)

        logo_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, bg_color=self.bg_color)
        logo_frame.grid(row=7, column=0, columnspan=2, pady=10)

        logo_path = resource_path("Kickbase_logo_new.png")
        self.logo_photo = self.load_image(logo_path)
        self.logo_label = ctk.CTkLabel(logo_frame, image=self.logo_photo, text="", fg_color=self.bg_color, bg_color=self.bg_color)
        self.logo_label.pack(side="left", padx=5)

        ligainsider_path = resource_path("ligainsider.jpg")
        self.ligainsider_photo = self.load_image(ligainsider_path)
        self.ligainsider_label = ctk.CTkLabel(logo_frame, image=self.ligainsider_photo, text="", fg_color=self.bg_color, bg_color=self.bg_color)
        self.ligainsider_label.pack(side="left", padx=5)

        text_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, bg_color=self.bg_color)
        text_frame.grid(row=8, column=0, columnspan=2, pady=10)

        additional_text_label = ctk.CTkLabel(text_frame, text="© Philip Stölzle I designed for KB Challenges I powered by LI Stats I V1.1 (Stand Juli 2024)", anchor="center", text_color=text_color, font=font, fg_color=self.bg_color, bg_color=self.bg_color)
        additional_text_label.pack()

        self.root.deiconify()  # Hauptfenster anzeigen
        self.root.mainloop()

    def load_image(self, path):
        image = Image.open(path)
        image = image.resize((30, 30), Image.Resampling.LANCZOS)
        return ctk.CTkImage(dark_image=image, size=(30, 30))

    def exit_program(self):
        sys.exit()

def select_file_and_budget():
    root = ctk.CTk()
    root.configure(bg="#2a3c48")  # Hintergrundfarbe setzen
    root.withdraw()  # Verstecke das Hauptfenster

    messagebox.showinfo("Dateiauswahl", "Bitte wählen Sie eine Excel-Datei aus.")
    file_path = filedialog.askopenfilename(filetypes=[("Excel-Dateien", "*.xlsx")])

    if file_path:
        max_spieler_pro_verein = {
            'Bayern': 3, 'Dortmund': 3, 'Leverkusen': 3, 'Leipzig': 3, 'Union Berlin': 3, 'Freiburg': 3,
            'Köln': 3, 'Mainz': 3, 'Hoffenheim': 3, 'Mönchengladbach': 3, 'Frankfurt': 3,
            'Wolfsburg': 3, 'Bochum': 3, 'Augsburg': 3, 'Stuttgart': 3, 'Heidenheim': 3, 'Darmstadt': 3,
            'Bremen': 3
        }

        df = pd.read_excel(file_path)
        spieler = {}
        for index, row in df.iterrows():
            Name = row['Spieler']
            Verein = row['Verein']
            spieler[Name] = {
                'Verein': Verein,
                'Marktwert': float(row['Marktwert Gesamt']),
                'Spielzeit': float(row['Erw. Spielz.']),
                'Rating': float(row['Rating']),
                'Gegner': row['Gegner'],
                'Position': row['Position'],
                'Punktewahrscheinlichkeit': float(row['Punktewahrscheinlichkeit'])
            }

        gui = InputGUI(root, spieler)
        gui.file_path = file_path
        gui.max_spieler_pro_verein = max_spieler_pro_verein
        gui.create_gui()
    else:
        print("Es wurde keine Datei ausgewählt.")
        root.quit()
        root.destroy()

def optimize_lineup(file_path, budget, min_rating, min_spielzeit, min_wahrscheinlichkeit, max_spieler_pro_verein):
    set_openblas_path(openblas_path)  # Set OpenBLAS path for the solver

    # Load player data from the Excel file
    df = pd.read_excel(file_path)

    # Filter and structure player data
    spieler = {}
    for index, row in df.iterrows():
        Name = row['Spieler']
        Verein = row['Verein']
        spieler[Name] = {
            'Verein': Verein,
            'Marktwert': float(row['Marktwert Gesamt']),
            'Spielzeit': float(row['Erw. Spielz.']),
            'Rating': float(row['Rating']),
            'Gegner': row['Gegner'],
            'Position': row['Position'],
            'Punktewahrscheinlichkeit': float(row['Punktewahrscheinlichkeit'])
        }

    # Filter players based on minimum criteria
    filtered_spieler = {Name: info for Name, info in spieler.items()
                        if info['Rating'] >= min_rating
                        and info['Spielzeit'] >= min_spielzeit
                        and info['Punktewahrscheinlichkeit'] >= min_wahrscheinlichkeit}

    # Define position constraints
    min_spieler_pro_position = {'Torhüter': 1, 'Abwehrspieler': 3, 'Mittelfeldspieler': 2, 'Stürmer': 1}
    max_spieler_pro_position = {'Torhüter': 1, 'Abwehrspieler': 4, 'Mittelfeldspieler': 5, 'Stürmer': 3}

    # Initialize the optimization problem
    optimizer = LpProblem("Lineup_Optimizer", LpMaximize)

    # Define decision variables
    lineup = LpVariable.dicts("Lineup", filtered_spieler, 0, 1, LpBinary)

    # Define the objective function to maximize total player rating
    optimizer += lpSum([filtered_spieler[Name]['Rating'] * lineup[Name] for Name in filtered_spieler])

    # Add constraints for total budget
    optimizer += lpSum([filtered_spieler[Name]['Marktwert'] * lineup[Name] for Name in filtered_spieler]) <= budget

    # Add constraints for minimum and maximum players per position
    for position in min_spieler_pro_position:
        optimizer += lpSum([lineup[Name] for Name in filtered_spieler if filtered_spieler[Name]['Position'] == position]) >= min_spieler_pro_position[position]

    for position in max_spieler_pro_position:
        optimizer += lpSum([lineup[Name] for Name in filtered_spieler if filtered_spieler[Name]['Position'] == position]) <= max_spieler_pro_position[position]

    # Add constraints for maximum players per team
    for verein in max_spieler_pro_verein:
        optimizer += lpSum([lineup[Name] for Name in filtered_spieler if filtered_spieler[Name]['Verein'] == verein]) <= max_spieler_pro_verein[verein]

    # Ensure exactly 11 players are selected
    optimizer += lpSum([lineup[Name] for Name in filtered_spieler]) == 11

    # Solve the optimization problem
    optimizer.solve()

    # Extract the optimized lineup
    lineup = sorted([(Name, filtered_spieler[Name]['Position']) for Name in filtered_spieler if value(lineup[Name]) > 0],
                    key=lambda x: (x[1] != 'Torhüter', x[1]))

    # Validate the lineup length
    if len(lineup) != 11:
        lineup = None

    return lineup

if __name__ == "__main__":
    select_file_and_budget()
    ctk.mainloop()

