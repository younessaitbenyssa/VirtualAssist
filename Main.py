import customtkinter as ctk
from PIL import Image
import chatInter
import todoList
import document
import voice
from movies import MovieRecommenderApp
from transaction.transaction import TransactionApp


app = ctk.CTk()
app.geometry("1200x630")

sideBar = ctk.CTkFrame(master=app, width=250, height=630, fg_color="#171717")
sideBar.pack(side="left", fill="both")
sideBar.pack_propagate(False)
frame_color = sideBar.cget("fg_color")

main_frame = ctk.CTkFrame(master=app, width=950, height=630)
main_frame.pack(side="right", fill="both")
main_frame.pack_propagate(False)

chatInter.ChatInterface(main_frame, app)

# Load images
logo_image = ctk.CTkImage(light_image=Image.open("images/virtual-assistant-logo.png"), size=(130, 130))
image = ctk.CTkImage(light_image=Image.open("images/expenses.png"), size=(30, 30))
todolist_img = ctk.CTkImage(light_image=Image.open("images/todolist.png"), size=(30, 30))
design_img = ctk.CTkImage(light_image=Image.open("images/design.png"), size=(30, 30))
chatbot_icon = ctk.CTkImage(light_image=Image.open("images/chatbot.png"), size=(40, 40))
document_img = ctk.CTkImage(light_image=Image.open("images/document.png"), size=(35, 35))
voice_Assistant_img = ctk.CTkImage(light_image=Image.open("images/voice.png"), size=(40,40))

# Logo
logo_label = ctk.CTkLabel(sideBar, text="", image=logo_image)
logo_label.place(y=25, x=60)

movie_img = ctk.CTkImage(light_image=Image.open("images/movie.png"), size=(40,40))
transaction_img = ctk.CTkImage(light_image=Image.open("images/transaction.png"), size=(45,45))


# Button Functions
def afficher_chat():
    clear_main_frame()
    chatInter.ChatInterface(main_frame, app)


def open_todo():
    clear_main_frame()
    todoList.ToDoListApp(main_frame)


def open_document():
    clear_main_frame()
    app = document.DocumentApp(main_frame)
    app.text_widget.bind("<<Selection>>", lambda e: app.highlight_selected_text())


def open_settings():
    print("Opening Settings")  # Placeholder for settings functionality


def voice_assistant():
    clear_main_frame()
    voice.Voice(main_frame)


def afficher_movie():
    clear_main_frame()
    MovieRecommenderApp(main_frame)


def transaction():
    clear_main_frame()
    TransactionApp(main_frame)


def clear_main_frame():
    for widget in main_frame.winfo_children():
        widget.destroy()


# Buttons with new labels and commands
todo_button = ctk.CTkButton(
    sideBar,
    text="          Todo List",
    image=todolist_img,
    height=40,
    width=230,
    fg_color=frame_color,
    command=open_todo,
    anchor="w"
)
todo_button.place(y=200, x=10)

document_button = ctk.CTkButton(
    sideBar,
    text="         Document",
    image=document_img,
    height=40,
    width=230,
    fg_color=frame_color,
    command=open_document,
    anchor="w"
)
document_button.place(y=260, x=10)


reminders_button = ctk.CTkButton(
    sideBar,
    text="      voice assistant",
    image=voice_Assistant_img,
    height=40,
    command=voice_assistant,
    width=230,
    fg_color=frame_color,
    anchor="w"
)
reminders_button.place(y=320, x=10)


chat_button = ctk.CTkButton(
    sideBar,
    text="         ChatBot",
    image=chatbot_icon,
    height=40,
    width=230,
    fg_color=frame_color,
    command=afficher_chat,
    anchor="w"
)
chat_button.place(y=380, x=10)

movie_button = ctk.CTkButton(
    sideBar,
    text="         Movies",
    image=movie_img,
    height=40,
    width=230,
    fg_color=frame_color,
    command=afficher_movie,
    anchor="w"
)
movie_button.place(y=440, x=10)

transaction_button = ctk.CTkButton(
    sideBar,
    text="          Transaction",
    image=transaction_img,
    height=40,
    width=230,
    fg_color=frame_color,
    command=transaction,
    anchor="w"
)
transaction_button.place(y=500, x=10)

app.mainloop()
