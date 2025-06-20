from dash_auth_external import DashAuthExternal
from dash import Dash, Input, Output, html, dcc, no_update, dash_table
import requests
import os
import json
import traceback

from dotenv import load_dotenv
load_dotenv()

SITE_URL = os.environ.get("SITE_URL","http://127.0.0.1:8000")
APP_URL = os.environ.get("APP_URL","http://127.0.0.1:8050")


# using spotify as an example
AUTH_URL = f"{SITE_URL}/o/authorize"
TOKEN_URL = f"{SITE_URL}/o/token/"
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

API_PEOPLE_URL = f"{SITE_URL}/api/registration/profile/"
API_ME_URL = f"{SITE_URL}/api/csiauth/me/"

# creating the instance of our auth class
auth = DashAuthExternal(AUTH_URL,
                        TOKEN_URL,
                        app_url=APP_URL,
                        client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET)
server = (
    auth.server
)  # retrieving the flask server which has our redirect rules assigned


app = Dash(__name__, server=server)  # instantiating our app using this server

app.layout = html.Div([
    dcc.Location(id="redirect-to", refresh=True),

    dcc.Interval(
        id="init-interval",
        interval=500,  # e.g., 1 second after page load
        n_intervals=0,
        max_intervals=1   # This ensures it fires only once
    ),
    html.H2("Who am I?"),
    html.Pre(id="current-user"),
    html.H2("Profile List"),
    dash_table.DataTable(
        id="person-table",
        columns=[
            {"name": "ID", "id": "id"},
            {"name": "First Name", "id": "first_name"},
            {"name": "Last Name", "id": "last_name"},
            {"name": "Sport", "id":"sport"},
            {"name": "Email", "id": "email"},
            {"name": "Enrollment", "id":"enrollment_status"}
        ],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"},
    )
])

@app.callback(
    Output("redirect-to", "href"),
    Output("person-table", "data"),
    Output("current-user", "children"),
    Input("init-interval", "n_intervals")
)
def initial_view(n):
    """When user clicks 'Fetch DRF Data', call the DRF endpoint with the OAuth token."""
    try:
        token = auth.get_token()
    except Exception as e:

        ## HERE, HOW DO I FORWARD A REDIRECT TO APP_URL???

        print(e)

        auth_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={APP_URL}"

        print(f"Forward to {APP_URL}")

        return APP_URL, no_update, no_update

    if not token:
        return no_update, no_update, no_update
        # return [], "No token found. You may need to authorize first."

    # Call DRF using the Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    people_res = []
    user_res = ""
    try:
        people_resp = requests.get(API_PEOPLE_URL, headers=headers, timeout=5)
        user_resp = requests.get(API_ME_URL, headers=headers, timeout=5)

        if people_resp.status_code == 200:
            # Return raw JSON as a string
            data = people_resp.json()
            people_res = [
                {'id':p['id'],
                 'first_name':p['person']['first_name'] if p['person'] else None,
                 'last_name':p['person']['last_name'] if p['person'] else None,
                 'email':p['person']['email'] if p['person'] else None,
                 'sport':p['sport']['name'] if p['sport'] else None,
                 'enrollment_status':p['current_enrollment']['enrollment_status'] if p['current_enrollment'] else None
                 }
                for p in data.get("results", [])]

            print(people_res)

        if user_resp.status_code == 200:
            data = user_resp.json()
            user_res = json.dumps(data,indent=2)

        return no_update, people_res, user_res

    except Exception as e:
        print(f"Error calling DRF: {str(e)}")

        traceback.print_exc()

        # return [], f"Error calling DRF: {str(e)}"
        return no_update



if __name__ == "__main__":
    app.run(debug=True, port=8050)