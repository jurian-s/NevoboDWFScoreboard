import requests
from PySide6 import QtWidgets as QtW
from PySide6.QtCore import QThread, QTimer, Signal, QDate, QObject, QLocale, Qt
from PySide6.QtGui import QShortcut, QKeySequence, QColor


class settingsWindow(QtW.QWidget):
    isScoreboardActive = False
    def __init__(self):
        super().__init__()
        Layout = QtW.QGridLayout(self)
        self.MatchList = {}
        self.searchparams = {
                        "sporthal": "/accommodatie/sporthallen/tu-sportcentrum",
                       "datum[after]": QDate().currentDate().toString("dd-MM-yyyy"),
                       "datum[before]": QDate().currentDate().toString("dd-MM-yyyy")}
        self.datumkiezerafter = QtW.QDateEdit(calendarPopup=True)
        self.datumkiezerafter.setLocale(QLocale("Dutch"))
        self.datumkiezerafter.setDate(QDate.currentDate())
        self.datumkiezerbefore = QtW.QDateEdit(calendarPopup=True)
        self.datumkiezerbefore.setLocale(QLocale("Dutch"))
        self.datumkiezerbefore.setDate(QDate.currentDate())
        Layout.addWidget(QtW.QLabel("Search for games from: "), 0, 0)
        Layout.addWidget(self.datumkiezerafter, 0, 1)
        Layout.addWidget(QtW.QLabel(" till "), 0, 2)
        Layout.addWidget(self.datumkiezerbefore, 0, 3)
        querymatchesbutton = QtW.QPushButton("query")
        querymatchesbutton.clicked.connect(self.queryMatches)
        Layout.addWidget(querymatchesbutton, 1, 2, 1, 2)
        self.MatchSelect = QtW.QComboBox()
        Layout.addWidget(self.MatchSelect, 2, 0, 1, 4)
        self.startScoreboardButton = QtW.QPushButton("Start scoreboard")
        self.startScoreboardButton.clicked.connect(self.toggleScoreboard)
        Layout.addWidget(self.startScoreboardButton, 3, 2, 1, 2)
        self.colorpicker1 = QtW.QColorDialog()
        self.colorpicker2 = QtW.QColorDialog()
        self.colorButton1 = QtW.QPushButton("Team 1 Color")
        self.colorButton2 = QtW.QPushButton("Team 2 Color")
        self.colorButton1.clicked.connect(self.colorpicker1.exec)
        self.colorButton2.clicked.connect(self.colorpicker2.exec)
        Layout.addWidget(self.colorButton1, 4, 0, 1, 2)
        Layout.addWidget(self.colorButton2, 4, 2, 1, 2)

        # while True:
        #     matchquery = (requests.get(f'https://api.nevobo.nl/{match["@id"]}/live', stream=True)).json()
        #     print(f"Stand: {matchquery["stand"][0]} - {matchquery["stand"][1]}")
        #     print(f"Set stand: {matchquery["sets"][-1][0]} - {matchquery["sets"][-1][1]}")
        #     time.sleep(5)
    def toggleScoreboard(self):
        if self.isScoreboardActive:
            self.ActiveScoreboard.close()
            self.isScoreboardActive = False
            self.startScoreboardButton.setText("Start scoreboard")
        else:
            if self.MatchSelect.currentText() == "":
                return
            self.ActiveScoreboard = ScoreBoard(self.MatchList[self.MatchSelect.currentText()],
                                               self.colorpicker1.currentColor(),
                                               self.colorpicker2.currentColor())
            self.ActiveScoreboard.closeCommand.connect(self.toggleScoreboard)
            self.ActiveScoreboard.show()
            self.isScoreboardActive = True
            self.startScoreboardButton.setText("Stop scoreboard")


    def queryMatches(self):
        self.MatchList = {}
        self.MatchSelect.clear()
        self.searchparams["datum[after]"] = self.datumkiezerafter.date().toString("dd-MM-yyyy")
        self.searchparams["datum[before]"] = self.datumkiezerbefore.date().toString("dd-MM-yyyy")
        matches = requests.get('https://api.nevobo.nl/competitie/wedstrijden', params=self.searchparams)
        matchinfo = matches.json()
        for match in matchinfo["hydra:member"]:
            teamlist = []
            for team in match["teams"]:
                teamquery = requests.get(f'https://api.nevobo.nl/{team}').json()
                teamlist.append(teamquery["omschrijving"])
            self.MatchList[" - ".join(teamlist)] = {
                "team1" : teamlist[0],
                "team2": teamlist[1],
                "id": match["@id"]}
        self.MatchSelect.addItems(list(self.MatchList.keys()))


class ScoreBoard(QtW.QWidget):
    closeCommand = Signal()
    def __init__(self, Matchlist: dict, color1: QColor, color2: QColor):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(Qt.FramelessWindowHint)
        Layout = QtW.QGridLayout(self)
        self.TeamFrame1 = QtW.QFrame()
        self.TeamFrame2 = QtW.QFrame()
        self.TeamFrame1.setStyleSheet(f"background-color: {color1.name()}")
        self.TeamFrame2.setStyleSheet(f"background-color: {color2.name()}")
        self.TeamLabel1 = QtW.QLabel(Matchlist["team1"], objectName="Title")
        self.TeamLabel2 = QtW.QLabel(Matchlist["team2"], objectName="Title")
        frameLayout1 = QtW.QVBoxLayout(self.TeamFrame1)
        frameLayout2 = QtW.QVBoxLayout(self.TeamFrame2)
        frameLayout1.addWidget(self.TeamLabel1)
        frameLayout2.addWidget(self.TeamLabel2)
        self.SetLabel1 = QtW.QLabel("0")
        self.SetLabel2 = QtW.QLabel("0")
        self.ScoreLabel1 = QtW.QLabel("0", objectName="Score")
        self.ScoreLabel2 = QtW.QLabel("0", objectName="Score")
        Layout.addWidget(self.TeamFrame1, 0, 0)
        Layout.addWidget(self.SetLabel1, 0, 2)
        Layout.addWidget(self.ScoreLabel1, 0, 1)
        Layout.addWidget(self.TeamFrame2, 1, 0)
        Layout.addWidget(self.SetLabel2, 1, 2)
        Layout.addWidget(self.ScoreLabel2, 1, 1)
        self.thread = QThread()
        self.worker = ScoreQuery(f'https://api.nevobo.nl/{Matchlist["id"]}/live')
        self.worker.QueryResult.connect(self.updateScores)
        self.thread.started.connect(self.worker.timer.start())
        self.thread.start()
        self.SC = QShortcut(QKeySequence("Ctrl+o"), self)
        self.SC.activated.connect(self.closeCommand.emit)

    def updateScores(self, result: dict):
        if "Error" in result:
            print(result["Error"])
        else:
            self.SetLabel1.setText(str(result["stand"][0]))
            self.SetLabel2.setText(str(result["stand"][1]))
            self.ScoreLabel1.setText(str(result["sets"][-1][0]))
            self.ScoreLabel2.setText(str(result["sets"][-1][1]))

    def closeEvent(self, event):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()


class ScoreQuery(QObject):
    QueryResult = Signal(dict)
    def __init__(self, url, interval=5000, parent=None):
        super().__init__(parent)
        self.interval = interval  # Interval in milliseconds
        self.timer = QTimer()
        self.url = url
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.query_api)


    def query_api(self):
        print("Querying API")
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            data = response.json()
            self.QueryResult.emit(data)
        except requests.exceptions.RequestException as e:
            self.QueryResult.emit({"Error": e})




    def stop(self):
        self.timer.stop()


if __name__ == "__main__":
    app = QtW.QApplication([])
    with open("src/BlueStyle.qss") as f:
        app.setStyleSheet(f.read())
    Widget = settingsWindow()
    Widget.showNormal()
    app.exec()

