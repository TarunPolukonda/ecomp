import smtplib
from smtplib import SMTP
from email.message import EmailMessage
def sendmail(email,subject,body):
    server=smtplib.SMTP_SSL("smtp.gmail.com",465)
    server.login('tarunsiddu217@gmail.com','erto dvns jhvy gtdj')
    msg=EmailMessage()
    msg['FROM']='tarunsiddu217@gmail.com'
    msg['To']=email
    msg['SUBJECT']=subject
    msg.set_content(body)
    server.send_message(msg)
    server.quit()