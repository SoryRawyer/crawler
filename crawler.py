import socket, re, sys
from urllib import urlencode


neu = "cs5700.ccs.neu.edu"
path = "/accounts/login/"

# The main function of the webcrawler
# Sends an initial GET request to the Fakebook homepage, then send a POST
# request with the given log in credentials
# After login, the function then collects and checks links found on the site
# for the secret flags
def crawler(args):
  username = args[1]
  password = args[2]

  # send a GET request to the fakebook homepage
  a = geturl(neu,"/fakebook/","GET"," ")
  token = getToken(a[0])[0]
  sessionid = getSessionId(a[0])[0]
  #encode login information
  parameter = urlencode({'csrfmiddlewaretoken':token,
                          'username': username,
                          'password': password,
                          'next':'/fakebook/'})
  global links
  links = []
  global fqueue
  fqueue=[]
  # Send a POST request to log in to Fakebook
  b = postUrl(neu,path,username,password,token, sessionid, parameter, "")
  # Get the initial set of links
  getlinks(b)
  # For each link we find, get the links from those pages and check for flags
  for each in links:
    if each[0] == "/":
      getlinks(geturl2(neu,each,"GET","DNT: 1\r\nReferer: http://cs5700.ccs.neu.edu/fakebook/\r\nCookie: csrftoken="+token+"; sessionid="+cid+"\r\nConnection: keep-alive"))


# Open a socket and send a GET request
def geturl(url,path,command,others):
    ss= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.connect((url,80))
    ss.send("%s %s HTTP/1.1\r\nHost: %s\r\n%s\r\n\r\n" %(command,path,neu,others))
    buf = ss.recv(4096)
    ss.close()
    return chkresponse([buf])


# Check response codes and handle them accordingly by either sending a
# request to a new URL, retry the request, ignore the URL, or return the
# page text to be searched for links
def redirect2(header,others, path):
    hList = header[0].split("\r\n")
    status = hList[0].split(" ")[1]
    if status =="200":
        findflag(header)
        return header
    # Handle temporarily or permanently moved pages
    elif status == "302" or status == "301":
        newPath = hList[6]
        newPath = newPath.split(neu)[1]
        geturl2(neu,newPath,"GET",others)
        return newPath
    # Server error, retry request until we get a differet response
    elif status == "500":
        geturl2(neu, path, "GET", others)
    # 403 - Forbidden or 404 - Not Found. Either way, ignore the URL
    elif status == "403" or status == "404":
        return ""

# Open a socket and send a GET request
def geturl2(url,path,command,others):
    ss= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.connect((url,80))
    ss.send("%s %s HTTP/1.1\r\nHost: %s\r\n%s\r\n\r\n" %(command,path,neu,others))
    buf = ss.recv(4096)
    ss.close()
    return redirect2([buf],others, path)

# check response for first geturl
def chkresponse(header):
    list1 = header[0].split("\r\n")
    status = list1[0].split(" ")
    if status[1] == "200":
        return header
    elif status[1] == "302": # redirect
        redirect = list1[5].split(neu)[1]
        return geturl(neu,redirect,"GET"," ")
    elif status =="400": # Bad request
        print "HTTP 400: Bad Request"

# Get csrftoken
def getToken(header):
    regex = "csrftoken=(.+?);"
    pattern = re.compile(regex)
    token = re.findall(pattern,str(header))
    return token

# Get session id
def getSessionId(header):
    regex = "sessionid=(.+?);"
    pattern = re.compile(regex)
    sid = re.findall(pattern,str(header))
    return sid


# Send a POST request to log in, then send a GET request for the homepage 
def postUrl(url,path,username,password,token, sessionid, parameter ,message):#post 
    ss= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.connect((url,80))
    ss.send("POST /accounts/login/ HTTP/1.1\r\nHost: cs5700.ccs.neu.edu\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 109\r\nReferer: http://cs5700.ccs.neu.edu/accounts/login/?next=/fakebook/\r\nCookie: csrftoken="+token+"; sessionid="+sessionid+"\r\n\r\n"+parameter)
    buf = ss.recv(4096)
    global cid
    cid = getSessionId([buf])[0]
    ss.send("GET /fakebook/ HTTP/1.1\r\nHost: cs5700.ccs.neu.edu\r\nDNT: 1\r\nReferer: http://cs5700.ccs.neu.edu/accounts/login/?next=/fakebook/\r\nCookie: csrftoken="+token+"; sessionid="+cid+"\r\nConnection: keep-alive\r\n\r\n")
    buf = ss.recv(4096)
    ss.close()
    return [buf]

# Add the URL, but only if we haven't seen it yet
def chkdupl(tqueue):
    nqueue = set(tqueue)
    for each in tqueue:
        if(each not in links):
            links.append(each)

# Get links from a page
def getlinks(text):
    text1 = str(text)
    regex = 'a href="(.+?)"'
    pattern = re.compile(regex)
    tqueue = re.findall(pattern,text1)
    chkdupl(tqueue)

# Use regular expressions to get the secret flags
def findflag(text):
    text1 = text[0]
    regex = '<h2 class=\\\'secret_flag\\\' style="color:red">FLAG: .{64}</h2>'
    pattern = re.compile(regex)
    flags = re.findall(pattern,text1)
    if flags:
        flag = flags[0][48:112]
        print flag
        fqueue.append(flag)


if __name__ == "__main__":
  if len(sys.argv) != 3:
    print "Improper usage. Input must be './webcrawler [username] [password]'"
  else:
    crawler(sys.argv)
