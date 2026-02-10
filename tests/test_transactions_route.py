from fastapi.testclient import TestClient

from main import app

Client = TestClient(app)


def make_auth_headers(email: str = "test@example.com", password: str = "secret"):
    # register (idempotent)
    Client.post("/api/v1/register", json={"name": "Test", "email": email, "password": password})
    # login to get token
    resp = Client.post("/api/v1/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_update_transaction_amount_same_account():
    headers = make_auth_headers()

    # create an account
    acct_resp = Client.post(
        "/api/v1/accounts", json={"name": "Checking", "initial_balance": 100}, headers=headers
    )
    assert acct_resp.status_code == 200
    account = acct_resp.json()
    assert float(account["balance"]) == 100.0

    # create a category (income)
    cat_resp = Client.post("/api/v1/categories", json={"name": "Salary", "kind": "income"}, headers=headers)
    assert cat_resp.status_code == 201
    category = cat_resp.json()

    # create a transaction (income 50)
    from datetime import date

    tx_payload = {
        "name": "Paycheck",
        "date": str(date.today()),
        "amount": 50,
        "notes": "",
        "account_id": account["id"],
        "category_id": category["id"],
        "kind": "income",
    }

    tx_resp = Client.post("/api/v1/transactions", json=tx_payload, headers=headers)
    assert tx_resp.status_code == 201
    tx = tx_resp.json()

    # account balance should be 150
    acct_get = Client.get(f"/api/v1/accounts/{account['id']}", headers=headers)
    assert acct_get.status_code == 200
    assert float(acct_get.json()["balance"]) == 150.0

    # update transaction amount to 100 (same account)
    update_resp = Client.put(f"/api/v1/transactions/{tx['id']}", json={"amount": 100}, headers=headers)
    assert update_resp.status_code == 200
    updated_tx = update_resp.json()
    assert float(updated_tx["amount"]) == 100.0

    # account balance should now be 200 (previous 150 + delta 50)
    acct_get2 = Client.get(f"/api/v1/accounts/{account['id']}", headers=headers)
    assert acct_get2.status_code == 200
    assert float(acct_get2.json()["balance"]) == 200.0


def test_update_transaction_kind_and_amount_same_account():
    headers = make_auth_headers(email="user2@example.com", password="secret2")

    # create an account
    acct_resp = Client.post(
        "/api/v1/accounts", json={"name": "Checking", "initial_balance": 100}, headers=headers
    )
    assert acct_resp.status_code == 200
    account = acct_resp.json()

    # create categories
    income_cat = Client.post(
        "/api/v1/categories", json={"name": "Salary", "kind": "income"}, headers=headers
    ).json()
    expense_cat = Client.post(
        "/api/v1/categories", json={"name": "Food", "kind": "expense"}, headers=headers
    ).json()

    # create a transaction (income 50)
    from datetime import date

    tx_payload = {
        "name": "Paycheck",
        "date": str(date.today()),
        "amount": 50,
        "notes": "",
        "account_id": account["id"],
        "category_id": income_cat["id"],
        "kind": "income",
    }

    tx_resp = Client.post("/api/v1/transactions", json=tx_payload, headers=headers)
    assert tx_resp.status_code == 201
    tx = tx_resp.json()

    # account balance should be 150
    acct_get = Client.get(f"/api/v1/accounts/{account['id']}", headers=headers)
    assert float(acct_get.json()["balance"]) == 150.0

    # update transaction to expense 30
    update_resp = Client.put(
        f"/api/v1/transactions/{tx['id']}",
        json={"amount": 30, "kind": "expense", "category_id": expense_cat["id"]},
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated_tx = update_resp.json()
    assert updated_tx["kind"] == "expense"
    assert float(updated_tx["amount"]) == 30.0

    # expected balance: previous 150, prev_effect +50 -> new_effect -30, delta = -80 -> new balance 70
    acct_get2 = Client.get(f"/api/v1/accounts/{account['id']}", headers=headers)
    assert float(acct_get2.json()["balance"]) == 70.0
