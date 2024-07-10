import http.client
import json
import requests

def CREATE_LIBRARY_ACCOUNT(student_id):
    try:
        conn = http.client.HTTPConnection("localhost", 80)
        payload = json.dumps({
            "studentId": student_id
        })
        headers = {
            'Content-Type': 'application/json'
        }
        conn.request("POST", "/api/register", payload, headers)
        response = conn.getresponse()
        if response.status == 200:
            return True
        else:
            print(f"Failed to create library account. Status code: {response.status}")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False



def CREATE_FINANCE_ACCOUNT(student):
    try:
        data = {"studentId": student.student_id}
        url = 'http://localhost:8081/accounts/'
        response = requests.post(url, json=data)
        if response.status_code == 201:           
            return True
        else:
            print(f"Failed to create finance account. Status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False


def get_student_info(student_id):
    url = f"http://localhost:8081/accounts/student/{student_id}"
    
    try:
        response = requests.get(url)
        
        switch = {
            200: lambda account_info: {
                'acc': True,
                'bal': account_info.get('hasOutstandingBalance', False),
                'grad': account_info.get('eligibleForGraduation', False),
                'err': False
            },
            404: lambda _: {'acc': False, 'err': False},
            'default': lambda _: {'err': "Something Went Wrong!"}
        }
        
        return switch.get(response.status_code, switch['default'])(response.json() if response.status_code == 200 else None)
    
    except requests.RequestException as e:
        return {'err': "Unable to Send Request. Please ensure Finance Module is Running"}
