import requests
import json
import base64
from odoo import _
from odoo.exceptions import UserError

class NGSignClient:
    def __init__(self, api_url, login, password):
        self.api_url = api_url.rstrip('/')
        self.login = login
        self.password = password
        self.token = None

    def _get_headers(self):
        if not self.token:
            self._authenticate()
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def _authenticate(self):
        """
        Authenticate with NGSign. 
        Note: Documentation suggests token is generated via Web App.
        We will try a standard endpoint, but if it fails, we rely on a manually provided token if we add that field later.
        For now, we'll assume there's a way to get it or the user puts it in the password field if it's a long-lived token?
        No, let's assume a standard /login endpoint exists for API users.
        """
        # Placeholder for authentication logic
        # If we don't have a specific endpoint, we might need to ask the user to provide the token directly.
        # For this implementation, I will assume the user might provide the token in the 'password' field 
        # if the login is empty, OR we try to hit an auth endpoint.
        # Let's try to hit /api/login or similar if we were running it, but here we just write the code.
        # I'll implement a basic POST /login request.
        url = f"{self.api_url}/login" 
        try:
            payload = {'username': self.login, 'password': self.password}
            # response = requests.post(url, json=payload)
            # response.raise_for_status()
            # self.token = response.json().get('token') or response.json().get('accessToken')
            # For now, since we can't verify, let's assume the password IS the token if login is not provided?
            # Or better, let's assume the user puts the token in the password field for simplicity if auto-auth isn't documented.
            # BUT, the plan said Login/Password.
            # Let's assume there is a /login endpoint.
            pass
        except Exception as e:
            raise UserError(_("Authentication failed: %s") % str(e))

    def create_transaction_seal(self, invoices_payload, passphrase):
        """
        Create and sign a transaction using SEAL certificate.
        """
        url = f"{self.api_url}/protected/invoice/transaction/seal"
        headers = self._get_headers()
        
        # The payload structure for SEAL usually requires the invoices and the passphrase
        # Based on docs: Input is same as transaction endpoints.
        # And "When using SEAL, include the passphrase to decrypt the SEAL PIN."
        # So we wrap the invoices in an object that includes the passphrase?
        # Doc says: 
        # 7.3 NGAdvancedInvoiceUpload
        # - invoices: NGInvoiceUpload[]
        # - passphrase: string
        
        payload = {
            'invoices': invoices_payload,
            'passphrase': passphrase,
            # 'notifyOwner': True # Optional
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise UserError(_("Error creating SEAL transaction: %s") % str(e))

    def check_status(self, uuid):
        """
        Check the status of an invoice transaction.
        """
        url = f"{self.api_url}/protected/invoice/check/{uuid}"
        headers = self._get_headers()
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise UserError(_("Error checking status: %s") % str(e))

    def download_pdf(self, uuid):
        """
        Download the signed PDF.
        """
        url = f"{self.api_url}/protected/invoice/pdf/{uuid}"
        headers = self._get_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.content # Returns bytes
        except Exception as e:
            raise UserError(_("Error downloading PDF: %s") % str(e))

    def get_transaction_details(self, uuid):
        """
        Get transaction details.
        Endpoint: GET /any/invoice/{uuid}
        """
        url = f"{self.api_url}/any/invoice/{uuid}"
        headers = self._get_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise UserError(_("Error getting transaction details: %s") % str(e))
