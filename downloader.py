#!/usr/local/bin/python3
import sys
import mechanicalsoup

browser = mechanicalsoup.StatefulBrowser()
browser.set_verbose(2)

browser.open("https://www.uottawa.ca/course-timetable/")

app_link = browser.find_link(link_text="Launch the Class Search Application")

browser.follow_link(app_link)

app_page = browser.get_current_page()

search_frame = app_page.find("iframe", id="ptifrmtgtframe")

if not search_frame:
    sys.exit("No search iframe found.")

browser.open(search_frame['src'])

browser.select_form("#UO_PUB_CLSSRCH")

# browser.get_current_form().print_summary()
browser["SSR_CLSRCH_WRK_SUBJECT$0"] = "HIS"

response = browser.submit_selected()

print(response.text)
