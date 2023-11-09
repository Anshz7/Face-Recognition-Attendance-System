import tkinter as tk
from tkinter import *
import util
import cv2
from PIL import Image, ImageTk
import os.path
import datetime
import subprocess
import mysql.connector

class App:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.title('Face Attendance System')
        self.main_window.configure(bg='#FFFADD')
        self.main_window.geometry("1200x520+350+100")

        self.login_button_main_window = util.get_button(self.main_window, 'Login', '#22668D', self.login)
        self.login_button_main_window.place(x=750, y=100)
        self.register_new_user_button_main_window = util.get_button(self.main_window, 'Register New User', '#FFCC70',
                                                                    self.register_new_user, fg='black')
        self.register_new_user_button_main_window.place(x=750, y=200)
        self.show_logs_button_main_window = util.get_button(self.main_window, 'Logs', '#22668D', self.log)
        self.show_logs_button_main_window.place(x=750, y=300)

        self.clear_logs_button_main_window = util.get_button(self.main_window, 'Clear Logs', '#FFCC70',
                                                                    self.clear_logs, fg='black')
        self.clear_logs_button_main_window.place(x=750, y=400)

        self.webcam_label = util.get_img_label(self.main_window)
        self.webcam_label.place(x=10, y=0, width=700, height=500)

        self.add_webcam(self.webcam_label)

        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)

        self.log_path = './log.txt'

        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='ansh',
            database='attendance_db'
        )
        self.cursor = self.conn.cursor(buffered=True)
        self.cursor = self.conn.cursor()
        self.create_mysql_table()

    def add_webcam(self, label):
        if 'cap' not in self.__dict__:
            self.cap = cv2.VideoCapture(0)

        self._label = label
        self.process_webcam()

    def process_webcam(self):
        ret, frame = self.cap.read()
        self.most_recent_capture_arr = frame

        face_cap = cv2.CascadeClassifier(r"C:\Users\Ansh Shrivastava\Desktop\app project py\haarcascade_frontalface_default.xml")
        col = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cap.detectMultiScale(col, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        img_ = cv2.cvtColor(self.most_recent_capture_arr, cv2.COLOR_BGR2RGB)
        self.most_recent_capture_pil = Image.fromarray(img_)

        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)

        self._label.imgtk = imgtk
        self._label.configure(image=imgtk)

        self._label.after(20, self.process_webcam)

    def login(self):
        unknown_img_path = './.tmp.jpg'

        cv2.imwrite(unknown_img_path, self.most_recent_capture_arr)
        output = str(subprocess.check_output(['face_recognition', self.db_dir, unknown_img_path]))
        name = output.split(",")[1][:-5]
        current_date = datetime.datetime.now().strftime("%d/%m/%y")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if name in ["unknown_person", "no_persons_found"]:
            util.msg_box("Oops", "Unknown user. Please register as a user or try again.")
        else:
            util.msg_box("Welcome", "Welcome, {}".format(name))
            self.insert_log_to_mysql(name, current_date, current_time)
        os.remove(unknown_img_path)

    def register_new_user(self):
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.geometry("1200x520+370+120")
        self.register_new_user_window.title('Register New User')
        self.register_new_user_window.configure(bg='#FFFADD')

        self.accept_button_register_new_user_window = util.get_button(self.register_new_user_window, 'Accept',
                                                                      '#22668D', self.accept_register_new_user)
        self.accept_button_register_new_user_window.place(x=750, y=300)
        self.try_again_button_register_new_user_window = util.get_button(self.register_new_user_window, 'Try Again',
                                                                         '#8ECDDD', self.try_again_register_new_user,
                                                                         fg='black')
        self.try_again_button_register_new_user_window.place(x=750, y=400)

        self.capture_label = util.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=0, width=700, height=500)

        self.add_img_to_label(self.capture_label)

        self.entry_text_register_new_user = util.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user.place(x=750, y=150)

        self.text_label_register_new_user = util.get_text_label(self.register_new_user_window, 'Input Username:')
        self.text_label_register_new_user.place(x=750, y=70)

    def try_again_register_new_user(self):
        self.register_new_user_window.destroy()

    def add_img_to_label(self, label):
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        label.imgtk = imgtk
        label.configure(image=imgtk)
        self.register_new_user_capture = self.most_recent_capture_arr.copy()

    def accept_register_new_user(self):
        name = self.entry_text_register_new_user.get(1.0, "end-1c")
        cv2.imwrite(os.path.join(self.db_dir, '{}.jpg'.format(name)), self.register_new_user_capture)
        util.msg_box('Success', 'User Registered Successfully')
        self.register_new_user_window.destroy()

    def clear_logs(self):
        clear_query = "DELETE FROM attendance_logs"
        self.cursor.execute(clear_query)
        self.conn.commit()
        util.msg_box("Logs Cleared", "Attendance logs have been cleared.")
    def create_mysql_table(self):
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS attendance_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL
            )
        '''
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def insert_log_to_mysql(self, name, date, time):
        insert_query = "INSERT INTO attendance_logs (name, date, time) VALUES (%s, %s, %s)"
        data = (name, date, time)
        self.cursor.execute(insert_query, data)
        self.conn.commit()

    def log(self):
        self.logs_window = tk.Toplevel(self.main_window)
        self.logs_window.geometry("720x720+800+100")
        self.logs_window.title('Attendance Logs')
        self.logs_window.configure(bg='#FFFADD')

        query = "SELECT name, date, time FROM attendance_logs"
        self.cursor.execute(query)
        logs_data = self.cursor.fetchall()

        log_text = ""
        for row in logs_data:
            name, date, time = row
            log_text += f"name= {name} || date= {date} || time= {time}\n"

        lab = Label(self.logs_window, text=log_text, font=('arial 20'))
        lab.pack()

    def start(self):
        self.main_window.mainloop()

    def __del__(self):
        # Close the cursor and connection explicitly
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

if __name__ == "__main__":
    app = App()
    app.start()