import sys
# import json # No longer needed for primary data storage
import random
import os

# --- PyQt5 Imports ---
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QAction, QDialog,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QDialogButtonBox,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont


# --- Data Handling Constants ---
FLASHCARD_FILE = 'flashcards.txt' # Default .txt file to try loading
CARD_SEPARATOR_LINE = "%%%"       # Separator for the text file format

# --- Data Handling Functions ---
def load_flashcards_data(filename=FLASHCARD_FILE):
    """Loads flashcards from a custom text file."""
    flashcards = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            current_term = None
            current_definition_lines = []
            for line in f:
                stripped_line = line.strip()
                if stripped_line == CARD_SEPARATOR_LINE:
                    if current_term is not None: # Finalize the previous card
                        definition = "\n".join(current_definition_lines).strip()
                        flashcards.append({"term": current_term, "definition": definition})
                        current_term = None
                        current_definition_lines = []
                elif current_term is None: # This line is a new term
                    if stripped_line: # Make sure term is not an empty line
                        current_term = stripped_line
                else: # This line is part of the current definition
                    current_definition_lines.append(line.rstrip('\n'))

            # Add the last card if the file doesn't end with a separator
            if current_term is not None:
                definition = "\n".join(current_definition_lines).strip()
                flashcards.append({"term": current_term, "definition": definition})

        if not flashcards and os.path.exists(filename) and os.path.getsize(filename) > 0:
            # File existed and had content, but nothing was parsed
            QMessageBox.warning(None, "Load Error", f"No valid flashcards found in '{filename}'. Please check the format.")
            return [] # Return empty list, not defaults
        return flashcards

    except FileNotFoundError:
        print(f"Info: File '{filename}' not found. Starting with no cards loaded.")
        return [] # Return empty list, not defaults
    except Exception as e:
        QMessageBox.critical(None, "Load Error", f"An error occurred parsing '{filename}': {e}. Starting with no cards.")
        return [] # Return empty list

def get_default_cards():
    """Returns an empty list as there are no built-in default cards."""
    return []

def save_flashcards_data(flashcards, filename=FLASHCARD_FILE):
    """Saves the current flashcards to a custom text file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for i, card in enumerate(flashcards):
                f.write(card.get("term", "Unnamed Term").strip() + "\n")
                f.write(card.get("definition", "").strip())
                if i < len(flashcards) - 1:
                    f.write("\n" + CARD_SEPARATOR_LINE + "\n")
                elif card.get("term","").strip():
                     f.write("\n")
        return True
    except Exception as e:
        QMessageBox.critical(None, "Save Error", f"Error saving flashcards to '{filename}': {e}")
        return False

# --- Dialog for Adding New Cards ---
class AddCardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Flashcard")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        self.term_label = QLabel("Term:")
        self.term_input = QLineEdit()
        layout.addWidget(self.term_label)
        layout.addWidget(self.term_input)

        self.def_label = QLabel("Definition:")
        self.def_input = QTextEdit()
        self.def_input.setAcceptRichText(False)
        layout.addWidget(self.def_label)
        layout.addWidget(self.def_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_data(self):
        """Returns the entered term and definition."""
        term = self.term_input.text().strip()
        definition = self.def_input.toPlainText().strip()
        if term:
            return {"term": term, "definition": definition}
        return None

# --- Dialog for Viewing All Cards ---
class ViewCardsDialog(QDialog):
    def __init__(self, flashcards, parent=None):
        super().__init__(parent)
        self.setWindowTitle("View All Flashcards")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        if not flashcards:
            self.list_widget.addItem("No flashcards available.")
        else:
            for i, card in enumerate(flashcards):
                # Assuming cards are dicts with 'term' and 'definition'
                item_text = f"{i + 1}. Term: {card.get('term', 'N/A')}\n   Definition: {card.get('definition', 'N/A')}"
                list_item = QListWidgetItem(item_text)
                self.list_widget.addItem(list_item)
        layout.addWidget(self.list_widget)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button, alignment=Qt.AlignRight)
        self.setLayout(layout)

# --- Main Application Window ---
class FlashcardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flashcards = []
        self.current_deck = []
        self.current_index = -1
        self.definition_visible = False
        self.dirty_flag = False # To track unsaved changes if cards are added/modified

        self.initUI()
        # Try to load the default file on startup
        self.flashcards = load_flashcards_data(FLASHCARD_FILE)
        self.update_initial_display()


    def initUI(self):
        self.setWindowTitle("PyQt5 Flashcard App (TXT File)")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.card_display = QLabel("Load a .txt flashcard file or add new cards!")
        self.card_display.setAlignment(Qt.AlignCenter)
        self.card_display.setFont(QFont('Arial', 18))
        self.card_display.setWordWrap(True)
        self.card_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.card_display)

        self.status_label = QLabel("Card: - / -")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Shuffle & Start")
        self.start_button.clicked.connect(self.start_session)
        self.reveal_button = QPushButton("Reveal Definition")
        self.reveal_button.clicked.connect(self.reveal_definition)
        self.reveal_button.setEnabled(False)
        self.next_button = QPushButton("Next Card")
        self.next_button.clicked.connect(self.next_card)
        self.next_button.setEnabled(False)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.reveal_button)
        button_layout.addWidget(self.next_button)
        main_layout.addLayout(button_layout)

        self.create_menu_bar()
        central_widget.setLayout(main_layout)
        self.update_status() # Initial status update

    def update_initial_display(self):
        if self.flashcards:
             self.card_display.setText(f"Loaded {len(self.flashcards)} cards from '{FLASHCARD_FILE}'.\nPress 'Shuffle & Start'.")
        else:
             self.card_display.setText("No cards loaded. Use 'File > Load' or 'Cards > Add'.")
        self.update_ui_state()


    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')

        load_action = QAction('&Load Cards...', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.load_cards_action_triggered)
        file_menu.addAction(load_action)

        save_action = QAction('&Save Cards', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_cards_action_triggered)
        file_menu.addAction(save_action)

        save_as_action = QAction('Save Cards &As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_cards_as_action_triggered)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()
        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        card_menu = menu_bar.addMenu('&Cards')
        add_action = QAction('&Add New Card...', self)
        add_action.setShortcut('Ctrl+N')
        add_action.triggered.connect(self.add_card_dialog_triggered)
        card_menu.addAction(add_action)

        view_action = QAction('&View All Cards...', self)
        view_action.triggered.connect(self.view_cards_dialog_triggered)
        card_menu.addAction(view_action)

        help_menu = menu_bar.addMenu('&Help')
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about_dialog_triggered)
        help_menu.addAction(about_action)

    def load_cards_action_triggered(self):
        if self.dirty_flag:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                       "You have unsaved changes. Load new file anyway?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Flashcards from Text File", "",
                                                  "Text Files (*.txt);;All Files (*)", options=options)
        if fileName:
            loaded_cards = load_flashcards_data(fileName)
            if loaded_cards is not None: # load_flashcards_data returns [] on error/not found
                self.flashcards = loaded_cards
                self.current_deck = []
                self.current_index = -1
                self.definition_visible = False
                self.dirty_flag = False # Reset dirty flag after successful load
                self.update_ui_state()
                if self.flashcards:
                    self.card_display.setText(f"Loaded {len(self.flashcards)} cards from '{os.path.basename(fileName)}'.\nPress 'Shuffle & Start'.")
                    QMessageBox.information(self, "Load Successful", f"Loaded {len(self.flashcards)} cards from {os.path.basename(fileName)}.")
                else: # File was valid but empty, or parsing resulted in no cards
                    self.card_display.setText(f"No cards found in '{os.path.basename(fileName)}'. Add new cards or load another file.")
                    QMessageBox.information(self, "Load Info", f"No flashcards were found in '{os.path.basename(fileName)}'.")
            # If load_flashcards_data returned None (shouldn't with current logic, returns []), handle explicitly if needed
        # else: User cancelled dialog, do nothing to current flashcards

    def save_cards_action_triggered(self):
        if not self.flashcards:
            QMessageBox.information(self, "No Cards", "There are no cards to save.")
            return
        if save_flashcards_data(self.flashcards, FLASHCARD_FILE): # Save to default file
             self.dirty_flag = False
             QMessageBox.information(self, "Save Successful", f"Saved {len(self.flashcards)} cards to {FLASHCARD_FILE}.")

    def save_cards_as_action_triggered(self):
        if not self.flashcards:
            QMessageBox.information(self, "No Cards", "There are no cards to save.")
            return
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Flashcards As...", "",
                                                  "Text Files (*.txt);;All Files (*)", options=options)
        if fileName:
            if not fileName.lower().endswith('.txt'):
                fileName += '.txt'
            if save_flashcards_data(self.flashcards, fileName):
                self.dirty_flag = False
                QMessageBox.information(self, "Save Successful", f"Saved {len(self.flashcards)} cards to {os.path.basename(fileName)}.")

    def add_card_dialog_triggered(self):
        dialog = AddCardDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_card_data = dialog.get_data()
            if new_card_data:
                if any(card['term'].lower() == new_card_data['term'].lower() for card in self.flashcards):
                     QMessageBox.warning(self, "Duplicate Term", f"The term '{new_card_data['term']}' already exists. Card not added.")
                else:
                    self.flashcards.append(new_card_data)
                    self.dirty_flag = True
                    self.update_ui_state()
                    if not self.current_deck: # If no session was active, update display
                        self.card_display.setText(f"Card '{new_card_data['term']}' added. Press 'Shuffle & Start'.")
                    QMessageBox.information(self, "Card Added", f"Card '{new_card_data['term']}' added successfully.")
            else:
                 QMessageBox.warning(self, "Input Error", "Term must be provided.")

    def view_cards_dialog_triggered(self):
        if not self.flashcards:
            QMessageBox.information(self, "No Cards", "There are no cards to view. Load or add some first.")
            return
        dialog = ViewCardsDialog(self.flashcards, self)
        dialog.exec_()

    def show_about_dialog_triggered(self):
        QMessageBox.about(self, "About Flashcard App",
                          "Simple Flashcard Application\nVersion 1.2 (TXT File Only)\n\n"
                          "Helps you study terms and definitions from text files.")

    def start_session(self):
        if not self.flashcards:
            QMessageBox.warning(self, "No Cards", "Please load a .txt file or add some flashcards first.")
            return

        self.current_deck = self.flashcards[:]
        random.shuffle(self.current_deck)
        self.current_index = 0
        self.definition_visible = False
        self.display_current_card()
        self.update_ui_state()

    def reveal_definition(self):
        if self.current_index != -1 and self.current_deck:
            self.definition_visible = True
            self.display_current_card()
            self.update_ui_state()

    def next_card(self):
        if self.current_index != -1 and self.current_deck:
            self.current_index += 1
            if self.current_index < len(self.current_deck):
                self.definition_visible = False
                self.display_current_card()
            else:
                self.card_display.setText("🎉 Deck Finished! 🎉\n\nPress 'Shuffle & Start' or load new cards.")
                self.current_index = -1 # Reset index
                # self.current_deck = [] # Optionally clear current deck
            self.update_ui_state()

    def display_current_card(self):
        if 0 <= self.current_index < len(self.current_deck):
            card = self.current_deck[self.current_index]
            display_text = f"Term:\n\n{card['term']}"
            if self.definition_visible:
                display_text += f"\n\n{'-'*20}\n\nDefinition:\n\n{card['definition']}"
            self.card_display.setText(display_text)
        elif not self.current_deck and self.flashcards:
             self.card_display.setText("Press 'Shuffle & Start' to begin.")
        elif not self.flashcards:
             self.card_display.setText("No cards loaded. Use 'File > Load' or 'Cards > Add'.")
        self.update_status()


    def update_status(self):
        total_in_session = len(self.current_deck) if self.current_deck else 0
        current_num_in_session = self.current_index + 1 if self.current_index != -1 and self.current_deck else 0
        total_all = len(self.flashcards)
        status_text = f"Card: {current_num_in_session} / {total_in_session} (in session) | Total loaded: {total_all}"
        if self.dirty_flag:
             status_text += " *"
        self.status_label.setText(status_text)

    def update_ui_state(self):
        """Enable/disable buttons based on the application state."""
        has_cards = bool(self.flashcards)
        in_session = self.current_index != -1 and bool(self.current_deck)

        self.start_button.setEnabled(has_cards)
        self.reveal_button.setEnabled(in_session and not self.definition_visible)
        self.next_button.setEnabled(in_session and self.definition_visible)
        self.update_status()

    def closeEvent(self, event):
        """Overrides the default close event to check for unsaved changes."""
        if self.dirty_flag:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                       "You have unsaved changes. Save before exiting?",
                                       QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                       QMessageBox.Save)
            if reply == QMessageBox.Save:
                if not self.flashcards: # Should not happen if dirty_flag is true, but good check
                    event.accept()
                    return
                if not save_flashcards_data(self.flashcards, FLASHCARD_FILE):
                    event.ignore() # Don't close if save failed
                    return
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else: # Cancel
                event.ignore()
        else:
            event.accept()

# --- Main Execution ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = FlashcardApp()
    main_win.show()
    sys.exit(app.exec_())
