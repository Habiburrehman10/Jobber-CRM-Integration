from flask import Flask, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Access individual configuration values
os.environ["BEARER_TOKEN"] = os.getenv('BEARER_TOKEN')
# os.environ["X-JOBBER-GRAPHQL-VERSION"] = os.getenv('X-JOBBER-GRAPHQL-VERSION')
os.environ["CLIENT_SECRET"] = os.getenv('CLIENT_SECRET')
os.environ["CLIENT_ID"] = os.getenv('CLIENT_id')
os.environ["REFRESH_TOKEN"] = os.getenv('REFRESH_TOKEN')

graphql_endpoint = 'https://api.getjobber.com/api/graphql'
headers = {
    'Authorization': f'Bearer {os.environ["BEARER_TOKEN"]}',
    'X-JOBBER-GRAPHQL-VERSION': '2024-08-30'
}


def refresh_token():
    api_url = "https://api.getjobber.com/api/oauth/token"
    payload = {
        "client_id": os.environ["CLIENT_ID"],
        "client_secret": os.environ["CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["REFRESH_TOKEN"]
    }
    try:
        response = requests.post(api_url, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")
            # Save the new tokens in environment variables
            os.environ["BEARER_TOKEN"] = new_access_token
            os.environ["REFRESH_TOKEN"] = new_refresh_token
            print("Token refreshed successfully!")
            return new_access_token, new_refresh_token
        else:
            print("Failed to refresh token. Status code:", response.status_code)
            return None, None
    except Exception as e:
        print("Error refreshing token:", e)
        return None, None


def get_client_by_phone(phone_number):
    # query = """
    # query SampleQuery ($searchTerm: String){
    #   clients(searchTerm: $searchTerm){
    #     nodes {
    #       id
    #       name
    #       firstName
    #       phones{
    #         number
    #       }
    #       billingAddress{
    #         city
    #         country
    #         postalCode
    #         province
    #         street
    #         street1
    #         street2
    #       }
    #     }
    #   }
    # }
    # """
    query = """query SampleQuery { clients { totalCount } }"""
    variables = {
        #"searchTerm": str(phone_number)  # Searching by phone number
        "phoneNumber": phone_number
    }

    try:
        response = requests.post(graphql_endpoint, json={'query': query, 'variables': variables}, headers=headers)
        print(response)

        if response.status_code == 401:
            print(response.status_code)
            # Refresh the token if it has expired
            refresh_token()
            headers["Authorization"] = f'Bearer {os.environ["BEARER_TOKEN"]}'
            response = requests.post(graphql_endpoint, json={'query': query, 'variables': variables}, headers=headers)

        return response.json()
        print(response_json)

        # Extract client information from response
        # client_data = response_json['data']['clients']['nodes']
        # if len(client_data) > 0:
        #     client_info = client_data[0]  # Fetching the first matched client
        #     return client_info
        # else:
        #     return "No client found with the provided phone number."

    except json.JSONDecodeError as e:
        return f"JSON decoding error: {e}"

    except Exception as e:
        return f"An error occurred: {e}"


# Define the /webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Get phone number from request JSON
        req_data = request.get_json()
        phone_number = req_data.get('phone_number')  # Change the key based on your webhook payload

        if phone_number:
            # Call get_client_by_phone function to get client info by phone number from Jobber
            client_info = get_client_by_phone(phone_number)
            print(client_info)
            return jsonify({
                'status': 'success',
                'client_info': client_info
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'No phone_number provided in the request.'
            }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # Run Flask app
    app.run(debug=True)
