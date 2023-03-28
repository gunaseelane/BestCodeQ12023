import imaplib
import os
import requests
from bs4 import BeautifulSoup
import email
import csv
import html2text
import urllib.parse
from urllib.parse import urlparse
from urllib.parse import parse_qs
from colorama import Fore, Back, Style

# importing the requests library
import requests

# defining the api-endpoint 
API_ENDPOINT = "http://localhost:8000/api/posts"
token = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwMDAvYXBpL2xvZ2luIiwiaWF0IjoxNjc4Mzc0NzcyLCJuYmYiOjE2NzgzNzQ3NzIsImp0aSI6Ik5WdG1qWWg5c2NUd1FrQVYiLCJzdWIiOiIyIiwicHJ2IjoiMjNiZDVjODk0OWY2MDBhZGIzOWU3MDFjNDAwODcyZGI3YTU5NzZmNyJ9.0DkOe5NhR8fgF5zouAIqi40-YMxw5KGeyQwL-sV6dG0"

headers = {"Content-Type": "application/json","Authorization":token,"Origin":"http://localhost:8080"}

mentions = []
utf = []
#Functions
def string_ends_with(string, items):
    """Check if a given string ends with any of the items in a given array"""
    for item in items:
        if string.endswith(item):
            return True
    return False
def string_starts_with(string, items):
    """Check if a given string starts with any of the items in a given array"""
    for item in items:
        if string.startswith(item):
            return True
    return False

# Connect to IMAP server
imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
user = 'gunaseelane@dckap.com' # Mail ID from which data is to be extracted
password = 'ldsqkqwqzwcpehem' # 16 Digit App Password
imap_server.login(user, password)

# Select the Inbox folder
imap_server.select('INBOX')

# Search for emails with from mail id ending with members.mobilize.io
pattern = "members.mobilize.io"
status, messages = imap_server.search(None, f'(HEADER FROM "*@{pattern}")')
counter=0 # Counter for post ID

posts_dictionary={} # To identify posts that were created and deleted

save_path = 'Mobilize'
# Write the post to CSV file - D:/Mobilize/Post<<counter>>/post.csv
with open(os.path.join(save_path,'posts.csv'), 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Post ID","Sender","Subject", "Body HTML","Attachment File","Timestamp"])
    print('<<<<<<<<<<<<<<<< STARTED >>>>>>>>>>>>>>>>')
    # Iterate through mails
    for msg_id in messages[0].split():

        # Fetch email message
        status, msg_data = imap_server.fetch(msg_id, '(RFC822)')
        #inceasing counter
        counter+=1

        if status == 'OK':

            post_data=[]

            

            # Parse email message
            raw_email = msg_data[0][1].decode("utf-8")
            email_message = email.message_from_string(raw_email)
            msg = email_message
            sender = msg['From']
            subject = msg['Subject']
            timestamp = msg['Date']
            if('UTF' in subject):
                utf.append(subject)
            

            #formatting mobilize email <srijas.dckap@members.mobilize.io> to dckap email srijas.dckap@com
            sender = sender.replace('.dckap@members.mobilize.io','@dckap.com').replace('<','').replace('>','')


            # Skip Comments and Replies
            Skip = [
                "Invitation to DCKAP community",
                "Re:",
                "You were mentioned",
                "RE:",
                "Welcome to  DCKAP community"
                ]
            
            if string_starts_with(subject,Skip):
                continue


            print(counter,"-",subject)

            # To Track Possible Duplicate Posts
            if subject in posts_dictionary:
                print('Duplicate Found - '+ subject)
                posts_dictionary[subject] = str(posts_dictionary[subject])+'-DUPLICATE-'+str(counter)
                print(posts_dictionary[subject])
            else:
                posts_dictionary[subject] = counter


            #Download Attachments
            raw_email_for_attachment = msg_data[0][1]
            email_message_for_attachment = email.message_from_bytes(raw_email_for_attachment)
            fileCounter = 0
            for part in email_message_for_attachment.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                filename = part.get_filename()
                print(Back.GREEN + filename)
                print(Style.RESET_ALL)
                save_path = 'Mobilize/'+subject+'-'+str(posts_dictionary[subject])
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                if filename is not None:
                    filepath = os.path.join(save_path, filename)
                    fileCounter += 1
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
            if fileCounter:
                print(str(fileCounter)+' - Attachments downloaded...')
                print(Back.GREEN + str(fileCounter)+' - Attachments downloaded...')
                print(Style.RESET_ALL)
            else:
                print('No Attachments...')
            

            # Printing the subjects of the emails processed

            #Get HTML Body
            html_body = None
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    html_body = part.get_payload(decode=True).decode('utf-8')

            if html_body:
                save_path=os.path.join(os.getcwd(),'Mobilize/'+str(posts_dictionary[subject]))
                if not os.path.exists(save_path):
                      os.makedirs(save_path)
                      
            # Download images - D:/Mobilize/Post<<counter>>/          
            soup = BeautifulSoup(html_body, 'html.parser')
            for element in soup.find_all("table", {"class":"post-footer-container"}):
                element.decompose()

            for element in soup.find_all("table", {"class":"email-max-width"}):
                element['style'] = "border-collapse: collapse; border-spacing: 0; padding: 0; vertical-align: top;";

            for element in soup.find_all("table", {"class":"files-container"}):
                element.decompose()

            if len(soup.find_all("table", {"class":"event-details"})):
                continue
            if len(soup.find_all("table", {"class":"poll-text"})):
                continue

            for img_tag in soup.find_all('img'):
                ignore = [
                    'https://d3ft6bzqwbqgiw.cloudfront.net/emails/heart_footer.png',
                    'http://dckap.mobilize.io/email_opens',
                    ]
                if string_starts_with(img_tag['src'],ignore):
                    img_tag.decompose()
                    continue
                if 'alt' in img_tag:
                    if img_tag['alt'] == 'Preview image':
                        img_tag.decompose()
                        continue
                img_url = img_tag['src']
                img_name = os.path.basename(img_tag['src'])
                img_path = os.path.join(save_path,img_name)
                try:
                    with open(img_path, 'wb') as img_file:
                        img_file.write(requests.get(img_url).content)
                        # img_tag['src'] = img_path
                except:
                    pass
                img_tag['alt']="IMAGE:"+img_name # Update alt tag
            

            #Find all mentions
            # for mention in soup.find_all('span',{"class":"mention fr-tribute"}):
            #     mentions.append(mention.text)
            #     mention.string = 'MENTION_START:::'+mention.text+':::MENTION_END'

            # Find all the links in the HTML body
            # Download the files
            for link in soup.find_all('a'):
                href = link.get('href')
                allowedTypes = ['.pdf','.jpg','.png','.jpeg','.mp4','.xlsx','.gif','.xls','.doc','.docx']
                if string_ends_with(href,allowedTypes): #endswith('.pdf') or href.endswith('.jpg') or href.endswith('.png') or href.endswith('.jpeg') or href.endswith('.mp4') or href.endswith('.xlsx') or href.endswith('.gif') or href.endswith('.xls') or href.endswith('.doc') or href.endswith('.docx'):
                    # # Make a GET request to the URL of the file and download the content
                    # file_response = requests.get(href)
                    # file_content = file_response.content
                    # # Write the file content to a local file with the same name as the remote file
                    # with open(save_path+'/'+href.split('/')[-1], 'wb') as f:
                    #     f.write(file_content)
                    # link['href'] = save_path+'/'+href.split('/')[-1]
                    continue
                else:
                    if 'http://app.mobilize.io/widget_clicks' in href and 'click?click_source=link_preview' in href:
                        parsed_url = urlparse(href)
                        captured_value = parse_qs(parsed_url.query)['url'][0]
                        link['href'] = captured_value
                        # if(link.string != None):
                        #     link.string = 'LINK_START:::LINK:::'+link['href']+':::LINK_NAME:::'+link.string.strip()+':::LINK_END'
                        #     index = link.parent.contents.index(link)
                        #     link.parent.insert(index+1,link.string)
                        #     link.decompose()

                        # else:
                        #     link.string = 'LINK_START:::LINK:::'+link['href']+':::LINK_NAME:::'+link['href']+':::LINK_END'
                        #     index= link.parent.contents.index(link)
                        #     link.parent.insert(index+1,link.string)
                        #     link.decompose()
                    else :
                        if 'http://dckap.mobilize.io/links?' in href and 'url=' in href:
                            parsed_url = urlparse(href)
                            captured_value = parse_qs(parsed_url.query)['url'][0]
                            link['href'] = captured_value
                            # if(link.string != None):
                            #     link.string = 'LINK_START:::LINK:::'+link['href']+':::LINK_NAME:::'+link.string.strip()+':::LINK_END'
                            #     index= link.parent.contents.index(link)
                            #     link.parent.insert(index+1,link.string)
                            #     link.decompose()
                            # else:
                            #     link.string = 'LINK_START:::LINK:::'+link['href']+':::LINK_NAME:::'+link['href']+':::LINK_END'
                            #     index= link.parent.contents.index(link)
                            #     link.parent.insert(index+1,link.string)
                            #     link.decompose()
                        else:
                            print(link)

            text_part = str(soup.prettify())

            with open('Mobilize/'+str(posts_dictionary[subject])+'.html', 'w') as f:
                        f.write(text_part)
            post_data.append(posts_dictionary[subject])
            post_data.append(sender)
            post_data.append(subject)
            post_data.append(text_part)
            post_data.append(save_path)
            post_data.append(timestamp)
            print('--------------------post api-----------------')
            data = {
                "title":"Post Owner : "+sender+" - "+subject,
                "channel_type":"community",
                "feedback_type":"",
                "body":text_part,
                "scheduled_time":"",
                "scheduled_timezone":"America/Los_Angeles",
                "is_scheduled":"false",
                "is_draft":"false",
                "is_scheduled":"false",
                "is_published":"true",
            }
             
            response = requests.post(API_ENDPOINT, headers=headers, json=data)
             
            print("Status Code", response.status_code)
            # # print("JSON Response ", response.json())
            print('--------------------Added to Main CSV File-----------------')
            writer.writerow(post_data)
            print('')
        # else:
        #     if counter > 60:
        #         break
        #     continue        

with open(os.path.join('Mobilize','mentions.csv'), 'w', newline='', encoding='utf-8') as fileMention:
    mWriter = csv.writer(fileMention)
    mWriter.writerow(["Name","email"])
    for mention in mentions:
        mWriter.writerow([mention,""])

print("Completed extracting.... Analysing Possible Duplicate Posts....")
print(utf)
# Print Possible Duplicate Posts
DulicateCount = 0
for key in posts_dictionary:
    # print(posts_dictionary[key])
    if 'DUPLICATE' in str(posts_dictionary[key]):
        print(posts_dictionary[key])
        DulicateCount +=1
if(DulicateCount):
    print(str(DulicateCount)+" Duplicates Found")
else:
    print("No Duplicates")
# Close IMAP Connection
imap_server.close()
imap_server.logout()
