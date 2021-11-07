import requests

address = "localhost"
page = "check_new_round"
port = 8000

r = requests.get("http://"+address+":"+str(port)+"/"+page)
print r.status_code
print r.text
