import smtplib
import email_config
import urllib.request as urq
import urllib.error
import xml.etree.ElementTree as ET

from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.headerregistry import Address


def construct_message(weather):
    msg = MIMEMultipart()
    
    msg['Subject'] = "Weather " + str(date.today().month) + "/" + str(date.today().day) + "/" + str(date.today().year)
    msg['From'] = email_config.from_address
    msg['To'] = ', '.join(email_config.to_addresses)
    
    text = "High: " + weather.high + "\nLow: " + weather.low + "\nRain: " + weather.rain[0] + "% " + weather.rain[1] + "%"
    html = """\
        <html>
            <head></head>
            <body>
                <p>High: {} {}</p>
                <p>Low: {} {}</p>
                <p>Precipitation:</p>
                <ul>
                    <li>00:00-11:00: {}%</li>
                    <li>12:00-23:00: {}%</li>
                </ul>
                <p>Conditions:</p>
                <ul>
                """
                
    for i in range(len(weather.conditions)):
        html += "   <li>" + weather.conditions[i]["intensity"] + " " + weather.conditions[i]["weather-type"] + "</li>\n"
    
    html += """\
                </ul>
                <p>Hazards:</p>
                <ul>
                """
                
    for j in range(len(weather.hazards)):
        html += "   <li>" + weather.hazards[j]['phenomena'] + " " + weather.hazards[j]['significance'] + "</li>\n"
    
    html += """\
                </ul>
             </body>
         </html>
            """
    
    unit = ""
    if weather.unit == "m":
        unit = "C"
    else:
        unit = "F"
    
    msg.attach(MIMEText(html.format(weather.high, unit, weather.low, unit, weather.rain[0], weather.rain[1]), 'html'))
    
    with urq.urlopen(weather.icon_path) as ic:
        msg.attach(MIMEImage(ic.read()))
        
    
    return msg

class Weather:
    def __init__(self, zcode, unit):
        self.high = ""
        self.low = ""
        self.rain = []
        self.icon_path = ""
        self.hazards = []
        self.conditions = []
        
        self.unit = unit
        
        self.url = "http://graphical.weather.gov/xml/sample_products/browser_interface/ndfdBrowserClientByDay.php" + "?whichClient=NDFDgenByDayMultiZipCode&zipCodeList=" + str(zcode) + "&format=24+hourly&startDate=" + str(date.today().year) + "-" + str(date.today().month) + "-" + str(date.today().day) + "&numDays=1&Unit=" + unit
        
        self.cnx = None
        
    def _parse(self):
        tree = ET.parse(self.cnx)
        self.high = tree.getroot()[1][5][0][1].text
        self.low = tree.getroot()[1][5][1][1].text
        self.rain = [tree.getroot()[1][5][2][1].text, tree.getroot()[1][5][2][2].text]
        self.icon_path = tree.getroot()[1][5][4][1].text
            
        for haz in tree.getroot()[1][5][5][1]:
             self.hazards.append(haz.attrib)
            
        for cond in tree.getroot()[1][5][3][1]:
             self.conditions.append(cond.attrib)
       
        
    def connect(self):
        try:
            self.cnx = urq.urlopen(self.url)
            self._parse()
            return True
        except urllib.error.HTTPError:
            try:
                urq.urlopen("http://www.google.com")
                return False
            except:
                raise IOError("Network doesn't seem to be available")
    


w = Weather(21229, "e")
w.connect()
s = smtplib.SMTP("smtp.gmail.com", port="587")
s.starttls()
s.login(email_config.from_address, email_config.password)
s.send_message(construct_message(w))
s.quit()
