import requests
from datetime import datetime

def GET_INVOICE_DATE():
    # Function to get the due date; replace with your actual implementation
    return datetime.now().strftime('%Y-%m-%d')

def GENERATE_INVOICE(amount, student_id):
    data = {
        "amount": float(amount),  # Ensure amount is a float
        "dueDate": GET_INVOICE_DATE(),
        "type": "TUITION_FEES",
        "account": {
            "studentId": student_id
        }
    }
    print("Sending data to invoice API:", data)
    url = "http://localhost:8081/invoices/"
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        print("Response status code:", response.status_code)
        print("Response content:", response.content)  # Log the raw response content

        if response.status_code == 201:
            invoice_data = response.json()
            return {
                "is_created": True,
                "reference": invoice_data.get('reference', None)
            }
        elif response.status_code == 422:
            return {
                "is_created": False,
                "invalid_student": True
            }
        else:
            return {
                "is_created": False,
            }
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {
            "is_created": False,
        }

def CANCEL_INVOICE(reference):
    url = f"http://localhost:8081/invoices/{reference}/cancel"
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers)
        print("Response status code:", response.status_code)
        print("Response content:", response.content)

        if response.status_code == 200:
            return {
                "is_cancelled": True,
                "message": f"Invoice {reference} successfully cancelled."
            }
        elif response.status_code == 404:
            return {
                "is_cancelled": False,
                "message": f"Invoice {reference} not found."
            }
        elif response.status_code == 422:
            return {
                "is_cancelled": False,
                "message": f"Invoice {reference} cannot be cancelled due to invalid state."
            }
        else:
            return {
                "is_cancelled": False,
                "message": f"Failed to cancel invoice {reference}. Because it is already paid."
            }
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {
            "is_cancelled": False,
            "message": f"An error occurred: {e}"
        }


