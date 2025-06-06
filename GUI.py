import tkinter as tk
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from style import STYLE
from PIL import Image, ImageTk
import platform

from main import analyze
path_destination = ""
path_files = ()
root = tk.Tk()
root.title("Column Detector")
# root.attributes("-fullscreen",True)
if platform.system() == "Windows":
    root.state('zoomed')  # Windows: Maximized with title bar
else:
    # macOS/Linux fallback
    root.attributes('-zoomed', True)
root.config(background = "lightgray")
root.update()
image_path = "./assets/logo.jpg"
image = Image.open(image_path)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

target_height = int(screen_height * 0.3)
aspect_ratio = image.width / image.height
target_width = int(target_height * aspect_ratio)
image = image.resize((target_width, target_height))

# Convert to Tkinter-compatible image
photo = ImageTk.PhotoImage(image)
image_label = tk.Label(root, image=photo, bg='white')
image_label.place(relx=0.5, rely=0.3, anchor='center')
# Create a button with active background and foreground colors
# Set window size

 
#Set window background color
label = tk.Label(root, text="To use this software, follow these simple steps: \n 1- Select the target file with h5 format \n Select the target folder to save the results in \n 3- Run the program", fg="black",font="monospace")

# Create an Entry widget with selection colors
entry = tk.Entry(root, selectforeground="black")

def browseFiles():
    global path_files
    path_files = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("h5",
                                                        "*.h5*"),
                                                       ("all files",
                                                        "*.*")))
    print(len(path_files))
    if path_files[-3:] == ".h5":
        toggle_Start_Btn()
    else:
        messagebox.showwarning("Warning", "Please select a file with correct h5 format")
        path_files = ""
    
def selectDestination():
    global path_destination
    path_destination = filedialog.askdirectory(initialdir="/",mustexist=True)
    print(path_destination)
    toggle_Start_Btn()
def analyzeFiles():
    print("start")
    analyze(path_files,path_destination,updateProgressbar)
    button_start.configure(state="disabled")
    
    # root.after(0, showProgressBar)
def showProgressBar():
    progress_bar.place(relx=0.5,rely=0.9,anchor="center")
def updateProgressbar(percent):
    progress_bar.config(value=percent)
    print("callback {}".format(percent))
    if percent >= 100:
        print("DONEEEEEEEEE")
        # progress_bar.place_forget()
        root.after(3000, progress_bar.place_forget)
        messagebox.showinfo("Info", "Analysis is done, please check the destination folder to find your results.")
    global path_files
    path_files = ""
    global path_destination
    path_destination = ""
    toggle_Start_Btn()
    
        
def toggle_Start_Btn():
    if not(path_destination == "") and not(path_files == ""):
        button_start.config(state="normal")
    else:
        button_start.config(state="disabled")
        
button_explore = Button(root, 
                        text = "Browse Files",
                        command = browseFiles,
                        padx=STYLE['padding'])
button_destination = Button(root, 
                        text = "Select destination folder",
                        padx=STYLE['padding'],
                        command = selectDestination)
button_start = Button(root, 
                     text = "Start",
                     command = analyzeFiles,default='disabled',
                     padx=STYLE['padding'])
progress_bar = ttk.Progressbar(root, mode='indeterminate', length=250)
progress_bar.configure(maximum=100)
toggle_Start_Btn()

# label.grid(column = 1, row = 1)
label.place(relx=0.5, rely=0.6, anchor='center')
button_explore.place(relx=0.3, rely=0.7, anchor='center')
button_destination.place(relx=0.7, rely=0.7, anchor='center')
button_start.place(relx=0.5, rely=0.8, anchor='center')
# button_explore.grid(column = 1, row = 2)
# button_destination.grid(column=2,row=2)
# button_start.grid(column = 1,row = 3)
root.mainloop()
