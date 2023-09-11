import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from PIL import Image, ImageTk
from pprint import pprint
from datetime import datetime, timedelta
from random import randint

import requests
import json
import matplotlib.pyplot as plt
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Baza = declarative_base()

engine = create_engine('sqlite:///PyFlora.db') #kreira bazu

Baza.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)

def get_pot_by_id(pot_id):
    session = Session()
    pot = session.query(Posuda).get(pot_id)
    session.close()
    return pot

def get_plant_by_id(plant_id):
    session = Session()
    plant = session.query(Biljka).get(plant_id)
    session.close()
    return plant

def get_all_pots():
    session = Session()
    pots = session.query(Posuda).all()
    session.close()
    return pots

def get_all_plants():
    session = Session()
    plants = session.query(Biljka).all()
    session.close()
    return plants

class Korisnik(Baza):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    password = Column(String)

class Biljka(Baza):
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    image_path = Column(String(100), nullable=False)
    watering = Column(String(20), nullable=False)
    environment = Column(String(20), nullable=False)
    substrate = Column(String(20), nullable=False)

    def __init__(self, name, image_path, watering, environment, substrate):
        self.name = name
        self.image_path = image_path
        self.watering = watering
        self.environment = environment
        self.substrate = substrate

class Posuda(Baza):
    __tablename__ = 'pots'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    image_path = Column(String(100), nullable=False)
    plant_id = Column(Integer, ForeignKey('plants.id'), nullable=True)

    plant = relationship('Biljka')

    def __init__(self, name, image_path, plant_id=None):
        self.name = name
        self.image_path = image_path
        self.plant_id = plant_id



class RaspberryPi:
    def __init__(self):
        self.sensors = [
            RaspberryPiSensor(sensor_name="Temperature", min_value=-15, max_value=50, unit="°C"),   
            RaspberryPiSensor(sensor_name="Pressure", min_value=900, max_value=1200, unit="hPa"),
            RaspberryPiSensor(sensor_name="Humidity", min_value=0, max_value=100, unit="%"),        
            RaspberryPiSensor(sensor_name="Salinity", min_value=0, max_value=35, unit="ppt"),       
            RaspberryPiSensor(sensor_name="Illuminance", min_value=0, max_value=100000, unit="lx"), 
        ]
    
    def get_data(self):
        current_datetime = datetime.now()
        past_datetimes = [current_datetime - timedelta(hours=i) for i in range(24)] #generira podatke za posljednja 24h
        data = []
        for dt in past_datetimes:
            for sensor in self.sensors:
                sensor.update_data()
                data.append(sensor.get_data(dt))
        
        return data
        

class RaspberryPiSensor:
    def __init__(self, sensor_name, min_value, max_value, unit):
        self.name = sensor_name
        self.max_value = max_value
        self.min_value = min_value
        self.unit = unit
        self.value = 0
    
    def generate_random_value(self):
        return randint(self.min_value, self.max_value)
    
    def update_data(self):
        self.value = self.generate_random_value()
    
    def get_data(self, datetime):
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "datetime": datetime,
        }


class UrediProfil(tk.Frame):
    def __init__(self, root, app, user_id):
        super().__init__(root)

        self.app = app
        self.user_id = user_id

        self.app.alatna_traka(self)

        self.username_label = tk.Label(self, text='Korisničko ime', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.username_label.pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        self.first_name_label = tk.Label(self, text='Ime', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.first_name_label.pack()
        self.first_name_entry = tk.Entry(self)
        self.first_name_entry.pack()

        self.last_name_label = tk.Label(self, text='Prezime', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.last_name_label.pack()
        self.last_name_entry = tk.Entry(self)
        self.last_name_entry.pack()
 
        frame = ttk.Frame(self)
        frame.pack()
        
        self.update_button = tk.Button(frame, text='Ažuriraj', command=self.update_profile)
        self.update_button.grid(row=0, column=1, padx=10, pady=10) 

        self.load_user_data()

    def load_user_data(self):
        session = Session()
        user = session.query(Korisnik).filter_by(id=self.user_id).first()

        if user is not None:
            self.username_entry.insert(tk.END, user.username)
            self.first_name_entry.insert(tk.END, user.first_name)
            self.last_name_entry.insert(tk.END, user.last_name)
            
    def update_profile(self):
        session = Session()
        user = session.query(Korisnik).filter_by(id=self.user_id).first()

        if user is not None:
            username = self.username_entry.get()
            first_name = self.first_name_entry.get()
            last_name = self.last_name_entry.get()

            if not username:
                messagebox.showerror('Pogreška!', 'Molim Vas ispunite sva polja!')
                return

            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            
            session.commit()
            messagebox.showinfo('Uspješno!', 'Podaci ažurirani uspješno!')

        self.app.show_plants_screen()

class UrediPosudu(tk.Frame):
    def __init__(self, root, app, pot_id):
        super().__init__(root)

        self.app = app
        self.pot_id = pot_id

        self.app.alatna_traka(self)
        
        self.name_label = tk.Label(self, text='Ime posude', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.name_label.pack()
        self.name_entry = tk.Entry(self)
        self.name_entry.pack()

        self.image_path_label = tk.Label(self, text='Slika', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.image_path_label.pack()
        self.image_path_entry = tk.Entry(self)
        self.image_path_entry.pack()
        
        self.plant_label = tk.Label(self, text="Biljka", font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.plant_label.pack()
        self.plant_combobox = ttk.Combobox(self, state="readonly")
        self.plant_combobox.pack()

        self.load_plants()

        # Actions
        frame = ttk.Frame(self)
        frame.pack()
        self.cancel_button = tk.Button(frame, text='Poništi', command=self.cancel)
        self.update_button = tk.Button(frame, text='Ažuriraj', command=self.update_pot)
        
        self.cancel_button.grid(row=0, column=0, padx=10, pady=10)
        self.update_button.grid(row=0, column=1, padx=10, pady=10)

        self.delete_button = tk.Button(self, text="Izbriši", command=self.delete_pot)
        self.delete_button.pack()

        self.load_pot_data()

    def load_plants(self):
        session = Session()
        self.plants = session.query(Biljka).all()
        plant_names = [plant.name for plant in self.plants]
        values = ['Empty']
        values.extend(plant_names)
        self.plant_combobox['values'] = values

    def load_pot_data(self):
        session = Session()
        pot = session.query(Posuda).filter_by(id=self.pot_id).first()

        if pot is not None:
            self.name_entry.insert(tk.END, pot.name)
            self.image_path_entry.insert(tk.END, pot.image_path)

            if pot.plant_id is not None:
                session = Session()
                plant = session.query(Biljka).filter_by(id=pot.plant_id).first()
                if plant:
                    self.plant_combobox.set(plant.name)

    def get_plant_id_by_name(self, name):
        plant_id = None
        for plant in self.plants:
            if plant.name == name:
                plant_id = plant.id
                break
        return plant_id

    def update_pot(self):
        session = Session()
        pot = session.query(Posuda).filter_by(id=self.pot_id).first()

        if pot is not None:
            name = self.name_entry.get()
            image_path = self.image_path_entry.get()
            plant_combobox_value = self.plant_combobox.get()
            
            plant_id = self.get_plant_id_by_name(plant_combobox_value)

            pot.name = name
            pot.image_path = image_path
            pot.plant_id = plant_id

            session.commit()
            messagebox.showinfo('Uspješno', 'Posuda ažurirana uspješno!')
            self.app.show_pots_screen()
            

    def cancel(self):
        self.app.show_pots_screen()

    def delete_pot(self):
        if messagebox.askyesno("Potvrđeno", "Jeste li sigurni da želite izbrisati posudu?"):
            session = Session()
            pot = session.query(Posuda).get(self.pot_id)
            
            session.delete(pot)
            session.commit()

            tk.messagebox.showinfo('Uspješno', 'Posuda obrisna uspješno!')
            self.app.show_pots_screen()


class UrediBiljku(tk.Frame):
    def __init__(self, root, app, plant_id):
        super().__init__(root)

        self.app = app
        self.plant_id = plant_id

        self.app.alatna_traka(self)

        self.name_label = tk.Label(self, text='Ime biljke', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.name_label.pack()
        self.name_entry = tk.Entry(self)
        self.name_entry.pack()

        self.image_path_label = tk.Label(self, text='Slika', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.image_path_label.pack()
        self.image_path_entry = tk.Entry(self)
        self.image_path_entry.pack()

        self.watering_label = tk.Label(self, text='Zalijevanje', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.watering_label.pack()
        self.watering_combobox = ttk.Combobox(self, values=['dnevno', 'tjedno', 'mjesečno'])
        self.watering_combobox.pack()

        self.environment_label = tk.Label(self, text='Okolina', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.environment_label.pack()
        self.environment_combobox = ttk.Combobox(self, values=['Toplo i tamno', 'toplo i svijetlo', 'hladno i tamno', 'hladno i svijetlo'])
        self.environment_combobox.pack()

        self.substrate_label = tk.Label(self, text='Supstrat')
        self.substrate_label.pack()
        self.substrate_combobox = ttk.Combobox(self, values=['potreban', 'nije potreban'])
        self.substrate_combobox.pack()

        frame = ttk.Frame(self)
        frame.pack()
        self.cancel_button = tk.Button(frame, text='Poništi', command=self.cancel)
        self.update_button = tk.Button(frame, text='Ažuriraj', command=self.update_plant)
        
        self.cancel_button.grid(row=0, column=0, padx=10, pady=10)
        self.update_button.grid(row=0, column=1, padx=10, pady=10)

        self.delete_button = tk.Button(self, text="Izbriši", command=self.delete_plant)
        self.delete_button.pack()

        self.load_plant_data()

    def load_plant_data(self):
        session = Session()
        plant = session.query(Biljka).filter_by(id=self.plant_id).first()

        if plant is not None:
            self.name_entry.insert(tk.END, plant.name)
            self.image_path_entry.insert(tk.END, plant.image_path)

            self.watering_combobox.set(plant.watering)
            self.environment_combobox.set(plant.environment)
            self.substrate_combobox.set(plant.substrate)

    def update_plant(self):
        session = Session()
        plant = session.query(Biljka).filter_by(id=self.plant_id).first()

        if plant is not None:
            name = self.name_entry.get()
            image_path = self.image_path_entry.get()
            watering = self.watering_combobox.get()
            environment = self.environment_combobox.get()
            substrate = self.substrate_combobox.get()

            if not name or not image_path or not watering or not environment or not substrate:
                messagebox.showerror('Pogreška!', 'Molim Vas ispunite sva potrebna polja!')
                return

            plant.name = name
            plant.image_path = image_path
            plant.watering = watering
            plant.environment = environment
            plant.substrate = substrate

            session.commit()
            messagebox.showinfo('Uspješno!', 'Biljka ažurirana uspješno!')

        self.app.show_plant_screen(self.plant_id)

    def cancel(self):
        self.app.show_plant_screen(self.plant_id)

    def delete_plant(self):
        if messagebox.askyesno("Potvrđeno!", "Jeste li sigurni da želite izbristai biljku?"):
            session = Session()
            plant = session.query(Biljka).get(self.plant_id)

            if plant:
                session = Session()
                associated_pots = session.query(Posuda).filter_by(plant_id=plant.id).all()
                if associated_pots:
                    tk.messagebox.showerror('Pogreška!', 'Ne možete obrisati biljku. Povezana s jednom ili više posuda.')
                    return
                
                session.delete(plant)

                pot = session.query(Posuda).filter_by(plant_id=self.plant_id).first()
                if pot:
                    pot.plant_id = None

                session.commit()
                tk.messagebox.showinfo('Uspješno!', 'Biljka obrisana uspiješno!')
                self.app.show_plants_screen()

class ProzorPosude(tk.Frame):
    def __init__(self, root, app):
        super().__init__(root)
        self.app = app

        self.pots = get_all_pots()

        self.app.alatna_traka(self)
        tk.Label(self, text='Posude', font=('Arial', 20, 'bold'), fg='forest green').pack(pady=10)

        self.scrollbar = ttk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.pots_canvas = tk.Canvas(self, bg='#00FF7F', yscrollcommand=self.scrollbar.set)
        self.pots_canvas.pack(side=tk.LEFT, fill='both', expand=True)

        self.scrollbar.config(command=self.pots_canvas.yview)
        self.pots_canvas.bind('<Configure>', lambda e: self.pots_canvas.configure(scrollregion=self.pots_canvas.bbox("all")))

        self.pots_frame = ttk.Frame(self.pots_canvas, style='MintGreen.TFrame')
        self.pots_canvas.create_window((0, 0), window=self.pots_frame, anchor="nw")

        self.display_pots()

    def display_pots(self):
        pots = self.pots

        style = ttk.Style()
        style.configure('Card.TFrame', background='white', borderwidth=1, relief='solid')

        style.configure('MintGreen.TFrame', background='white')

        row = 0
        col = 0

        for pot in pots:
            pot_frame = ttk.Frame(self.pots_frame, padding=10, style='Card.TFrame')
            pot_frame.grid(row=row, column=col, padx=10, pady=10)
            pot_frame.bind('<Button-1>', lambda event, pot_id=pot.id: self.app.show_pot_screen(pot_id))

            pot_image_path = pot.image_path
            pot_image = self.app.load_image(pot_image_path, width=200, height=200)

            pot_image_label = tk.Label(pot_frame, image=pot_image, bg='#00FF7F')
            pot_image_label.image = pot_image
            pot_image_label.pack()

            pot_name_label = tk.Label(pot_frame, text=pot.name, bg='#00FF7F')
            pot_name_label.pack()

            if Posuda.plant_id is None:
                pot_name_label = tk.Label(pot_frame, text='Empty pot', bg='#00FF7F')
                pot_name_label.pack()

            for child in pot_frame.winfo_children():
                child.bind('<Button-1>', lambda event, pot_id=pot.id: self.app.show_pot_screen(pot_id))

            col += 1
            if col > 2:
                col = 0
                row += 1


class ProzorPosuda(ttk.Frame):
    def __init__(self, root, app, pot_id):
        super().__init__(root)
        self.root = root
        self.app = app
        self.sensors_data = []
        self.sensors_data_pivoted = None

        self.pot_id = pot_id
        self.pot = get_pot_by_id(pot_id)
        self.plant = None  # Related plant
        if self.pot.plant_id:
            self.plant = get_plant_by_id(self.pot.plant_id)

        self.app.alatna_traka(self)

        self.frame = tk.Frame(self, width=400, bg='#00FF7F')
        self.frame.pack()

        self.create_widgets()

    def create_widgets(self):
        pot = self.pot
        plant = self.plant

        # Sync button to get data from sensors
        sync_button = ttk.Button(self.frame, text="Sinkroniziraj", command=self.handle_sync)
        sync_button.pack(pady=8)

        # Edit button to navigate to the Edit Pot screen
        back_button = ttk.Button(self.frame, text="Uredi", command=lambda: self.app.show_edit_pot_screen(self.pot_id))
        back_button.pack(pady=8)

        # Pot state
        if plant is None:
            is_empty_label = ttk.Label(self.frame, text="Posuda je prazna", background='#00FF7F')
            is_empty_label.pack(pady=8)

        image = self.app.load_image(pot.image_path, width=200, height=200)

        pot_name_value = ttk.Label(self.frame, text=pot.name, font='Helvetica 16', background='#00FF7F')
        pot_name_value.pack(pady=8)

        # Create a label to display the image
        image_label = ttk.Label(self.frame, image=image, background='#00FF7F')
        image_label.image = image
        image_label.pack()

        grid_frame = tk.Frame(self.frame, width=400, bg='#00FF7F')
        grid_frame.pack()

        if plant:
            ttk.Label(grid_frame, text="Podaci o biljci", font='Arial', background='#00FF7F').grid(row=2, column=0, sticky="w", pady=4)

            ttk.Label(grid_frame, text="Ime:", background='#00FF7F').grid(row=3, column=0, sticky="w")
            ttk.Label(grid_frame, text=plant.name, background='#00FF7F').grid(row=3, column=1, sticky="w")

            ttk.Label(grid_frame, text="Zalijevanje:", background='#00FF7F').grid(row=4, column=0, sticky="w")
            ttk.Label(grid_frame, text=plant.watering, background='#00FF7F').grid(row=4, column=1, sticky="w")

            ttk.Label(grid_frame, text="Okolina:", background='#00FF7F').grid(row=5, column=0, sticky="w")
            ttk.Label(grid_frame, text=plant.environment, background='#00FF7F').grid(row=5, column=1, sticky="w")

            ttk.Label(grid_frame, text="Supstrat:", background='#00FF7F').grid(row=6, column=0, sticky="w")
            ttk.Label(grid_frame, text=plant.substrate, background='#00FF7F').grid(row=6, column=1, sticky="w")

            ttk.Label(grid_frame, text="Status:", font='Arial', padding=8, background='#00FF7F').grid(row=7, column=0, sticky="w")
            ttk.Label(grid_frame, text='Uredu', background='#00FF7F').grid(row=7, column=1, sticky="w")

            self.label_var = tk.StringVar()
            self.label_var.set("Sve uredu!")

            label = ttk.Label(grid_frame, textvariable=self.label_var, background='#00FF7F')
            label.grid(row=7, column=1, sticky="w")

    def handle_sync(self):
        if self.plant is None:
            tk.messagebox.showerror('Pogreška', 'Posuda je prazna!')
            return
        sensors_data = self.get_sensors_data()
        forecast_data = self.app.dohvati_prognozu()
        self.create_forecast_charts(forecast_data)
        self.create_sensors_charts(sensors_data)

        last_row = sensors_data.iloc[-1]

        if last_row['Humidity'] < 60: #mjenja status posude ovisno i vlažnosti zemlje
            self.label_var.set('Potrebno zalijevanje')
        else:
            self.label_var.set('Uredu')

    def create_sensors_charts(self, df):
        fig, axs = plt.subplots(len(df.columns), 1, figsize=(8, 10))

        for i, column in enumerate(df.columns):
            ax = axs[i]
            ax.plot(df.index, df[column])
            ax.set_xlabel('Datetime')
            ax.set_ylabel(column)
            ax.set_title(f'{column} Variation')
            ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.show()

    def create_forecast_charts(self, forecast_data):
        hourly_data = forecast_data["hourly"]
        time = hourly_data["time"]
        temperature = hourly_data["temperature_2m"]
        humidity = hourly_data["relativehumidity_2m"]
        pressure = hourly_data["surface_pressure"]

        time = [datetime.strptime(t, "%Y-%m-%dT%H:%M") for t in time]
        fig, axs = plt.subplots(3, 1, figsize=(8, 10))

        axs[0].plot(time, temperature, label="Temperature (°C)")
        axs[0].set_ylabel("Temperature (°C)")
        axs[0].set_title("Temperature Variation")
        axs[0].legend()

        axs[1].plot(time, humidity, label="Relative Humidity (%)")
        axs[1].set_ylabel("Relative Humidity (%)")
        axs[1].set_title("Relative Humidity Variation")
        axs[1].legend()

        axs[2].plot(time, pressure, label="Surface Pressure (hPa)")
        axs[2].set_xlabel("Date")
        axs[2].set_ylabel("Surface Pressure (hPa)")
        axs[2].set_title("Surface Pressure Variation")
        axs[2].legend()

        plt.xticks(rotation=45)
        plt.tight_layout()

        plt.show()

    def get_sensors_data(self):
        raspi = RaspberryPi()
        data = raspi.get_data()

        df = pd.DataFrame(data)

        pivot_df = df.pivot(index='datetime', columns='name', values='value')
        pprint(pivot_df)

        return pivot_df


class LoginProzor(tk.Frame):
    def __init__(self, root, app):
        super().__init__(root)

        self.app = app
        
        self.configure(bg="white")
        
        background_image = Image.open("slike/slika1.png")
        background_photo = ImageTk.PhotoImage(background_image)
        background_label = tk.Label(self, image=background_photo)
        background_label.image = background_photo
        background_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        self.username_label = tk.Label(self, text='Korisničko ime', fg='forest green', font=('Arial', 15, 'bold'))
        self.username_label.pack()
        self.username_entry = tk.Entry(self,width=30, border=0)
        self.username_entry.pack()

        self.password_label = tk.Label(self, text='Lozinka', fg='forest green', font=('Arial', 15, 'bold'))
        self.password_label.pack()
        self.password_entry = tk.Entry(self,border=0, width=30, show='*')
        self.password_entry.pack()

        self.login_button = tk.Button(self, text='Prijava', command=self.login, fg='forest green', font=('Arial', 10, 'bold'))
        self.login_button.pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        session = Session()
        user = session.query(Korisnik).filter_by(username=username, password=password).first()

        if user is not None:
            self.app.show_plants_screen()
        else:
            messagebox.showerror('Prijava nije uspijela', 'Pogrešno korisničko ime ili lozinka!')


class DodajPosudu(tk.Frame):
    def __init__(self, root, app):
        super().__init__(root)
        self.app = app

        self.app.alatna_traka(self)
        tk.Label(self, text='Dodaj posudu', font=('Arial', 20, 'bold'), fg='forest green').pack(pady=10)

        self.name_label = tk.Label(self, text="Ime", font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.name_label.pack()
        self.name_entry = tk.Entry(self, font=('Arial', 12))
        self.name_entry.pack()

        self.image_path_label = tk.Label(self, text="Slika", font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.image_path_label.pack()
        self.image_path_entry = tk.Entry(self, font=('Arial', 12))
        self.image_path_entry.pack()

        self.plant_label = tk.Label(self, text="Biljka", font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.plant_label.pack()
        self.plant_combobox = ttk.Combobox(self, state="readonly", font=('Arial', 12))
        self.plant_combobox.pack()

        self.load_plants()

        self.add_button = tk.Button(self, text="Dodaj", command=self.add_pot, font=('Arial', 12), bg='green', fg='white')
        self.add_button.pack()

        self.cancel_button = tk.Button(self, text="Poništi", command=self.cancel, font=('Arial', 12), bg='red', fg='white')
        self.cancel_button.pack()

    def load_plants(self):
        session = Session()
        self.plants = session.query(Biljka).all()
        plant_names = [plant.name for plant in self.plants]
        values = ['Empty']
        values.extend(plant_names)
        self.plant_combobox['values'] = values

    def get_plant_id_by_name(self, name):
        plant_id = None
        for plant in self.plants:
            if plant.name == name:
                plant_id = plant.id
                break
        return plant_id

    def add_pot(self):
        name = self.name_entry.get()
        image_path = self.image_path_entry.get()
        plant_combobox_value = self.plant_combobox.get()

        if not name:
            tk.messagebox.showerror('Pogreška!', 'Molim Vas unesite ime.')
            return

        plant_id = self.get_plant_id_by_name(plant_combobox_value)

        session = Session()
        pot = Posuda(name=name, image_path=image_path, plant_id=plant_id)
        session.add(pot)
        session.commit()

        tk.messagebox.showinfo('Uspješno!', 'Posuda dodana uspješno!')
        self.app.show_pots_screen()

    def cancel(self):
        self.app.show_pots_screen()

class ProzorBiljka(ttk.Frame):
    def __init__(self, root, app, plant_id):
        super().__init__(root)
        self.root = root
        self.app = app
        self.plant_id = plant_id
        self.plant = get_plant_by_id(plant_id)

        self.app.alatna_traka(self)

        self.frame = tk.Frame(self, width=400)
        self.frame.pack()

        self.create_widgets()

    def create_widgets(self):
        image = self.app.load_image(self.plant.image_path, width=200, height=200)
        
        image_label = ttk.Label(self.frame, image=image)
        image_label.image = image
        image_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        ttk.Label(self.frame, text="Ime biljke:").grid(row=1, column=0, sticky="w")
        ttk.Label(self.frame, text=self.plant.name).grid(row=1, column=1, sticky="w")

        ttk.Label(self.frame, text="Zalijevanje:").grid(row=2, column=0, sticky="w")
        ttk.Label(self.frame, text=self.plant.watering).grid(row=2, column=1, sticky="w")

        ttk.Label(self.frame, text="Okolina:").grid(row=3, column=0, sticky="w")
        ttk.Label(self.frame, text=self.plant.environment).grid(row=3, column=1, sticky="w")

        ttk.Label(self.frame, text="Supstrat:").grid(row=4, column=0, sticky="w")
        ttk.Label(self.frame, text=self.plant.substrate).grid(row=4, column=1, sticky="w")

        back_button = ttk.Button(self.frame, text="Uredi", command=lambda: self.app.show_edit_plant_screen(self.plant_id))
        back_button.grid(row=5, column=1, pady=10)

class ProzorBiljke(tk.Frame):
    def __init__(self, root, app):
        super().__init__(root)

        self.app = app
        self.plants = get_all_plants()

        self.app.alatna_traka(self)
        tk.Label(self, text='Biljke', font=('Arial', 20, 'bold'), fg='forest green').pack(pady=10)

        self.canvas = tk.Canvas(self, bg='#00FF7F')
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview) #scrollbar
        scrollbar.pack(side='right', fill='y')

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))

        self.plants_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.plants_frame, anchor='nw')

        self.display_plants()

    def display_plants(self):
        plants = self.plants
        style = ttk.Style()
        style.configure('Card.TFrame', background='white', borderwidth=1, relief='solid')

        row = 0
        col = 0

        for plant in plants:
            plant_frame = ttk.Frame(self.plants_frame, padding=10, style='Card.TFrame')
            plant_frame.grid(row=row, column=col, padx=10, pady=10)
            plant_frame.bind('<Button-1>', lambda event, plant_id=plant.id: self.app.show_plant_screen(plant_id))

            plant_image_path = plant.image_path
            plant_image = self.app.load_image(plant_image_path, width=200, height=200)

            plant_image_label = tk.Label(plant_frame, image=plant_image, bg='#00FF7F')
            plant_image_label.image = plant_image
            plant_image_label.pack(pady=10)

            plant_name_label = tk.Label(plant_frame, text=plant.name, font=('Arial', 14, 'bold'), fg='#00FF7F', bg='white')
            plant_name_label.pack()

            for child in plant_frame.winfo_children():
                child.bind('<Button-1>', lambda event, plant_id=plant.id: self.app.show_plant_screen(plant_id))

            col += 1
            if col > 2:
                col = 0
                row += 1

class DodajBiljku(tk.Frame):
    def __init__(self, root, app):
        super().__init__(root)

        self.app = app

        self.app.alatna_traka(self)
        tk.Label(self, text='Dodaj biljku', font=('Arial', 20, 'bold'), fg='forest green').pack(pady=10)

        tk.Label(self, text='Ime biljke', font=('Arial', 12, 'bold'), fg='#00FF7F').pack()

        self.name_entry = tk.Entry(self, font=('Arial', 12))
        self.name_entry.pack()

        tk.Label(self, text='Slika', font=('Arial', 12, 'bold'), fg='#00FF7F').pack()

        self.image_path_entry = tk.Entry(self, font=('Arial', 12))
        self.image_path_entry.pack()

        self.watering_label = tk.Label(self, text='Zalijevanje', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.watering_label.pack()
        self.watering_combobox = ttk.Combobox(self, values=['dnevno', 'tjedno', 'mjesečno'], font=('Arial', 12))
        self.watering_combobox.pack()

        self.environment_label = tk.Label(self, text='Okolina', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.environment_label.pack()
        self.environment_combobox = ttk.Combobox(self, values=['toplo i tamno', 'toplo i svijetlo', 'hladno i tamno', 'hladno i svijetlo'], font=('Arial', 12))
        self.environment_combobox.pack()

        self.substrate_label = tk.Label(self, text='Supstrat', font=('Arial', 12, 'bold'), fg='#00FF7F')
        self.substrate_label.pack()
        self.substrate_combobox = ttk.Combobox(self, values=['potreban', 'nije potreban'], font=('Arial', 12))
        self.substrate_combobox.pack()

        tk.Button(self, text='Dodaj', command=self.add_plant, font=('Arial', 12), bg='green', fg='white').pack()

        tk.Button(self, text='Poništi', command=self.cancel, font=('Arial', 12), bg='red', fg='white').pack()

    def add_plant(self):
        name = self.name_entry.get()
        image_path = self.image_path_entry.get()
        watering = self.watering_combobox.get()
        environment = self.environment_combobox.get()
        substrate = self.substrate_combobox.get()

        if not name or not image_path or not watering or not environment or not substrate:
            tk.messagebox.showerror('Pogreška', 'Molim Vas ispunite sva polja!')
            return

        session = Session()
        plant = Biljka(name=name, image_path=image_path, watering=watering, environment=environment, substrate=substrate)
        session.add(plant)
        session.commit()

        tk.messagebox.showinfo('Uspješno!', 'Biljka dodana uspiješno!')

        self.name_entry.delete(0, tk.END) 
        self.image_path_entry.delete(0, tk.END)
        self.watering_combobox.set('')
        self.environment_combobox.set('')
        self.substrate_combobox.set('')

    def cancel(self):
        self.app.show_plants_screen()


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('PyFlora 1.0')
        self.root.geometry('1280x720')
        self.current_screen = None
        
        self.show_login_screen()
    
    def show_login_screen(self):
        self.login_screen = LoginProzor(self.root, self)
        self.show_screen(self.login_screen)
        
    def load_image(self, image_path, width=100, height=100):
        full_path = "slike/" + image_path
        try:
            plant_image = Image.open(full_path)
        except FileNotFoundError: 
            fallback_image_path = 'slike/default_image.jpg'
            plant_image = Image.open(fallback_image_path)
        except PermissionError:
            fallback_image_path = 'slike/default_image.jpg'
            plant_image = Image.open(fallback_image_path)

        plant_image = plant_image.resize((width, height))
        tk_image = ImageTk.PhotoImage(plant_image)

        return tk_image
        
    def show_screen(self, screen):
        if self.current_screen is not None:
            self.current_screen.destroy()

        self.current_screen = screen
        self.current_screen.pack(fill='both', expand=True)

    def show_plants_screen(self):
        plants_screen = ProzorBiljke(self.root, self)
        self.show_screen(plants_screen)

    def show_add_plant_screen(self):
        add_plant_screen = DodajBiljku(self.root, self)
        self.show_screen(add_plant_screen)

    def show_plant_screen(self, plant_id):
        add_plant_screen = ProzorBiljka(self.root, self, plant_id)
        self.show_screen(add_plant_screen)

    def show_edit_plant_screen(self, plant_id):
        edit_plant_screen = UrediBiljku(self.root, self, plant_id)
        self.show_screen(edit_plant_screen)

    def show_pots_screen(self):
        pots_screen = ProzorPosude(self.root, self)
        self.show_screen(pots_screen)
        
    def show_pot_screen(self, pot_id):
            pot_screen = ProzorPosuda(self.root, self, pot_id)
            self.show_screen(pot_screen)

    def show_add_pot_screen(self):
        add_pots_screen = DodajPosudu(self.root, self)
        self.show_screen(add_pots_screen)

    def show_edit_pot_screen(self, pot_id):
        edit_pot_screen = UrediPosudu(self.root, self, pot_id)
        self.show_screen(edit_pot_screen)

    def show_edit_profile_screen(self):
        user_id = 1
        edit_profile_screen = UrediProfil(self.root, self, user_id)
        self.show_screen(edit_profile_screen)
        
    def alatna_traka(self, frame):
        
        style = ttk.Style() 

        self.alatna_traka_frame = ttk.Frame(frame)
        self.alatna_traka_frame.pack(side="top", fill="x")
        
        okvir_trake = ttk.Frame(self.alatna_traka_frame, padding=(8, 8, 8, 8))
        okvir_trake.pack(side="top", fill="x")
        
        tk.Button(okvir_trake, text='Biljke', fg='forest green', command=self.show_plants_screen, font=("Arial", 12, "bold")).pack(side='left')

        tk.Button(okvir_trake, text='Posude', fg='forest green', command=self.show_pots_screen, font=("Arial", 12, "bold")).pack(side='left')

        tk.Button(okvir_trake, text='Dodaj biljku', fg='forest green', command=self.show_add_plant_screen, font=("Arial", 12, "bold")).pack(side='left')

        tk.Button(okvir_trake, text='Dodaj posudu', fg='forest green', command=self.show_add_pot_screen, font=("Arial", 12, "bold")).pack(side='left')

        tk.Button(okvir_trake, text='Uredi profil', fg='forest green', command=self.show_edit_profile_screen, font=("Arial", 12, "bold")).pack(side='right')
        
        tk.Button(okvir_trake, text='Odjava', fg='forest green', command=self.show_login_screen, font=("Arial", 12, "bold")).pack(side='right')
        
        separator = ttk.Separator(self.alatna_traka_frame, orient="horizontal")
        separator.pack(side="bottom", fill="x")
        separator.configure(style="Separator.TSeparator")
        style.configure("Separator.TSeparator", background="black")
        
    def dohvati_prognozu(self):
        try: 
            url = "https://api.open-meteo.com/v1/forecast?latitude=45.81&longitude=15.98&hourly=temperature_2m,relativehumidity_2m,surface_pressure"
            response = requests.get(url)
            json_forecast = response.json()
            with open("prognoza.json", "w") as file:
                json.dump(json_forecast, file)
        except requests.exceptions.RequestException as e:
            with open("prognoza.json") as file:
                json_forecast = json.load(file)

        return json_forecast


app = App()
app.root.mainloop()