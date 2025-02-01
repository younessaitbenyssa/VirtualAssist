import customtkinter as ctk
from tkcalendar import DateEntry, Calendar
from datetime import datetime
from tkinter import messagebox

class ToDoListApp:
    def __init__(self, parent_frame):
        # Create main container in the parent frame
        self.main_container = ctk.CTkFrame(parent_frame)
        self.main_container.pack(side="right", fill="both", expand=True)

        # Dictionary to store tasks by date
        self.tasks = {}

        # Create two columns
        self.left_column = ctk.CTkFrame(self.main_container, width=300)
        self.left_column.pack(side="left", fill="both", padx=10, pady=10)

        self.right_column = ctk.CTkFrame(self.main_container)
        self.right_column.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Calendar section
        self.calendar_frame = ctk.CTkFrame(self.left_column)
        self.calendar_frame.pack(fill="x", pady=(0, 10))

        self.calendar = Calendar(
            self.calendar_frame,
            selectmode='day',
            date_pattern='yyyy-mm-dd'
        )
        self.calendar.pack(pady=10)
        self.calendar.bind("<<CalendarSelected>>", self.on_date_selected)

        # Add task section
        self.add_task_frame = ctk.CTkFrame(self.left_column)
        self.add_task_frame.pack(fill="x")

        self.task_entry = ctk.CTkEntry(
            self.add_task_frame,
            placeholder_text="Enter new task",
            height=40
        )
        self.task_entry.pack(fill="x", pady=5)

        self.priority_var = ctk.StringVar(value="Normal")
        self.priority_menu = ctk.CTkOptionMenu(
            self.add_task_frame,
            values=["Low", "Normal", "High"],
            variable=self.priority_var
        )
        self.priority_menu.pack(fill="x", pady=5)

        self.add_button = ctk.CTkButton(
            self.add_task_frame,
            text="Add Task",
            command=self.add_task,
            height=40
        )
        self.add_button.pack(fill="x", pady=5)

        # Tasks display section
        self.tasks_label = ctk.CTkLabel(
            self.right_column,
            text="Tasks",
            font=("Arial", 20, "bold")
        )
        self.tasks_label.pack(pady=10)

        self.tasks_frame = ctk.CTkScrollableFrame(
            self.right_column,
            width=400,
            height=500
        )
        self.tasks_frame.pack(fill="both", expand=True)

        # Initialize with today's date
        today = datetime.now().strftime("%Y-%m-%d")
        self.on_date_selected(None, initial_date=today)

    def add_task(self):
        task_text = self.task_entry.get()
        if task_text.strip() == "":
            messagebox.showwarning("Warning", "Please enter a task!")
            return

        selected_date = self.calendar.get_date()
        priority = self.priority_var.get()

        if selected_date not in self.tasks:
            self.tasks[selected_date] = []

        task = {
            'text': task_text,
            'priority': priority,
            'completed': False,
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'due_date': selected_date
        }

        self.tasks[selected_date].append(task)
        self.task_entry.delete(0, "end")
        self.display_tasks_for_date(selected_date)

    def on_date_selected(self, event, initial_date=None):
        if initial_date:
            selected_date = initial_date
        else:
            selected_date = self.calendar.get_date()
        
        self.display_tasks_for_date(selected_date)

    def display_tasks_for_date(self, date):
        self.tasks_label.configure(text=f"Tasks for {date}")
        
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

        if date in self.tasks and self.tasks[date]:
            for task in self.tasks[date]:
                self.create_task_widget(task)
        else:
            no_tasks_label = ctk.CTkLabel(
                self.tasks_frame,
                text="No tasks for this date"
            )
            no_tasks_label.pack(pady=10)

    def create_task_widget(self, task):
        task_frame = ctk.CTkFrame(self.tasks_frame)
        task_frame.pack(fill="x", padx=5, pady=2)

        priority_colors = {"Low": "gray", "Normal": "blue", "High": "red"}
        priority_indicator = ctk.CTkLabel(
            task_frame,
            text="●",
            text_color=priority_colors[task['priority']]
        )
        priority_indicator.pack(side="left", padx=2)

        checkbox = ctk.CTkCheckBox(
            task_frame,
            text=task['text'],
            command=lambda t=task: self.toggle_task(t)
        )
        checkbox.pack(side="left", padx=5)
        checkbox.select() if task['completed'] else checkbox.deselect()

        delete_button = ctk.CTkButton(
            task_frame,
            text="Delete",
            width=60,
            command=lambda t=task: self.delete_task(t)
        )
        delete_button.pack(side="right", padx=5)

    def toggle_task(self, task):
        task['completed'] = not task['completed']
        self.display_tasks_for_date(task['due_date'])

    def delete_task(self, task):
        date = task['due_date']
        if date in self.tasks:
            self.tasks[date].remove(task)
            if not self.tasks[date]:
                del self.tasks[date]
            self.display_tasks_for_date(date)

    def hide(self):
        self.main_container.pack_forget()

    def show(self):
        self.main_container.pack(side="right", fill="both", expand=True)