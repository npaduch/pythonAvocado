# For best results, run this from the command line.
#
# Run:
# python AvocadoSignTest.py
#
# Then answer the following...
#    Email of an Avocado account:
#    Password:
#    Developer ID:
#    Developer key:
#
# If successful, you'll see your developer signature...
#    1:crazylongweirdlookinghashedstring

import cookielib
import getpass
import hashlib
import logging
import json
import urllib
import urllib2
import threading
import time
import datetime
import win32gui
import win32process

AVOCADO_API_URL_BASE = "https://avocado.io/api/";
AVOCADO_API_URL_LOGIN = AVOCADO_API_URL_BASE + "authentication/login";
AVOCADO_API_URL_COUPLE = AVOCADO_API_URL_BASE + "couple";
AVOCADO_API_URL_ACT = AVOCADO_API_URL_BASE + "activities";
AVOCADO_API_URL_SEND = AVOCADO_API_URL_BASE + "conversation";
AVOCADO_COOKIE_NAME = "user_email";
AVOCADO_USER_AGENT = "Avocado Test Api Client v.1.0";
ERROR_MSG = "Login failed."

class AvocadoAPI(object):
  def __init__(self, auth_client):
    '''
    @type authClient: L{AuthClient}
    '''
    self.auth_client = auth_client
    self.couple = None
    self.act = None
    self.userid = None
    self.otherid = None
    self.username = None
    self.othername = None
    self.message_list = {}

  def update_from_command_line(self):
    # Ask the user for all of the necessary authentication info
    self.auth_client.email = raw_input("Email of an Avocado account: ")
    self.auth_client.password = getpass.getpass()
    #self.auth_client.dev_id = int(raw_input("Developer ID: "))
    #self.auth_client.dev_key = raw_input("Developer key: ")
    self.auth_client.dev_id = 81
    self.auth_client.dev_key = "7UZiE6na8htEm1f2HhqimSQyX213pgmQjEvxiGnvpzccvE+GDiMrZ/1v9RlfPKFY"

    self.auth_client.update_signature()
    if self.auth_client.dev_signature is None:
      print ERROR_MSG
      return
    
    print "Getting most recent messages."
    self.update_couple();
    if self.couple is None:
      print ERROR_MSG
    else:
      #print "\nBelow is your Avocado API signature:"
      #print self.auth_client.dev_signature
      temp = json.loads(self.couple.read())
      self.userid = temp["currentUser"]["id"] 
      self.username = temp["currentUser"]["firstName"] 
      self.otherid = temp["otherUser"]["id"] 
      self.othername = temp["otherUser"]["firstName"]
      print  "Hello",self.username

  def update_couple(self):
    try:
      cookies = cookielib.CookieJar()
      request = urllib2.Request(
        url = AVOCADO_API_URL_COUPLE,
        headers = {
          "Content-type": "application/x-www-form-urlencoded",
          "User-Agent": AVOCADO_USER_AGENT,
          "X-AvoSig": self.auth_client.dev_signature,
          }
      )
      request.add_header('Cookie',
        '%s=%s' % (AVOCADO_COOKIE_NAME, self.auth_client.cookie_value))
      self.couple = urllib2.urlopen(request)

    except urllib2.URLError, e:
      logging.error(e.read())
    
  def get_msgs(self):
    try:
      cookies = cookielib.CookieJar()
      request = urllib2.Request(
        url = AVOCADO_API_URL_ACT,
        headers = {
          "Content-type": "application/x-www-form-urlencoded",
          "User-Agent": AVOCADO_USER_AGENT,
          "X-AvoSig": self.auth_client.dev_signature,
          }
      )
      request.add_header('Cookie',
        '%s=%s' % (AVOCADO_COOKIE_NAME, self.auth_client.cookie_value))
      self.act = urllib2.urlopen(request)

    except urllib2.URLError, e:
      logging.error(e.read())

    if self.act is not None:
      first = 0
      other = 0
      temp = json.loads(self.act.read())
      for item in temp:
        if item["type"] == "message":
          if item["timeCreated"] not in self.message_list.keys():
            if first == 0:
              print
              first = 1
            self.message_list[\
              item["timeCreated"]]\
              = self.get_name(item["userId"])+' ('+\
              datetime.datetime.fromtimestamp(int(item["timeCreated"])/1000).strftime("%H:%M:%S")+\
              "):\t",item["data"]["text"]
            print self.get_name(item["userId"])+' ('+\
              datetime.datetime.fromtimestamp(int(item["timeCreated"])/1000).strftime("%H:%M:%S")+\
              "):\t",item["data"]["text"]
            if item["userId"] == self.otherid:
              other = 1
      if first == 1:
        print ">",
        if other == 1:
          self.flash_window()

  def send_msg(self,msg):
    if msg == '':
        return
    if msg == 'help':
        print_help()
        return
    if msg == 'get':
        self.get_msgs()
        return
    if msg == 'lasttime':
        self.update_couple()
        temp = json.loads(self.couple.read())
        time = temp["otherUser"]["lastReadTime"] 
        print self.othername, "last read at", datetime.datetime.fromtimestamp(int(time)/1000).strftime("%H:%M:%S")
        return
    try:
      cookies = cookielib.CookieJar()
      request = urllib2.Request(
        url = AVOCADO_API_URL_SEND,
        headers = {
          "Content-type": "application/x-www-form-urlencoded",
          "User-Agent": AVOCADO_USER_AGENT,
          "X-AvoSig": self.auth_client.dev_signature,
          },
        data = urllib.urlencode(
          {"message": msg}
          )
      )
      request.add_header('Cookie',
        '%s=%s' % (AVOCADO_COOKIE_NAME, self.auth_client.cookie_value))
      self.act = urllib2.urlopen(request)

    except urllib2.URLError, e:
      logging.error(e.read())
      
  def get_name(self,id):
    if id == self.userid: return self.username
    else: return self.othername
    
  def flash_window(self):
    win32gui.EnumWindows(self.check_window,None)
      
  def check_window(self,window,ignore):
    if win32gui.GetWindowText(window) == "talk":
        win32gui.FlashWindowEx(window,2,1,1000)
    
class AuthClient(object):
  def __init__(self, email = None, password = None, dev_id = 0, dev_key = None):
    '''
    @type email: C{string}
    @type password: C{string}
    @type dev_id: C{int}
    @type dev_key: C{string}
    '''
    self.email = email
    self.password = password
    self.dev_id = dev_id
    self.dev_key = dev_key
    self.dev_signature = None
    self.cookie_value = None

  def get_cookie_from_login(self):
    params = urllib.urlencode({
      "email": self.email,
      "password": self.password,
    })
    try:
      request = urllib2.Request(
        url = AVOCADO_API_URL_LOGIN,
        data = params,
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "User-Agent": AVOCADO_USER_AGENT
            }
        )
      response = urllib2.urlopen(request)

      cookies = cookielib.CookieJar()
      cookies.extract_cookies(response, request)
      for cookie in cookies:
          if cookie.name == AVOCADO_COOKIE_NAME:
               self.cookie_value = cookie.value
               break
    except urllib2.URLError, e:
      logging.error(e.read())

  def hash_signature(self):
    hasher = hashlib.sha256()
    hasher.update(self.cookie_value + self.dev_key)
    self.dev_signature = '%d:%s' % (self.dev_id, hasher.hexdigest())

  def update_signature(self):
    self.get_cookie_from_login()
    if self.cookie_value is not None:
      self.hash_signature()

class TimerClass(threading.Thread):
    def __init__(self,api):
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.api = api;
        self.total_time = 0

    def run(self):
        while not self.event.is_set():
            self.api.get_msgs()
            self.total_time+=1
            if self.total_time > 600:
              print "We have stopped polling for messages. Please exit and relogin."
              self.stop()
            self.event.wait( 60 )

    def stop(self):
        self.event.set()
        print "ALERT: No longer Polling. Exit and relogin."

def print_help():
    print
    print "------------------------------------------"
    print "--              COMMANDS                --"
    print "------------------------------------------"
    print
    print " Empty input lines are ignored."
    print
    print " 'get'      -- Forces update of conversation"
    print " 'lasttime' -- Gets last time that" 
    print "               other user looked at the"
    print "               conversation."
    print " 'help'     -- Displays this help dialog"
    print
    print
        
def main():
  logging.basicConfig(level=logging.DEBUG)
  win32gui.SetWindowText(win32gui.GetForegroundWindow(),"talk")
  api = AvocadoAPI(AuthClient())
  while api.userid == None:
    api.update_from_command_line()
  timer = TimerClass(api)
  timer.start()
  cmd = ''
  while cmd != "exit":
    #if cmd == "get":
    #  api.get_msgs()
    #  cmd = raw_input(">")
    #  continue
    cmd = raw_input(">")
    api.send_msg(cmd)
  timer.stop()
    
  


if __name__ == '__main__':
  main()
