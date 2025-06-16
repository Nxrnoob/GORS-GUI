import sys
import os
import json
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QTextBrowser, QHBoxLayout, QFileDialog, QCheckBox, QMessageBox
)
from PyQt6.QtGui import QPalette, QColor, QFont, QIcon
from PyQt6.QtCore import Qt
import requests
import csv
import time
from collections import defaultdict

class GitHubOSINTScraper(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("GitHub OSINT Scraper")
        self.setGeometry(100, 100, 800, 600)
        self.layout = QVBoxLayout()
        
        # API Key Input with Save Button
        self.api_key_label = QLabel("GitHub API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.save_key_button = self.create_material_button("Save API Key", self.save_api_key, 12)
        self.forget_key_button = self.create_material_button("Forget API Key", self.forget_api_key, 12)
        self.token_button = QPushButton("Get Your API key token")
        self.token_button.setStyleSheet("""
            QPushButton {
                background-color: #6200EE;
                color: white;
                border-radius: 12px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3700B3;
            }
            QPushButton:pressed {
                background-color: #03DAC5;
            }
        """)
        self.token_button.clicked.connect(self.open_github_tokens_page)

        # Search Input
        self.search_label = QLabel("Search Keywords:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter keywords...")
        
        # Sorting Options
        self.sort_label = QLabel("Sort By:")
        self.sort_options = QComboBox()
        self.sort_options.addItems(["Best Match", "Stars", "Forks", "Recently Updated"])

        # Filter by Language
        self.language_label = QLabel("Filter by Language:")
        self.language_filter = QComboBox()
        self.language_filter.addItems(["All", "Python", "JavaScript", "Java", "C++", "Go", "Custom..."])
        self.custom_language_input = QLineEdit()
        self.custom_language_input.setPlaceholderText("Enter custom language...")
        self.custom_language_input.setEnabled(False)
        self.language_filter.currentIndexChanged.connect(self.toggle_custom_language)

        # Search Button
        self.search_button = self.create_material_button("Search", self.fetch_repositories, 12)

        # Results Display (Use QTextBrowser for clickable links)
        self.results_area = QTextBrowser()

        # Exit Button
        self.exit_button = self.create_material_button("Exit", self.close, 12)

        # Layout Arrangement
        self.layout.addWidget(self.api_key_label)
        self.layout.addWidget(self.api_key_input)
        self.layout.addWidget(self.save_key_button)
        self.layout.addWidget(self.forget_key_button)
        self.layout.addWidget(self.token_button)
        self.layout.addWidget(self.search_label)
        self.layout.addWidget(self.search_input)
        self.layout.addWidget(self.sort_label)
        self.layout.addWidget(self.sort_options)
        self.layout.addWidget(self.language_label)
        self.layout.addWidget(self.language_filter)
        self.layout.addWidget(self.custom_language_input)
        self.layout.addWidget(self.search_button)
        self.layout.addWidget(self.results_area)
        self.layout.addWidget(self.exit_button)

        self.setLayout(self.layout)

        self.setMaterialYouStyle()

    def create_material_button(self, text, handler, font_size=16):
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #6200EE;
                color: white;
                border-radius: 12px;
                padding: 10px 20px;
                font-size: {font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3700B3;
            }}
            QPushButton:pressed {{
                background-color: #03DAC5;
            }}
        """)
        button.clicked.connect(handler)
        return button

    def setMaterialYouStyle(self):
        # Apply dark mode style
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))  # Dark mode background
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))  # Light text color
        palette.setColor(QPalette.ColorRole.Base, QColor(40, 40, 40))  # Darker background for input fields
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))  # Text in input fields
        self.setPalette(palette)
        
        # Update text color for labels and inputs
        self.search_label.setStyleSheet("color: white; font-size: 16px;")
        self.language_label.setStyleSheet("color: white; font-size: 16px;")
        self.api_key_label.setStyleSheet("color: white; font-size: 16px;")
        self.search_input.setStyleSheet("color: black; font-size: 16px;")
        self.custom_language_input.setStyleSheet("color: black; font-size: 16px;")

        # Ensure links are clickable
        self.results_area.setOpenExternalLinks(True)

    def save_api_key(self):
        api_key = self.api_key_input.text().strip()
        if api_key:
            with open("config.json", "w") as f:
                json.dump({"api_key": api_key}, f)
            QMessageBox.information(self, "Success", "API Key saved successfully!")
        else:
            QMessageBox.warning(self, "Warning", "API Key cannot be empty!")

    def forget_api_key(self):
        if os.path.exists("config.json"):
            os.remove("config.json")
        self.api_key_input.clear()
        QMessageBox.information(self, "Success", "API Key forgotten!")

    def load_settings(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                data = json.load(f)
                self.api_key_input.setText(data.get("api_key", ""))

    def fetch_repositories(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Error", "Please enter your GitHub API key.")
            return

        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Error", "Please enter search keywords.")
            return

        sort_by = self.sort_options.currentText().lower().replace(" ", "")
        language = self.language_filter.currentText()
        if language == "Custom...":
            language = self.custom_language_input.text().strip()
        language_filter = f"+language:{language}" if language and language != "All" else ""

        url = f"https://api.github.com/search/repositories?q={query}{language_filter}&sort={sort_by}&per_page=100"
        headers = {"Authorization": f"token {api_key}"}

        # Clear previous results
        self.results_area.clear()

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos = response.json().get("items", [])
            if repos:  # Check if there are results
                results = ""
                for repo in repos:
                    repo_name = repo['name']
                    repo_url = repo['html_url']
                    repo_desc = repo.get('description', 'No description')
                    repo_stars = repo['stargazers_count']
                    repo_forks = repo['forks_count']

                    # Shorten the description to 100 characters
                    short_desc = repo_desc[:100] + "..." if len(repo_desc) > 100 else repo_desc

                    # Apply appropriate icons based on the sort type
                    if sort_by == "stars":
                        sort_icon = f"⭐ {repo_stars} stars"
                    elif sort_by == "forks":
                        sort_icon = f"🍴 {repo_forks} forks"
                    else:
                        sort_icon = f"🔍 {repo_name}"

                    results += f"<b>{repo_name}</b> - <a href='{repo_url}' style='color: #6200EE;'>{repo_url}</a><br><br>{sort_icon}<br>{short_desc}<br><br>"
                self.results_area.setHtml(results)  # Display the repositories
            else:
                self.results_area.setHtml("<p style='color: red;'>No results found for the given search criteria.</p>")  # Show no results message
        else:
            QMessageBox.critical(self, "Error", f"Failed to fetch repositories: {response.status_code}")

    def toggle_custom_language(self):
        self.custom_language_input.setEnabled(self.language_filter.currentText() == "Custom...")

    def open_github_tokens_page(self):
        webbrowser.open("https://github.com/settings/tokens")

    def close(self):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitHubOSINTScraper()
    window.show()
    sys.exit(app.exec())

