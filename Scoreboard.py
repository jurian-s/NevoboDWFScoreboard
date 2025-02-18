import requests
import time
import datetime
from PySide6 import QtWidgets as QtW
from PySide6.QtCore import QThread, QTimer, Signal, QDate, QObject, QLocale


class settingsWindow(QtW.QWidget):
    def __init__(self):
        super().__init__()
        Layout = QtW.QGridLayout(self)
        self.searchparams = {
                        "sporthal": "/accommodatie/sporthallen/tu-sportcentrum",
                       "datum[after]": QDate().currentDate().toString("dd-MM-yyyy"),
                       "datum[before]": QDate().currentDate().addMonths(1).toString("dd-MM-yyyy")}
        self.datumkiezerafter = QtW.QDateEdit(calendarPopup=True)
        self.datumkiezerafter.setLocale(QLocale("Dutch"))
        self.datumkiezerafter.setDate(QDate.currentDate())
        # while True:
        #     matchquery = (requests.get(f'https://api.nevobo.nl/{match["@id"]}/live', stream=True)).json()
        #     print(f"Stand: {matchquery["stand"][0]} - {matchquery["stand"][1]}")
        #     print(f"Set stand: {matchquery["sets"][-1][0]} - {matchquery["sets"][-1][1]}")
        #     time.sleep(5)
    def queryMatches(self):
        Matchlist = {}
        matches = requests.get('https://api.nevobo.nl/competitie/wedstrijden', params=self.searchparams)
        matchinfo = matches.json()
        for match in matchinfo["hydra:member"]:
            teamlist = []
            for team in match["teams"]:
                teamquery = requests.get(f'https://api.nevobo.nl/{team}').json()
                teamlist.append(teamquery["omschrijving"])
            Matchlist[" - ".join(teamlist)] = match["@id"]
        print(Matchlist)

class ScoreBoard(QtW.QWidget):
    def __init__(self, Matchlist: dict):
        super().__init__()
        Layout = QtW.QGridLayout(self)
        self.TeamLabel1 = QtW.QLabel(list(Matchlist.keys())[0])
        self.TeamLabel2 = QtW.QLabel(list(Matchlist.keys())[1])
        self.SetLabel1 = QtW.QLabel("0")
        self.SetLabel2 = QtW.QLabel("0")
        self.ScoreLabel1 = QtW.QLabel("0")
        self.ScoreLabel2 = QtW.QLabel("0")
        Layout.addWidget(self.TeamLabel1, 0, 0)
        Layout.addWidget(self.SetLabel1, 0, 1)
        Layout.addWidget(self.ScoreLabel1, 0, 2)
        Layout.addWidget(self.TeamLabel1, 1, 0)
        Layout.addWidget(self.SetLabel1, 1, 1)
        Layout.addWidget(self.ScoreLabel1, 1, 2)

class ScoreQuery(QObject):
    QueryResult = Signal(dict)
    def __init__(self, url, interval=5000, parent=None):
        super().__init__(parent)
        self.interval = interval  # Interval in milliseconds
        self.timer = QTimer()
        self.url = url
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.query_api)
        self.timer.start()
    def query_api(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            data = response.json()
            self.QueryResult.emit(data)
        except requests.exceptions.RequestException as e:
            self.resultReady.emit({"Error": e})


if __name__ == "__main__":
    app = QtW.QApplication([])
    with open("src/BlueStyle.qss") as f:
        app.setStyleSheet(f.read())
    Widget = settingsWindow()
    Widget.queryMatches()
    app.exec()

