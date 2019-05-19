import re
import pandas as pd
import ast

class TermSubjectParser:
    def __init__(self, discipline, year, term):
        self.course_descriptions = self.load_course_descriptions(discipline)

        self.courses = self.load_courses_from_file(discipline, year, term)
        self.courses = self.extract_sections_by_course(self.courses)
        self.courses = self.clean_badly_processed_courses(self.courses)
        self.courses = self.convert_courses_to_dataframe(self.courses)
        self.courses = self.describe_course_sections(self.courses, self.course_descriptions)

    def handle_section(self, section):
        sectionCode = section[0].split('-')[0]
        
        sectionData = {
            "admin": {},
            "days": []
        }
        
        ## Handling admin stuff
        sectionData["admin"]["code"] = sectionCode
        sectionData["admin"]["type"] = section[0].split('-')[1].split('\n')[0]
        sectionData["admin"]["duration"] = section[0].split('-')[1].split('\n')[1]
        sectionData["admin"]["isOpen"] = 'Open' in section[5]
        
        ## Handling days
        
        ### Helper function to extract datetime details
        def handle_section_datetime(datetime):
            return {
                "weekday": datetime[:2],
                "time.start": datetime[3:].split(' - ')[0],
                "time.end": datetime[3:].split(' - ')[1]
            }

        ### Extract the relevant details in a very hacky way :)
        def mini_day_extractor(sectionToHandle, index):
            return {
                **handle_section_datetime(sectionToHandle[1].split('\n')[index]),
                "location": sectionToHandle[2].split('\n')[index],
                "prof": sectionToHandle[3].split('\n')[index],
                "date.start": sectionToHandle[4].split('\n')[index].split(' - ')[0],
                "date.end": sectionToHandle[4].split('\n')[index].split(' - ')[1]
            }
        
        ### Given the number of days (counted by the number of `\n` in the datetime string...), extract them
        for index in range(0, section[1].count('\n') + 1):
            sectionData["days"].append(mini_day_extractor(section, index))
                
        return {sectionCode: sectionData}

    ###
    # Get the courses from a file, into a dict.
    ###
    def load_courses_from_file(self, discipline, year, term):
        courses = {}

        with open(str('./pages/' + discipline + '-' + str(year) + '-' + term + '.txt'), 'r') as course_file:
            # Read course file into one big string
            data = course_file.read()

            # Break down to courses
            data = data.split('Collapse section ')

            # Remove erroneous space items
            del data[0]

            # Key the courses into the `courses` object
            for course in data:
                courses[course[0:8]] = course

        return courses

    ###
    # Get the sections from each course, adding as a list to the dict item.
    ###
    def extract_sections_by_course(self, courses_to_process):
        sections_by_course = {}
        
        for courseCode, courseStr in courses_to_process.items():
            sections = {}

            if ' \n\t\t\n\t\n\t\t\n\t\n\t\t\t\n\t\n  \tSection \tDays & Times \tRoom \tInstructor \tMeeting Dates \tStatus\nDetails\n\t\n' in courseStr:
                sectionContainer = courseStr.split(' \n\t\t\n\t\n\t\t\n\t\n\t\t\t\n\t\n  \tSection \tDays & Times \tRoom \tInstructor \tMeeting Dates \tStatus\nDetails\n\t\n')[1]
            else:
                sectionContainer = courseStr.split(' \n\t\t\n\t\n\t\t\n\t\n\t\t\n\t\n  \tSection \tDays & Times \tRoom \tInstructor \tMeeting Dates \tStatus\nDetails\n\t\n')[1]

            sectionData = sectionContainer.split('\n\t\n\t\t\n\t\n  \tSection \tDays & Times \tRoom \tInstructor \tMeeting Dates \tStatus\nDetails\n\t\n')

            for section in sectionData:
                try:
                    sectionInfo = handle_section(section.split('\n\t\n'))
                except:
                    pass

                sections.update(sectionInfo)

            sections_by_course[courseCode] = sections
            
        return sections_by_course

    ## Clean badly processed courses :)
    def clean_badly_processed_courses(self, courses):
        courses_to_process = courses.copy()

        coursesToDelete = {}

        for courseCode, courseObj in courses_to_process.items():
            if isinstance(courseObj, str):
                coursesToDelete[courseCode] = courseObj

        for course in coursesToDelete:
            courses_to_process.pop(course, None)

        print(str(len(coursesToDelete)) + " courses removed due to badly formed data.")
        
        return courses_to_process

    def convert_courses_to_dataframe(self, courses):
        ## 1. Convert the courses object to a dataframe
        df = pd.DataFrame.from_dict(courses, orient='index')
        df = pd.DataFrame(df.stack())
        
        ## 2. Unpack the `data` column
        df = df.reset_index()
        df.columns = ['course', 'code', 'data']

        df2 = df.join(pd.io.json.json_normalize(df['data']))
        df2 = df2.set_index(['course', 'code'])
        
        ## 3. Unpack the `days` column
        ### Convert the days column from an object to a string
        days_as_string = df2.astype({'days': str}).reset_index()['days'].apply(ast.literal_eval)
        days_as_string

        ### Unpack the column. The column contains lists of objects with consistent keys, so each object becomes its own row
        days_by_section = pd.concat([pd.DataFrame(x) for x in days_as_string], keys=days_as_string.index)
        days_by_section

        ### Join the expanded rows with their original courses, dropping the now-unused columns
        df3 = df2.reset_index().join(days_by_section.reset_index(1, drop=True))
        df3 = df3.set_index(['course', 'code']).drop('data', 1).drop('days', 1)

        ## 4. Reorganize columns 
        courses_by_section_by_day = df3[[
            'admin.duration',
            'admin.isOpen',
            'admin.type',
            'prof',
            'weekday',
            'time.start',
            'time.end',
            'location',
            'date.start',
            'date.end'
        ]]
        
        return courses_by_section_by_day
        
    def load_course_descriptions(self, discipline):
        return pd.read_csv(str('./data/courses/' + discipline + '.csv')).set_index('code')

    def describe_course_sections(self, courses_by_section_by_day, course_descriptions):
        described_courses_by_section_by_day = pd.merge(courses_by_section_by_day.reset_index(1), course_descriptions, left_index=True, right_index=True)

        described_courses_by_section_by_day = described_courses_by_section_by_day.reset_index().set_index(['index', 'code'])
        described_courses_by_section_by_day.index.names = ['course', 'section']

        return described_courses_by_section_by_day
