import os
import json
import re

from bs4 import BeautifulSoup

htmlFilesDir = "pages/"
htmlFiles = os.listdir(htmlFilesDir)

dataFilesDir = "data/"

files = []

courses = {}

sessions = []

for file in htmlFiles:
    if ".html" in file:
        files.append(htmlFilesDir + file)

for file in files:
    disciplineCourses = []

    disciplineSessionCode = file.replace(htmlFilesDir, "").replace(".html", "")

    soup = BeautifulSoup(open(file, "r", encoding="utf-8"), "html.parser")

    courseTables = soup.find_all(name="div", class_="schedule")

    for courseTable in courseTables:
        sectionTables = courseTable.find_all(name="table")

        courseData = {}

        courseSections = []

        for sectionTable in sectionTables:
            sectionData = {}
            lecturesData = []

            sectionLectures = sectionTable.find_all(name="tr")[1:]

            for sectionLecture in sectionLectures:
                lectureData = {}

                keysAndClasses = [
                    ["activityName", "Activity"],
                    ["day", "Day"],
                    ["location", "Place"],
                    ["teacher", "Professor"]
                ]

                for keyAndClass in keysAndClasses:
                    dataElement = sectionLecture.find(class_=keyAndClass[1])

                    if dataElement is not None:
                        lectureData[keyAndClass[0]] = re.sub('\s+', ' ', dataElement.text).strip()
                    else:
                        lectureData[keyAndClass[0]] = ""

                lecturesData.append(lectureData.copy())

            courseCodeRegEx = re.compile('[A-Z]{3}[0-9]{4} [A-Z]*')

            courseCodeMatch = courseCodeRegEx.match(sectionTable.find(class_="Section").text)

            if courseCodeMatch:
                sectionData['sectionName'] = courseCodeMatch.group(0)
            else:
                sectionData['sectionName'] = 'Section name unknown'

            sectionData['lectures'] = lecturesData

            courseSections.append(sectionData.copy())

        courseData['code'] = courseTable.find(class_="Section").text[:7]

        courseData['sections'] = courseSections

        disciplineCourses.append(courseData.copy())

    courses[disciplineSessionCode] = disciplineCourses

    sessions.append(disciplineSessionCode)

    with open(dataFilesDir + disciplineSessionCode + ".json", "w", encoding="utf8") as jsonFile:
        json.dump(disciplineCourses, jsonFile, sort_keys=True, indent=4, ensure_ascii=False)

with open(dataFilesDir + "data.json", "w", encoding="utf8") as jsonFile:
    json.dump(courses, jsonFile, sort_keys=True, indent=4, ensure_ascii=False)

with open(dataFilesDir + "sessions.json", "w", encoding="utf8") as jsonFile:
    json.dump(sessions, jsonFile, sort_keys=True, indent=4, ensure_ascii=False)
