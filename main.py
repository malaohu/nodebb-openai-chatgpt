import requests
import json
import openai
import uuid
import time
import re
import config as conf
openai.api_key = conf.API_KEY
tern = re.compile(r'<[^>]+>',re.S)

class nodebb_gpt():

    def __init__(self):
        self.api_route = {
            "notice": conf.NB_HOST+"/api/notifications?filter=mention",
            "replay": conf.NB_HOST+"/api/v3/topics/",
        }


    def get_unread(self, last_pid=0):
        notice_info = self.req_util("GET", self.api_route.get("notice"), None)
        if not notice_info and notice_info.get("notifications") is None:
            return None
            
        pid_list = [last_pid]
        for notic in notice_info.get("notifications"):
            pid_list.append(notic.get("pid"))
            if notic and notic.get("pid", -1) > last_pid and notic.get("bodyLong") and notic.get("bodyLong").find("@ChatGPT")>-1:
                ask_str = notic.get("bodyLong")
         
                if ask_str.find("@ChatGPT")> -1:
                    result = ""
                    try:
                        result = self.gtp(ask_str)
                    except Exception as e:
                        print (e)
                        result = "哎呀, ChatGPT 出问题了, 站长快来修复一下~ @malaohu "
                    print (self.send_post(notic.get("tid"), notic.get("pid"), result, ask_str, notic.get("user").get("username")))
                    time.sleep(5)
            else:
                break
        print (pid_list)
        return max(pid_list)
            
                
    def gtp(self, prompt):
        res =  openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt.replace("@ChatGPT", ""),
            temperature=0.7,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return res.choices[0].text


    def send_post(self, tid, pid, content, quote_content="", username=""):
        '''
        帖子中发回复内容
        '''
        if quote_content:
            content = "\n"+ username.replace("[[global:guest]]", "guest") + "说:\n" + re.sub(r'^', '>',  quote_content.replace("@ChatGPT", "") , flags=re.M)+ "\n\n" + content
        data = {"uuid": str(uuid.uuid1()), "tid": tid,
                "toPid": pid, "content": tern.sub("", content)}

        url = self.api_route.get("replay") + str(tid)

        return self.req_util("POST", url, {},  data)

    def req_util(self, method, url, params={}, data={}, retry=3):
        retry = retry - 1
        headers = {
            'Authorization': 'Bearer '+ conf.NB_TOKEN,
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request(method, url, headers=headers, data=json.dumps(data))
            return json.loads(response.text)
        except Exception as e:
            print("ERROR: ", e)
            if retry > 0:
                return self.req_util(method, url, params=params, data=data, retry=retry)
            return None


    def doit(self):

        fileName='last_pid'
        while(1==1):
            ofile = open(fileName, "r")
            last_pid = ofile.read()    
            ofile.close()

            print ("last_pid", last_pid)
            _last_pid = self.get_unread(last_pid=int(last_pid))
            print ("new_pid", _last_pid)
            if _last_pid and last_pid and _last_pid > int(last_pid):
                with open(fileName,'w',encoding='utf-8') as file:
                    file.write(str(_last_pid))
            time.sleep(15)


if __name__ == '__main__':
    nodebb_gpt().doit()
