import sys
from Tkinter import *


def clickAbout():
    toplevel = Toplevel()
    label1 = Label(toplevel, text=msg, height=0, width=100)
    label1.pack()

app = Tk()
app.title("Have you pre-processed the las files already?")
app.geometry("500x130")

msg = '''
The output directory already contains pre-processed files.  Do you wish to 
continue with pre-processing the las files (and overwrite any existing files),
or do you want to use the existing pre-processed files and skip this step?'''

yes_bttn_msg = 'Continue with pre-processing (i.e., overwrite any existing files'
no_bttn_msg = 'Skip this step (i.e., use existing pre-processed files)'

label = Label(app, text=msg, height=0, width=100)
b = Button(app, text=no_bttn_msg, width=50, command=app.destroy)
button1 = Button(app, text=yes_bttn_msg, width=50, command=clickAbout)
label.pack()
b.pack(side='bottom', padx=0, pady=0)
button1.pack(side='bottom', padx=5, pady=5)

app.mainloop()
