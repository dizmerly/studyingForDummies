import customtkinter as ctk
from tkinter import filedialog, messagebox
from quiz_logic import load_questions  # Import from our logic module

""" 
Global variables in order to standardized certain parameters such as delay, 
maybe how certain things interact etc. 

Later down the road these variables will be able to be adjusted by the user in a settings menu
"""

# Global delay (for any action that has an automatic skip, i.e. getting an answer correct/incorrect)
DELAY = 800 





class QuizApp(ctk.CTk):
    """Quiz application using Custom Tkinter"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Studying for Dummies")
        self.geometry("800x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("#E8B45A")
        
        # Application state variables
        self.questions = []
        self.current_question = 0
        self.score = 0
        self.selected_answer = ctk.StringVar()
        
        # Create main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Show start screen
        self.show_start_screen()
    
    def show_start_screen(self):
        """Display the initial screen with file selection."""
        # Clear frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Title
        title = ctk.CTkLabel(
            self.main_frame,
            text="Studying for Dummies ¯\_(ツ)_/¯",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(40, 20))
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Load a quiz file to get started",
            font=ctk.CTkFont(size=16)
        )
        subtitle.pack(pady=(0, 40))
        
        # Load button
        load_btn = ctk.CTkButton(
            self.main_frame,
            text="Upload Quiz File",
            command=self.load_file,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        load_btn.pack(pady=20)
        
        paste_btn = ctk.CTkButton(
            self.main_frame,
            text="Paste Quiz File",
            command=self.load_file,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        paste_btn.pack(pady=10)
        
        # Theme toggle
        theme_btn = ctk.CTkButton(
            self.main_frame,
            text="Toggle Dark/Light Mode",
            command=self.toggle_theme,
            width=200,
            height=40
        )
        theme_btn.pack(side="bottom", anchor="se",pady=10, padx=10)
    
    def toggle_theme(self):
        """Toggle between dark and light mode."""
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
    
    def load_file(self):
        """Open file dialog and load questions."""
        file_path = filedialog.askopenfilename(
            title="Select Quiz File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Use the load_questions function from quiz_logic.py
            self.questions = load_questions(file_path)
            
            if not self.questions:
                messagebox.showerror("Error", "No valid questions found in file!")
                return
            
            # Reset quiz state
            self.current_question = 0
            self.score = 0
            self.show_question()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def show_question(self):
        """Display current question."""
        # Clear frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        q = self.questions[self.current_question]
        total = len(self.questions)
        
        # Progress bar
        progress = ctk.CTkProgressBar(self.main_frame, width=400)
        progress.pack(pady=(20, 10))
        progress.set((self.current_question + 1) / total)
        
        # Progress text
        progress_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Question {self.current_question + 1} of {total} | Score: {self.score}/{self.current_question}",
            font=ctk.CTkFont(size=14)
        )
        progress_label.pack(pady=(0, 20))
        
        # Question card
        question_frame = ctk.CTkFrame(self.main_frame)
        question_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Question text
        question_label = ctk.CTkLabel(
            question_frame,
            text=q['question'],
            font=ctk.CTkFont(size=18, weight="bold"),
            wraplength=600,
            justify="left"
        )
        question_label.pack(pady=20, padx=20)
        
        # Reset selection
        self.selected_answer.set("")
        
        # Choice buttons (radio buttons)
        for letter, text in q['choices']:
            # RADIO BUTTON CHOICES 
            rb = ctk.CTkRadioButton(
                question_frame,
                text=f"{letter}: {text}",
                variable=self.selected_answer,
                value=letter,
                font=ctk.CTkFont(size=16),
                radiobutton_width=20,
                radiobutton_height=20
            )
            rb.pack(pady=10, padx=40, anchor="w")
        
        # Submit button
        submit_btn = ctk.CTkButton(
            self.main_frame,
            text="Submit Answer",
            command=self.check_answer,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        submit_btn.pack(pady=20)
        
        self.feedback_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.feedback_label.pack(pady=(5, 10))
    # Next question helper
    def next_question(self):
        self.current_question += 1
        if self.current_question < len(self.questions):
            self.show_question()
        else:
            self.show_results()

    def check_answer(self):
        """Check if answer is correct and show feedback."""
        if not self.selected_answer.get():
            # FIXME make sure the return statement doesnt prematurely leave question
            self.feedback_label.configure(text="Please select an answer", text_color="yellow")
            return
        
        q = self.questions[self.current_question]
        correct = q['answer']
        user_answer = self.selected_answer.get()
        
        # Update score
        if user_answer == correct:
            self.score += 1
            # FIXME change this to a message inside the application with a popup
            self.feedback_label.configure(text="Correct!", text_color="green")
        else:
            # FIXME change this to a message inside the application with a popup
            self.feedback_label.configure(text=(f"Incorrect. The correct answer is {correct}"), text_color="red")
        
        # Move to next question or show results
        self.after(DELAY, self.next_question)
        
        
    def show_results(self):
        """Display final quiz results."""
        # Clear frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        total = len(self.questions)
        percentage = (self.score / total) * 100
        
        # Results title
        title = ctk.CTkLabel(
            self.main_frame,
            text="🎉 Quiz Complete!",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(40, 20))
        
        # Score display
        score_frame = ctk.CTkFrame(self.main_frame)
        score_frame.pack(pady=30, padx=40, fill="x")
        
        score_label = ctk.CTkLabel(
            score_frame,
            text=f"Your Score: {self.score} / {total}",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        score_label.pack(pady=20)
        
        percentage_label = ctk.CTkLabel(
            score_frame,
            text=f"{percentage:.1f}%",
            font=ctk.CTkFont(size=48, weight="bold")
        )
        percentage_label.pack(pady=10)
        
        # Performance message
        if percentage >= 90:
            message = "Excellent work! 🌟"
        elif percentage >= 70:
            message = "Good job! 👍"
        elif percentage >= 50:
            message = "Not bad! Keep practicing. 📚"
        else:
            message = "Keep studying! You'll do better next time. 💪"
        
        message_label = ctk.CTkLabel(
            self.main_frame,
            text=message,
            font=ctk.CTkFont(size=18)
        )
        message_label.pack(pady=20)
        
        # Buttons
        restart_btn = ctk.CTkButton(
            self.main_frame,
            text="Take Quiz Again",
            command=lambda: self.restart_quiz(),
            width=200,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        restart_btn.pack(pady=10)
        
        new_quiz_btn = ctk.CTkButton(
            self.main_frame,
            text="Load New Quiz",
            command=self.show_start_screen,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        new_quiz_btn.pack(pady=10)
    
    def restart_quiz(self):
        """Restart the current quiz."""
        self.current_question = 0
        self.score = 0
        self.show_question()

# ---------- Run the application ----------
if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()