from msal import PublicClientApplication
import requests



#%%
def get_access_token(client_id, client_secret, tenant_id):
    app = PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception("Failed to get access token", result)


if __name__ == "__main__":
    client_id = "your-client-id"
    client_secret = "your-client-secret"
    tenant_id = "your-tenant-id"

    access_token = get_access_token(client_id, client_secret, tenant_id)
    print(access_token)  # This prints the acquired access token


#%%
def get_notebooks(access_token):
    url = "https://graph.microsoft.com/v1.0/me/onenote/notebooks"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json()

