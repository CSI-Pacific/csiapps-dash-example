from dash_auth_external import DashAuthExternal
from dash import Dash, Input, Output, html, dcc, no_update, dash_table
import requests
import os
import json

from dotenv import load_dotenv
load_dotenv()

# using spotify as an example
AUTH_URL = "http://127.0.0.1:8000/o/authorize"
TOKEN_URL = "http://127.0.0.1:8000/o/token/"
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

API_PEOPLE_URL = "http://127.0.0.1:8000/api/registration/persons/"
API_ME_URL = "http://127.0.0.1:8000/api/csiauth/me/"

# creating the instance of our auth class
auth = DashAuthExternal(AUTH_URL,
                        TOKEN_URL,
                        client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET)
server = (
    auth.server
)  # retrieving the flask server which has our redirect rules assigned


app = Dash(__name__, server=server)  # instantiating our app using this server

app.layout = html.Div([
    dcc.Interval(
        id="init-interval",
        interval=500,  # e.g., 1 second after page load
        n_intervals=0,
        max_intervals=1   # This ensures it fires only once
    ),
    html.H2("Who am I?"),
    html.Pre(id="current-user"),
    html.H2("People List"),
    dash_table.DataTable(
        id="person-table",
        columns=[
            {"name": "ID", "id": "id"},
            {"name": "First Name", "id": "first_name"},
            {"name": "Last Name", "id": "last_name"},
            {"name": "Email", "id": "email"},
        ],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"},
    )
])

@app.callback(
    Output("person-table", "data"),
    Output("current-user", "children"),
    Input("init-interval", "n_intervals")
)
def initial_view(n):
    if n == 0:
        """When user clicks 'Fetch DRF Data', call the DRF endpoint with the OAuth token."""
        token = auth.get_token()

        if not token:
            return "No token found. You may need to authorize first."

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
                people_res = data.get("results", [])
            if user_resp.status_code == 200:
                data = user_resp.json()
                user_res = json.dumps(data)

            return people_res, user_res
        except Exception as e:
            return f"Error calling DRF: {str(e)}"
    return no_update

if __name__ == "__main__":
    app.run(debug=True, port=8050)