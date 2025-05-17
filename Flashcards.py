import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkbootstrap import Style
import random # Import the random module for shuffling
from PIL import Image, ImageTk # Import Image and ImageTk from Pillow

# Create database tables if they don't exist
def create_tables(conn):
    cursor = conn.cursor()

    # Create flashcard_sets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcard_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
        )
    ''')

    # Create flashcards table with foreign key reference to flashcard_sets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            definition TEXT NOT NULL,
            FOREIGN KEY (set_id) REFERENCES flashcard_sets(id)
        )
    ''')

# Add a new flashcard set to the database
def add_set(conn, name):
    cursor = conn.cursor()

    # Insert the set name into flashcard_sets table
    cursor.execute('''
        INSERT INTO flashcard_sets (name)
        VALUES (?)
    ''', (name,))

    set_id = cursor.lastrowid
    conn.commit()

    return set_id

# Function to add a flashcard to the database
def add_card(conn, set_id, word, definition):
    cursor = conn.cursor()

    # Execute SQL query to insert a new flashcard into the database
    cursor.execute('''
        INSERT INTO flashcards (set_id, word, definition)
        VALUES (?, ?, ?)
    ''', (set_id, word, definition))

    # Get the ID of the newly inserted card
    card_id = cursor.lastrowid
    conn.commit()

    return card_id

# Function to retrieve all flashcard sets from the database
def get_sets(conn):
    cursor = conn.cursor()

    # Execite SQL query to fetch all flashcard sets
    cursor.execute('''
        SELECT id, name FROM flashcard_sets
    ''')

    rows = cursor.fetchall()
    sets = {row[1]: row[0] for row in rows} # Create a dictionary of sets (name: id)

    return sets

# Function to retrieve all flashcards of a specific set
def get_cards(conn, set_id):
    cursor = conn.cursor()

    cursor.execute('''
        SELECT word, definition FROM flashcards
        WHERE set_id = ?
    ''', (set_id,))

    rows = cursor.fetchall()
    cards = [(row[0], row[1]) for row in rows] # Create a list of cards (word, definition)

    return cards

# Function to delete a flashcard set from the database
def delete_set(conn, set_id):
    cursor = conn.cursor()

    # Execute SQL query to delete a flashcard set
    cursor.execute('''
        DELETE FROM flashcard_sets
        WHERE id = ?
    ''', (set_id,))

    conn.commit()
    sets_combobox.set('')
    clear_flashcard_display()
    populate_sets_combobox()

    # Clear the current_cards list and reset card_index
    global current_cards, card_index
    current_cards = []
    card_index = 0

# Function to create a new flashcard set
def create_set():
    set_name = set_name_var.get()
    if set_name:
        if set_name not in get_sets(conn):
            set_id = add_set(conn, set_name)
            populate_sets_combobox()
            set_name_var.set('')

            # Clear the input fields
            set_name_var.set('')
            word_var.set('')
            definition_var.set('')

def add_word():
    set_name = set_name_var.get()
    word = word_var.get()
    definition = definition_var.get()

    if set_name and word and definition:
        if set_name not in get_sets(conn):
            set_id = add_set(conn, set_name)
        else:
            set_id = get_sets(conn)[set_name]

        add_card(conn, set_id, word, definition)

        word_var.set('')
        definition_var.set('')

        populate_sets_combobox()

def populate_sets_combobox():
    sets_combobox['values'] = tuple(get_sets(conn).keys())

# Function to delete a selected flashcard set
def delete_selected_set():
    set_name = sets_combobox.get()

    if set_name:
        result = messagebox.askyesno(
            'Confirmation', f'Are you sure you want to delete the "{set_name}" set?'
        )

        if result == tk.YES:
            set_id = get_sets(conn)[set_name]
            delete_set(conn, set_id)
            populate_sets_combobox()
            clear_flashcard_display()

def select_set():
    set_name = sets_combobox.get()

    if set_name:
        set_id = get_sets(conn)[set_name]
        cards = get_cards(conn, set_id)

        if cards:
            display_flashcards(cards)
            # Automatically shuffle when a new set is selected
            shuffle_cards()
        else:
            word_label.config(text="No cards in this set")
            definition_label.config(text='')
    else:
        # Clear the current cards list and reset card index
        global current_cards, card_index
        current_cards = []
        card_index = 0
        clear_flashcard_display()

def display_flashcards(cards):
    global card_index
    global current_cards

    card_index = 0
    current_cards = cards

    # Clear the display
    if not cards:
        clear_flashcard_display()
    else:
        show_card()

    show_card()

def clear_flashcard_display():
    word_label.config(text='')
    definition_label.config(text='')

# Function to display the current flashcards word
def show_card():
    global card_index
    global current_cards

    if current_cards:
        if 0 <= card_index < len(current_cards):
            word, _ = current_cards[card_index]
            word_label.config(text=word)
            definition_label.config(text='') # Hide definition when showing word
        else:
            clear_flashcard_display()
    else:
        clear_flashcard_display()

# Function to flip the current card and display its definition
def flip_card():
    global card_index
    global current_cards

    if current_cards:
        if 0 <= card_index < len(current_cards):
            _, definition = current_cards[card_index]
            definition_label.config(text=definition)
        else:
            definition_label.config(text='')


# Function to move to the next card
def next_card():
    global card_index
    global current_cards

    if current_cards:
        card_index = min(card_index + 1, len(current_cards) -1)
        show_card()

# Function to move to the previous card
def prev_card():
    global card_index
    global current_cards

    if current_cards:
        card_index = max(card_index - 1, 0)
        show_card()

# Function to shuffle the current flashcards
def shuffle_cards():
    global current_cards, card_index
    if current_cards:
        random.shuffle(current_cards)
        card_index = 0 # Reset to the first card after shuffling
        show_card()
        messagebox.showinfo("Shuffle", "Cards have been shuffled!")
    else:
        messagebox.showinfo("Shuffle", "No cards to shuffle in the current set.")


if __name__ == '__main__':
    # Connect to the SQLite database and create tables
    conn = sqlite3.connect('flashcards.db')
    create_tables(conn)

    # Create the main GUI window
    root = tk.Tk()
    from tkinter import PhotoImage
    # Ensure the image file exists at this path or use a relative path
    try:
        icon = PhotoImage(file='D:\Downloads\CC15Flashcards\FlashMe.png')
        root.iconphoto(True, icon)
    except tk.TclError:
        print("Warning: Icon file not found at D:\Downloads\CC15Flashcards\FlashMe.png")

    root.title('FlashMe!')
    root.geometry('500x550') # Increased height slightly to accommodate the card box and footer
    root.resizable(False, False)

    # Apply styling to the GUI elements
    style = Style(theme='darkly')
    style.configure('TLabel', font=('TkHeadingFont', 18))
    style.configure('TButton', font=('TkDefaultFont', 16))

    # Set up variables for storing user input
    set_name_var = tk.StringVar()
    word_var = tk.StringVar()
    definition_var = tk.StringVar()

    # Create a notebook widget to manage tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10) # Added padding

    # Create the "Create Set" tab and its content
    create_set_frame = ttk.Frame(notebook, padding="10") # Added padding
    notebook.add(create_set_frame, text='Create Set')

    # Label and Entry widgets for entering set name, word and definition
    ttk.Label(create_set_frame, text='Set Name').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Question').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=word_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Definition').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=definition_var, width=30).pack(padx=5, pady=5)

    # Button to add a word to the set
    ttk.Button(create_set_frame, text='Add Question', command=add_word, bootstyle='light').pack(padx=5, pady=10)

    # Button to save the set
    ttk.Button(create_set_frame, text='Save Set', command=create_set, bootstyle='light').pack(padx=5, pady=10)

    # Create the "Select Set" tab and its content
    select_set_frame = ttk.Frame(notebook, padding="10") # Added padding
    notebook.add(select_set_frame, text="Select Set")

    # Combobox widget for selecting existing flashcard sets
    sets_combobox = ttk.Combobox(select_set_frame, state='readonly', width=27) # Adjusted width
    sets_combobox.pack(padx=5, pady=20) # Adjusted padding

    # Button to select a set
    ttk.Button(select_set_frame, text='Select Set', command=select_set, bootstyle='light').pack(padx=5, pady=5)

    # Button to delete a set
    ttk.Button(select_set_frame, text='Delete Set', command=delete_selected_set, bootstyle='light').pack(padx=5, pady=5)

    # Create the "Learn mode" tab and its content
    flashcards_frame = ttk.Frame(notebook, padding="10") # Added padding
    notebook.add(flashcards_frame, text='Learn Mode')

    # Initialize variables for tracking card index and current cards
    card_index = 0
    current_cards = [] # Initialize current_cards list

    # Frame to act as the "card" box
    # Enhanced styling for a more card-like appearance
    card_box_frame = ttk.Frame(flashcards_frame, relief='raised', borderwidth=3, padding="40") # Increased borderwidth and padding
    card_box_frame.pack(pady=20, fill='both', expand=True) # Added padding and expand

    # Label to display the word on flashcards
    word_label = ttk.Label(card_box_frame, text='', font=('TkHeadingFont', 24), wraplength=400, anchor='center', justify='center') # Added anchor and justify
    word_label.pack(padx=10, pady=10)

    # Label to display the definition on flashcards
    definition_label = ttk.Label(card_box_frame, text='', wraplength=400, anchor='center', justify='center') # Added anchor and justify
    definition_label.pack(padx=10, pady=10)

    # Frame for the control buttons
    control_frame = ttk.Frame(flashcards_frame)
    control_frame.pack(pady=10)

    # Button to flip the flashcard
    ttk.Button(control_frame, text='Flip', command=flip_card, bootstyle='light').pack(side='left', padx=5)

    # Button to view the previous flashcard
    ttk.Button(control_frame, text='Previous', command=prev_card, bootstyle='light').pack(side='left', padx=5)

    # Button to view the next flashcard
    ttk.Button(control_frame, text='Next', command=next_card, bootstyle='light').pack(side='left', padx=5)

    # Button to shuffle the cards
    ttk.Button(control_frame, text='Shuffle', command=shuffle_cards, bootstyle='light').pack(side='left', padx=5)


    populate_sets_combobox()

    # Added error handling for the footer image loading
    try:
        # Open and resize the image
        original_image = Image.open('D:\Downloads\CC15Flashcards\FlashMe2.png')
        resized_image = original_image.resize((75, 75))  # Resize to fit at bottom
        footer_image = ImageTk.PhotoImage(resized_image)

        # Create and pack a label for the image
        footer_label = ttk.Label(root, image=footer_image)
        footer_label.image = footer_image  # Keep a reference to avoid garbage collection
        footer_label.pack(side='bottom', pady=10)
    except FileNotFoundError:
        print("Warning: Footer image file not found at D:\Downloads\CC15Flashcards\FlashMe2.png")
    except ImportError:
        print("Warning: Pillow library not found. Install it with 'pip install Pillow' to display the footer image.")


    root.mainloop()
