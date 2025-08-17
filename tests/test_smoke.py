def test_availability(status_client):
    response = status_client.get()
    is_users_loaded = response.json()['database']
    assert is_users_loaded is True
