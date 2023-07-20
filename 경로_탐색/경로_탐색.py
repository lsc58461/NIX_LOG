#pyinstaller --onefile --icon=.\NIX.ico --add-data "NanumSquareRoundL.ttf;." main.py
import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import font
import pkg_resources

# 롤과 크롬의 실행 파일 이름
LOL_EXE = "LeagueClient.exe"
CHROME_EXE = "chrome.exe"

# 검색할 폴더 리스트
SEARCH_FOLDERS = [
    "C:\Riot Games",
    "D:\Riot Games",
    "E:\Riot Games",
    "C:\Program Files\Google\Chrome\Application",
    "C:\Program Files (x86)\Google\Chrome\Application",
    "D:\Program Files\Google\Chrome\Application",
    "D:\Program Files (x86)\Google\Chrome\Application",
    "E:\Program Files\Google\Chrome\Application",
    "E:\Program Files (x86)\Google\Chrome\Application",
    "C:\Program Files",
    "C:\Program Files (x86)",
    "D:\Program Files",
    "D:\Program Files (x86)",
    "E:\Program Files",
    "E:\Program Files (x86)"
]

def search_file(file_name):
    for folder in SEARCH_FOLDERS:
        print(folder)
        for root, dirs, files in os.walk(folder):
            print(root, dirs, files)
            if file_name in files:
                return os.path.join(root + '\\'+ file_name)

    for drive in range(ord('A'), ord('Z')+1):
        drive = chr(drive) + ":\\"
        print(drive)
        for root, dirs, files in os.walk(drive):
            print(root, dirs, files)
            if file_name in files:
                return os.path.join(root + '\\'+ file_name)

    return None

def copy_to_clipboard(text, type):
    if type == 'LOL':
        type == '롤'
    elif type == 'Chrome':
        type == '크롬'
    window.clipboard_clear()
    window.clipboard_append(text)
    window.update()
    copied_label = tk.Label(window, text=f"{type} 경로가 복사되었습니다.", fg="green", bg='white', font=custom_font)
    copied_label.pack(pady=5)
    window.after(1500, lambda: copied_label.destroy())

def search_and_display_path():
    # 결과 레이블 초기화
    lol_result_label.config(text="", font=custom_font)
    chrome_result_label.config(text="", font=custom_font)
    
    search_button.config(state=tk.DISABLED)

    if lol_var.get():
        lol_result = search_file(LOL_EXE)

        if lol_result:
            print('롤 경로 검색 완료')
            lol_result_label.config(text="롤 경로:\n{}\n클릭하면 클립보드에 복사됩니다.".format(lol_result), fg="green", font=custom_font)
            lol_result_label.bind("<Button-1>", lambda e: copy_to_clipboard(lol_result, 'LOL'))
        else:
            print('롤 경로를 찾을 수 없습니다.')
            lol_result_label.config(text="롤 경로를 찾을 수 없습니다.", fg="red", font=custom_font)

    if chrome_var.get():
        chrome_result = search_file(CHROME_EXE)

        if chrome_result:
            print('크롬 경로 검색 완료')
            chrome_result_label.config(text="크롬 경로:\n{}\n클릭하면 클립보드에 복사됩니다.".format(chrome_result), fg="green", font=custom_font)
            chrome_result_label.bind("<Button-1>", lambda e: copy_to_clipboard(chrome_result, 'Chrome'))
        else:
            print('크롬 경로를 찾을 수 없습니다.')
            chrome_result_label.config(text="크롬 경로를 찾을 수 없습니다.", fg="red", font=custom_font)

    search_button.config(state=tk.NORMAL)

# PyInstaller로 패키징된 실행 파일에서 리소스 파일의 경로를 제대로 찾을 수 있도록 돕는 역할
def get_file_path(filename):
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller로 패키징된 실행 파일에서 실행 중인 경우
        # _MEIPASS는 PyInstaller가 임시로 리소스를 추출하는 디렉토리를 가리키는 환경 변수입니다.
        print(f'get_file_path : {os.path.join(sys._MEIPASS, filename)}')
        print('실행 파일 내부')
        # _MEIPASS 디렉토리 경로와 파일명을 합쳐서 반환합니다.
        return os.path.join(sys._MEIPASS, filename)
    else:
        # 일반적인 파이썬 스크립트로 실행 중인 경우
        # 현재 스크립트의 디렉토리 경로를 얻습니다.
        print(f'get_file_path : {os.path.dirname(os.path.abspath(__file__))}\\{filename}')
        # 스크립트의 경로와 파일명을 합쳐서 반환합니다.
        return os.path.dirname(os.path.abspath(__file__)) + "\\" + filename


# GUI를 생성합니다.
window = tk.Tk()

# 폰트 파일 경로 설정
font_file = "NanumSquareRoundL.ttf"
font_path = get_file_path(font_file)
print(font_path)

# 창의 크기와 위치 설정
window_width = 450
window_height = 200
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x_coordinate = int((screen_width / 2) - (window_width / 2))
y_coordinate = int((screen_height / 2) - (window_height / 2))
window.geometry("{}x{}+{}+{}".format(window_width, window_height, x_coordinate, y_coordinate))
window.configure(bg='white')

# 창의 타이틀 설정
window.title("롤 경로 검색")

# 새로운 폰트 객체 생성
custom_font = font.Font(family="나눔스퀘어라운드 Light", size=10)

# 롤 체크 박스 생성
lol_var = tk.BooleanVar()
lol_var.set(True)
lol_checkbox = ttk.Checkbutton(window, text="롤", variable=lol_var, onvalue=True, offvalue=False, style="my.TCheckbutton")
lol_checkbox.place(x=185, y=10)

# 크롬 체크 박스 생성
chrome_var = tk.BooleanVar()
chrome_var.set(True)
chrome_checkbox = ttk.Checkbutton(window, text="크롬", variable=chrome_var, onvalue=True, offvalue=False, style="my.TCheckbutton")
chrome_checkbox.place(x=225, y=10)

style = ttk.Style()
style.configure("my.TCheckbutton", foreground="black", background="white", font=custom_font)

# 검색 버튼 생성
search_button = ttk.Button(window, text="검색", command=search_and_display_path, style="my.TButton")
style = ttk.Style()
style.configure("my.TButton", foreground="black", background="white", font=custom_font, borderwidth=10, focuscolor="none", focusthickness=0, padding=10)
search_button.place(x=170, y=40)

# 검색 결과 출력 레이블 생성 - 롤
lol_result_label = tk.Label(window, text="", font=custom_font, width=56, height=3, anchor='center')
lol_result_label.place(x=1, y=85)

# 검색 결과 출력 레이블 생성 - 크롬
chrome_result_label = tk.Label(window, text="", font=custom_font, width=56, height=3, anchor='center')
chrome_result_label.place(x=1, y=135)

# GUI를 실행합니다
print('롤 경로 검색 대기 중 입니다.')
window.mainloop()