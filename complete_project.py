import tkinter as tk
from tabulate import tabulate
import random
from tkinter import messagebox, simpledialog
import mysql.connector



class TimetableGeneratorGA:
    def __init__(self, subjects, professors, semester, lab_availability, working_days, num_periods):
        self.subjects = subjects
        self.professors = professors
        self.semester = semester
        self.lab_availability = lab_availability
        self.working_days = working_days
        self.num_periods = num_periods
        self.professor_subjects = {professor: None for professor in professors}
        self.population_size = 10
        self.population = []
#First, let's talk about the Genetic Algorithm (GA) used for generating timetables. The TimetableGeneratorGA class is responsible for this.
#It creates random timetables and evolves them over several generations to find the most balanced and clash-free schedules for two sections, A and B.
#The GA involves initialization, fitness evaluation, selection, crossover, and mutation processes.

    def generate_random_timetable(self):
        timetable = [[] for _ in range(len(self.working_days))]

        for i, day in enumerate(self.working_days):
            time_slot = 9
            lunch_hour = False
            day_schedule = []
            while time_slot <= 16:
                if lunch_hour:
                    time_slot += 1
                    lunch_hour = False
                    continue
                elif time_slot == 13:
                    # Add a 20-minute break at 13:00
                    day_schedule.append((day, f"{time_slot}:00 - {time_slot}:20", "Break", None))
                    time_slot += 1
                    continue
                subject = random.choice(self.subjects)
                professor = self.get_available_professor(subject)
                if subject not in self.lab_availability or day != self.lab_availability[subject]:
                    if time_slot - 9 < self.num_periods:
                        day_schedule.append((day, f"{time_slot}:00 - {time_slot+1}:00", subject, professor))
                    time_slot += 1
                else:
                    if time_slot - 9 < self.num_periods:
                        day_schedule.append((day, f"{time_slot}:00 - {time_slot+1}:00", "Lab", None))
                    time_slot += 1

            timetable[i] = day_schedule

            # Remove consecutive occurrences of the same subject
            for j in range(1, len(day_schedule)):
                if day_schedule[j][2] == day_schedule[j-1][2]:
                    available_subjects = [s for s in self.subjects if s != day_schedule[j][2]]
                    subject = random.choice(available_subjects)
                    professor = self.get_available_professor(subject)
                    day_schedule[j] = (day_schedule[j][0], day_schedule[j][1], subject, professor)

        return timetable

    def get_available_professor(self, subject):
        available_professors = [professor for professor, assigned_subject in self.professor_subjects.items() if assigned_subject is None or assigned_subject == subject]
        if available_professors:
            return random.choice(available_professors)
        else:
            return None

    def initialize_population(self):
        self.population = [self.generate_random_timetable() for _ in range(self.population_size)]
        
    #The fitness method evaluates each timetable by checking the workload balance among professors and assigns a score to minimize imbalance.
    #Calculates the fitness score using the formula 1 / (1 + penalty). The fitness score is higher when the penalty is lower.
    def fitness(self, timetable):
        penalty = 0
        workload = {professor: 0 for professor in self.professors}

        for day in timetable:
            for _, _, subject, professor in day:
                if professor:
                    workload[professor] += 1

        max_workload = max(workload.values())
        min_workload = min(workload.values())
        workload_imbalance = max_workload - min_workload
        penalty += workload_imbalance

        fitness_score = 1 / (1 + penalty)
        return fitness_score
    #The selection method picks the best timetables based on their fitness scores.
    #The crossover and mutate methods combine and slightly alter these timetables to produce new ones.

    def selection(self):
        selected = random.choices(self.population, weights=[self.fitness(timetable) for timetable in self.population], k=2)
        return selected[0], selected[1]

    def crossover(self, parent1, parent2):
        if len(parent1) <= 1:
            return parent1, parent2

        crossover_point = random.randint(1, len(parent1) - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        return child1, child2
    #Here, random.random() generates a random float between 0 and 1.
    #If this random value is less than 0.1 (i.e., 10% of the time), the mutation operation will be performed. Otherwise, it will be skipped.
    def mutate(self, timetable):
        for day in timetable:
            for i, (_, _, subject, _) in enumerate(day):
                #This condition checks if the current class session subject is the same as the previous class session subject.
                #i > 0 ensures that we are not checking before the first element.
                #The purpose of introducing probability in mutation is to control the rate at which mutations occur.
                if i > 0 and day[i-1][2] == subject:
                    new_subject = random.choice(self.subjects)
                    professor = self.get_available_professor(new_subject)
                    if professor:
                        day[i] = (day[i][0], day[i][1], new_subject, professor)

    def evolve(self):
        parent1, parent2 = self.selection()
        child1, child2 = self.crossover(parent1, parent2)

        if random.random() < 0.1:
            self.mutate(child1)
        if random.random() < 0.1:
            self.mutate(child2)

        self.population.extend([child1, child2])

        self.population = sorted(self.population, key=lambda x: self.fitness(x), reverse=True)[:self.population_size]

    def generate_timetable(self, generations, section):
        self.initialize_population()
        for _ in range(generations):
            self.evolve()
        best_timetable = max(self.population, key=lambda x: self.fitness(x))
        return best_timetable

    def compare_and_adjust_timetables(self, timetable_a, timetable_b):
        clashes_exist = True
        while clashes_exist:
            clashes_exist = False
            for i in range(len(self.working_days)):
                for j in range(self.num_periods):
                    if timetable_a[i][j][2] == timetable_b[i][j][2]:
                        available_subjects = [s for s in self.subjects if s != timetable_a[i][j][2]]
                        new_subject_a = random.choice(available_subjects)
                        available_subjects.remove(new_subject_a)  # Remove selected subject from available subjects
                        new_subject_b = random.choice([s for s in available_subjects if s != new_subject_a]) if available_subjects else new_subject_a
                        professor_a = self.get_available_professor(new_subject_a)
                        professor_b = self.get_available_professor(new_subject_b)
                        timetable_a[i][j] = (timetable_a[i][j][0], timetable_a[i][j][1], new_subject_a, professor_a)
                        timetable_b[i][j] = (timetable_b[i][j][0], timetable_b[i][j][1], new_subject_b, professor_b)
                        clashes_exist = True

                        # Break out of inner loop if a clash is found
                        break
                # Break out of outer loop if a clash is found
                if clashes_exist:
                    break


class TimetableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Timetable Generator")

        self.create_widgets()

    def create_widgets(self):
        # Labels and Entry fields for input
        tk.Label(self.root, text="Number of Subjects:").grid(row=0, column=0, padx=10, pady=5)
        self.subjects_entry = tk.Entry(self.root)
        self.subjects_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.root, text="Number of Professors:").grid(row=1, column=0, padx=10, pady=5)
        self.professors_entry = tk.Entry(self.root)
        self.professors_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.root, text="Number of Periods:").grid(row=2, column=0, padx=10, pady=5)
        self.periods_entry = tk.Entry(self.root)
        self.periods_entry.grid(row=2, column=1, padx=10, pady=5)

        # Button to generate timetables
        self.generate_button = tk.Button(self.root, text="Generate Timetables", command=self.generate_timetables)
        self.generate_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Text area to display timetables
        self.timetable_text = tk.Text(self.root, width=150, height=30)
        self.timetable_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    def generate_timetables(self):
        try:
            num_subjects = int(self.subjects_entry.get())
            num_professors = int(self.professors_entry.get())
            num_periods = int(self.periods_entry.get())

            subjects = self.get_user_input("Subjects", num_subjects)
            professors = self.get_user_input("Professors", num_professors)

            semester = "Fall 2024"
            working_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            lab_availability = {}

            # Create TimetableGeneratorGA instances
            generator_section_a = TimetableGeneratorGA(subjects, professors, semester, lab_availability, working_days, num_periods)
            generator_section_b = TimetableGeneratorGA(subjects, professors, semester, lab_availability, working_days, num_periods)

            # Generate timetables for both sections
            best_timetable_section_a = generator_section_a.generate_timetable(generations=100, section="A")
            best_timetable_section_b = generator_section_b.generate_timetable(generations=100, section="B")

            # Compare and adjust timetables if necessary
            generator_section_a.compare_and_adjust_timetables(best_timetable_section_a, best_timetable_section_b)

            # Display timetables in the GUI or console
            self.display_timetable(best_timetable_section_a, best_timetable_section_b, num_periods)

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for subjects, professors, and periods.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def get_user_input(self, title, count):
        result = []
        for i in range(count):
            prompt = f"Enter the name of {title.lower()} {i+1}:"
            user_input = simpledialog.askstring("User Input", prompt, parent=self.root)
            if user_input is None:
                return []  # Cancel button was pressed
            result.append(user_input)
        return result

    def display_timetable(self, timetable_a, timetable_b, num_periods):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [f"{i+9}:00 - {i+9}:00" if i == 11 else f"{i+9}:00 - {i+10}:00" for i in range(num_periods)]

        timetable_data_a = [[""] * (num_periods + 1) for _ in range(len(days) + 1)]
        timetable_data_b = [[""] * (num_periods + 1) for _ in range(len(days) + 1)]

        timetable_data_a[0][1:] = periods
        timetable_data_b[0][1:] = periods

        for i, day_schedule in enumerate(timetable_a):
            if i < len(days):
                timetable_data_a[i + 1][0] = days[i]
                for j, period_info in enumerate(day_schedule):
                    if j < len(periods) and len(period_info) >= 3:
                        timetable_data_a[i + 1][j + 1] = period_info[2]

        for i, day_schedule in enumerate(timetable_b):
            if i < len(days):
                timetable_data_b[i + 1][0] = days[i]
                for j, period_info in enumerate(day_schedule):
                    if j < len(periods) and len(period_info) >= 3:
                        timetable_data_b[i + 1][j + 1] = period_info[2]

        # Display timetable for Section A
        self.timetable_text.insert(tk.END, "Best Timetable for Section A:\n")
        self.timetable_text.insert(tk.END, tabulate(timetable_data_a, headers="firstrow") + "\n\n")

        # Display timetable for Section B
        self.timetable_text.insert(tk.END, "Best Timetable for Section B:\n")
        self.timetable_text.insert(tk.END, tabulate(timetable_data_b, headers="firstrow") + "\n\n")

def validate_login(username, password):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="2004",
            database="timetable"
        )

        cursor = connection.cursor()
        query = "SELECT * FROM login WHERE uname = %s AND pass = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchall()
        cursor.close()
        connection.close()

        if user:
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            root.destroy()
            root1 = tk.Tk()
            app = TimetableApp(root1)
            root1.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Database error: {err}")

def register_user(username, password):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="2004",
            database="timetable"
        )

        cursor = connection.cursor()
        query = "INSERT INTO login (uname, pass) VALUES (%s, %s)"
        cursor.execute(query, (username, password))
        connection.commit()
        cursor.close()
        connection.close()

        messagebox.showinfo("Registration Successful", "User registered successfully!")

    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Database error: {err}")

root = tk.Tk()
root.title("Login or Register")
root.geometry('500x500')

tk.Label(root, text="Username:").pack(pady=10)
username_entry = tk.Entry(root)
username_entry.pack(pady=5)

tk.Label(root, text="Password:").pack(pady=10)
password_entry = tk.Entry(root, show="*")
password_entry.pack(pady=5)

def login_clicked():
    username = username_entry.get()
    password = password_entry.get()

    if username == "" or password == "":
        messagebox.showerror("Error", "Please enter both username and password.")
    else:
        validate_login(username, password)

def register_clicked():
    username = username_entry.get()
    password = password_entry.get()

    if username == "" or password == "":
        messagebox.showerror("Error", "Please enter both username and password.")
    else:
        register_user(username, password)

tk.Button(root, text="Login", command=login_clicked).pack(pady=10)
tk.Button(root, text="Register", command=register_clicked).pack(pady=10)

root.mainloop()




